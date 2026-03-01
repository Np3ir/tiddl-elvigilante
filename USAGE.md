<<<<<<< HEAD
# 📖 Usage Guide - tiddl

**For detailed command reference and placeholders, see [COMPLETE_COMMAND_REFERENCE.md](COMPLETE_COMMAND_REFERENCE.md) ⭐**

This guide covers practical examples and common scenarios.

---

## 🔐 Authentication

Before downloading, you must authenticate with TIDAL.

### Initial Setup
```bash
tiddl auth login
```

This will:
1. Open your browser
2. Show a code to enter
3. Redirect to tidal.com
4. Save credentials locally

**Credentials stored at:** `~/.tiddl/auth.json`

---

## 🎵 Downloading Music

### Download Single Track
```bash
tiddl download url https://tidal.com/track/123456789
```

### Download Album
```bash
tiddl download url https://tidal.com/album/497662013
```

### Download Playlist
```bash
tiddl download url https://tidal.com/playlist/abc123xyz
```

### Download Artist (All Albums)
```bash
tiddl download url https://tidal.com/artist/789123456
```

### Download Your Favorites
```bash
tiddl download fav
```

Supports all options of `download url`.

---

## 📝 Advanced Options

### Quality
```bash
# Maximum quality (24-bit, 192kHz FLAC)
tiddl download url --track-quality max https://...

# High quality (16-bit, 44.1kHz FLAC)
tiddl download url --track-quality high https://...

# Normal quality (320kbps AAC)
tiddl download url --track-quality normal https://...

# Low quality (96kbps AAC)
tiddl download url --track-quality low https://...
```

### Download Location
```bash
tiddl download url --path "D:/Music" https://...
tiddl download url --path "~/Music/Tidal" https://...
```

### Number of Threads
```bash
# Faster
tiddl download url --threads-count 8 https://...

# Default
tiddl download url --threads-count 4 https://...

# Slower but less resource-intensive
tiddl download url --threads-count 2 https://...
```

### Custom File Naming
```bash
# Artist/Album/Track format
tiddl download url --template "{album.artist}/{album.title}/{item.title}" https://...

# With year
tiddl download url --template "{album.artist}/({album.date:%Y}) {album.title}/{item.number}. {item.title}" https://...
```

**See [COMPLETE_COMMAND_REFERENCE.md](COMPLETE_COMMAND_REFERENCE.md) for complete placeholder reference.**

---

## 📊 Getting Information

### Track Info
```bash
tiddl info url https://tidal.com/track/123456789
```

Shows:
- Title, artist, album
- Duration, bitrate
- Release date
- Availability

---

## 📦 Playlist Export

### Export as M3U8
```bash
tiddl export url https://tidal.com/playlist/xyz -o my_playlist.m3u8
```

Works with VLC, Winamp, iTunes, and other media players.

---

## 💡 Common Use Cases

### Maximum Quality Download
```bash
tiddl download url \
  --track-quality max \
  --threads-count 8 \
  https://tidal.com/album/497662013
```

### Organize by Year
In `config.toml`:
```toml
[templates]
default = "{album.artist}/({album.date:%Y}) {album.title}/{item.number}. {item.title}"
```

Then:
```bash
tiddl download url https://...
```

Result:
```
Adele/(2008) 21/01. Rolling in the Deep.flac
Adele/(2015) 25/01. Hello.flac
```

### Space-Limited Download
```bash
tiddl download url \
  --track-quality normal \
  --threads-count 2 \
  https://...
```

### Re-download Everything
```bash
tiddl download url --no-skip https://...
```

---

## 🛠️ Troubleshooting

### Authentication Issues
```bash
# Re-authenticate
tiddl auth login

# Debug
tiddl download url --debug https://...
```

### Slow Downloads
```bash
# Increase threads
tiddl download url --threads-count 8 https://...

# Reduce quality
tiddl download url --track-quality high https://...
```

### Network Problems
```bash
# Use fewer threads
tiddl download url --threads-count 2 https://...

# Check debug logs
cat ~/.tiddl/api_debug/...
```

---

## 📚 Reference

- **[COMPLETE_COMMAND_REFERENCE.md](COMPLETE_COMMAND_REFERENCE.md)** - All commands and placeholders
- **[INDICE_RAPIDO.md](INDICE_RAPIDO.md)** - Quick index
- **[CONFIG.md](CONFIG.md)** - Configuration options

---

**For more options and complete reference, see [COMPLETE_COMMAND_REFERENCE.md](COMPLETE_COMMAND_REFERENCE.md)**
=======
# Tiddl User Manual

Tiddl is a command-line interface (CLI) tool for downloading music and videos from Tidal.

## General Usage

```bash
tiddl [GLOBAL_OPTIONS] COMMAND [ARGS]...
```

### Global Options
*   `--version`, `-v`: Show the version and exit.
*   `--debug`: Enable debug logging (useful for troubleshooting).
*   `--omit-cache`: Disable API caching.

---

## Authentication (`auth`)

Manage your Tidal session.

### `login`
Log in to your Tidal account using the device authorization flow.
```bash
tiddl auth login
```
Follow the on-screen instructions to authenticate via your browser.

### `logout`
Log out and remove the stored access token.
```bash
tiddl auth logout
```

### `refresh`
Manually refresh your access token.
```bash
tiddl auth refresh [OPTIONS]
```
*   `--force`, `-f`: Force a token refresh even if the current one is valid.
*   `--early-expire`, `-e <seconds>`: Refresh if the token expires within the specified number of seconds.

---

## Downloading (`download`)

The core functionality of Tiddl. The `download` command groups common configuration options for its subcommands (`url` and `fav`).

```bash
tiddl download [OPTIONS] SUBCOMMAND [ARGS]...
```

### Configuration Options
These options apply to all download subcommands.

#### Audio & Video Quality
*   `--track-quality`, `-q`: Select audio quality.
    *   Values: `LOW`, `HIGH`, `LOSSLESS`, `HI_RES`, `MAX` (default).
*   `--video-quality`, `-vq`: Select video quality.
    *   Values: `AUDIO_ONLY`, `LOW`, `MEDIUM`, `HIGH`, `MAX` (default).

#### Output & Filesystem
*   `--path`, `-p <path>`: Base directory for downloads.
*   `--scan-path`, `--sp <path>`: Directory to scan for existing files (to avoid re-downloading).
*   `--no-skip`, `-ns`: Download files even if they already exist (overwrite).
*   `--rewrite-metadata`, `-r`: Update tags/metadata for already downloaded files without re-downloading audio.
*   `--threads-count`, `-t <int>`: Number of concurrent download threads (default: 1).
*   `--m3u`, `-m`: Generate M3U8 playlists for albums and playlists.
*   `--keep-cover`, `-kc`: Keep the album cover image file (`cover.jpg`) in the album folder.

#### Filters
*   `--no-singles`, `-nsi`: When downloading an artist, skip singles and EPs.
*   `--videos`, `-v`: Video download policy.
    *   Values: `true` (download videos), `false` (skip videos), `only` (download *only* videos).

#### Templates (Advanced)
Customize how files and folders are named. Templates allow you to define the directory structure and filenames for your downloads.

**Options:**
*   `--template`, `--output`, `-o`: Global fallback template. Used if a specific template is not provided.
*   `--album-template`, `--atf`: Template for album tracks.
*   `--track-template`, `--ttf`: Template for individual tracks (singles).
*   `--video-template`, `--vtf`: Template for videos.
*   `--playlist-template`, `--ptf`: Template for playlist tracks.

**Template Variables:**
You can use the following placeholders in your templates. They support Python-style attribute access (e.g., `{album.title}`).

*   **Common Variables:**
    *   `{item.title}`: Track or video title.
    *   `{item.artist.name}`: Artist name of the track/video.
    *   `{item.trackNumber}`: Track number.
    *   `{item.volumeNumber}`: Disc number.
    *   `{item.duration}`: Duration in seconds.
    *   `{quality}`: Quality of the download (e.g., "LOSSLESS", "HI_RES").

*   **Album Variables:**
    *   `{album.title}`: Album title.
    *   `{album.artist.name}`: Album artist name.
    *   `{album.releaseDate}`: Release date (YYYY-MM-DD).
    *   `{album.year}`: Release year (extracted from date).

*   **Playlist Variables (only for playlists):**
    *   `{playlist.title}`: Playlist title.
    *   `{playlist.uuid}`: Playlist ID.
    *   `{playlist_index}`: Position of the track in the playlist.

**Examples:**
*   Default structure:
    `{album.artist.name}/{album.title}/{item.trackNumber} - {item.title}`
*   Flat structure with quality:
    `{item.artist.name} - {item.title} [{quality}]`
*   Playlist with index:
    `{playlist.title}/{playlist_index:02d} - {item.title}`

### Subcommands

#### 1. `url`
Download specific resources by URL or ID.

```bash
tiddl download [OPTIONS] url [URLS]...
```

**Arguments:**
*   `URLS`: One or more Tidal URLs (e.g., `https://tidal.com/album/12345`) or ID strings (e.g., `album/12345`, `track/98765`). Supported types: `track`, `video`, `album`, `playlist`, `artist`, `mix`.

**Examples:**
```bash
# Download an album in Lossless quality
tiddl download -q LOSSLESS url https://tidal.com/album/12345

# Download a specific track and a playlist
tiddl download url track/123456 playlist/789012
```

#### 2. `fav`
Download items from your Tidal favorites (My Collection).

```bash
tiddl download [OPTIONS] fav [OPTIONS]
```

**Options:**
*   `--types`, `-t`: Specify which resource types to download. Can be used multiple times.
    *   Values: `track`, `video`, `album`, `playlist`, `artist`.
    *   Default: All types.

**Examples:**
```bash
# Download all favorite albums and playlists
tiddl download fav -t album -t playlist

# Download everything in your collection
tiddl download fav
```

---

## Other Commands

### `info`
Get information about a specific resource (metadata).
*(Usage details depending on implementation)*

### `export`
Export data.
*(Usage details depending on implementation)*
>>>>>>> 51f206d9cee155d16ba05c48767a0da1772ff3c1
