import json
from logging import getLogger
from pathlib import Path
from typing import Any, Type, TypeVar, Callable, Optional, Literal

from pydantic import BaseModel
from time import sleep
import time

# CRITICAL FIX: Import HTTPError
from requests.exceptions import JSONDecodeError, HTTPError
from requests_cache import (
    CachedSession,
    StrOrPath,
    NEVER_EXPIRE,
)

from .exceptions import ApiError

T = TypeVar("T", bound=BaseModel)

API_URL = "https://api.tidal.com/v1"
API_V1_URL = "https://api.tidal.com/v1"
API_V2_URL = "https://api.tidal.com/v2"  # Para Feed y Activity API
MAX_RETRIES = 5
RETRY_DELAY = 2

log = getLogger(__name__)


class TidalClientImproved:
    """Cliente mejorado con soporte para v1 y v2, refresh automático y rate limiting"""
    
    _token: str
    _refresh_token: Optional[str]
    _token_expiry: Optional[int]  # Unix timestamp
    debug_path: Path | None
    session: CachedSession
    on_token_expiry: Optional[Callable[[bool, int], tuple[str, int, str | None] | None]]
    
    # Rate Limiting: 60 requests per minute
    _last_request_time: float
    _request_interval: float

    def __init__(
        self,
        token: str,
        cache_name: StrOrPath,
        omit_cache: bool = False,
        debug_path: Path | None = None,
        on_token_expiry: Optional[Callable[[bool, int], tuple[str, int, str | None] | None]] = None,
        refresh_token: Optional[str] = None,
        token_expiry: Optional[int] = None,  # Unix timestamp
    ) -> None:
        self.on_token_expiry = on_token_expiry
        self.debug_path = debug_path
        self._refresh_token = refresh_token
        self._token_expiry = token_expiry
        
        # Rate Limiting Init
        self._last_request_time = 0
        self._request_interval = 60.0 / 50.0  # 1.2 second between requests
        
        self.session = CachedSession(
            cache_name=cache_name,
            always_revalidate=omit_cache
        )
        
        # MEJORA: Agregar headers completos según documentación
        self.session.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "TIDAL_ANDROID/1039 okhttp/3.14.9",  # Camuflaje
            "Connection": "keep-alive",
        }
        self._token = token
    
    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token: str):
        self._token = token
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
            }
        )

    def _check_token_expiry(self) -> bool:
        """Verifica si el token está por expirar (< 1 hora restante)"""
        if not self._token_expiry:
            return True  # No sabemos, asumir válido
        
        current_time = int(time.time())
        time_remaining = self._token_expiry - current_time
        
        # Si quedan menos de 1 hora (3600 segundos), renovar
        if time_remaining < 3600:
            log.warning(f"Token expiring soon ({time_remaining}s remaining)")
            return False
        
        return True
    
    def _auto_refresh_token(self, force_refresh: bool = False) -> bool:
        """Intenta renovar el token automáticamente"""
        if not self._refresh_token or not self.on_token_expiry:
            return False
        
        try:
            # Expects (access_token, expires_at, refresh_token)
            # Request at least 3600s validity if we are proactive refreshing (force_refresh=False)
            # If force_refresh=True, validity check is skipped inside callback anyway.
            result = self.on_token_expiry(force_refresh=force_refresh, min_validity=3600)
            if result:
                new_token, new_expiry, new_refresh_token = result
                self.token = new_token
                self._token_expiry = new_expiry
                if new_refresh_token:
                    self._refresh_token = new_refresh_token
                
                log.info(f"Token refreshed successfully. Expires at: {new_expiry}")
                return True
        except Exception as e:
            log.error(f"Failed to refresh token: {e}")
        
        return False
    
    def fetch(
        self,
        model: Type[T],
        endpoint: str,
        params: dict[str, Any] = {},
        expire_after: int = NEVER_EXPIRE,
        api_version: Literal["v1", "v2"] = "v1",
        _attempt: int = 1,
        _refreshed: bool = False,
    ) -> T:
        """
        Fetch mejorado con:
        - Soporte para API v1 y v2
        - Auto-refresh de token
        - Mejor manejo de rate limiting
        - Debug mejorado
        """
        
        # Verificar expiración del token
        if not self._check_token_expiry():
            self._auto_refresh_token()
        
        # Seleccionar URL base según versión
        base_url = API_V1_URL if api_version == "v1" else API_V2_URL
        
        # Rate Limiting Enforcement
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._request_interval:
            sleep_time = self._request_interval - elapsed
            # log.debug(f"Rate limiting: Sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()

        res = self.session.get(
            f"{base_url}/{endpoint}",
            params=params,
            expire_after=expire_after
        )

        # ============================================================ 
        # MEJORA 5: Manejo detallado de rate limiting (429) 
        # ============================================================ 
        if res.status_code == 429:
            retry_after = res.headers.get("Retry-After", "60")
            
            try:
                wait_time = int(retry_after)
            except ValueError:
                wait_time = 60
            
            log.warning(
                f"Rate limit hit (429). Retry-After: {wait_time}s. "
                f"Attempt {_attempt}/{MAX_RETRIES}"
            )
            
            if _attempt < MAX_RETRIES:
                time.sleep(wait_time)
                return self.fetch(
                    model=model,
                    endpoint=endpoint,
                    params=params,
                    expire_after=expire_after,
                    api_version=api_version,
                    _attempt=_attempt + 1,
                    _refreshed=_refreshed,
                )
            
            res.raise_for_status()

        # ============================================================ 
        # MEJORA 6: Auto-refresh en 401 
        # ============================================================ 
        if res.status_code == 401:
            try:
                error_json = res.json()
                sub_status = error_json.get("subStatus")
                user_message = error_json.get("userMessage", "")
            except:
                error_json = None
                sub_status = None
                user_message = ""
            
            # Si es error de contenido (Asset not ready), NO refrescar token
            if sub_status == 4005:
                log.debug(f"Asset not ready (401/4005): {user_message}. Skipping token refresh.")
                res.raise_for_status()

            log.warning(f"Received 401 Unauthorized. Attempting token refresh. Body: {res.text}")
            
            if not _refreshed and self._auto_refresh_token(force_refresh=True):
                return self.fetch(
                    model=model,
                    endpoint=endpoint,
                    params=params,
                    expire_after=expire_after,
                    api_version=api_version,
                    _attempt=_attempt, # Keep attempt count or reset? Resetting is safer if we trust refresh logic.
                    _refreshed=True,
                )
            
            # Si falla el refresh, lanzar error
            res.raise_for_status()

        # ============================================================ 
        # MEJORA 7: Logging mejorado con más contexto 
        # ============================================================ 
        cache_status = "HIT" if res.from_cache else "MISS"
        log.debug(
            f"[{api_version.upper()}] {endpoint} "
            f"params={params} "
            f"cache={cache_status} "
            f"status={res.status_code} "
            f"size={len(res.content) if res.content else 0}B"
        )

        # ============================================================ 
        # Parse JSON con mejor manejo de errores 
        # ============================================================ 
        try:
            data = res.json()
        except JSONDecodeError as e:
            if _attempt >= MAX_RETRIES:
                log.error(
                    f"JSON decode failed after {MAX_RETRIES} attempts\n"
                    f"Endpoint: {endpoint}\n"
                    f"Status: {res.status_code}\n"
                    f"Content preview: {res.text[:200]}"
                )
                raise ApiError(
                    status=res.status_code,
                    subStatus="0",
                    userMessage="Response body does not contain valid json.",
                )

            log.warning(f"JSON decode error, retrying {_attempt}/{MAX_RETRIES}")
            time.sleep(RETRY_DELAY)

            return self.fetch(
                model=model,
                endpoint=endpoint,
                params=params,
                expire_after=expire_after,
                api_version=api_version,
                _attempt=_attempt + 1,
                _refreshed=_refreshed,
            )

        # ============================================================ 
        # IMPROVEMENT 8: Improved debug with organized structure 
        # ============================================================ 
        if self.debug_path:
            # Organize by API version
            debug_dir = self.debug_path / api_version
            file = debug_dir / f"{endpoint.replace('/', '_')}.json"
            file.parent.mkdir(parents=True, exist_ok=True)
            
            debug_data = {
                "timestamp": time.time(),
                "api_version": api_version,
                "status_code": res.status_code,
                "endpoint": endpoint,
                "params": params,
                "cache_hit": res.from_cache,
                "headers": dict(res.headers),
                "data": data,
            }
            
            file.write_text(json.dumps(debug_data, indent=2, default=str))

        # ============================================================ 
        # IMPROVEMENT 9: Logical error detection in 200 responses 
        # ============================================================ 
        if res.status_code == 200 and isinstance(data, dict):
            # Detect embedded errors in successful responses
            if "error" in data:
                log.error(f"Logic error in 200 OK response: {data}")
                raise ApiError(
                    status=200,
                    subStatus="LogicError",
                    userMessage=str(data.get("error"))
                )
            
            # Detect error fields according to TIDAL documentation
            if "userMessage" in data and "status" in data and data["status"] != 200:
                log.error(f"TIDAL API error in response: {data}")
                raise ApiError(**data)

        if res.status_code != 200:
            # ============================================================ 
            # IMPROVEMENT 10: Specific logging by error code 
            # ============================================================ 
            error_context = {
                "endpoint": endpoint,
                "params": params,
                "status": res.status_code,
                "data": data,
            }
            
            if res.status_code == 404:
                log.debug(f"Resource not found: {error_context}")
            elif res.status_code == 403:
                log.warning(f"Forbidden (geo-blocked or premium only): {error_context}")
            elif res.status_code == 451:
                log.warning(f"Unavailable for legal reasons: {error_context}")
            elif res.status_code in [500, 502, 503, 504]:
                log.warning(f"Server error ({res.status_code}): {error_context}")
            else:
                log.error(f"API error: {error_context}")
            
            raise ApiError(**data)

        return model.model_validate(data)

    # ================================================================ 
    # MEJORA 11: Método para obtener estadísticas de uso 
    # ================================================================ 

    def get_cache_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas del cache"""
        # Validar si requests_cache está habilitado y tiene backend
        if not hasattr(self.session, 'cache'):
            return {"enabled": False}
            
        try:
            return {
                "cache_name": getattr(self.session.cache, 'db_path', 'unknown'),
                # Usar responses.keys() o similar dependiendo del backend
                # Nota: responses suele ser un dict-like object
                "responses_cached": len(self.session.cache.responses) if hasattr(self.session.cache, 'responses') else 0,
            }
        except Exception as e:
            log.warning(f"Could not retrieve cache stats: {e}")
            return {"error": str(e)}

    # ================================================================ 
    # MEJORA 12: Método para limpiar cache selectivamente 
    # ================================================================ 

    def clear_cache(
        self,
        endpoints: Optional[list[str]] = None,
        older_than: Optional[int] = None  # Segundos
    ) -> None:
        """
        Limpia el cache de forma selectiva
        
        Args:
            endpoints: Lista de endpoints a limpiar (None = todos)
            older_than: Limpiar entradas más viejas que N segundos
        """
        if not hasattr(self.session, 'cache'):
            return

        if not endpoints and not older_than:
            self.session.cache.clear()
            log.info("Cache cleared completely")
            return
        
        # Limpieza por antigüedad
        if older_than:
            self.session.cache.remove_old_entries(older_than)
            
        # Limpieza por endpoints (más complejo con requests-cache, requiere iterar)
        if endpoints:
            # Nota: Esta es una implementación simplificada. 
            # requests-cache usa claves hash, no URLs directas.
            # Una limpieza precisa por URL requiere iterar todas las claves
            # o usar delete_url si el backend lo soporta.
            try:
                for url in endpoints:
                    self.session.cache.delete(urls=[url])
                    # También intentar con la base URL completa si se pasó solo el endpoint
                    if not url.startswith("http"):
                         self.session.cache.delete(urls=[f"{API_V1_URL}/{url}", f"{API_V2_URL}/{url}"])
            except Exception as e:
                log.warning(f"Error clearing specific endpoints: {e}")


# TODO add token expiry check
# maybe refactor to aiohttp.ClientSession
class TidalClient(TidalClientImproved):
    """
    DEPRECATED: Use TidalClientImproved directly.
    This class exists only for backward compatibility.
    """
    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn(
            "TidalClient is deprecated. Use TidalClientImproved instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)