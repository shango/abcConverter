# Alembic to After Effects JSX Converter

**Version 1.0.0**

Convert Alembic (.abc) camera tracking files from SynthEyes, Nuke, and other DCCs to After Effects 2025 compatible JSX scripts with full animation support.

## Features

- ✅ **Multi-DCC Support** - Works with Alembic files from SynthEyes, Nuke, Maya, Houdini, and other DCCs
- ✅ **Intelligent Structure Detection** - Automatically handles different hierarchies and organizational groups
- ✅ **Animated Camera Export** - Full camera animation with focal length, aperture, and transforms
- ✅ **Geometry Transforms** - Export mesh objects with animation as 3D nulls
- ✅ **Locators/Trackers** - Export 3D tracking points as shy, yellow-labeled null layers
- ✅ **OBJ Mesh Export** - Automatically exports meshes to OBJ files with correct scale
- ✅ **Coordinate Conversion** - Automatic Y-up to After Effects composition space transformation
- ✅ **Auto-Detection** - Automatically detects frame count and composition resolution from Alembic metadata
- ✅ **Auto-Open Comp** - Generated composition opens automatically in After Effects viewer
- ✅ **User-Friendly GUI** - Modern dark-themed interface, no command line required
- ✅ **Standalone Executable** - Build a single .exe file with no dependencies needed

## 🚀 Quick Start

### For Windows Users (Recommended)

**Build a standalone .exe in 3 simple steps:**

```cmd
1. setup_windows.bat    # Install everything (one-time setup)
2. build_windows.bat    # Create AlembicToJSX.exe
3. Double-click AlembicToJSX.exe to run!
```

The resulting executable (~50-80 MB) can be distributed to users without requiring Python installation.

**See [WINDOWS_BUILD.md](WINDOWS_BUILD.md) for detailed Windows build instructions.**

---

### For Developers (macOS/Linux)

#### Setup and Run GUI:
```bash
./setup.sh      # Install dependencies (one-time)
./run.sh        # Launch the GUI
```

#### Build Standalone Executable:
```bash
./setup.sh      # Install dependencies (one-time)
./build.sh      # Create executable in dist/ folder
```

## GUI Usage

1. **Launch the Application**
   - Windows: Double-click `run.bat` or the built executable
   - macOS/Linux: Run `./run.sh`

2. **Select Input File**
   - Click "Browse..." next to "Input Alembic File"
   - Choose your .abc file (from SynthEyes, Nuke, or any other DCC)

3. **Configure Settings** (auto-populated from Alembic when possible)
   - **Composition Name**: Auto-set from filename
   - **Frame Rate**: Default 24 fps (or detected from Alembic)
   - **Duration**: Auto-detected from Alembic file
   - **Resolution**: Auto-detected as 1920×1080

4. **Convert**
   - Click "⚡ Convert to JSX"
   - Watch progress in the log window
   - OBJ files are automatically created alongside the JSX file

5. **Import to After Effects**
   - In After Effects: File → Scripts → Run Script File
   - Select the generated .jsx file
   - Composition will auto-open with all elements properly positioned

## What Gets Exported

| Alembic Element | After Effects Result | Notes |
|----------------|---------------------|-------|
| **Camera** | 3D Camera layer | Full animation, focal length, zoom calculated automatically |
| **Meshes** (IPolyMesh) | 3D Null + OBJ footage | Transform animation with linked OBJ geometry |
| **Locators/Trackers** (IXform) | 3D Null layers | Shy layers with yellow label color for easy management |

## Coordinate System & Transform

The converter handles the coordinate system transformation automatically:

- **Alembic**: Y-up world space (standard in 3D applications)
- **After Effects**: Y-down composition space (screen convention)

**Transformation formula:**
```
X_ae = X_alembic × 10 + (comp_width / 2)
Y_ae = -Y_alembic × 10 + (comp_height / 2)
Z_ae = -Z_alembic × 10
```

This ensures:
- ✅ Unit conversion (Alembic cm → AE units)
- ✅ Y-axis flip for composition space
- ✅ Z-axis flip for AE depth convention
- ✅ Origin shift to composition center

**Scale handling:**
- Mesh vertices are exported at world-scale in OBJ files
- Scale value of 2% is applied in After Effects to compensate
- This maintains correct proportions and relationships

## Requirements

### Prerequisites (Install First)

- **Python 3.8 or higher**
- **PyAlembic** - Install according to [official PyAlembic documentation](https://github.com/alembic/alembic) for your platform

### Additional Dependencies

- NumPy
- imath
- tkinter (usually included with Python)

**The setup scripts will install NumPy and imath automatically.**

## Installation & Setup

**⚠️ IMPORTANT:** Install PyAlembic first before running setup scripts!

### Windows

```cmd
setup_windows.bat
```

### macOS/Linux

```bash
chmod +x setup.sh
./setup.sh
```

**For building executables:** See [WINDOWS_BUILD.md](WINDOWS_BUILD.md)

## Building Standalone Executables

### Windows

```cmd
build_windows.bat
```

Output: `dist/AlembicToJSX.exe` (single-file executable, ~50-80 MB)

### macOS/Linux

```bash
./build.sh
```

Output: `dist/AlembicToJSX` (single-file executable)

The standalone executable includes all dependencies and requires no Python installation!

## After Effects Compatibility

- ✅ Tested with After Effects 2025 (25.0+)
- ✅ Compatible with After Effects 24.x
- ✅ Uses standard AE JSX API
- ✅ Works with Classic 3D and Advanced 3D renderers

## Troubleshooting

### "Permission denied" (macOS/Linux)

Make scripts executable:
```bash
chmod +x setup.sh run.sh build.sh
```

### GUI won't start

Install tkinter:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS - Usually included, reinstall Python from python.org if needed
```

## Project Structure

```
alembic_to_jsx/
├── a2j_gui.py                  # Main application (GUI)
├── requirements.txt             # Python dependencies
├── build_executable.py          # PyInstaller build configuration
│
├── setup_windows.bat            # Windows setup (recommended)
├── setup.bat                    # Windows setup (alternative)
├── setup.sh                     # macOS/Linux setup
│
├── run.bat                      # Run GUI (Windows)
├── run.sh                       # Run GUI (macOS/Linux)
│
├── build_windows.bat            # Build .exe (Windows - recommended)
├── build.bat                    # Build .exe (Windows - alternative)
├── build.sh                     # Build executable (macOS/Linux)
│
├── README.md                    # This file
├── WINDOWS_BUILD.md             # Detailed Windows build guide
├── QUICK_REFERENCE.md           # Quick command reference
├── README_FOR_USERS.txt         # End-user documentation
│
└── syntheyes_output/            # Example/reference files
    ├── ae_jsx.jsx               # SynthEyes reference JSX output
    ├── alembic.abc              # Test Alembic file
    └── *.obj                    # Example mesh exports
```

## Development

### Running from Source

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate.bat  # Windows

# Run GUI
python a2j_gui.py
```

### Making Changes

The main application code is in `a2j_gui.py`. Key functions:

- `process_camera()` - Handles camera export with animation
- `process_geometry()` - Exports mesh transforms and OBJ files
- `process_locator()` - Exports tracker/locator nulls
- `extract_render_resolution()` - Auto-detects comp size from Alembic

## Known Limitations

- Mesh deformation/animation is not exported (only transforms)
- Materials and textures are not included (OBJ files only contain geometry)
- Some DCC-specific features may not be supported

## Changelog

### Version 1.0.0 (January 2026)
- ✅ **STABLE RELEASE**
- ✅ **Multi-DCC Support** - Works with SynthEyes, Nuke, Maya, Houdini, and other Alembic exporters
- ✅ **Intelligent Structure Detection** - Automatically handles different hierarchies, organizational groups, and nesting depths
- ✅ Full camera animation support with focal length and aperture
- ✅ Geometry transform export with automatic OBJ file generation
- ✅ Tracker/locator export as shy, yellow-labeled null layers
- ✅ Auto-detection of frame count and resolution from Alembic metadata
- ✅ Composition auto-opens in After Effects viewer
- ✅ Correct coordinate system transformation (Y-up to AE composition space)
- ✅ Modern dark-themed GUI interface
- ✅ Standalone executable build support for Windows, macOS, and Linux

## License

MIT License - Feel free to use and modify!

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## Credits

Created for VFX professionals working with 3D camera tracking and After Effects compositing workflows across multiple DCCs.

## Support

For issues, questions, or feature requests, please open an issue on the project repository.
