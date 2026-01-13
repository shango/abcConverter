"""
PyInstaller hook for USD (pxr) library

This hook tells PyInstaller how to collect USD's Python modules, data files,
and binary dependencies during the build process. It also sets up runtime
DLL search paths when the executable runs.
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

# ============================================================================
# BUILD-TIME COLLECTION (tells PyInstaller what to bundle)
# ============================================================================

# Collect all pxr submodules, including C extensions like pxr.Tf._tf
# This is critical because USD uses dynamic imports that static analysis can't detect
hiddenimports = collect_submodules('pxr')

# Collect all data files (plugInfo.json, shaders, etc.)
datas = collect_data_files('pxr')

# Collect all binary files (.pyd C extensions and .dll dependencies)
binaries = collect_dynamic_libs('pxr')

# ============================================================================
# RUNTIME HOOK (runs when the executable starts)
# ============================================================================

# This section will be executed at runtime via PyInstaller's runtime hook mechanism
# To use this as a runtime hook, reference it in the build script with:
#   --runtime-hook=hook-pxr.py

import os
import sys

# When running as a PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Get the folder where PyInstaller extracted files
    bundle_dir = sys._MEIPASS

    # Add potential USD binary locations to PATH
    potential_paths = [
        bundle_dir,
        os.path.join(bundle_dir, 'pxr'),
        os.path.join(bundle_dir, 'pxr', 'lib'),
        os.path.join(bundle_dir, 'lib'),
        os.path.join(bundle_dir, 'bin'),
    ]

    # Add to PATH so DLLs can be found
    for path in potential_paths:
        if os.path.exists(path):
            os.environ['PATH'] = path + os.pathsep + os.environ.get('PATH', '')

    # Also add to DLL directory search path on Windows
    if sys.platform == 'win32' and hasattr(os, 'add_dll_directory'):
        for path in potential_paths:
            if os.path.exists(path):
                try:
                    os.add_dll_directory(path)
                except Exception:
                    pass
