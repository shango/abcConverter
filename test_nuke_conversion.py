#!/usr/bin/env python3
"""
Test script to verify Nuke-style Alembic conversion
"""

import sys
import os
from pathlib import Path
from alembic.Abc import IArchive, WrapExistingFlag
from alembic.AbcGeom import IXform, ICamera, IPolyMesh

# Add the current directory to path to import from a2j_gui
sys.path.insert(0, str(Path(__file__).parent))

# Import the converter class
from a2j_gui import AlembicConverter

def test_nuke_conversion():
    """Test conversion of nuke_export.abc with diagnostic output"""

    abc_file = Path(__file__).parent / "syntheyes_output" / "nuke_export.abc"

    if not abc_file.exists():
        print(f"Error: {abc_file} not found")
        return

    print("=" * 80)
    print("TESTING NUKE-STYLE ALEMBIC CONVERSION")
    print("=" * 80)
    print(f"\nInput file: {abc_file}")
    print()

    # First, show the structure we're dealing with
    print("=" * 80)
    print("ALEMBIC STRUCTURE ANALYSIS")
    print("=" * 80)

    archive = IArchive(str(abc_file))
    top = archive.getTop()

    def analyze_structure(obj, depth=0, max_depth=3):
        """Show structure with type annotations"""
        if depth > max_depth:
            return

        indent = "  " * depth
        name = obj.getName()

        obj_type = "Unknown"
        if ICamera.matches(obj.getHeader()):
            obj_type = "ICamera"
        elif IPolyMesh.matches(obj.getHeader()):
            obj_type = "IPolyMesh"
        elif IXform.matches(obj.getHeader()):
            xform = IXform(obj, WrapExistingFlag.kWrapExisting)
            schema = xform.getSchema()
            num_samples = schema.getNumSamples()
            obj_type = f"IXform (samples={num_samples})"

        print(f"{indent}{name} [{obj_type}]")

        for child in obj.children:
            analyze_structure(child, depth + 1, max_depth)

    analyze_structure(top)

    # Now test the converter
    print("\n" + "=" * 80)
    print("CONVERSION TEST")
    print("=" * 80)
    print()

    # Create a test converter instance
    converter = AlembicConverter()

    # Test the helper functions on the actual file
    print("Testing organizational group detection:")

    def test_detection(obj, depth=0):
        """Test detection functions on each object"""
        if depth > 3:
            return

        name = obj.getName()
        indent = "  " * depth

        if IXform.matches(obj.getHeader()):
            is_org = converter.is_organizational_group(obj)
            has_shape = converter.has_shape_child(obj)
            nested_mesh = converter.find_mesh_recursive(obj)
            nested_camera = converter.find_camera_recursive(obj)

            print(f"{indent}{name}:")
            print(f"{indent}  - is_organizational_group: {is_org}")
            print(f"{indent}  - has_shape_child: {has_shape}")
            print(f"{indent}  - find_mesh_recursive: {nested_mesh.getName() if nested_mesh else None}")
            print(f"{indent}  - find_camera_recursive: {nested_camera.getName() if nested_camera else None}")

        for child in obj.children:
            test_detection(child, depth + 1)

    test_detection(top)

    print("\n" + "=" * 80)
    print("CONVERSION SIMULATION")
    print("=" * 80)
    print("\nBased on the detection results above, the converter should:")
    print("1. Skip organizational groups (Meshes, Cameras, ReadGeo1, root)")
    print("2. Detect nested meshes and process as 'Box01 -> mesh' etc.")
    print("3. Use parent name for layers when mesh is generically named 'mesh'")
    print()

    print("Expected processing:")
    print("  - Meshes: SKIP (organizational)")
    print("  - ReadGeo1: SKIP (organizational)")
    print("  - root: SKIP (organizational)")
    print("  - Box01: Process as geometry (Nuke-style) with nested mesh")
    print("  - Box02: Process as geometry (Nuke-style) with nested mesh")
    print("  - ... (and other mesh parent IXforms)")
    print("  - Camera1: Process as camera (Nuke-style) with nested camera")
    print()

if __name__ == "__main__":
    test_nuke_conversion()
