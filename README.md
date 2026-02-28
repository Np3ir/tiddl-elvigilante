### Warning

This app is for personal, educational, and archival purposes only. It is not affiliated with Tidal. Users must ensure their use complies with Tidal's terms of service and all applicable local copyright laws. Downloaded content is for personal use and may not be shared or redistributed. The developer assumes no responsibility for misuse of this app.

---

# tiddl-elvigilante

This is a custom and enhanced fork of the popular Tidal downloader, **tiddl**. This repository is based on the original [oskvr37/tiddl](https://github.com/oskvr37/tiddl) project and introduces the following key improvements.

## Key Features & Improvements

*   **Advanced Metadata Handling**: Correctly adds `genre` and formats the `year` (YYYY) in file tags.
*   **Robust Filenames**: Preserves special and full-width characters, while also fixing errors in title cleaning (e.g., `(feat. ...)`).
*   **Performance Optimization**: Implements a directory caching system to drastically speed up the verification of existing files, avoiding unnecessary disk I/O.
*   **Smart Error Handling**: Prevents download queue stalls with a limited, intelligent retry system for non-essential resources like song lyrics.

## Installation

Ensure you have [FFmpeg](https://ffmpeg.org/download.html) installed and available in your system's PATH.

You can install the original package via `pip`:
```bash
pip install tiddl
```
*(Note: To use the improvements from this fork, you will need to manually replace the installed files with the ones from this repository).*

## Basic Usage

1.  **Login**:
    ```bash
    tiddl auth login
    ```

2.  **Download**:
    You can download tracks, videos, albums, artists, playlists, or mixes by providing their URL or ID.
    ```bash
    tiddl download url <url_or_id>
    ```
    **Examples:**
    ```bash
    tiddl download url https://github.com/oskvr37/tiddl/issues/11
    tiddl download url track/103805726
    tiddl download url artist/4311528
    ```

## Configuration

For detailed information on all available command-line flags and `config.toml` options, please see the **[Configuration Guide](CONFIG.md)**.
