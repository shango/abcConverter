================================================================================
abcConverter - Multi-Format Alembic Converter
User Guide Version 2.1.0
================================================================================

WHAT IS THIS?
-------------
Converts Alembic (.abc) files to multiple formats:
  • After Effects JSX + OBJ - Cameras, transforms, locators
  • USD (.usdc) - Full 3D scenes with vertex animation
  • Maya USD (.usdc) - Maya-optimized USD export

Perfect for VFX workflows across SynthEyes, Nuke, Maya, Houdini, and more.

================================================================================

INSTALLATION
------------
1. Install Visual C++ Redistributable 2015-2022 (Windows only)
   https://aka.ms/vs/17/release/vc_redist.x64.exe

2. Extract the abcConverter folder to any location
3. Run abcConverter.exe - No Python installation needed!

================================================================================

HOW TO USE
----------
1. Launch abcConverter.exe

2. Select Input File
   → Browse for your .abc file

3. Select Output Directory
   → Choose where to save exported files

4. Choose Export Formats
   → Check boxes for formats you want:
      ☑ After Effects (JSX + OBJ)
      ☑ USD (.usdc)
      ☑ Maya USD (.usdc)

5. Configure Settings (auto-detected from file)
   • Shot Name: Auto-filled from filename
   • Frame Rate: Default 24 fps
   • Duration: Auto-detected

6. Click "Convert to Formats"
   → Files created in separate folders per format

7. Import to Your Software
   • After Effects: File → Scripts → Run Script File → Select .jsx
   • Maya: File → Import → Select .usdc
   • Houdini: File → Import → USD → Select .usdc

================================================================================

OUTPUT STRUCTURE
----------------
output_folder/
├── shotname_ae/      # After Effects export
│   ├── shotname.jsx
│   └── *.obj
├── shotname_usd/     # USD export
│   └── shotname.usdc
└── shotname_maya/    # Maya export
    └── shotname.usdc

================================================================================

WHAT GETS EXPORTED
------------------
• Cameras: Full animation with focal length and aperture
• Meshes: Transform animation + static geometry
• Vertex Animation: Exported to USD/Maya (skipped for After Effects)
• Locators: 3D tracking points as nulls (AE) or transforms (USD)

Coordinate conversion handled automatically!

================================================================================

COMPATIBILITY
-------------
• After Effects 2025 / 2024
• Maya 2022+ (USD support)
• Houdini (USD import)
• Python 3.11/3.12 (if building from source)

================================================================================

VERSION INFORMATION
-------------------
Version: 2.1.0
License: MIT
Support: Open issues at project repository


