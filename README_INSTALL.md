# Installation Guide for Another Computer

Follow these steps to move and run `tiddl` on another machine.

## 1. Prepare the New Computer
1. **Install Python:**
   - Download and install Python (version 3.10 or higher) from [python.org](https://www.python.org/downloads/).
   - **IMPORTANT:** During installation, check the box "Add Python to PATH".

2. **Install FFmpeg:**
   - `tiddl` needs FFmpeg to process media files.
   - Download the executable from [ffmpeg.org](https://ffmpeg.org/download.html) or use a package manager (like `winget install ffmpeg` on Windows).
   - Ensure `ffmpeg` is accessible from the terminal (open CMD and type `ffmpeg -version` to test).

## 2. Copy the Files
You need to copy two things from this computer to the new one:

1. **The Code Folder (`tiddl`):**
   - Copy this entire folder where you are reading this file.
   - Example: `C:\Tools\tiddl`

2. **The Configuration Folder (`.tiddl`):**
   - This folder contains your **login session** and **settings**.
   - Usual location: `C:\Users\YOUR_USER\.tiddl`
   - Copy this folder to the same location on the new computer (`C:\Users\NEW_USER\.tiddl`).

## 3. Install Dependencies
1. Open the `tiddl` folder on the new computer.
2. Double-click the **`install_dependencies.bat`** file.
   - This will automatically run `pip install -r requirements.txt`.

Alternatively, via terminal:
```bash
cd C:\Tools\tiddl
pip install -r requirements.txt
```

## 4. Run tiddl
You can now use `tiddl` directly by running the `__main__.py` file with Python.

**Basic command:**
```bash
python . --help
```

**Download example:**
```bash
python . dl "https://tidal.com/browse/album/12345"
```

**(Optional) Create a shortcut (tiddl.bat):**
Create a file named `tiddl.bat` in the folder with this content:
```bat
@echo off
python "%~dp0\__main__.py" %*
```
Now you can type `tiddl` (if you add the folder to PATH) or drag the bat to the terminal.
