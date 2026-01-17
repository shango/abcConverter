# Alembic File Format - Data Extraction Specification

**MultiConverter v2.6.1 - VFX-Experts**
*Technical Reference for Alembic Scene Data Extraction*

---

## Executive Summary

Alembic is an open-source geometry caching format developed by Sony Pictures Imageworks and Industrial Light & Magic. It is designed to store **baked, computed results** of complex procedural geometric constructions in a non-procedural, application-independent format.

**Core Philosophy**: Alembic stores the *results* of animation and simulation, NOT the procedural systems that created them. This is both its strength (universal interchange) and its limitation (no rigs, no procedural data).

---

## CRITICAL: Reality Check for Pipeline Planning

### The Question
> "Can we use Alembic as a master source to generate native Maya (.ma), FBX, and USD files?"

### The Short Answer
**Partially.** It works well for **cameras** and **simple animated geometry**, but fundamentally breaks down for **character rigs** and **complex hierarchical relationships**.

### The Evidence

#### From Official Alembic Documentation:

> *"Alembic is very specifically NOT concerned with storing the complex dependency graph of procedural tools used to create the computed results. For example, Alembic will efficiently store the animated vertex positions and animated transforms that result from an arbitrarily complex animation and simulation process, but will NOT attempt to store a representation of the network of computations (rigs, basically) which were required to produce the final, animated vertex positions."*
> — [Alembic.io](https://www.alembic.io/)

> *"Alembic is a caching system, and not a live scenegraph."*
> — [Alembic Reference Documentation](https://docs.alembic.io/reference/index.html)

#### From Foundry (Mari Documentation):

> *"As opposed to the Alembic format, which is a point cache format that bakes rigs and constraints to vertices, FBX files export these entities to FBX nodes, which gives you the flexibility to have the original data."*
> — [Foundry Learn](https://learn.foundry.com/mari/Content/user_guide/alembic_fbx/alembic_fbx.html)

### What This Means in Practice

| Scenario | Alembic → Maya/FBX/USD | Result |
|----------|------------------------|--------|
| **Animated Camera** | **WORKS** | Full camera with lens properties and animation |
| **Static Props/Environment** | **WORKS** | Geometry with transforms, UVs, normals |
| **Rigid Body Animation** | **WORKS** | Objects moving/rotating without deformation |
| **Character with Baked Animation** | **PARTIAL** | Mesh deforms correctly BUT no skeleton, no rig controls, no ability to modify animation |
| **Character Rig (editable)** | **FAILS** | Skeleton, skin weights, IK/FK, constraints are NOT in Alembic |
| **Blend Shapes (as sliders)** | **FAILS** | Only baked vertex positions, no morph targets |
| **Cloth/Hair Simulation Setup** | **FAILS** | Only baked results, cannot re-simulate |
| **Constraints & Expressions** | **FAILS** | Procedural relationships not stored |
| **Materials & Shaders** | **FAILS** | Only material names, no shader networks |

### The Character Rig Problem - Detailed

When a character is exported from Maya to Alembic:

**What IS stored:**
```
Frame 1: [vertex positions for 10,000 vertices]
Frame 2: [vertex positions for 10,000 vertices]
Frame 3: [vertex positions for 10,000 vertices]
... (every frame, full vertex data)
```

**What is NOT stored:**
```
❌ Skeleton hierarchy (joints)
❌ Skin cluster / bone weights
❌ IK handles and solvers
❌ FK controls
❌ Blend shape targets
❌ Constraints (parent, point, orient, aim)
❌ Set driven keys
❌ Animation curves (only sampled values)
❌ Rig control shapes
❌ Custom attributes on controls
```

### Conversion Reality Matrix

| Source → Target | Cameras | Static Geo | Transform Anim | Vertex Anim | Skeleton | Rig |
|-----------------|---------|------------|----------------|-------------|----------|-----|
| Alembic → Maya MA | ✅ | ✅ | ✅ | ✅* | ❌ | ❌ |
| Alembic → FBX | ✅ | ✅ | ✅ | ⚠️** | ❌ | ❌ |
| Alembic → USD | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |

\* Maya can reference Alembic directly for vertex animation playback
\** FBX supports vertex animation but file sizes become enormous

### When Alembic-as-Master Works

1. **Layout/Previs → Final**: Camera and environment geo
2. **Animation Review**: Baked character for lighting/rendering (no edits needed)
3. **VFX Plates**: Background elements, set pieces
4. **Simulation Caching**: Pre-computed cloth, hair, fluids
5. **Cross-Software Rendering**: Geometry for rendering in different applications

### When Alembic-as-Master Fails

1. **Animation Revisions**: Cannot modify poses, timing, or curves
2. **Rig Sharing**: Cannot transfer rigging work between artists
3. **Character Library**: Cannot reuse rigs on new animation
4. **Blend Shape Editing**: Cannot adjust facial expressions
5. **Constraint Updates**: Cannot change parent/child relationships dynamically

### Recommendation for Your Pipeline

| Use Case | Recommended Master Format |
|----------|---------------------------|
| Camera moves | **Alembic** ✅ (works perfectly) |
| Environment/Props | **Alembic** ✅ (works well) |
| Character Animation (final, no edits) | **Alembic** ⚠️ (view-only) |
| Character Animation (editable) | **Maya (.ma/.mb)** or **FBX** |
| Full Scene with Rigs | **Native format** (Maya, Max, etc.) |

### The Bottom Line

**Alembic is excellent for what it was designed for**: caching computed geometry for interchange. It is **not designed to replace native scene files** for complex rigged assets.

If your pipeline requires:
- Editing animation after export → **Don't use Alembic as master**
- Re-rigging or weight painting → **Don't use Alembic as master**
- Modifying constraints/relationships → **Don't use Alembic as master**
- Just viewing/rendering baked animation → **Alembic works great**

---

## What CAN Be Extracted from Alembic

### 1. Hierarchy & Scene Structure

| Data Type | Extractable | Notes |
|-----------|-------------|-------|
| Object hierarchy | **YES** | Full parent-child relationships |
| Object names | **YES** | Preserved from source application |
| Transform nodes (Xform) | **YES** | Position, rotation, scale per frame |
| Visibility states | **YES** | Hidden, Visible, Deferred |
| Bounding boxes | **YES** | Per-object and child bounds |

**Hierarchy traversal**: Objects can be traversed from root to leaf, with full parent chain accessible for computing world-space transforms.

---

### 2. Cameras (ICamera)

Alembic provides comprehensive camera data extraction:

| Property | Unit | Extractable |
|----------|------|-------------|
| **Focal Length** | millimeters | **YES** |
| **Horizontal Aperture** | centimeters | **YES** |
| **Vertical Aperture** | centimeters | **YES** |
| **Horizontal Film Offset** | centimeters | **YES** |
| **Vertical Film Offset** | centimeters | **YES** |
| **Lens Squeeze Ratio** | ratio | **YES** |
| **Near Clipping Plane** | centimeters | **YES** |
| **Far Clipping Plane** | centimeters | **YES** |
| **F-Stop** | f-number | **YES** |
| **Focus Distance** | centimeters | **YES** |
| **Shutter Open/Close** | seconds (relative to frame) | **YES** |
| **Field of View** | degrees (computed) | **YES** |
| **Overscan** (L/R/T/B) | percentage | **YES** |
| **Screen Window** | configuration dict | **YES** |
| **Film Back Transform Ops** | matrix operations | **YES** |
| **Transform Animation** | per-sample | **YES** |

**Camera Animation**: Full keyframe animation of all camera properties and transforms is supported.

---

### 3. Geometry Types

#### 3.1 Polygon Meshes (IPolyMesh)

| Data | Extractable | Notes |
|------|-------------|-------|
| **Vertex Positions** | **YES** | Array of V3f (x, y, z) |
| **Face Counts** | **YES** | Vertices per face |
| **Face Indices** | **YES** | Vertex indices per face |
| **Normals** | **YES** | Per-vertex or per-face-vertex |
| **UV Coordinates** | **YES** | 2D only (Alembic stores UV as V2f) |
| **Velocities** | **YES** | Per-vertex motion vectors |
| **Face Sets** | **YES** | Named groups of faces |
| **Arbitrary Geometry Params** | **YES** | Custom per-vertex/face attributes |
| **Bounding Box** | **YES** | Self-bounds per sample |

**Topology Variance**: Alembic tracks whether mesh topology is:
- **Constant**: Same vertex count and connectivity throughout
- **Homogeneous**: Same vertex count, connectivity may change
- **Heterogeneous**: Everything can change (fluid sims, etc.)

#### 3.2 Subdivision Surfaces (ISubD)

| Data | Extractable | Notes |
|------|-------------|-------|
| All PolyMesh data | **YES** | Same as above |
| **Subdivision Scheme** | **YES** | Catmull-Clark, Loop, etc. |
| **Crease Indices** | **YES** | Edge crease locations |
| **Crease Lengths** | **YES** | Crease edge counts |
| **Crease Sharpnesses** | **YES** | Per-crease sharpness values |
| **Corner Indices** | **YES** | Vertex corner locations |
| **Corner Sharpnesses** | **YES** | Per-corner sharpness values |
| **Holes** | **YES** | Face hole flags |
| **Interpolate Boundary** | **YES** | Boundary interpolation mode |
| **Face-Varying Interpolate** | **YES** | UV boundary handling |

**Note**: Normals are NOT stored as first-class attributes on SubD surfaces.

#### 3.3 Curves (ICurves)

| Data | Extractable | Notes |
|------|-------------|-------|
| **Control Points** | **YES** | Positions array |
| **Curve Counts** | **YES** | Points per curve |
| **Curve Type** | **YES** | Linear, Cubic, etc. |
| **Wrap Mode** | **YES** | Periodic, Non-periodic |
| **Width/Radius** | **YES** | Per-point or constant |
| **Normals** | **YES** | Orientation vectors |
| **UVs** | **YES** | Parametric coordinates |

#### 3.4 Points (IPoints)

| Data | Extractable | Notes |
|------|-------------|-------|
| **Positions** | **YES** | V3f array |
| **Point IDs** | **YES** | Persistent identification |
| **Velocities** | **YES** | Motion vectors |
| **Widths** | **YES** | Per-point size |

#### 3.5 NURBS Surfaces (INuPatch)

| Data | Extractable | Notes |
|------|-------------|-------|
| **Control Points** | **YES** | UV grid of positions |
| **U/V Order** | **YES** | Degree + 1 |
| **U/V Knots** | **YES** | Knot vectors |
| **Trim Curves** | **YES** | Surface trimming data |

---

### 4. Transforms (IXform)

Transform data can be extracted as either decomposed components or combined matrix:

| Data | Extractable | Notes |
|------|-------------|-------|
| **Translation** | **YES** | V3d (x, y, z) |
| **Rotation** | **YES** | Euler angles or axis-angle |
| **Scale** | **YES** | V3d (x, y, z) |
| **Combined Matrix** | **YES** | 4x4 transformation matrix (M44d) |
| **Operation Stack** | **YES** | Individual transform operations in order |
| **Inherits Transform** | **YES** | Whether to inherit parent transform |

**Transform Operations Stack**: Alembic stores transforms as an ordered list of operations:
- `kTranslateOperation`
- `kRotateXOperation`, `kRotateYOperation`, `kRotateZOperation`
- `kScaleOperation`
- `kMatrixOperation`

This allows preservation of the exact transform order from the source application.

---

### 5. Animation & Time Sampling

| Data | Extractable | Notes |
|------|-------------|-------|
| **Sample Count** | **YES** | Number of time samples |
| **Time Sampling Type** | **YES** | Uniform, Cyclic, Acyclic |
| **Sample Times** | **YES** | Exact time for each sample |
| **Start/End Time** | **YES** | Computed from samples |

**Important**: Alembic works in **time (seconds)**, not frames. Frame rate must be inferred or provided separately.

**Types of Time Sampling**:
1. **Uniform**: Regular intervals (e.g., every 1/24th second)
2. **Cyclic**: Repeating pattern
3. **Acyclic**: Arbitrary time values

---

### 6. Custom Properties & Metadata

| Data | Extractable | Notes |
|------|-------------|-------|
| **User Properties** | **YES** | Arbitrary named properties |
| **Arbitrary Geom Params** | **YES** | Per-vertex/face custom data |
| **Object Metadata** | **YES** | Key-value string pairs |
| **Archive Info** | **YES** | Application, date, etc. |

**Supported Property Types**:
- Scalars: bool, int, float, double, string
- Vectors: V2f, V3f, V2d, V3d
- Matrices: M33f, M33d, M44f, M44d
- Quaternions: Quatf, Quatd
- Bounding boxes: Box2, Box3
- Arrays of all above types

---

## What CANNOT Be Extracted from Alembic

### Fundamental Limitations

| Data Type | Available | Reason |
|-----------|-----------|--------|
| **Rigs/Skeletons** | **NO** | Alembic stores baked results only |
| **Constraints** | **NO** | Procedural relationships not stored |
| **IK/FK Systems** | **NO** | Rig logic not preserved |
| **Blend Shapes (as controllers)** | **NO** | Only baked vertex positions |
| **Deformers** | **NO** | Only resulting deformation |
| **Expressions** | **NO** | Procedural logic not stored |
| **Simulation Setup** | **NO** | Only simulation results |
| **Node Graphs** | **NO** | No procedural networks |
| **Animation Curves** | **NO** | Only sampled values, no bezier handles |

### Partial/Limited Support

| Data Type | Status | Notes |
|-----------|--------|-------|
| **Materials** | **LIMITED** | Material *names* only, no shader data |
| **Lights** | **LIMITED** | Basic light schema exists but rarely used |
| **Textures** | **NO** | Not stored in Alembic |
| **UV W-coordinate** | **NO** | Only UV (2D), not UVW |
| **SubD Normals** | **NO** | Not a first-class attribute |
| **Frame Numbers** | **NO** | Time-based only, no frame concept |

---

## Animation Categories in MultiConverter

Our converter categorizes animation based on what Alembic provides:

### 1. Static Geometry
- Single sample or identical samples across time
- Export: Geometry at frame 1, no animation keyframes

### 2. Transform-Only Animation
- Constant topology (same vertices/faces throughout)
- Vertex positions change only due to transform
- Export: Static geometry + transform keyframes

### 3. Vertex Animation (Deformation)
- Vertex positions change per-frame
- Could be: skinning, blend shapes, cloth, fluids
- **Limitation**: Cannot export to formats that don't support vertex caching (After Effects)

---

## Coordinate System Notes

| Application | Up Axis | Forward | Handedness |
|-------------|---------|---------|------------|
| Alembic (Maya default) | Y-up | -Z | Right-handed |
| Unreal Engine | Z-up | X | Left-handed |
| After Effects | Y-up | -Z | Left-handed |

**MultiConverter handles these conversions automatically.**

---

## Practical Extraction Examples

### What You Can Expect to Extract:

1. **Animated Character**:
   - Full mesh with vertex animation (baked skinning)
   - Transform hierarchy preserved
   - UVs and normals intact
   - **Cannot**: Re-rig or modify bone weights

2. **Camera Move**:
   - Full camera path with all lens properties
   - Focal length changes (dolly zoom)
   - Focus pulls
   - **Can**: Reproduce exact camera in any application

3. **Cloth Simulation**:
   - Frame-by-frame vertex positions
   - Changing topology supported
   - **Cannot**: Re-simulate or modify physics

4. **Environment/Props**:
   - Static or animated transforms
   - Full geometry detail
   - Material names for reassignment
   - **Cannot**: Procedural instancing, material properties

---

## References

- [Alembic Official Documentation](https://docs.alembic.io/)
- [Alembic.io](https://www.alembic.io/)
- [Alembic GitHub Repository](https://github.com/alembic/alembic)
- [Houdini Alembic Documentation](https://www.sidefx.com/docs/houdini/io/alembic.html)
- [Blender Alembic Manual](https://docs.blender.org/manual/en/latest/files/import_export/alembic.html)

---

## MultiConverter Extraction Summary

**Currently Extracted by MultiConverter v2.6.1**:
- Cameras (full properties + animation)
- Polygon Meshes (geometry + UVs + animation)
- Transforms/Locators (hierarchy + animation)
- Time sampling and frame detection

**Planned for Future Versions**:
- Subdivision surfaces
- Curves
- Points/Particles
- Face sets
- Custom properties passthrough

---

*Document prepared for VFX-Experts pipeline review*
*Last updated: January 2026*
