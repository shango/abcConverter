# abcConverter

**Version 2.1.0**

Convert Alembic (.abc) files to After Effects JSX, USD, and Maya formats with intelligent vertex animation detection.

## Features

- **Multi-Format Export** - After Effects JSX + OBJ, USD (.usdc), Maya USD
- **Animation Intelligence** - Auto-detects vertex deformation vs transform-only animation
- **Multi-DCC Support** - Works with Alembic from SynthEyes, Nuke, Maya, Houdini, and more
- **Cameras & Geometry** - Full animation support with automatic coordinate conversion
- **User-Friendly** - Modern GUI or powerful CLI
- **Standalone Builds** - Distribute as .exe with no dependencies

## Quick Start

### Windows

```cmd
setup_windows_v2.1.bat    # One-time setup (installs dependencies + USD)
build_windows_v2.1.bat    # Build abcConverter.exe
```

Or use the all-in-one script: `build_all_windows.bat`

See [WINDOWS_BUILD.md](WINDOWS_BUILD.md) for details.

### macOS/Linux

```bash
./setup.sh                # One-time setup
./run.sh                  # Launch GUI
```

See [MACOS_SETUP.md](MACOS_SETUP.md) for CLI usage and build instructions.

## Usage

### GUI

1. Launch: `./run.sh` (macOS/Linux) or `abcConverter.exe` (Windows)
2. Select input `.abc` file and output directory
3. Choose export formats (After Effects, USD, Maya)
4. Configure settings (auto-detected from Alembic)
5. Click "Convert to Formats"
6. Import result files into your DCC:
   - **After Effects**: File → Scripts → Run Script File
   - **Maya/Houdini**: File → Import → Select .usdc file

### CLI

```bash
# Export all formats
python a2j.py scene.abc --output-dir ./export --shot-name shot_010

# Export specific formats
python a2j.py scene.abc --output-dir ./export --format ae usd

# Custom settings
python a2j.py scene.abc --output-dir ./export --fps 30 --frames 240

# Help
python a2j.py --help
```

**Output structure:**
```
output_dir/
├── shot_010_ae/    # After Effects (JSX + OBJ)
├── shot_010_usd/   # USD export (.usdc)
└── shot_010_maya/  # Maya USD (.usdc)
```

See [MACOS_SETUP.md](MACOS_SETUP.md) for detailed CLI documentation.

## What Gets Exported

| Element | After Effects | USD / Maya |
|---------|---------------|------------|
| Cameras | 3D Camera with full animation | UsdGeom.Camera |
| Meshes (transform-only) | 3D Null + OBJ | UsdGeom.Mesh |
| Meshes (vertex animation) | Skipped (not supported) | Time-sampled vertices |
| Locators/Trackers | 3D Null (yellow, shy) | Xform nodes |

**Note:** Coordinate system conversion handled automatically (Y-up to Y-down for AE).

## Requirements

- **Python 3.11 or 3.12**
- **PyAlembic** (auto-installed by setup scripts)
- **USD Library** (optional, for USD/Maya export)
  - Windows: `pip install usd-core` or [NVIDIA USD](https://developer.nvidia.com/usd)
  - macOS/Linux: `pip install usd-core`
- **Other dependencies** (NumPy, imath, tkinter) auto-installed

## Installation

Run the setup script for your platform:

**Windows:** `setup_windows_v2.1.bat` or `build_all_windows.bat`
**macOS/Linux:** `./setup.sh`

See [WINDOWS_BUILD.md](WINDOWS_BUILD.md) and [MACOS_SETUP.md](MACOS_SETUP.md) for details.

## Building Executables

**Windows:** `build_windows_v2.1.bat` → `dist/abcConverter/abcConverter.exe` (~70-100 MB folder)
**macOS/Linux:** `./build.sh` → `dist/abcConverter` (single file)

End users need **Visual C++ Redistributable 2015-2022** (Windows only): https://aka.ms/vs/17/release/vc_redist.x64.exe

## Project Structure

```
alembic_to_jsx/
├── core/              # Core utilities (Alembic reader, animation detection)
├── exporters/         # Format exporters (AE, USD)
├── alembic_converter.py  # Main orchestrator
├── a2j_gui.py         # GUI application
├── a2j.py             # CLI application
└── [build and setup scripts]
```

## Development

Run from source:
```bash
source venv/bin/activate    # macOS/Linux
python a2j_gui.py           # Launch GUI
```

Modular architecture with `core/` utilities and `exporters/` for format-specific export logic.

## License

MIT License

---

**Documentation:** [WINDOWS_BUILD.md](WINDOWS_BUILD.md) | [MACOS_SETUP.md](MACOS_SETUP.md)
**Support:** Open an issue on the project repository
