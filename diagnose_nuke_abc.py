#!/usr/bin/env python3
"""
Diagnose why nuke_export.abc might be causing issues
Specifically check for things that would cause geo to appear as solids
"""

import sys
from alembic.Abc import IArchive, WrapExistingFlag
from alembic.AbcGeom import IXform, ICamera, IPolyMesh

def diagnose_file(abc_file):
    """Diagnose potential issues in an Alembic file"""
    print("=" * 80)
    print(f"DIAGNOSING: {abc_file}")
    print("=" * 80)

    archive = IArchive(str(abc_file))
    top = archive.getTop()

    print("\n### ISSUE CHECK 1: Objects without proper parent transforms ###")
    # Check if meshes are directly under root without IXform parent
    def check_parents(obj, parent_type=None, depth=0):
        obj_name = obj.getName()
        indent = "  " * depth

        if IPolyMesh.matches(obj.getHeader()):
            print(f"{indent}MESH: {obj_name}")
            print(f"{indent}  Parent type: {parent_type}")
            if parent_type != "IXform":
                print(f"{indent}  ⚠️  WARNING: Mesh has no IXform parent!")

            # Check if mesh has transform
            mesh = IPolyMesh(obj, WrapExistingFlag.kWrapExisting)
            schema = mesh.getSchema()

            # Check for .xform property
            if schema.getArbGeomParams():
                arb = schema.getArbGeomParams()
                print(f"{indent}  ArbGeomParams: {arb.getNumProperties()} properties")
                for i in range(arb.getNumProperties()):
                    header = arb.getPropertyHeader(i)
                    print(f"{indent}    - {header.getName()}")

        my_type = None
        if ICamera.matches(obj.getHeader()):
            my_type = "ICamera"
        elif IPolyMesh.matches(obj.getHeader()):
            my_type = "IPolyMesh"
        elif IXform.matches(obj.getHeader()):
            my_type = "IXform"

        for child in obj.children:
            check_parents(child, my_type, depth + 1)

    check_parents(top)

    print("\n### ISSUE CHECK 2: Objects with 'Screen' in name ###")
    # These are typically helper geometry that should be skipped
    def find_screens(obj, depth=0):
        obj_name = obj.getName()
        indent = "  " * depth

        if "screen" in obj_name.lower():
            obj_type = "Unknown"
            if ICamera.matches(obj.getHeader()):
                obj_type = "ICamera"
            elif IPolyMesh.matches(obj.getHeader()):
                obj_type = "IPolyMesh"
            elif IXform.matches(obj.getHeader()):
                obj_type = "IXform"

            print(f"{indent}Found: {obj_name} ({obj_type})")

        for child in obj.children:
            find_screens(child, depth + 1)

    find_screens(top)

    print("\n### ISSUE CHECK 3: Meshes without vertices ###")
    # Check for empty/invalid meshes
    def check_mesh_data(obj, depth=0):
        obj_name = obj.getName()
        indent = "  " * depth

        if IPolyMesh.matches(obj.getHeader()):
            mesh = IPolyMesh(obj, WrapExistingFlag.kWrapExisting)
            schema = mesh.getSchema()

            print(f"{indent}MESH: {obj_name}")
            print(f"{indent}  NumSamples: {schema.getNumSamples()}")

            if schema.getNumSamples() > 0:
                sample = schema.getValue()
                positions = sample.getPositions()
                face_counts = sample.getFaceCounts()

                print(f"{indent}  Vertices: {len(positions)}")
                print(f"{indent}  Faces: {len(face_counts)}")

                if len(positions) == 0:
                    print(f"{indent}  ⚠️  WARNING: Mesh has no vertices!")
                if len(face_counts) == 0:
                    print(f"{indent}  ⚠️  WARNING: Mesh has no faces!")

                # Show first few vertex positions to check scale
                if len(positions) > 0:
                    print(f"{indent}  First vertex: {positions[0]}")
                    if len(positions) > 1:
                        print(f"{indent}  Second vertex: {positions[1]}")

        for child in obj.children:
            check_mesh_data(child, depth + 1)

    check_mesh_data(top)

    print("\n### ISSUE CHECK 4: Object naming patterns ###")
    # Show all object names to identify patterns
    def show_all_names(obj, depth=0):
        obj_name = obj.getName()
        indent = "  " * depth

        obj_type = "Unknown"
        if ICamera.matches(obj.getHeader()):
            obj_type = "CAM"
        elif IPolyMesh.matches(obj.getHeader()):
            obj_type = "MESH"
        elif IXform.matches(obj.getHeader()):
            obj_type = "XFORM"

        print(f"{indent}[{obj_type}] {obj_name}")

        for child in obj.children:
            show_all_names(child, depth + 1)

    show_all_names(top)

    print("\n### ISSUE CHECK 5: Conversion logic check ###")
    print("\nBased on a2j_gui.py logic:")
    print("- ICamera objects -> Camera layers (process_camera)")
    print("- IPolyMesh with IXform parent -> 3D Null + OBJ (process_geometry)")
    print("- IXform objects (no mesh child) -> 3D Null (process_locator)")
    print("- Objects with 'Screen' in name -> SKIPPED")
    print()
    print("If meshes appear as solids, possible causes:")
    print("1. Mesh is not wrapped in IXform (becomes orphaned)")
    print("2. OBJ file export failed")
    print("3. Mesh has no vertices/faces")
    print("4. Name contains special characters causing issues")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_nuke_abc.py <alembic_file.abc>")
        sys.exit(1)

    diagnose_file(sys.argv[1])
