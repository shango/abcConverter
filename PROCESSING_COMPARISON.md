# Processing Comparison: SynthEyes vs Nuke Alembic Files

## SynthEyes Format Processing

### Structure
```
Box01 (IXform, 1 sample)
  └─ Box01Shape (IPolyMesh, 1 sample)
```

### Processing Flow
1. **Box01** (IXform)
   - `is_organizational_group(Box01)` → False (has 1 sample, not organizational)
   - `find_mesh_recursive(Box01)` → Finds "Box01Shape" (direct child)
   - **Action:** Process as geometry (Nuke-style)
     - Transform from: Box01 (IXform)
     - Mesh data from: Box01Shape (IPolyMesh)
     - Layer name: "Box01Shape"
     - OBJ file: "Box01Shape.obj"
   - Add to processed_names: ["Box01", "Box01Shape"]

2. **Box01Shape** (IPolyMesh)
   - Already in processed_names
   - **Action:** Skip

### Result
- ✅ One 3D Null layer named "Box01Shape"
- ✅ One OBJ file "Box01Shape.obj"
- ✅ Transform from Box01 applied correctly

---

## Nuke Format Processing

### Structure
```
Meshes (IXform, 0 samples)                    <- organizational
  └─ ReadGeo1 (IXform, 0 samples)            <- organizational
     └─ root (IXform, 0 samples)             <- organizational
        └─ Box01 (IXform, 0 samples)         <- container
           └─ Box01Shape (IXform, 165 samples) <- actual transform
              └─ mesh (IPolyMesh, 165 samples) <- geometry
```

### Processing Flow
1. **Meshes** (IXform)
   - `is_organizational_group(Meshes)` → True (0 samples, only contains IXforms)
   - **Action:** Skip with log "Skipping organizational group: Meshes"

2. **ReadGeo1** (IXform)
   - `is_organizational_group(ReadGeo1)` → True
   - **Action:** Skip with log "Skipping organizational group: ReadGeo1"

3. **root** (IXform)
   - `is_organizational_group(root)` → True
   - **Action:** Skip with log "Skipping organizational group: root"

4. **Box01** (IXform, 0 samples)
   - `is_organizational_group(Box01)` → True (0 samples, only contains IXforms)
   - **Action:** Skip with log "Skipping organizational group: Box01"

5. **Box01Shape** (IXform, 165 samples)
   - `is_organizational_group(Box01Shape)` → False (165 samples, is animated)
   - `find_mesh_recursive(Box01Shape)` → Finds "mesh" (direct child)
   - **Action:** Process as geometry (Nuke-style)
     - Transform from: Box01Shape (IXform)
     - Mesh data from: mesh (IPolyMesh)
     - Layer name: "mesh" is generic → use parent name "Box01Shape" instead
     - OBJ file: "Box01Shape.obj"
   - Add to processed_names: ["Box01Shape", "mesh"]

6. **mesh** (IPolyMesh)
   - Already in processed_names
   - **Action:** Skip

### Result
- ✅ One 3D Null layer named "Box01Shape"
- ✅ One OBJ file "Box01Shape.obj"
- ✅ Transform from Box01Shape (the animated one) applied correctly
- ✅ Organizational groups (Meshes, ReadGeo1, root, Box01) skipped

---

## Camera Processing Comparison

### SynthEyes Camera
```
Camera01 (IXform, 165 samples)
  └─ Camera01Data (ICamera, 1 sample)
```

**Processing:**
- Direct child camera detected
- Process as camera with parent transform
- Result: Camera layer "Camera01" with animation

### Nuke Camera
```
Cameras (IXform, 0 samples)                 <- organizational
  └─ Camera1 (IXform, 165 samples)
     └─ object (ICamera, 165 samples)
```

**Processing:**
1. **Cameras** → Skip (organizational group)
2. **Camera1** (IXform)
   - `find_camera_recursive(Camera1)` → Finds "object"
   - Process as camera (Nuke-style)
   - Layer name: "Camera1" (parent name)
   - Result: Camera layer "Camera1" with animation

---

## Key Differences Handled

| Aspect | SynthEyes | Nuke | How Handled |
|--------|-----------|------|-------------|
| Nesting depth | 1 level | 2 levels | Recursive search (depth=2) |
| Organizational groups | None | 3-4 levels | Auto-detection by sample count |
| Mesh names | Descriptive | Generic "mesh" | Use parent name if generic |
| Transform location | Parent IXform | Nested IXform | Find recursively |
| Animation samples | 1 or 165 | 0 or 165 | Detect static containers |

---

## Expected After Effects Result (Both Formats)

### Layers Created
- Camera1 (or Camera01) - Camera layer
- Box01Shape - 3D Null
- Box02Shape - 3D Null
- Box03Shape - 3D Null
- GenMan6FT_loShape - 3D Null
- Hemisphere01Shape - 3D Null
- Plane01Shape - 3D Null
- Plane02Shape - 3D Null

### Project Panel
- Box01Shape.obj - Footage
- Box02Shape.obj - Footage
- Box03Shape.obj - Footage
- GenMan6FT_loShape.obj - Footage
- Hemisphere01Shape.obj - Footage
- Plane01Shape.obj - Footage
- Plane02Shape.obj - Footage

### Behavior
- ✅ All geometry is 3D Null + OBJ (NOT solid layers)
- ✅ Transforms animate correctly
- ✅ Camera has proper animation and properties
- ✅ No duplicate layers
- ✅ No organizational group layers

---

## Console Log Comparison

### SynthEyes Export
```
Processing camera: Camera01
Processing geometry (Nuke-style): Box01 -> Box01Shape
  Created OBJ: output/Box01Shape/Box01Shape.obj
Processing geometry (Nuke-style): Box02 -> Box02Shape
  Created OBJ: output/Box02Shape/Box02Shape.obj
[... etc ...]
```

### Nuke Export
```
Skipping organizational group: Meshes
Skipping organizational group: ReadGeo1
Skipping organizational group: root
Skipping organizational group: Box01
Processing geometry (Nuke-style): Box01Shape -> mesh
  Created OBJ: output/Box01Shape/Box01Shape.obj
Skipping organizational group: Box02
Processing geometry (Nuke-style): Box02Shape -> mesh
  Created OBJ: output/Box02Shape/Box02Shape.obj
[... etc ...]
Skipping organizational group: Cameras
Processing camera (Nuke-style): Camera1 -> object
```

---

## Testing Steps

1. **Test SynthEyes file (baseline)**
   ```
   - Open AlembicToJSX.exe
   - Select: syntheyes_output/syntheyes_export.abc
   - Convert
   - Import JSX in After Effects
   - Verify: 7 nulls + OBJs, 1 camera, no solids
   ```

2. **Test Nuke file (new support)**
   ```
   - Open AlembicToJSX.exe
   - Select: syntheyes_output/nuke_export.abc
   - Convert
   - Check console for "Skipping organizational group" messages
   - Import JSX in After Effects
   - Verify: Same result as SynthEyes (7 nulls + OBJs, 1 camera, no solids)
   ```

3. **Compare results**
   - Both should have identical layer structure
   - Both should have OBJ files with same names
   - Animation should work correctly in both

---

## Success Criteria

✅ **Nuke file converts without errors**
✅ **Console shows organizational groups being skipped**
✅ **Console shows "Processing geometry (Nuke-style)" for meshes**
✅ **7 OBJ files created with correct names (Box01Shape.obj, etc.)**
✅ **After Effects shows 3D Nulls + OBJ footage (NOT solids)**
✅ **Transforms and animation work correctly**
✅ **No duplicate layers**
✅ **No "Meshes", "ReadGeo1", "root", or other organizational layers**

If all criteria are met, the Nuke support is working correctly! 🎉
