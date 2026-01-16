# Windows Build Instructions (v2.1.0)

Complete guide for building MultiConverter with multi-format export on Windows.

## Prerequisites

### Required Software (Install Before Building)

1. **Python 3.11 or 3.12**
   - Download: https://www.python.org/downloads/
   - ✅ **IMPORTANT**: Check "Add Python to PATH" during installation
   - Verify: Open Command Prompt and run `python --version`

2. **PyAlembic**
   - **⚠️ MUST BE INSTALLED FIRST**
   - Follow official installation instructions for Windows: https://github.com/alembic/alembic
   - Verify installation: `python -c "from alembic.Abc import IArchive; print('OK')"`

3. **Microsoft Visual C++ Redistributable 2015-2022**
   - Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Required for PyAlembic to work
   - Install before running the setup script

4. **Internet Connection**
   - Needed to download NumPy and other Python packages

## Quick Start (2 Steps)

### Step 1: Run Setup

```cmd
setup_windows_v2.1.bat
```

This will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Download and install PyAlembic wheel
- ✅ Install NumPy, imath, and PyInstaller
- ✅ Optionally install USD library for multi-format export

**Time:** ~2-5 minutes (depending on USD installation)

### Step 2: Build the Executable

```cmd
build_windows_v2.1.bat
```

This creates: **`dist\MultiConverter\`** folder with the executable and all dependencies

**Time:** ~5-10 minutes (PyInstaller bundling)

## What Gets Built

After running `build_windows_v2.1.bat`, you'll have:

```
dist/
  └── MultiConverter/          (~70-100 MB with USD support)
      ├── MultiConverter.exe   - Main executable
      ├── python312.dll      - Python runtime
      ├── pxr/               - USD libraries (if installed)
      ├── _internal/         - PyInstaller bundled files
      └── [other dependencies]
```

This **folder distribution** contains:
- Python runtime
- PyAlembic and all dependencies
- USD library (if installed during setup)
- GUI application
- Everything needed to run!

**Important:** The entire `MultiConverter/` folder must be distributed together. The .exe will NOT work if copied separately from the folder.

## Distribution

### For End Users

**Package for distribution:**
1. Zip the entire `dist\MultiConverter\` folder
2. Name it `MultiConverter-v2.1.0-windows.zip`
3. Include Visual C++ Redistributable link: https://aka.ms/vs/17/release/vc_redist.x64.exe

**Users need to:**
1. Install Visual C++ Redistributable (if not already installed)
2. Extract the zip file to any folder
3. Run `MultiConverter.exe` from the extracted folder
4. Use the GUI to convert to After Effects, USD, or Maya!

**File size expectations:**
- With USD support: ~70-100 MB (zipped: ~30-40 MB)
- Without USD: ~40-50 MB (zipped: ~15-20 MB)

No Python installation needed for end users!

## Troubleshooting

### "Python not found"

**Solution:** Install Python 3.11 or 3.12 and check "Add Python to PATH"

Verify with:
```cmd
python --version
```

### "ModuleNotFoundError: No module named 'alembic'"

**Cause:** PyAlembic not installed

**Solution:** Install PyAlembic according to the official documentation before running setup:
- https://github.com/alembic/alembic

Verify installation:
```cmd
python -c "from alembic.Abc import IArchive; print('PyAlembic installed successfully')"
```

### Build folder is large

The distribution folder will be 70-100 MB (with USD) because it includes:
- Python runtime (~15 MB)
- NumPy (~20 MB)
- PyAlembic (~15 MB)
- USD library (~47 MB)
- Other dependencies

This is normal for PyInstaller bundles with complex C extensions. The zip file will be smaller (~30-40 MB).

### USD export fails with "No module named 'pxr.Tf._tf'"

**Cause:** USD libraries not properly bundled by PyInstaller

**Solution:** This should be fixed in v2.1.0 with the new build script. If you still see this error:
1. Verify USD is installed: `python -c "from pxr import Usd; print('USD OK')"`
2. Check the build output shows "USD library found"
3. Verify `dist\MultiConverter\pxr\` folder exists and contains `.pyd` files
4. Rebuild with clean: `build_windows_v2.1.bat` (it runs `--clean` automatically)

### "The code execution cannot proceed because VCRUNTIME140.dll was not found"

**Solution:** Install Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

## Build Customization

### Change Exe Icon

1. Create or download an `.ico` file (e.g., `icon.ico`)
2. Edit `build_windows.bat` and add:
   ```batch
   --icon=icon.ico ^
   ```
   After the `--windowed` line

### Add Version Information

Edit `build_windows.bat` and add:
```batch
--version-file=version.txt ^
```

Then create `version.txt` with version info.

### Debug Mode

To see console output during execution, change in `build_windows.bat`:
```batch
--windowed ^
```
to:
```batch
--console ^
```

## File Structure After Build

```
alembic_to_jsx/
├── venv/                          # Virtual environment (don't distribute)
├── build/                         # PyInstaller temp files (don't distribute)
├── dist/
│   └── MultiConverter/             # ✅ ZIP AND DISTRIBUTE THIS FOLDER
│       ├── MultiConverter.exe
│       ├── python312.dll
│       ├── pxr/                  # USD libraries
│       └── _internal/            # Dependencies
├── setup_windows_v2.1.bat        # Setup script
├── build_windows_v2.1.bat        # Build script
├── hook-pxr.py                   # PyInstaller hook for USD
└── README.md                     # Documentation
```

## Architecture Support

| Platform | Python 3.11 | Python 3.12 | Status |
|----------|------------|------------|--------|
| Windows x64 (64-bit) | ✅ | ✅ | Fully Supported |
| Windows x86 (32-bit) | ✅ | ✅ | Supported |
| Windows ARM64 | ✅ | ✅ | Supported |

**Note:** Most users have 64-bit Windows. Build with Python 3.11 or 3.12 x64 for maximum compatibility.

## USD Library Installation

The setup script (`setup_windows_v2.1.bat`) will prompt you to install USD for multi-format export support.

**Option 3 (Recommended):** Install `usd-core` via pip
```cmd
pip install usd-core
```

This is the recommended option because:
- ✅ Proper package metadata for PyInstaller
- ✅ Automatic dependency resolution
- ✅ Easy to install and update
- ✅ Works reliably with the build script

**If USD is not installed:** The converter will still work for After Effects export only. USD and Maya export options will be unavailable.

## Next Steps

After building:
1. Test `dist\MultiConverter\MultiConverter.exe` on a clean Windows machine (no Python installed)
2. Zip the `dist\MultiConverter\` folder as `MultiConverter-v2.1.0-windows.zip`
3. Create a release on GitHub with the zipped folder
4. Test After Effects, USD, and Maya export functionality
5. Write user documentation
6. Share with your team!

## Support

For issues with:
- **PyAlembic wheel**: https://github.com/cgohlke/pyalembic-wheels/issues
- **This converter**: Check the main README.md
- **PyInstaller**: https://pyinstaller.org/en/stable/

## Build Time Summary

| Step | Time | Output |
|------|------|--------|
| Setup (first time) | ~2-5 min | venv + packages + USD |
| Build | ~5-10 min | dist/MultiConverter/ folder |
| Zip folder | ~30 sec | MultiConverter-v2.1.0-windows.zip |
| **Total** | **~8-16 min** | **Ready to distribute!** |

Subsequent builds are faster (~3-5 min) since dependencies are cached.

**Distribution size:**
- Folder: ~70-100 MB (with USD), ~40-50 MB (without USD)
- Zipped: ~30-40 MB (with USD), ~15-20 MB (without USD)
