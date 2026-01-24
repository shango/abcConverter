================================================================================
MultiConverter - Multi-Format Scene Converter
User Guide Version 2.7.0 - VFX-Experts
================================================================================

WHAT IS THIS?
-------------
Converts Alembic (.abc), USD (.usd, .usda, .usdc), and Maya ASCII (.ma) files
to multiple formats:
  • After Effects JSX + OBJ - Cameras, transforms, locators
  • USD (.usdc) - Full 3D scenes with vertex animation
  • Maya USD (.usdc) - Maya-optimized USD export
  • Maya MA (.ma) - Native Maya ASCII with source file references
  • FBX (.fbx) - Unreal Engine compatible (cameras, meshes, locators)

Perfect for VFX and game dev workflows across SynthEyes, Nuke, Maya, Houdini,
Unreal Engine, and more.

================================================================================

INSTALLATION
------------
1. Install Visual C++ Redistributable 2015-2022 (Windows only)
   https://aka.ms/vs/17/release/vc_redist.x64.exe

2. Extract the MultiConverter folder to any location
3. Run MultiConverter.exe - No Python installation needed!

================================================================================

HOW TO USE
----------
1. Launch MultiConverter.exe

2. Select Input File
   → Browse for your scene file (.abc, .usd, .usda, .usdc)
   → Both Alembic and USD input formats are supported

3. Select Output Directory
   → Choose where to save exported files

4. Choose Export Formats
   → Check boxes for formats you want:
      ☑ After Effects (JSX + OBJ)
      ☑ USD (.usdc)
      ☑ Maya USD (.usdc)
      ☑ Maya MA (.ma) - Native Maya ASCII
      ☑ FBX (.fbx) - For Unreal Engine

5. Configure Settings (auto-detected from file)
   • Shot Name: Auto-filled from filename
   • Frame Rate: Default 24 fps
   • Duration: Auto-detected

6. Click "Convert"
   → Files created in separate folders per format

7. Import to Your Software
   • After Effects: File → Scripts → Run Script File → Select .jsx
   • Maya: File → Import → Select .usdc or .ma
   • Houdini: File → Import → USD → Select .usdc
   • Unreal Engine: File → Import → Select .fbx

================================================================================

OUTPUT STRUCTURE
----------------
output_folder/
├── shotname_ae/      # After Effects export
│   ├── shotname.jsx
│   └── *.obj
├── shotname_usd/     # USD export
│   └── shotname.usdc
├── shotname_maya/    # Maya export (both formats)
│   ├── shotname.usdc # Maya USD
│   └── shotname.ma   # Maya MA (ASCII)
└── shotname_fbx/     # FBX export for Unreal Engine
    └── shotname.fbx  # FBX ASCII format

================================================================================

WHAT GETS EXPORTED
------------------
• Cameras: Full animation with focal length and aperture
• Meshes: Transform animation + static geometry
• Vertex Animation: Exported to USD/Maya (skipped for After Effects and FBX)
• Locators: 3D tracking points as nulls (AE/FBX) or transforms (USD)

Coordinate conversion handled automatically!
  - After Effects: Y-up to Y-down
  - FBX/Unreal: Y-up to Z-up

================================================================================

COMPATIBILITY
-------------
• After Effects 2025 / 2024
• Maya 2020+ (MA format), 2022+ (USD support)
• Houdini (USD import)
• Unreal Engine 4.27+ / 5.x (FBX import)

================================================================================

VERSION INFORMATION
-------------------
Version: 2.6.2
License: MIT
Support: Open issues at project repository


