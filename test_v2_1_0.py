#!/usr/bin/env python3
"""
Quick test script for MultiConverter v2.1.0
Verifies all modules import correctly and basic functionality works
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all v2.1.0 modules can be imported"""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)

    # Test core modules
    try:
        from core.alembic_reader import AlembicReader
        print("✓ core.alembic_reader imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import core.alembic_reader: {e}")
        return False

    try:
        from core.animation_detector import AnimationDetector
        print("✓ core.animation_detector imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import core.animation_detector: {e}")
        return False

    # Test exporter modules
    try:
        from exporters.base_exporter import BaseExporter
        print("✓ exporters.base_exporter imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import exporters.base_exporter: {e}")
        return False

    try:
        from exporters.ae_exporter import AfterEffectsExporter
        print("✓ exporters.ae_exporter imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import exporters.ae_exporter: {e}")
        return False

    try:
        from exporters.usd_exporter import USDExporter
        print("✓ exporters.usd_exporter imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import exporters.usd_exporter: {e}")
        return False

    # Test main orchestrator
    try:
        from alembic_converter import AlembicToJSXConverter
        print("✓ alembic_converter imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import alembic_converter: {e}")
        return False

    print()
    return True

def test_dependencies():
    """Test that all required dependencies are available"""
    print("=" * 60)
    print("Testing Dependencies")
    print("=" * 60)

    # Test PyAlembic
    try:
        import alembic
        import alembic.Abc
        import alembic.AbcGeom
        print(f"✓ PyAlembic available")
    except ImportError as e:
        print(f"✗ PyAlembic not available: {e}")
        return False

    # Test USD
    try:
        from pxr import Usd, UsdGeom, Gf, Vt, Sdf
        print(f"✓ USD (pxr) available")
    except ImportError as e:
        print(f"✗ USD not available: {e}")
        print("  Multi-format export will not work!")
        return False

    # Test NumPy
    try:
        import numpy as np
        print(f"✓ NumPy available (version: {np.__version__})")
    except ImportError as e:
        print(f"✗ NumPy not available: {e}")
        return False

    # Test imath
    try:
        import imath
        import imathnumpy
        print(f"✓ Imath available")
    except ImportError as e:
        print(f"✗ Imath not available: {e}")
        return False

    print()
    return True

def test_converter_initialization():
    """Test that converter can be initialized"""
    print("=" * 60)
    print("Testing Converter Initialization")
    print("=" * 60)

    try:
        from alembic_converter import AlembicToJSXConverter
        converter = AlembicToJSXConverter()
        print("✓ AlembicToJSXConverter initialized successfully")
        print()
        return True
    except Exception as e:
        print(f"✗ Failed to initialize converter: {e}")
        print()
        return False

def test_exporter_initialization():
    """Test that all exporters can be initialized"""
    print("=" * 60)
    print("Testing Exporter Initialization")
    print("=" * 60)

    try:
        from exporters.ae_exporter import AfterEffectsExporter
        ae_exporter = AfterEffectsExporter()
        print(f"✓ AfterEffectsExporter initialized")
        print(f"  Format: {ae_exporter.get_format_name()}")
        print(f"  Extension: {ae_exporter.get_file_extension()}")
    except Exception as e:
        print(f"✗ Failed to initialize AfterEffectsExporter: {e}")
        return False

    try:
        from exporters.usd_exporter import USDExporter
        usd_exporter = USDExporter()
        print(f"✓ USDExporter initialized")
        print(f"  Format: {usd_exporter.get_format_name()}")
        print(f"  Extension: {usd_exporter.get_file_extension()}")
    except Exception as e:
        print(f"✗ Failed to initialize USDExporter: {e}")
        return False

    print()
    return True

def main():
    """Run all tests"""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 9 + "MultiConverter v2.1.0 Test Suite" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = []

    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Dependencies", test_dependencies()))
    results.append(("Converter Initialization", test_converter_initialization()))
    results.append(("Exporter Initialization", test_exporter_initialization()))

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 15 + "ALL TESTS PASSED!" + " " * 22 + "║")
        print("║" + " " * 58 + "║")
        print("║" + "  Ready for multi-format export testing!" + " " * 16 + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        print("Next steps:")
        print("  1. Test with real Alembic file: python a2j_gui.py")
        print("  2. Or test via CLI: python a2j.py input.abc --output-dir ./output")
        print("  3. Build executable: build_windows_v2.1.bat")
        print()
        return 0
    else:
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 15 + "SOME TESTS FAILED" + " " * 22 + "║")
        print("║" + " " * 58 + "║")
        print("║" + "  Please fix the errors above before proceeding" + " " * 10 + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
