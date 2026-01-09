#!/usr/bin/env python3
"""
Compare structure of two Alembic files to identify differences
"""

import sys
from alembic.Abc import IArchive, WrapExistingFlag
from alembic.AbcGeom import IXform, ICamera, IPolyMesh, IPoints, ISubD, ICurves

def get_object_type(obj):
    """Determine the type of an Alembic object"""
    if ICamera.matches(obj.getHeader()):
        return "ICamera"
    elif IPolyMesh.matches(obj.getHeader()):
        return "IPolyMesh"
    elif IXform.matches(obj.getHeader()):
        return "IXform"
    elif IPoints.matches(obj.getHeader()):
        return "IPoints"
    elif ISubD.matches(obj.getHeader()):
        return "ISubD"
    elif ICurves.matches(obj.getHeader()):
        return "ICurves"
    else:
        return "Unknown"

def inspect_object(obj, indent=0, max_depth=10):
    """Recursively inspect an Alembic object and return structure info"""
    if indent > max_depth:
        return []

    prefix = "  " * indent
    obj_type = get_object_type(obj)
    name = obj.getName()

    info = []
    info.append(f"{prefix}{name} ({obj_type})")

    # Get metadata info
    metadata = obj.getMetaData()
    if metadata:
        info.append(f"{prefix}  MetaData: {metadata}")

    # If it's a typed object, get more details
    if ICamera.matches(obj.getHeader()):
        camera = ICamera(obj, WrapExistingFlag.kWrapExisting)
        schema = camera.getSchema()
        info.append(f"{prefix}  - Camera properties:")
        info.append(f"{prefix}    - NumSamples: {schema.getNumSamples()}")

        # Check for custom properties
        if schema.getArbGeomParams():
            arb = schema.getArbGeomParams()
            info.append(f"{prefix}    - ArbGeomParams: {arb.getNumProperties()} properties")
            for i in range(arb.getNumProperties()):
                prop_name = arb.getPropertyHeader(i).getName()
                info.append(f"{prefix}      - {prop_name}")

        if schema.getUserProperties():
            user = schema.getUserProperties()
            info.append(f"{prefix}    - UserProperties: {user.getNumProperties()} properties")
            for i in range(user.getNumProperties()):
                prop_name = user.getPropertyHeader(i).getName()
                info.append(f"{prefix}      - {prop_name}")

    elif IPolyMesh.matches(obj.getHeader()):
        mesh = IPolyMesh(obj, WrapExistingFlag.kWrapExisting)
        schema = mesh.getSchema()
        info.append(f"{prefix}  - Mesh properties:")
        info.append(f"{prefix}    - NumSamples: {schema.getNumSamples()}")

        # Get sample to check vertex/face counts
        if schema.getNumSamples() > 0:
            sample = schema.getValue()
            positions = sample.getPositions()
            info.append(f"{prefix}    - Vertices: {len(positions)}")

            face_counts = sample.getFaceCounts()
            info.append(f"{prefix}    - Faces: {len(face_counts)}")

    elif IXform.matches(obj.getHeader()):
        xform = IXform(obj, WrapExistingFlag.kWrapExisting)
        schema = xform.getSchema()
        info.append(f"{prefix}  - Transform properties:")
        info.append(f"{prefix}    - NumSamples: {schema.getNumSamples()}")
        info.append(f"{prefix}    - IsConstant: {schema.isConstant()}")

    # Recurse into children
    for child in obj.children:
        info.extend(inspect_object(child, indent + 1, max_depth))

    return info

def compare_alembic_files(file1, file2):
    """Compare two Alembic files and show differences"""
    print("=" * 80)
    print(f"COMPARING ALEMBIC FILES")
    print("=" * 80)

    print(f"\nFile 1: {file1}")
    print(f"File 2: {file2}")
    print()

    # Open both archives
    archive1 = IArchive(str(file1))
    archive2 = IArchive(str(file2))

    # Compare time sampling
    print("\n" + "=" * 80)
    print("TIME SAMPLING")
    print("=" * 80)

    print(f"\nFile 1:")
    print(f"  Num time samplings: {archive1.getNumTimeSamplings()}")
    for i in range(archive1.getNumTimeSamplings()):
        ts = archive1.getTimeSampling(i)
        num_samples = archive1.getMaxNumSamplesForTimeSamplingIndex(i)
        print(f"  Time sampling {i}: {num_samples} samples")
        if num_samples > 0 and i > 0:
            print(f"    Start time: {ts.getSampleTime(0)}")
            if num_samples > 1:
                print(f"    End time: {ts.getSampleTime(num_samples-1)}")

    print(f"\nFile 2:")
    print(f"  Num time samplings: {archive2.getNumTimeSamplings()}")
    for i in range(archive2.getNumTimeSamplings()):
        ts = archive2.getTimeSampling(i)
        num_samples = archive2.getMaxNumSamplesForTimeSamplingIndex(i)
        print(f"  Time sampling {i}: {num_samples} samples")
        if num_samples > 0 and i > 0:
            print(f"    Start time: {ts.getSampleTime(0)}")
            if num_samples > 1:
                print(f"    End time: {ts.getSampleTime(num_samples-1)}")

    # Compare hierarchy
    print("\n" + "=" * 80)
    print("HIERARCHY - FILE 1")
    print("=" * 80)
    top1 = archive1.getTop()
    structure1 = inspect_object(top1)
    for line in structure1:
        print(line)

    print("\n" + "=" * 80)
    print("HIERARCHY - FILE 2")
    print("=" * 80)
    top2 = archive2.getTop()
    structure2 = inspect_object(top2)
    for line in structure2:
        print(line)

    # Compare object counts
    print("\n" + "=" * 80)
    print("OBJECT TYPE SUMMARY")
    print("=" * 80)

    def count_types(lines):
        counts = {}
        for line in lines:
            if "ICamera" in line:
                counts["ICamera"] = counts.get("ICamera", 0) + 1
            elif "IPolyMesh" in line:
                counts["IPolyMesh"] = counts.get("IPolyMesh", 0) + 1
            elif "IXform" in line:
                counts["IXform"] = counts.get("IXform", 0) + 1
            elif "IPoints" in line:
                counts["IPoints"] = counts.get("IPoints", 0) + 1
        return counts

    counts1 = count_types(structure1)
    counts2 = count_types(structure2)

    print(f"\nFile 1 ({file1}):")
    for obj_type, count in sorted(counts1.items()):
        print(f"  {obj_type}: {count}")

    print(f"\nFile 2 ({file2}):")
    for obj_type, count in sorted(counts2.items()):
        print(f"  {obj_type}: {count}")

    # Show differences
    print("\n" + "=" * 80)
    print("DIFFERENCES")
    print("=" * 80)

    all_types = set(counts1.keys()) | set(counts2.keys())
    for obj_type in sorted(all_types):
        count1 = counts1.get(obj_type, 0)
        count2 = counts2.get(obj_type, 0)
        if count1 != count2:
            print(f"  {obj_type}: File1={count1}, File2={count2} (diff={count2-count1})")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python compare_abc_structure.py <file1.abc> <file2.abc>")
        sys.exit(1)

    compare_alembic_files(sys.argv[1], sys.argv[2])
