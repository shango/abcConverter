
# Quick Reference Guide for Alembic To JSX Converter 
## Version 1.0.0

## For End Users (Using the Converter)

### Requirements
- Windows 10/11 (64-bit recommended)
- [Visual C++ Redistributable 2015-2022](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### How to Use
1. Double-click `AlembicToJSX.exe`
2. Click "Browse" to select your `.abc` file
3. Configure composition settings (FPS, duration, resolution)
4. Click "Convert to JSX"
5. Import the `.jsx` file in After Effects:
   - **File > Scripts > Run Script File**
   - Select your generated `.jsx` file

---

## Supported Alembic Objects

| Type | After Effects Export |
|------|---------------------|
| **Camera** (ICamera) | Camera layer with focal length, aperture, position, rotation |
| **Geometry** (IPolyMesh) | 3D Null with transform animation |
| **Locator** (IXform) | 3D Null with transform animation |

---

## File Paths

### After Building:
```
dist/
  └── AlembicToJSX.exe    # ✅ Distribute this file
```

### Input Files:
- `.abc` - Alembic file (from Maya, Houdini, Blender, etc.)

### Output Files:
- `.jsx` - After Effects script

---

## Common Issues

### "ModuleNotFoundError: No module named 'alembic'"
**Fix:** Install PyAlembic first: https://github.com/alembic/alembic

### "VCRUNTIME140.dll not found"
**Fix:** Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### "Python not found" (when building)
**Fix:** Install [Python 3.11 or 3.12](https://www.python.org/downloads/) and check "Add to PATH"

### GUI doesn't open
**Fix:** Make sure you're running `AlembicToJSX.exe`

---

## Command Line Usage (Advanced)

### Run GUI from source:
```cmd
python a2j_gui.py
```

---

## Distribution Checklist

When sharing the converter with others:

- ✅ Include `AlembicToJSX.exe`
- ✅ Include link to Visual C++ Redistributable
- ✅ Include user documentation (how to use)
- ❌ Don't include `venv/` or `build/` directories
- ❌ Don't include Python source files (users don't need them)

---

## Build Times

| Task | Duration |
|------|----------|
| First setup | 1-2 minutes |
| Building .exe | 5-10 minutes |
| Subsequent builds | 3-5 minutes (cached) |

---

## File Size

- **AlembicToJSX.exe**: ~50-80 MB
- **Visual C++ Redistributable**: ~14 MB (end users need this)

---

## Support & Links

- **PyAlembic Wheels**: https://github.com/cgohlke/pyalembic-wheels
- **Alembic Documentation**: https://docs.alembic.io/
- **After Effects Scripting Guide**: https://ae-scripting.docsforadobe.dev/
- **PyInstaller Docs**: https://pyinstaller.org/

---

## Version Info

- **Alembic**: 1.8.10
- **Python**: 3.11 or 3.12
- **After Effects**: 2025.x (24.x+)
- **Coordinate System**: Y-up
- **Scale**: 1:1 (no conversion)
