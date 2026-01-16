#!/usr/bin/env python3
"""
Build script for creating standalone executables using PyInstaller
Run this after setting up the environment with setup_windows_v2.1.bat
"""

import PyInstaller.__main__
import sys
import os

def build():
    """Build standalone executable"""

    # Determine platform
    if sys.platform.startswith('win'):
        exe_name = 'MultiConverter.exe'
        icon_option = []  # Add '--icon=icon.ico' if you have an icon file
    elif sys.platform.startswith('darwin'):
        exe_name = 'MultiConverter'
        icon_option = []  # Add '--icon=icon.icns' if you have an icon file
    else:
        exe_name = 'MultiConverter'
        icon_option = []

    print("=" * 50)
    print("Building Standalone Executable")
    print("=" * 50)
    print(f"Platform: {sys.platform}")
    print(f"Output: {exe_name}")
    print("=" * 50)

    # PyInstaller arguments
    args = [
        'a2j_gui.py',
        '--name=' + exe_name,
        '--onefile',  # Single executable file
        '--windowed',  # No console window (GUI mode)
        '--clean',
        '--noconfirm',
        # Include hidden imports - v2.3.0 modular architecture
        '--hidden-import=alembic_converter',
        # Readers module (v2.3.0 - supports Alembic and USD input)
        '--hidden-import=readers',
        '--hidden-import=readers.base_reader',
        '--hidden-import=readers.alembic_reader',
        '--hidden-import=readers.usd_reader',
        # Core module
        '--hidden-import=core.animation_detector',
        # Exporters module
        '--hidden-import=exporters.base_exporter',
        '--hidden-import=exporters.ae_exporter',
        '--hidden-import=exporters.usd_exporter',
        '--hidden-import=exporters.maya_ma_exporter',
        # Alembic library
        '--hidden-import=alembic',
        '--hidden-import=alembic.Abc',
        '--hidden-import=alembic.AbcGeom',
        '--hidden-import=imath',
        '--hidden-import=numpy',
        # USD library (for USD input/output)
        '--hidden-import=pxr',
        '--hidden-import=pxr.Usd',
        '--hidden-import=pxr.UsdGeom',
        '--hidden-import=pxr.Gf',
        '--hidden-import=pxr.Vt',
        '--hidden-import=pxr.Sdf',
        # Collect all necessary data files
        '--collect-all=alembic',
        '--collect-all=imath',
    ] + icon_option

    # Run PyInstaller
    try:
        PyInstaller.__main__.run(args)

        print("\n" + "=" * 50)
        print("Build Complete!")
        print("=" * 50)

        if sys.platform.startswith('win'):
            print(f"\nExecutable location: dist\\{exe_name}")
        else:
            print(f"\nExecutable location: dist/{exe_name}")

        print("\nYou can now distribute this executable without requiring")
        print("users to install Python or any dependencies!")

    except Exception as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
