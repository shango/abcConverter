# MultiConverter

**Version 2.5.0**

Convert Alembic (.abc) and USD (.usd/.usda/.usdc) files to After Effects JSX, USD, and Maya formats with intelligent vertex animation detection.

## Features

- **Multi-Format Input** - Accept both Alembic and USD scene files
- **Multi-Format Export** - After Effects JSX + OBJ, USD (.usdc), Maya USD, Maya MA
- **Animation Intelligence** - Auto-detects vertex deformation vs transform-only animation
- **Multi-DCC Support** - Works with Alembic from SynthEyes, Nuke, Maya, Houdini, and more
- **Cameras & Geometry** - Full animation support with automatic coordinate conversion
- **User-Friendly** - Modern GUI or powerful CLI
- **Standalone Builds** - Distribute as .exe with no dependencies

## Quick Start (Windows)

```cmd
setup_windows_v2.1.bat    # One-time setup (installs dependencies + USD)
build_windows_v2.1.bat    # Build MultiConverter.exe
```

Or use the all-in-one script: `build_all_windows.bat`

See [WINDOWS_BUILD.md](WINDOWS_BUILD.md) for detailed build instructions.

## Usage

### GUI

1. Launch `MultiConverter.exe` (or `python a2j_gui.py` from source)
2. Select input scene file (`.abc`, `.usd`, `.usda`, `.usdc`)
3. Choose output directory
4. Select export formats (After Effects, USD, Maya)
5. Configure settings (auto-detected from input file)
6. Click "Convert"
7. Import result files into your DCC:
   - **After Effects**: File > Scripts > Run Script File
   - **Maya/Houdini**: File > Import > Select .usdc file

### CLI

```cmd
# Export all formats from Alembic
python a2j.py scene.abc --output-dir ./export --shot-name shot_010

# Export from USD to specific formats
python a2j.py scene.usd --output-dir ./export --format ae maya_ma

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
└── shot_010_maya/  # Maya export
    ├── shot_010.usdc  # Maya USD
    └── shot_010.ma    # Maya MA (ASCII)
```

## Supported Input Formats

| Format | Extensions |
|--------|------------|
| Alembic | `.abc` |
| USD | `.usd`, `.usda`, `.usdc` |

## What Gets Exported

| Element | After Effects | USD / Maya USD | Maya MA |
|---------|---------------|----------------|---------|
| Cameras | 3D Camera with full animation | UsdGeom.Camera | Camera node + animCurves |
| Meshes (transform-only) | 3D Null + OBJ | UsdGeom.Mesh | Mesh + animCurves |
| Meshes (vertex animation) | Skipped (not supported) | Time-sampled vertices | Source file reference |
| Locators/Trackers | 3D Null (yellow, shy) | Xform nodes | Transform nodes |

**Notes:**
- All export formats now support both Alembic (.abc) and USD input files (v2.5.0)
- Coordinate system conversion handled automatically (Y-up to Y-down for AE)
- Maya MA uses source file references for vertex animation (requires original .abc or .usd file)

## Requirements

- **Windows 10/11** (64-bit)
- **Python 3.11 or 3.12** (for building from source)
- **Visual C++ Redistributable 2015-2022** (for running .exe): https://aka.ms/vs/17/release/vc_redist.x64.exe
- **PyAlembic** (auto-installed by setup scripts)
- **USD Library** (optional, for USD input/output): `pip install usd-core` or [NVIDIA USD](https://developer.nvidia.com/usd)

## Installation

Run the setup script:

```cmd
setup_windows_v2.1.bat
```

Or use `build_all_windows.bat` to setup and build in one step.

See [WINDOWS_BUILD.md](WINDOWS_BUILD.md) for detailed instructions.

## Building Executables

```cmd
build_windows_v2.1.bat
```

Output: `dist/MultiConverter/MultiConverter.exe` (~70-100 MB folder)

End users only need **Visual C++ Redistributable 2015-2022**.

## Project Structure

```
alembic_to_jsx/
├── readers/           # Input readers (Alembic, USD)
├── core/              # Core utilities (animation detection)
├── exporters/         # Format exporters (AE, USD, Maya MA)
├── alembic_converter.py  # Main orchestrator
├── a2j_gui.py         # GUI application
├── a2j.py             # CLI application
└── [build and setup scripts]
```

## Development

Run from source:
```cmd
call venv\Scripts\activate.bat
python a2j_gui.py
```

Modular architecture with `readers/` for input formats, `core/` utilities, and `exporters/` for output formats.

## License

MIT License

---

**Documentation:** [WINDOWS_BUILD.md](WINDOWS_BUILD.md) | [README_FOR_USERS.txt](README_FOR_USERS.txt)
**Support:** Open an issue on the project repository
