import asyncio
import shutil
import hashlib
import uuid
from logging import getLogger
from pathlib import Path
from typing import Optional, Callable, Literal
from dataclasses import dataclass
from enum import Enum

import aiofiles
import aiohttp
from requests import HTTPError

from tiddl.cli.config import VIDEOS_FILTER_LITERAL
from tiddl.cli.utils.download import get_existing_track_filename
from tiddl.core.api import ApiError, TidalAPI
import sys
from tiddl.core.api.models import StreamVideoQuality, Track, TrackQuality, Video
from tiddl.core.utils import parse_track_stream, parse_video_stream
from tiddl.core.utils.format import _prepare_long_path
from tiddl.core.utils.const import (
    TRACK_QUALITY_LITERAL,
    VIDEO_QUALITY_LITERAL,
    track_qualities,
    video_qualities,
)
from tiddl.core.utils.ffmpeg import convert_to_mp4, extract_flac, fix_mp4_faststart

from .output import RichOutput

log = getLogger(__name__)

CHUNK_SIZE = 1024**2
MAX_RETRIES = 3  # Maximum number of retries for corrupt files

# ==================================================================== 
# MEJORA 1: Enums para estados de descarga 
# ==================================================================== 

class DownloadStatus(Enum): 
    """Estados posibles de una descarga""" 
    PENDING = "pending" 
    DOWNLOADING = "downloading" 
    VERIFYING = "verifying" 
    COMPLETED = "completed" 
    FAILED = "failed" 
    SKIPPED = "skipped" 
    CORRUPTED = "corrupted" 


class DownloadPriority(Enum): 
    """Prioridades de descarga""" 
    LOW = 0 
    NORMAL = 1 
    HIGH = 2 
    CRITICAL = 3 


# ==================================================================== 
# MEJORA 2: Dataclass para tracking de descarga 
# ==================================================================== 

@dataclass 
class DownloadTask: 
    """Tarea de descarga con metadata completa""" 
    url: str 
    output_path: Path 
    track_id: Optional[int] = None 
    track_title: Optional[str] = None 
    expected_size: Optional[int] = None  # Bytes esperados 
    expected_hash: Optional[str] = None  # Hash MD5/SHA256 esperado 
    status: DownloadStatus = DownloadStatus.PENDING 
    priority: DownloadPriority = DownloadPriority.NORMAL 
    attempts: int = 0 
    max_attempts: int = 3 
    bytes_downloaded: int = 0 
    error_message: Optional[str] = None 
    
    @property 
    def progress_percentage(self) -> float: 
        """Porcentaje de progreso (0-100)""" 
        if not self.expected_size or self.expected_size == 0: 
            return 0.0 
        return (self.bytes_downloaded / self.expected_size) * 100 
    
    @property 
    def can_retry(self) -> bool: 
        """Verifica si se puede reintentar""" 
        return self.attempts < self.max_attempts 
    
    def increment_attempt(self) -> None: 
        """Incrementa contador de intentos""" 
        self.attempts += 1


# ==================================================================== 
# MEJORA 5: Gestor de cola de descargas 
# ==================================================================== 

class DownloadQueue: 
    """Cola de descargas con prioridades""" 
    
    def __init__(self): 
        self.tasks: list[DownloadTask] = [] 
        self.completed: list[DownloadTask] = [] 
        self.failed: list[DownloadTask] = [] 
    
    def add_task(self, task: DownloadTask) -> None: 
        """Agrega tarea a la cola""" 
        self.tasks.append(task) 
    
    def add_tasks(self, tasks: list[DownloadTask]) -> None: 
        """Agrega múltiples tareas""" 
        self.tasks.extend(tasks) 
    
    def get_pending_tasks(self) -> list[DownloadTask]: 
        """Obtiene tareas pendientes ordenadas por prioridad""" 
        pending = [t for t in self.tasks if t.status == DownloadStatus.PENDING] 
        return sorted(pending, key=lambda t: t.priority.value, reverse=True) 
    
    def mark_completed(self, task: DownloadTask) -> None: 
        """Marca tarea como completada""" 
        task.status = DownloadStatus.COMPLETED 
        self.completed.append(task) 
        if task in self.tasks: 
            self.tasks.remove(task) 
    
    def mark_failed(self, task: DownloadTask) -> None: 
        """Marca tarea como fallida""" 
        task.status = DownloadStatus.FAILED 
        self.failed.append(task) 
        if task in self.tasks: 
            self.tasks.remove(task) 
    
    def get_stats(self) -> dict: 
        """Obtiene estadísticas de la cola""" 
        return { 
            "pending": len([t for t in self.tasks if t.status == DownloadStatus.PENDING]), 
            "downloading": len([t for t in self.tasks if t.status == DownloadStatus.DOWNLOADING]), 
            "completed": len(self.completed), 
            "failed": len(self.failed), 
            "total": len(self.tasks) + len(self.completed) + len(self.failed), 
        }



track_qualities_color: dict[TrackQuality, str] = {
    "LOW": "[gray]96 kbps",
    "HIGH": "[gray]320 kbps",
    "LOSSLESS": "[cyan]",
    "HI_RES_LOSSLESS": "[yellow]",
}

video_qualities_color: dict[StreamVideoQuality, str] = {
    "LOW": "[gray]360p",
    "MEDIUM": "[cyan]720p",
    "HIGH": "[yellow]1080p",
}


# ====================================================================
# IMPROVEMENT 4: Downloader with smart retry and verification
# ====================================================================

class ImprovedDownloader:
    """
    Downloader mejorado con:
    - Retry automático con backoff exponencial
    - Verificación de integridad
    - Gestión de rate limiting
    - Tracking detallado de progreso
    """
    
    def __init__(
        self,
        max_concurrent_downloads: int = 3,
        chunk_size: int = 1024**2, # 1MB
        timeout: int = 300, # 5 minutos
        on_progress: Optional[Callable] = None,
    ):
        self.max_concurrent = max_concurrent_downloads
        self.chunk_size = chunk_size
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.on_progress = on_progress

        # Semáforo para limitar descargas concurrentes
        self.semaphore = asyncio.Semaphore(max_concurrent_downloads)

        # Estadísticas
        self.stats = {
            "completed": 0,
            "failed": 0,
            "skipped": 0,
            "total_bytes": 0,
        }

    async def download_file(
        self,
        task: DownloadTask,
        session: aiohttp.ClientSession
    ) -> tuple[bool, Optional[str]]:
        """
        Descarga un archivo con retry y verificación

        Returns:
            tuple[success, error_message]
        """
        async with self.semaphore:
            # Si el archivo existe y es válido, saltar
            if task.output_path.exists():
                is_valid, error = await FileIntegrityChecker.verify_file_async(
                    task.output_path,
                    task.expected_size
                )

                if is_valid:
                    task.status = DownloadStatus.SKIPPED
                    self.stats["skipped"] += 1
                    return True, None
                else:
                    # Archivo corrupto, eliminar y reintentar
                    task.output_path.unlink()
            
            # Intentar descarga con reintentos
            while task.can_retry:
                task.increment_attempt()
                task.status = DownloadStatus.DOWNLOADING
                
                try:
                    # Descarga
                    success, error = await self._download_with_progress(task, session)

                    if not success:
                        if "429" in str(error) or "rate limit" in str(error).lower():
                            # Rate limiting - esperar más tiempo
                            wait_time = min(60 * task.attempts, 300) # Max 5 min
                            await asyncio.sleep(wait_time)
                            continue
                        
                        # Otro error - esperar menos
                        await asyncio.sleep(2 ** task.attempts) # Backoff exponencial
                        continue
                    
                    # Verificar integridad
                    task.status = DownloadStatus.VERIFYING
                    is_valid, error = await FileIntegrityChecker.verify_file_async(
                        task.output_path,
                        task.expected_size,
                        task.expected_hash
                    )

                    if is_valid:
                        task.status = DownloadStatus.COMPLETED
                        self.stats["completed"] += 1
                        self.stats["total_bytes"] += task.bytes_downloaded
                        return True, None
                    else:
                        # Archivo corrupto - eliminar y reintentar
                        task.output_path.unlink(missing_ok=True)
                        task.status = DownloadStatus.CORRUPTED
                        
                        if not task.can_retry:
                            break
                        
                        await asyncio.sleep(2 ** task.attempts)

                except Exception as e:
                     task.error_message = str(e)
                     
                     if not task.can_retry:
                         break
                     
                     await asyncio.sleep(2 ** task.attempts)
            
            # Todos los intentos fallaron
            task.status = DownloadStatus.FAILED
            self.stats["failed"] += 1
            return False, task.error_message or "Max retries exceeded"

    async def _download_with_progress(
        self,
        task: DownloadTask,
        session: aiohttp.ClientSession
    ) -> tuple[bool, Optional[str]]:
        """
        Descarga un archivo con tracking de progreso

        Returns:
            tuple[success, error_message]
        """
        try:
            # Crear directorio si no existe
            task.output_path.parent.mkdir(parents=True, exist_ok=True)

            # Descargar
            async with session.get(task.url, timeout=self.timeout) as response:
                # Verificar status
                if response.status == 429:
                     retry_after = response.headers.get("Retry-After", "60")
                     return False, f"Rate limited - retry after {retry_after}s"
                
                if response.status != 200:
                    return False, f"HTTP {response.status}"
                
                # Obtener tamaño
                total_size = int(response.headers.get('content-length', 0))
                if total_size > 0:
                    task.expected_size = total_size
                
                # Escribir a archivo
                task.bytes_downloaded = 0

                async with aiofiles.open(task.output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(self.chunk_size):
                        await f.write(chunk)
                        task.bytes_downloaded += len(chunk)

                        # Callback de progreso
                        if self.on_progress:
                            self.on_progress(task)
            
            return True, None
        
        except asyncio.TimeoutError:
            return False, "Download timeout"
        except aiohttp.ClientError as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    async def download_batch(
        self,
        tasks: list[DownloadTask],
        headers: Optional[dict] = None
    ) -> dict[str, int]:
        """
        Descarga un batch de archivos de forma concurrente

        Returns:
            Estadísticas de descarga
        """
        # Ordenar por prioridad
        tasks.sort(key=lambda t: t.priority.value, reverse=True)

        # Crear sesión
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
             # Crear tareas
             download_tasks = [
                 self.download_file(task, session)
                 for task in tasks
             ]

             # Ejecutar concurrentemente
             results = await asyncio.gather(*download_tasks, return_exceptions=True)

             # Procesar resultados
             for task, result in zip(tasks, results):
                 if isinstance(result, Exception):
                     task.status = DownloadStatus.FAILED
                     task.error_message = str(result)
                     self.stats["failed"] += 1
        
        return self.stats



# ==================================================================== 
# MEJORA 3: Verificador de integridad de archivos mejorado 
# ==================================================================== 

class FileIntegrityChecker: 
    """Verificador de integridad de archivos descargados""" 
    
    @staticmethod 
    async def verify_file_async( 
        file_path: Path, 
        expected_size: Optional[int] = None, 
        expected_hash: Optional[str] = None, 
        hash_algorithm: Literal["md5", "sha256"] = "md5" 
    ) -> tuple[bool, Optional[str]]: 
        """ 
        Verifica la integridad de un archivo de forma asíncrona 
        
        Returns: 
            tuple[is_valid, error_message] 
        """ 
        if not file_path.exists(): 
            return False, "File does not exist" 
        
        # Verificar tamaño 
        actual_size = file_path.stat().st_size 
        
        # Archivos muy pequeños son sospechosos 
        if actual_size < 2048:  # Menos de 2KB 
            return False, f"File too small ({actual_size} bytes)" 
        
        # Verificar tamaño esperado 
        if expected_size and abs(actual_size - expected_size) > 1024:  # Tolerancia de 1KB 
            return False, f"Size mismatch: expected {expected_size}, got {actual_size}" 
        
        # Verificar magic bytes según extensión 
        try: 
            async with aiofiles.open(file_path, "rb") as f: 
                header = await f.read(12) 
                
                if not FileIntegrityChecker._check_magic_bytes(file_path, header): 
                    return False, "Invalid file format (magic bytes check failed)" 
                
                # Para archivos MP4/M4A, verificar átomos 
                if file_path.suffix.lower() in ['.m4a', '.mp4', '.m4v']: 
                    await f.seek(0) 
                    first_256kb = await f.read(262144) 
                    
                    if b'moov' not in first_256kb: 
                        return False, "Invalid MP4/M4A: missing 'moov' atom" 
                
                # Verificar hash si se proporciona 
                if expected_hash: 
                    actual_hash = await FileIntegrityChecker._calculate_hash_async( 
                        file_path, 
                        hash_algorithm 
                    ) 
                    
                    if actual_hash != expected_hash.lower(): 
                        return False, f"Hash mismatch: expected {expected_hash}, got {actual_hash}" 
        
        except Exception as e: 
            return False, f"Verification error: {str(e)}" 
        
        return True, None 
    
    @staticmethod 
    def _check_magic_bytes(file_path: Path, header: bytes) -> bool: 
        """Verifica los magic bytes según el tipo de archivo""" 
        ext = file_path.suffix.lower() 
        
        # FLAC 
        if ext == '.flac': 
            return header.startswith(b'fLaC') 
        
        # MP4/M4A 
        elif ext in ['.m4a', '.mp4', '.m4v']: 
            return len(header) >= 8 and header[4:8] == b'ftyp' 
        
        # MP3 
        elif ext == '.mp3': 
            # ID3v2 tag o frame sync 
            return header.startswith(b'ID3') or (header[0] == 0xFF and (header[1] & 0xE0) == 0xE0) 
        
        # AAC 
        elif ext == '.aac': 
            return header.startswith(b'\xFF\xF1') or header.startswith(b'\xFF\xF9') 
        
        # Si no conocemos el formato, asumir válido 
        return True 
    
    @staticmethod 
    async def _calculate_hash_async( 
        file_path: Path, 
        algorithm: Literal["md5", "sha256"] = "md5" 
    ) -> str: 
        """Calcula el hash de un archivo de forma asíncrona""" 
        hash_obj = hashlib.md5() if algorithm == "md5" else hashlib.sha256() 
        
        async with aiofiles.open(file_path, "rb") as f: 
            while True: 
                chunk = await f.read(8192) 
                if not chunk: 
                    break 
                hash_obj.update(chunk) 
        
        return hash_obj.hexdigest()


class Downloader:
    api: TidalAPI
    rich_output: RichOutput
    semaphore: asyncio.Semaphore
    track_quality: TrackQuality
    video_quality: StreamVideoQuality
    videos_filter: VIDEOS_FILTER_LITERAL
    skip_existing: bool
    download_path: Path
    scan_path: Path

    def __init__(
        self,
        tidal_api: TidalAPI,
        threads_count: int,
        rich_output: RichOutput,
        track_quality: TRACK_QUALITY_LITERAL,
        video_quality: VIDEO_QUALITY_LITERAL,
        videos_filter: VIDEOS_FILTER_LITERAL,
        skip_existing: bool,
        download_path: Path,
        scan_path: Path,
    ) -> None:
        self.api = tidal_api
        self.rich_output = rich_output
        self.semaphore = asyncio.Semaphore(threads_count)
        self.track_quality = track_qualities[track_quality]
        self.video_quality = video_qualities[video_quality]
        self.videos_filter = videos_filter
        self.skip_existing = skip_existing
        self.download_path = download_path
        self.scan_path = scan_path
        self.dir_cache: dict[Path, set[str]] = {}

    def _scan_directory(self, dir_path: Path) -> None:
        """Scans a directory and caches its contents."""
        if dir_path not in self.dir_cache:
            try:
                self.dir_cache[dir_path] = {f.name for f in dir_path.iterdir() if f.is_file()}
            except FileNotFoundError:
                self.dir_cache[dir_path] = set()

    def _is_file_in_cache(self, file_path: Path) -> bool:
        """Checks if a file exists in the cached directory listing."""
        dir_path = file_path.parent
        if dir_path not in self.dir_cache:
            self._scan_directory(dir_path)
        return file_path.name in self.dir_cache.get(dir_path, set())

    async def _download_with_retry(
        self,
        task: DownloadTask,
        urls: list[str],
        task_id: int,
        headers: Optional[dict] = None,
    ) -> bool:
        """
        Downloads a file with automatic retry in case of corruption.
        Validates the file after each download.
        
        Returns:
            True if download was successful and validated, False if failed after all retries
        """
        tmp_path = None
        task.status = DownloadStatus.DOWNLOADING
        
        while task.can_retry:
            task.increment_attempt()
            attempt = task.attempts
            
            try:
                # Create temporary file with unique name to avoid Windows file locking collisions
                # especially on network shares where handles linger
                unique_suffix = f".part.{uuid.uuid4().hex[:8]}"
                tmp_path = task.output_path.with_suffix(task.output_path.suffix + unique_suffix)
                
                # Download
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with aiofiles.open(tmp_path, "wb") as f:
                        for url in urls:
                            async with session.get(url) as resp:
                                
                                # 1. Intercept HTTP Status Errors with specific messages
                                if resp.status == 451:
                                    raise Exception(f"HTTP 451 Unavailable For Legal Reasons (Geo-block) for {url}")
                                if resp.status == 403:
                                    raise Exception(f"HTTP 403 Forbidden (Token expired or Blocked) for {url}")
                                if resp.status != 200:
                                    raise Exception(f"HTTP {resp.status} for {url}")
                                
                                # 2. Intercept Invalid Content-Type
                                content_type = resp.headers.get("Content-Type", "").lower()
                                if "application/json" in content_type or "text/" in content_type or "xml" in content_type:
                                     # Try to read the error message
                                     try:
                                         error_content = await resp.text()
                                         # Truncate if too long
                                         if len(error_content) > 200: error_content = error_content[:200] + "..."
                                         raise Exception(f"Invalid Content-Type '{content_type}' with content: {error_content}")
                                     except Exception as read_err:
                                         if "Invalid Content-Type" in str(read_err): raise read_err
                                         raise Exception(f"Invalid Content-Type '{content_type}'")

                                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                                    await f.write(chunk)
                                    task.bytes_downloaded += len(chunk)
                                    self.rich_output.download_advance(
                                        task_id, size=len(chunk)
                                    )
                
                # Move temporary file to destination with retry logic
                # This fixes WinError 32 on network shares where file close is not instant
                move_success = False
                for move_attempt in range(5):
                    try:
                        shutil.move(tmp_path, task.output_path)
                        move_success = True
                        break
                    except OSError as e:
                        # WinError 32: The process cannot access the file...
                        if move_attempt == 4:
                            log.warning(f"Failed to move file after 5 attempts: {e}")
                            raise e
                        
                        log.warning(f"File move locked (attempt {move_attempt+1}), retrying: {e}")
                        await asyncio.sleep(1.0 + move_attempt)

                tmp_path = None  # No longer exists, moved
                
                # ===================================================================
                # Critical validation: ensure the file is not corrupt
                # ===================================================================
                task.status = DownloadStatus.VERIFYING
                
                is_valid, error_msg = await FileIntegrityChecker.verify_file_async(
                    task.output_path,
                    expected_size=task.expected_size,
                    expected_hash=task.expected_hash
                )
                
                if not is_valid:
                    task.status = DownloadStatus.CORRUPTED
                    log.warning(f"File validation failed for '{task.track_title}': {error_msg}")
                    
                    # Attempt to repair MP4/M4A container using ffmpeg faststart remux
                    if task.output_path.suffix.lower() in [".m4a", ".mp4", ".m4v"]:
                        try:
                            repaired_path = fix_mp4_faststart(task.output_path)
                            # Verify again after repair
                            is_valid_repaired, error_msg_repaired = await FileIntegrityChecker.verify_file_async(repaired_path)
                            
                            if is_valid_repaired:
                                self.rich_output.console.print(
                                    f"[green]✓ Repaired container (moov atom) [/]{task.track_title}"
                                )
                                task.status = DownloadStatus.COMPLETED
                                return True
                            else:
                                log.warning(f"Repair validation failed: {error_msg_repaired}")
                        except Exception as repair_exc:
                            log.error(f"Repair failed for '{task.track_title}': {repair_exc}")

                    if task.can_retry:
                        log.warning(
                            f"File validation failed for '{task.track_title}' "
                            f"(attempt {attempt}/{task.max_attempts}). Retrying..."
                        )
                        self.rich_output.console.print(
                            f"[yellow]⚠️  Corrupt file detected ({error_msg}), retrying... "
                            f"({attempt}/{task.max_attempts})[/] {task.track_title}"
                        )
                        
                        # Delete corrupt file
                        if task.output_path.exists():
                            task.output_path.unlink()
                        
                        # Wait before retrying
                        await asyncio.sleep(2)
                        task.status = DownloadStatus.DOWNLOADING
                        continue
                    else:
                        # Final attempt failed
                        log.error(
                            f"File validation failed for '{task.track_title}' "
                            f"after {task.max_attempts} attempts. File is corrupt."
                        )
                        self.rich_output.console.print(
                            f"[red]❌ File corrupt after {task.max_attempts} attempts: {error_msg}[/] {task.track_title}"
                        )
                        if task.output_path.exists():
                            task.output_path.unlink()
                        task.status = DownloadStatus.FAILED
                        return False
                
                # Successful validation
                task.status = DownloadStatus.COMPLETED
                if attempt > 1:
                    log.info(f"Successfully downloaded '{task.track_title}' on attempt {attempt}")
                    self.rich_output.console.print(
                        f"[green]✓ Retry successful![/] {task.track_title}"
                    )
                
                return True
                
            except Exception as e:
                task.error_message = str(e)
                log.error(f"Download error for '{task.track_title}' (attempt {attempt}): {e}")
                
                # Clean up temporary file if exists
                if tmp_path and tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except:
                        pass
                
                # Clean up destination file if partial
                if task.output_path.exists():
                    try:
                        task.output_path.unlink()
                    except:
                        pass
                
                if task.can_retry:
                    self.rich_output.console.print(
                        f"[yellow]⚠️  Download failed, retrying... "
                        f"({attempt}/{task.max_attempts})[/] {task.track_title}"
                    )
                    await asyncio.sleep(2)
                    task.status = DownloadStatus.DOWNLOADING
                    continue
                else:
                    # Todos los intentos fallaron
                    task.status = DownloadStatus.FAILED
                    self.rich_output.console.print(
                        f"[red]❌ Download failed after {task.max_attempts} attempts[/] {task.track_title}"
                    )
                    return False
        
        return False

    async def download_batch(
        self,
        tasks: list[DownloadTask],
        headers: Optional[dict] = None
    ) -> dict:
        """
        Descarga un lote de tareas usando la cola y semáforo
        """
        completed = 0
        failed = 0
        skipped = 0
        total_bytes = 0
        
        # Crear tareas asíncronas
        async def process_task(task: DownloadTask, i: int):
            nonlocal completed, failed, skipped, total_bytes
            
            async with self.semaphore:
                if not task.url:
                    task.status = DownloadStatus.FAILED
                    task.error_message = "No URL provided"
                    failed += 1
                    return

                # Si task.url es string, la convertimos a lista
                urls = [task.url]
                
                # Configurar visualización en rich_output
                task_id = self.rich_output.download_start(
                    f"[cyan]Batch[/] {task.track_title or 'Unknown'}",
                    total=task.expected_size
                )
                
                success = await self._download_with_retry(
                    task=task,
                    urls=urls,
                    task_id=task_id,
                    headers=headers
                )
                
                # Finalizar tarea en UI
                self.rich_output.download_finish(task_id=task_id)
                
                if success:
                    completed += 1
                    total_bytes += task.bytes_downloaded
                    self.rich_output.show_item_result(
                        result_message="[green]Completed",
                        item_description=f"{task.track_title}",
                        item_path=task.output_path
                    )
                else:
                    failed += 1
                    self.rich_output.show_item_result(
                        result_message="[red]Failed",
                        item_description=f"{task.track_title}",
                        item_path=None
                    )
                    
        # Ejecutar todas las tareas
        await asyncio.gather(*[
            process_task(task, i) 
            for i, task in enumerate(tasks)
        ])
        
        return {
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "total_bytes": total_bytes
        }

    async def download(
        self, item: Track | Video, file_path: Path
    ) -> tuple[Path | None, bool]:
        """
        returns
        - Path `item_path` path of existing/downloaded item
        - bool `was_downloaded`
        """
        
        artist_name = item.artist.name if getattr(item, 'artist', None) else "Unknown"
        display_title = f"{artist_name} - {item.title}"

        if not item.allowStreaming:
            self.rich_output.console.print(
                f"[red]Can't stream[/] {display_title} ({item.id})"
            )
            return None, False

        if isinstance(item, Track):
            filename = get_existing_track_filename(
                item.audioQuality, self.track_quality, file_path
            )
            vibrant_color = item.album.vibrantColor

        elif isinstance(item, Video):
            filename = file_path.with_suffix(".mp4")
            vibrant_color = item.vibrantColor

        vibrant_color = vibrant_color or "gray"

        existing_file_path = self.scan_path / filename

        log.debug(f"{file_path=}, {filename=}, {existing_file_path=}")

        result_message = "[green]Downloaded"

        if self._is_file_in_cache(existing_file_path):
            result_message = "[cyan]Overwrited"

            if self.skip_existing:
                self.rich_output.show_item_result(
                    result_message="[yellow]Exists",
                    item_description=f"[{vibrant_color}]{display_title}",
                    item_path=existing_file_path,
                )
                return existing_file_path, False

        # Check for alternative extensions (e.g. have FLAC, requesting M4A)
        elif self.skip_existing:
            qual_map = {".flac": 2, ".m4a": 1, ".mp4": 1}
            target_score = qual_map.get(filename.suffix, 0)

            for ext in [".flac", ".m4a", ".mp4"]:
                if ext == filename.suffix:
                    continue

                alt_path = existing_file_path.with_suffix(ext)
                if self._is_file_in_cache(alt_path):
                    found_score = qual_map.get(ext, 0)

                    # Only skip if the existing file is equal or better quality
                    if found_score >= target_score:
                        self.rich_output.show_item_result(
                            result_message="[yellow]Exists (Alt)",
                            item_description=f"[{vibrant_color}]{display_title}",
                            item_path=alt_path,
                        )
                        return alt_path, False

        elif (isinstance(item, Video) and self.videos_filter == "none") or (
            isinstance(item, Track) and self.videos_filter == "only"
        ):
            log.debug(f"skipping {item.id} due to {self.videos_filter=}")
            self.rich_output.console.print(
                f"Skipping '{display_title}' due to video filter set to '{self.videos_filter}'"
            )
            return None, False

        should_extract_flac = False

        async with self.semaphore:
            if isinstance(item, Track):
                # Optimization: Only attempt qualities up to the track's available quality
                quality_score = {"HI_RES_LOSSLESS": 3, "LOSSLESS": 2, "HIGH": 1, "LOW": 0}
                max_score = quality_score.get(item.audioQuality, 3)
                
                # Check for Dolby Atmos
                is_atmos = False
                if item.mediaMetadata:
                    tags = []
                    if isinstance(item.mediaMetadata, dict):
                        tags = item.mediaMetadata.get("tags", [])
                    elif hasattr(item.mediaMetadata, "tags"):
                        tags = item.mediaMetadata.tags
                    if "DOLBY_ATMOS" in tags:
                        is_atmos = True
                
                if not is_atmos and item.audioModes and "DOLBY_ATMOS" in item.audioModes:
                    is_atmos = True

                attempt_qualities: list[TrackQuality] = ["HI_RES_LOSSLESS", "LOSSLESS", "HIGH", "LOW"]
                # Filter out qualities higher than what the track supports
                attempt_qualities = [q for q in attempt_qualities if quality_score.get(q, 0) <= max_score]

                for q in attempt_qualities:
                    try:
                        # Use asyncio.to_thread to prevent blocking the event loop during retries (sleep)
                        stream = await asyncio.to_thread(self.api.get_track_stream, track_id=item.id, quality=q)
                    except Exception as e:
                        # Check for Asset Not Ready (4005) first to avoid noisy logs
                        try:
                            if hasattr(e, 'response') and e.response is not None:
                                err_json = e.response.json()
                                if err_json.get("subStatus") == 4005:
                                    self.rich_output.console.print(f"[yellow]Skipped '{display_title}' (Asset not ready)[/]")
                                    return None, False
                        except:
                            pass

                        # Catch all exceptions (ApiError, HTTPError, etc.) to allow fallback or skip
                        log.warning(f"Quality '{q}' failed for {item.id}: {e}")

                        # FIX: Fail fast on Rate Limit to avoid "Error Could not download..." spam
                        if "429" in str(e) or "Limit" in str(e):
                             self.rich_output.console.print(f"[yellow]Skipped '{display_title}' (Rate Limit)[/]")
                             return None, False
                             
                        continue
                    urls, _ = parse_track_stream(stream)
                    chosen_filename = get_existing_track_filename(item.audioQuality, q, file_path)
                    
                    # Prepare path for Windows Long Path / UNC
                    download_path = self.download_path / chosen_filename
                    if sys.platform == "win32":
                        download_path = Path(_prepare_long_path(str(download_path.absolute())))
                        
                    quality = track_qualities_color[stream.audioQuality]
                    if is_atmos:
                        quality = "[purple]Dolby Atmos"
                    elif stream.audioQuality in ["HI_RES_LOSSLESS", "LOSSLESS"]:
                        quality = f"{quality} {stream.bitDepth}-bit, {(stream.sampleRate or 0) / 1000:.1f} kHz"
                    should_extract_flac = stream.audioQuality == "HI_RES_LOSSLESS"
                    
                    task_id = self.rich_output.download_start(f"[{vibrant_color}]{display_title} {quality}")
                    
                    download_path.parent.mkdir(exist_ok=True, parents=True)
                    
                    task = DownloadTask(
                        url=urls[0] if urls else "",
                        output_path=download_path,
                        track_id=item.id,
                        track_title=display_title,
                        max_attempts=MAX_RETRIES
                    )
                    
                    download_success = await self._download_with_retry(
                        task=task,
                        urls=urls,
                        task_id=task_id,
                    )
                    if not download_success:
                        task = self.rich_output.download_finish(task_id=task_id)
                        self.rich_output.show_item_result(
                            result_message="[yellow]Failed (Retrying lower quality)",
                            item_description=task.description,
                            item_path=None,
                        )
                        continue
                    try:
                        if should_extract_flac:
                            download_path = extract_flac(download_path)
                    except Exception as exc:
                        log.error(f"{should_extract_flac=}, {exc=}")
                        self.rich_output.console.print(
                            f"[red]Error converting format:[/] {display_title} - {exc}"
                        )
                    task = self.rich_output.download_finish(task_id=task_id)
                    self.rich_output.show_item_result(
                        result_message=result_message,
                        item_description=task.description,
                        item_path=download_path,
                    )
                    return download_path, True
                
                self.rich_output.console.print(
                    f"[red]Error[/] Could not download '{display_title}' in any quality"
                )
                return None, False

            elif isinstance(item, Video):
                attempt_v_qualities: list[StreamVideoQuality] = ["HIGH", "MEDIUM", "LOW"]
                for q in attempt_v_qualities:
                    try:
                        # Run blocking API call in a thread to avoid freezing the event loop
                        stream = await asyncio.to_thread(self.api.get_video_stream, video_id=item.id, quality=q)
                    except (ApiError, HTTPError) as e:
                        log.warning(f"video quality '{q}' failed for {item.id}: {e}")
                        continue
                    except Exception as e:
                        log.error(f"Unexpected error for video {item.id} q={q}: {e}")
                        continue
                        
                    urls, ext = parse_video_stream(stream), ".ts"
                    quality = video_qualities_color[stream.videoQuality]
                    
                    # Prepare path for Windows Long Path / UNC
                    download_path = (self.download_path / filename).with_suffix(ext)
                    if sys.platform == "win32":
                        download_path = Path(_prepare_long_path(str(download_path.absolute())))
                    
                    task_id = self.rich_output.download_start(f"[{vibrant_color}]{display_title} {quality}")
                    
                    download_path.parent.mkdir(exist_ok=True, parents=True)
                    
                    task = DownloadTask(
                        url=urls[0] if urls else "",
                        output_path=download_path,
                        track_id=item.id,
                        track_title=display_title,
                        max_attempts=MAX_RETRIES
                    )
                    
                    download_success = await self._download_with_retry(
                        task=task,
                        urls=urls,
                        task_id=task_id,
                    )
                    if not download_success:
                        task = self.rich_output.download_finish(task_id=task_id)
                        self.rich_output.show_item_result(
                            result_message="[yellow]Failed (Retrying lower quality)",
                            item_description=task.description,
                            item_path=None,
                        )
                        continue
                    try:
                        download_path = convert_to_mp4(download_path)
                    except Exception as exc:
                        log.error(f"{should_extract_flac=}, {exc=}")
                        self.rich_output.console.print(
                            f"[red]Error converting format:[/] {display_title} - {exc}"
                        )
                    task = self.rich_output.download_finish(task_id=task_id)
                    self.rich_output.show_item_result(
                        result_message=result_message,
                        item_description=task.description,
                        item_path=download_path,
                    )
                    return download_path, True
                
                self.rich_output.console.print(
                    f"[red]Error[/] Could not download video '{display_title}' in any quality"
                )
                return None, False
