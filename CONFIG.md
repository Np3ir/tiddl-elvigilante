<<<<<<< HEAD
# ⚙️ Configuration Guide - tiddl

**For complete placeholder reference, see [COMPLETE_COMMAND_REFERENCE.md](COMPLETE_COMMAND_REFERENCE.md) ⭐**

Configuration file location and all available options.

---

## 📍 Configuration File Location

**Windows:**
```
C:\Users\YourName\.tiddl\config.toml
```

**Linux/macOS:**
```
~/.tiddl/config.toml
```

---

## 🚀 Quick Start Config

```toml
enable_cache = true
debug = false

[download]
track_quality = "max"
video_quality = "fhd"
skip_existing = true
threads_count = 4
download_path = "~/Music/tiddl"

[metadata]
enable = true
lyrics = true
save_lyrics = true
cover = true

[templates]
default = "{album.artist}/{album.title}/{item.number}. {item.title}"
```

---

## 📝 General Settings

### `enable_cache`
- **Type**: boolean
- **Default**: true
- **Description**: Enable API response caching

### `debug`
- **Type**: boolean
- **Default**: false
- **Description**: Enable verbose logging to `~/.tiddl/api_debug/`

---

## 🎵 [download] Section

### `track_quality`
- **Type**: low / normal / high / max
- **Default**: high
- Options:
  - `max`: 24-bit, 192kHz FLAC (best)
  - `high`: 16-bit, 44.1kHz FLAC
  - `normal`: 320kbps AAC
  - `low`: 96kbps AAC (worst)

### `video_quality`
- **Type**: sd / hd / fhd
- **Default**: fhd
- Options:
  - `fhd`: 1080p (best)
  - `hd`: 720p
  - `sd`: 360p (worst)

### `skip_existing`
- **Type**: boolean
- **Default**: true
- Skip files already downloaded

### `threads_count`
- **Type**: integer
- **Default**: 4
- **Range**: 1-20
- Number of concurrent downloads

### `download_path`
- **Type**: path
- **Default**: ~/Music/tiddl
- Base directory for downloads

### `scan_path`
- **Type**: path
- **Default**: same as download_path
- Directory to scan for existing files

### `singles_filter`
- **Type**: none / only / include
- **Default**: none
- How to handle artist singles

### `videos_filter`
- **Type**: none / only / allow
- **Default**: none
- How to handle music videos

---

## 📝 [metadata] Section

### `enable`
- **Type**: boolean
- **Default**: true
- Master switch for all metadata processing

### `lyrics`
- **Type**: boolean
- **Default**: false
- Embed lyrics in file metadata

### `save_lyrics`
- **Type**: boolean
- **Default**: false
- Save lyrics as separate `.lrc` file

### `cover`
- **Type**: boolean
- **Default**: false
- Embed album cover in file metadata

### `album_review`
- **Type**: boolean
- **Default**: false
- Embed album review in metadata

---

## 🖼️ [cover] Section

### `save`
- **Type**: boolean
- **Default**: false
- Save cover as separate image file

### `size`
- **Type**: integer
- **Default**: 1280
- **Range**: 1-1280
- Cover image width in pixels

### `allowed`
- **Type**: array
- **Default**: []
- Resource types: track, album, playlist

---

## 📂 [templates] Section

Controls file naming and organization.

### `default`
- **Type**: string
- **Default**: "{album.artist}/{album.title}/{item.title}"
- Default template for all content

### `track`
- **Type**: string
- Specific template for tracks

### `album`
- **Type**: string
- Specific template for albums

### `playlist`
- **Type**: string
- Specific template for playlists

### `video`
- **Type**: string
- Specific template for videos

---

## 📝 Template Variables

**For complete placeholder reference, see [COMPLETE_COMMAND_REFERENCE.md](COMPLETE_COMMAND_REFERENCE.md)**

Common variables:

```bash
{item.title}              # Track title
{item.number}             # Track number (01, 02, etc)
{item.version}            # Track version (Remix, etc)
{item.artist}             # Track artist
{item.artists_with_features}  # With featuring artists
{item.releaseDate:%Y}     # Year

{album.artist}            # Album artist
{album.title}             # Album name
{album.date:%Y}           # Release year

{artist_initials}         # First letter (groups by letter)
{playlist.title}          # Playlist name
```

---

## 💡 Common Templates

### Simple (Default)
```toml
default = "{album.artist}/{album.title}/{item.title}"
```

### With Track Numbers
```toml
default = "{album.artist}/{album.title}/{item.number}. {item.title}"
```

### By Year
```toml
default = "{album.artist}/({album.date:%Y}) {album.title}/{item.number}. {item.title}"
```

### Grouped by Initial
```toml
default = "{artist_initials}/{album.artist}/{album.title}/{item.title}"
```

### With Featuring Artists
```toml
default = "{album.artist}/{album.title}/{item.number}. {item.artists_with_features}"
```

---

## 🎬 [m3u] Section

M3U8 playlist export settings.

### `save`
- **Type**: boolean
- **Default**: false
- Save M3U8 files

### `allowed`
- **Type**: array
- **Default**: []
- Resource types: album, playlist, mix

---

## 📋 Full Example Config

```toml
enable_cache = true
debug = false

[download]
track_quality = "max"
video_quality = "fhd"
skip_existing = true
threads_count = 4
download_path = "~/Music/tiddl"
scan_path = "~/Music/tiddl"
singles_filter = "include"
videos_filter = "allow"
update_mtime = false
rewrite_metadata = true

[metadata]
enable = true
lyrics = true
save_lyrics = true
cover = true
album_review = false

[cover]
save = true
size = 1280
allowed = ["track", "album", "playlist"]

[templates]
track = ""
video = ""
album = ""
playlist = ""
default = "{album.artist}/{album.title}/{item.number}. {item.title}"

[m3u]
save = false
allowed = ["album", "playlist"]
```

---

## 🔄 Command-Line Overrides

Command-line arguments override config.toml:

```bash
# Override quality
tiddl download url --track-quality high https://...

# Override download path
tiddl download url --path "D:/Music" https://...

# Override threads
tiddl download url --threads-count 8 https://...
```

---

## 🛠️ Troubleshooting

### Config Not Loading
```bash
# Check location
cat ~/.tiddl/config.toml

# Validate TOML syntax
```

### Metadata Not Embedding
```toml
[metadata]
enable = true  # Must be true
```

### Wrong Quality
```bash
# Check config
grep track_quality ~/.tiddl/config.toml

# Override with flag
tiddl download url --track-quality max https://...
```

---

## 📚 More Information

- **[COMPLETE_COMMAND_REFERENCE.md](COMPLETE_COMMAND_REFERENCE.md)** - Complete placeholders and variables
- **[USAGE.md](USAGE.md)** - Usage examples
- **[README.md](README.md)** - Overview

---

**For complete placeholder reference, see [COMPLETE_COMMAND_REFERENCE.md](COMPLETE_COMMAND_REFERENCE.md)**
=======
# Configuration Guide for tiddl

This guide provides a detailed overview of all configuration options available through the `config.toml` file and command-line arguments.

## `config.toml` File

The configuration file is the best way to set your preferences permanently. The file is located at `~/.tiddl/config.toml` (or `%USERPROFILE%\.tiddl\config.toml` on Windows).

### General Settings

| Parameter      | Type    | Default | Description                                                   |
| -------------- | ------- | ------- | ------------------------------------------------------------- |
| `enable_cache` | boolean | `true`  | Enables caching for API responses to speed up repeated requests. |
| `debug`        | boolean | `false` | Enables verbose debug logging.                                |

### `[metadata]` Section

Controls how metadata is handled for downloaded files.

| Parameter        | Type    | Default | Description                                                          |
| ---------------- | ------- | ------- | -------------------------------------------------------------------- |
| `enable`         | boolean | `true`  | Master switch to enable or disable all metadata processing.          |
| `embed_lyrics`   | boolean | `false` | Embeds lyrics into the music file's metadata tag.                  |
| `save_lyrics`    | boolean | `false` | Saves lyrics as a separate `.lrc` file alongside the music file.     |
| `cover`          | boolean | `false` | Embeds the album cover art into the music file's metadata.         |
| `album_review`   | boolean | `false` | Embeds the album review (if available) into the comment metadata tag. |

### `[cover]` Section

Controls the handling of separate cover art image files.

| Parameter | Type                  | Default | Description                                                                |
| --------- | --------------------- | ------- | -------------------------------------------------------------------------- |
| `save`    | boolean               | `false` | Saves cover art as a separate image file.                                  |
| `size`    | integer               | `1280`  | The desired size (width) of the cover art image in pixels.                 |
| `allowed` | list of strings       | `[]`    | Specifies for which resource types to save covers. e.g., `["album", "playlist"]` |

#### `[cover.templates]`

Defines the filename for saved cover art.

| Parameter  | Type   | Default | Description                       |
| ---------- | ------ | ------- | --------------------------------- |
| `track`    | string | `""`    | Template for track-specific covers. |
| `album`    | string | `""`    | Template for album covers.        |
| `playlist` | string | `""`    | Template for playlist covers.     |

### `[download]` Section

Core settings related to the download process.

| Parameter          | Type    | Default                          | Description                                                                                             |
| ------------------ | ------- | -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `track_quality`    | string  | `"high"`                         | Desired track quality. Options: `"LOW"`, `"HIGH"`, `"LOSSLESS"`, `"HIRES"`.                           |
| `video_quality`    | string  | `"fhd"`                          | Desired video quality. Options: `"360"`, `"480"`, `"720"`, `"1080"`.                                 |
| `skip_existing`    | boolean | `true`                           | If `true`, skips downloading files that already exist in the destination.                               |
| `threads_count`    | integer | `2`                              | Number of concurrent download threads.                                                                  |
| `download_path`    | string  | `"~/Music/tiddl"`                | The base directory where all files will be downloaded.                                                  |
| `scan_path`        | string  | `"~/Music/tiddl"`                | The directory to scan for existing files (defaults to `download_path` if not set).                      |
| `singles_filter`   | string  | `"none"`                         | When downloading an artist: `"none"` (albums only), `"only"` (singles only), or `"include"` (both). |
| `videos_filter`    | string  | `"none"`                         | `"none"` (no videos), `"allow"` (download videos alongside tracks), `"only"` (download only videos). |
| `update_mtime`     | boolean | `false`                          | If `true`, updates the file's modification time upon download/metadata rewrite.                         |
| `rewrite_metadata` | boolean | `false`                          | If `true`, forces a rewrite of metadata tags for already existing files.                                |

### `[m3u]` Section

Controls the creation of M3U playlist files.

| Parameter | Type                  | Default | Description                                                                   |
| --------- | --------------------- | ------- | ----------------------------------------------------------------------------- |
| `save`    | boolean               | `false` | If `true`, creates an `.m3u` playlist file for albums, playlists, or mixes.   |
| `allowed` | list of strings       | `[]`    | Specifies for which resource types to create M3U files. e.g., `["album"]` |

#### `[m3u.templates]`

| Parameter  | Type   | Default | Description                          |
| ---------- | ------ | ------- | ------------------------------------ |
| `album`    | string | `""`    | Filename template for album M3U files. |
| `playlist` | string | `""`    | Filename template for playlist M3U files. |
| `mix`      | string | `""`    | Filename template for mix M3U files.      |

### `[templates]` Section

Defines the directory and file naming structure for downloads.

| Parameter  | Type   | Default                                     | Description                                                                                                                              |
| ---------- | ------ | ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `default`  | string | `"{album.artist}/{album.title}/{item.title}"` | The global fallback template used if a more specific template is not provided.                                                           |
| `track`    | string | `""`                                        | Specific template for track downloads. Falls back to `default`.                                                                          |
| `video`    | string | `""`                                        | Specific template for video downloads. Falls back to `default`.                                                                          |
| `album`    | string | `""`                                        | Specific template for album downloads (used for folder structure). Falls back to `default`.                                            |
| `playlist` | string | `""`                                        | Specific template for playlist downloads (used for folder structure). Falls back to `default`.                                           |
| `mix`      | string | `""`                                        | Specific template for mix downloads. Falls back to `default`.                                                                            |

---

## Command-Line Options

These options can be used with `tiddl download` to override the `config.toml` settings for a single run.

| Option                 | Short | Description                                                   |
| ---------------------- | ----- | ------------------------------------------------------------- |
| `--track-quality`      | `-q`  | Set the track quality for this run.                           |
| `--video-quality`      | `-vq` | Set the video quality for this run.                           |
| `--no-skip`            | `-ns` | Force downloads even if files exist (opposite of `skip_existing`). |
| `--rewrite-metadata`   | `-r`  | Force a rewrite of metadata for existing files.               |
| `--threads-count`      | `-t`  | Set the number of concurrent download threads.                |
| `--path`               | `-p`  | Set the base download directory for this run.                 |
| `--scan-path`          | `--sp`| Set the directory to scan for existing files.                 |
| `--template`, `--output`| `-o`  | Set the global fallback template for this run.                |
| `--album-template`     | `--atf` | Set the album folder template for this run.                   |
| `--track-template`     | `--ttf` | Set the track filename template for this run.                 |
| `--video-template`     | `--vtf` | Set the video filename template for this run.                 |
| `--playlist-template`  | `--ptf` | Set the playlist folder template for this run.                |
| `--singles`            | `-s`  | Set the artist singles filter for this run.                   |
| `--videos`             | `-vid`| Set the video download filter for this run.                   |
>>>>>>> 51f206d9cee155d16ba05c48767a0da1772ff3c1
