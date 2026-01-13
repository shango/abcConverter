#!/usr/bin/env python3
"""
After Effects Exporter Module
Exports Alembic data to After Effects JSX + OBJ format with vertex animation filtering
"""

import os
from pathlib import Path

from alembic.Abc import WrapExistingFlag
from alembic.AbcGeom import IXform, ICamera, IPolyMesh

from .base_exporter import BaseExporter


class AfterEffectsExporter(BaseExporter):
    """After Effects JSX + OBJ exporter with vertex animation filtering

    After Effects can only handle transform animation (position, rotation, scale).
    Meshes with vertex animation (deformation) must be skipped entirely.

    Exports:
    - Single JSX file with scene setup and animation
    - Multiple OBJ files (one per mesh, frame 1 only)
    """

    def get_format_name(self):
        return "After Effects JSX + OBJ"

    def get_file_extension(self):
        return "jsx"

    def export(self, reader, output_path, shot_name, fps, frame_count, animation_data):
        """Export to After Effects JSX format

        Args:
            reader: AlembicReader instance
            output_path: Output directory path
            shot_name: Shot name for composition and file naming
            fps: Frames per second
            frame_count: Total number of frames
            animation_data: Animation analysis with keys 'vertex_animated', 'transform_only', 'static'

        Returns:
            dict: Export results with keys:
                - 'success': bool
                - 'jsx_file': Path to created JSX file
                - 'obj_files': List of created OBJ file paths
                - 'skipped_meshes': List of skipped mesh names (vertex animated)
                - 'message': Status message
        """
        try:
            output_dir = self.validate_output_path(output_path)

            # Log vertex animation skipping
            skipped_meshes = animation_data['vertex_animated']
            if skipped_meshes:
                self.log(f"⚠ Skipping {len(skipped_meshes)} meshes with vertex animation:")
                for mesh_name in skipped_meshes:
                    self.log(f"  - {mesh_name}")

            # Get scene info
            comp_width, comp_height = reader.extract_render_resolution()
            footage_path = reader.extract_footage_path()
            duration = frame_count / fps

            # Build parent map
            parent_map = reader.get_parent_map()
            objects = reader.get_all_objects()

            # Generate JSX
            jsx_lines = []

            # Header
            jsx_lines.extend(self._generate_header(shot_name, reader.abc_file.name))

            # Helper functions
            jsx_lines.extend(self._generate_helper_functions())

            # Main function start
            jsx_lines.append("function SceneImportFunction() {")
            jsx_lines.append("")
            jsx_lines.append("app.exitAfterLaunchAndEval = false;")
            jsx_lines.append("")
            jsx_lines.append("app.beginUndoGroup('Scene Import');")
            jsx_lines.append("")

            # Create composition
            jsx_lines.append(f"var comp = app.project.items.addComp('{shot_name}', {comp_width}, {comp_height}, 1.0, {duration}, {fps});")
            jsx_lines.append("comp.displayStartFrame = 1;")
            jsx_lines.append("")

            # Import footage if available
            if footage_path:
                jsx_lines.extend(self._generate_footage_import(footage_path, shot_name))

            # Process objects
            processed_names = set()

            for obj in objects:
                name = obj.getName()

                if name == "ABC" or not name:
                    continue

                if name in processed_names:
                    continue

                # Skip helper/organizational objects
                parent = parent_map.get(name)
                parent_name_for_check = parent.getName() if parent else None
                if self._should_skip_object(name, parent_name_for_check):
                    continue

                # Skip organizational groups
                if IXform.matches(obj.getHeader()) and self._is_organizational_group(obj):
                    continue

                # Process cameras
                if ICamera.matches(obj.getHeader()):
                    parent = parent_map.get(name)
                    if parent and IXform.matches(parent.getHeader()):
                        parent_name = parent.getName()
                        transform_obj = parent
                    else:
                        parent_name = name
                        transform_obj = obj

                    self.log(f"Processing camera: {parent_name}")
                    camera_jsx = self._process_camera(reader, obj, transform_obj, parent_name,
                                                     frame_count, fps, comp_width, comp_height)
                    jsx_lines.extend(camera_jsx)
                    jsx_lines.append("")
                    processed_names.add(name)
                    if parent_name != name:
                        processed_names.add(parent_name)

                # Process meshes (skip vertex-animated ones)
                elif IPolyMesh.matches(obj.getHeader()):
                    # Skip if mesh has vertex animation
                    if name in skipped_meshes:
                        self.log(f"Skipping vertex-animated mesh: {name}")
                        processed_names.add(name)
                        continue

                    parent = parent_map.get(name)
                    if parent and IXform.matches(parent.getHeader()):
                        parent_name = parent.getName()
                        transform_obj = parent
                    else:
                        parent_name = None
                        transform_obj = obj

                    self.log(f"Processing geometry: {parent_name or name}")
                    geom_jsx = self._process_geometry(reader, obj, transform_obj, name, parent_name,
                                                      frame_count, fps, output_dir, comp_width, comp_height)
                    jsx_lines.extend(geom_jsx)
                    jsx_lines.append("")
                    processed_names.add(name)
                    if parent_name:
                        processed_names.add(parent_name)

                # Process transforms (cameras/meshes with Nuke-style nesting, or locators)
                elif IXform.matches(obj.getHeader()):
                    # Check for nested camera
                    nested_camera = self._find_camera_recursive(obj)
                    if nested_camera:
                        camera_name = nested_camera.getName()
                        self.log(f"Processing camera (Nuke-style): {name} -> {camera_name}")
                        camera_jsx = self._process_camera(reader, nested_camera, obj, name,
                                                         frame_count, fps, comp_width, comp_height)
                        jsx_lines.extend(camera_jsx)
                        jsx_lines.append("")
                        processed_names.add(name)
                        processed_names.add(camera_name)
                        for child in obj.children:
                            if IXform.matches(child.getHeader()):
                                processed_names.add(child.getName())

                    # Check for nested mesh
                    elif self._find_mesh_recursive(obj):
                        nested_mesh = self._find_mesh_recursive(obj)
                        mesh_name = nested_mesh.getName()

                        # Skip if mesh has vertex animation
                        if mesh_name in skipped_meshes:
                            self.log(f"Skipping vertex-animated mesh: {mesh_name}")
                            processed_names.add(name)
                            processed_names.add(mesh_name)
                            continue

                        self.log(f"Processing geometry (Nuke-style): {name} -> {mesh_name}")
                        geom_jsx = self._process_geometry(reader, nested_mesh, obj, mesh_name, name,
                                                          frame_count, fps, output_dir, comp_width, comp_height)
                        jsx_lines.extend(geom_jsx)
                        jsx_lines.append("")
                        processed_names.add(name)
                        processed_names.add(mesh_name)
                        for child in obj.children:
                            if IXform.matches(child.getHeader()):
                                processed_names.add(child.getName())

                    # Process as locator
                    else:
                        self.log(f"Processing locator: {name}")
                        loc_jsx = self._process_locator(reader, obj, name, frame_count, fps,
                                                       comp_width, comp_height)
                        jsx_lines.extend(loc_jsx)
                        jsx_lines.append("")
                        processed_names.add(name)

            # Footer
            jsx_lines.extend(self._generate_footer())

            # Write JSX file
            jsx_file = output_dir / f"{shot_name}.jsx"
            with open(jsx_file, 'w') as f:
                f.write("\n".join(jsx_lines))

            # Collect OBJ files
            obj_files = list(output_dir.glob('*.obj'))

            self.log(f"\n✓ JSX written to: {jsx_file}")
            self.log(f"✓ Frame count: {frame_count}")
            self.log(f"✓ Duration: {duration}s @ {fps} fps")
            self.log(f"✓ OBJ files exported: {len(obj_files)}")

            return {
                'success': True,
                'jsx_file': str(jsx_file),
                'obj_files': [str(f) for f in obj_files],
                'skipped_meshes': skipped_meshes,
                'message': f"Exported {len(obj_files)} OBJ files, skipped {len(skipped_meshes)} vertex-animated meshes",
                'files': [str(jsx_file)] + [str(f) for f in obj_files]
            }

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            return {
                'success': False,
                'message': f"Export failed: {str(e)}",
                'files': []
            }

    def _generate_header(self, shot_name, abc_filename):
        """Generate JSX file header"""
        lines = []
        lines.append("// Auto-generated JSX from Alembic")
        lines.append(f"// Exported from: {abc_filename}")
        lines.append("// Y-up coordinate system, 1:1 scale")
        lines.append("")
        lines.append("app.activate();")
        lines.append("")
        return lines

    def _generate_helper_functions(self):
        """Generate JSX helper functions"""
        lines = []
        lines.append("function findComp(nm) {")
        lines.append("    var i, n, prjitm;")
        lines.append("")
        lines.append("    prjitm = app.project.items;")
        lines.append("    n = prjitm.length;")
        lines.append("    for (i = 1; i <= n; i++) {")
        lines.append("        if (prjitm[i].name == nm)")
        lines.append("            return prjitm[i];")
        lines.append("    }")
        lines.append("    return null;")
        lines.append("}")
        lines.append("")
        lines.append("function firstComp() {")
        lines.append("    var i, n, prjitm;")
        lines.append("")
        lines.append("    if (app.project.activeItem.typeName == \"Composition\")")
        lines.append("        return app.project.activeItem;")
        lines.append("")
        lines.append("    prjitm = app.project.items;")
        lines.append("    n = prjitm.length;")
        lines.append("    for (i = 1; i <= n; i++) {")
        lines.append("        if (prjitm[i].typeName == \"Composition\")")
        lines.append("            return prjitm[i];")
        lines.append("    }")
        lines.append("    return null;")
        lines.append("}")
        lines.append("")
        lines.append("function firstSelectedComp(items) {")
        lines.append("    var i, itm, subitm;")
        lines.append("")
        lines.append("    for (i = 1; i <= items.length; i++) {")
        lines.append("        itm = items[i];")
        lines.append("        if (itm instanceof CompItem && itm.selected)")
        lines.append("            return itm;")
        lines.append("        if (itm instanceof FolderItem) {")
        lines.append("            subitm = firstSelectedComp(itm.items);")
        lines.append("            if (subitm)")
        lines.append("                return subitm;")
        lines.append("        }")
        lines.append("    };")
        lines.append("    return null;")
        lines.append("}")
        lines.append("")
        lines.append("function deselectAll(items) {")
        lines.append("    var i, itm;")
        lines.append("")
        lines.append("    for (i = 1; i <= items.length; i++) {")
        lines.append("        itm = items[i];")
        lines.append("        if (itm instanceof FolderItem)")
        lines.append("            deselectAll(itm.items);")
        lines.append("        itm.selected = false;")
        lines.append("    };")
        lines.append("}")
        lines.append("")
        return lines

    def _generate_footage_import(self, footage_path, shot_name):
        """Generate JSX code for footage import"""
        lines = []
        lines.append("// Import footage file from Alembic metadata")
        lines.append(f"var footagePath = '{footage_path.replace(chr(92), '/')}';")
        lines.append("var footageFile = new File(footagePath);")
        lines.append("if (footageFile.exists) {")
        lines.append("    var footageImportOptions = new ImportOptions(footageFile);")
        lines.append("    var footageItem = app.project.importFile(footageImportOptions);")
        lines.append("    footageItem.selected = false;")
        lines.append(f"    footageItem.name = '{shot_name}_Footage';")
        lines.append("    // Add footage to composition as background layer")
        lines.append("    var footageLayer = comp.layers.add(footageItem);")
        lines.append(f"    footageLayer.name = '{shot_name}_Footage';")
        lines.append("    footageLayer.moveToEnd();  // Move to bottom of layer stack")
        lines.append("} else {")
        lines.append(f"    alert('Warning: Footage file not found at path: ' + footagePath);")
        lines.append("}")
        lines.append("")
        return lines

    def _generate_footer(self):
        """Generate JSX file footer"""
        lines = []
        lines.append("// Make comp the current open composition")
        lines.append("comp.selected = true;")
        lines.append("deselectAll(app.project.items);")
        lines.append("comp.selected = true;")
        lines.append("comp.openInViewer();")
        lines.append("")
        lines.append("app.endUndoGroup();")
        lines.append("alert('Scene import complete!');")
        lines.append("")
        lines.append("} // End SceneImportFunction")
        lines.append("")
        lines.append("SceneImportFunction();")
        return lines

    def _collect_animation_data(self, reader, obj, frame_count, fps):
        """Collect all animation keyframes into arrays"""
        times_array = []
        pos_array = []
        rotX_array = []
        rotY_array = []
        rotZ_array = []
        scale_array = []

        # Collect keyframes starting from frame 1
        for frame in range(1, frame_count + 1):
            time_seconds = frame / fps
            pos, rot, scale = reader.get_transform_at_time(obj, time_seconds)

            times_array.append(time_seconds)
            pos_array.append(pos)
            rotX_array.append(rot[0])
            rotY_array.append(rot[1])
            rotZ_array.append(rot[2])
            # AE scale is in percent, compensate for world-scale OBJ vertices
            scale_array.append([s * 2 for s in scale])

        return times_array, pos_array, rotX_array, rotY_array, rotZ_array, scale_array

    def _is_animated(self, times, pos, rotX, rotY, rotZ, scale):
        """Check if animation data has any variation (not static)"""
        if len(times) <= 1:
            return False

        # Check if any values differ from the first frame
        for i in range(1, len(times)):
            # Check position
            if (abs(pos[i][0] - pos[0][0]) > 0.0001 or
                abs(pos[i][1] - pos[0][1]) > 0.0001 or
                abs(pos[i][2] - pos[0][2]) > 0.0001):
                return True
            # Check rotation
            if (abs(rotX[i] - rotX[0]) > 0.0001 or
                abs(rotY[i] - rotY[0]) > 0.0001 or
                abs(rotZ[i] - rotZ[0]) > 0.0001):
                return True
            # Check scale
            if (abs(scale[i][0] - scale[0][0]) > 0.0001 or
                abs(scale[i][1] - scale[0][1]) > 0.0001 or
                abs(scale[i][2] - scale[0][2]) > 0.0001):
                return True

        return False

    def _process_camera(self, reader, cam_obj, transform_obj, name, frame_count, fps, comp_width, comp_height):
        """Process camera and return JSX with array-based animation"""
        jsx = []
        camera = ICamera(cam_obj, WrapExistingFlag.kWrapExisting)
        cam_schema = camera.getSchema()
        cam_sample = cam_schema.getValue()

        focal_length = cam_sample.getFocalLength()
        h_aperture = cam_sample.getHorizontalAperture() * 10  # cm to mm

        # Calculate AE zoom value
        ae_zoom = focal_length * comp_width / h_aperture

        layer_var = f"camera_{name.replace(' ', '_').replace('-', '_')}"

        # Create camera
        jsx.append(f"var {layer_var} = comp.layers.addCamera('{name}', [0, 0]);")
        jsx.append(f"{layer_var}.autoOrient = AutoOrientType.NO_AUTO_ORIENT;")

        # Collect animation data
        times, pos, rotX, rotY, rotZ, scale = self._collect_animation_data(reader, transform_obj, frame_count, fps)

        # Generate array definitions and population
        jsx.append(f"var timesArray = new Array();")
        jsx.append(f"var posArray = new Array();")
        jsx.append(f"var rotXArray = new Array();")
        jsx.append(f"var rotYArray = new Array();")
        jsx.append(f"var rotZArray = new Array();")

        # Coordinate system transformation (Alembic Y-up to AE composition space)
        comp_center_x = comp_width / 2
        comp_center_y = comp_height / 2

        for i in range(len(times)):
            x_ae = pos[i][0] * 10 + comp_center_x
            y_ae = -pos[i][1] * 10 + comp_center_y
            z_ae = -pos[i][2] * 10

            jsx.append(f"timesArray.push({times[i]:.10f});")
            jsx.append(f"posArray.push([{x_ae:.10f}, {y_ae:.10f}, {z_ae:.10f}]);")
            jsx.append(f"rotXArray.push({-rotX[i]:.10f});")
            jsx.append(f"rotYArray.push({rotY[i]:.10f});")
            jsx.append(f"rotZArray.push({rotZ[i]:.10f});")

        # Apply arrays to properties
        jsx.append(f"{layer_var}.position.setValuesAtTimes(timesArray, posArray);")
        jsx.append(f"{layer_var}.rotationX.setValuesAtTimes(timesArray, rotXArray);")
        jsx.append(f"{layer_var}.rotationY.setValuesAtTimes(timesArray, rotYArray);")
        jsx.append(f"{layer_var}.rotationZ.setValuesAtTimes(timesArray, rotZArray);")

        # Set camera zoom
        jsx.append(f"{layer_var}.zoom.setValue({ae_zoom:.10f});")

        return jsx

    def _process_geometry(self, reader, mesh_obj, transform_obj, name, parent_name, frame_count, fps, output_dir, comp_width, comp_height):
        """Process geometry mesh with OBJ export and transform"""
        jsx = []
        layer_name = parent_name if parent_name else name
        layer_var = f"mesh_{layer_name.replace(' ', '_').replace('-', '_')}"

        # Export OBJ
        obj_filename = f"{layer_name}.obj"
        obj_path = os.path.join(output_dir, obj_filename)
        self._export_mesh_to_obj(mesh_obj, obj_path)

        # Generate OBJ import code
        jsx.append(f"var importOptions = new ImportOptions();")
        jsx.append(f"importOptions.file = File(new File($.fileName).parent.fsName + '/{obj_filename}');")
        jsx.append(f"var objFootage = app.project.importFile(importOptions);")
        jsx.append(f"objFootage.selected = false;")
        jsx.append(f"app.beginSuppressDialogs();")
        jsx.append(f"var {layer_var} = comp.layers.add(objFootage);")
        jsx.append(f"{layer_var}.name = '{layer_name}';")
        jsx.append(f"app.endSuppressDialogs(true);")

        # Set anchor point to [0,0,0]
        jsx.append(f"{layer_var}.anchorPoint.setValue([0, 0, 0]);")

        # Collect animation data
        times, pos, rotX, rotY, rotZ, scale = self._collect_animation_data(reader, transform_obj, frame_count, fps)

        # Check if animated or static
        if len(times) > 0 and self._is_animated(times, pos, rotX, rotY, rotZ, scale):
            # Animated - use setValuesAtTimes
            jsx.append(f"var timesArray = new Array();")
            jsx.append(f"var posArray = new Array();")
            jsx.append(f"var rotXArray = new Array();")
            jsx.append(f"var rotYArray = new Array();")
            jsx.append(f"var rotZArray = new Array();")
            jsx.append(f"var scaleArray = new Array();")

            comp_center_x = comp_width / 2
            comp_center_y = comp_height / 2

            for i in range(len(times)):
                x_ae = pos[i][0] * 10 + comp_center_x
                y_ae = -pos[i][1] * 10 + comp_center_y
                z_ae = -pos[i][2] * 10

                jsx.append(f"timesArray.push({times[i]:.10f});")
                jsx.append(f"posArray.push([{x_ae:.10f}, {y_ae:.10f}, {z_ae:.10f}]);")
                jsx.append(f"rotXArray.push({-rotX[i]:.10f});")
                jsx.append(f"rotYArray.push({rotY[i]:.10f});")
                jsx.append(f"rotZArray.push({rotZ[i]:.10f});")
                jsx.append(f"scaleArray.push([{scale[i][0]:.10f}, {scale[i][1]:.10f}, {scale[i][2]:.10f}]);")

            jsx.append(f"{layer_var}.position.setValuesAtTimes(timesArray, posArray);")
            jsx.append(f"{layer_var}.rotationX.setValuesAtTimes(timesArray, rotXArray);")
            jsx.append(f"{layer_var}.rotationY.setValuesAtTimes(timesArray, rotYArray);")
            jsx.append(f"{layer_var}.rotationZ.setValuesAtTimes(timesArray, rotZArray);")
            jsx.append(f"{layer_var}.scale.setValuesAtTimes(timesArray, scaleArray);")
        elif len(times) > 0:
            # Static - use setValue with first frame values
            comp_center_x = comp_width / 2
            comp_center_y = comp_height / 2

            x_ae = pos[0][0] * 10 + comp_center_x
            y_ae = -pos[0][1] * 10 + comp_center_y
            z_ae = -pos[0][2] * 10

            jsx.append(f"{layer_var}.scale.setValue([{scale[0][0]:.10f}, {scale[0][1]:.10f}, {scale[0][2]:.10f}]);")
            jsx.append(f"{layer_var}.position.setValue([{x_ae:.10f}, {y_ae:.10f}, {z_ae:.10f}]);")
            jsx.append(f"{layer_var}.rotationX.setValue({-rotX[0]:.10f});")
            jsx.append(f"{layer_var}.rotationY.setValue({rotY[0]:.10f});")
            jsx.append(f"{layer_var}.rotationZ.setValue({rotZ[0]:.10f});")

        jsx.append("")
        return jsx

    def _process_locator(self, reader, loc_obj, name, frame_count, fps, comp_width, comp_height):
        """Process locator/transform as 3D null"""
        jsx = []
        layer_var = f"locator_{name.replace(' ', '_').replace('-', '_')}"

        jsx.append(f"var {layer_var} = comp.layers.addNull();")
        jsx.append(f"{layer_var}.name = '{name}';")
        jsx.append(f"{layer_var}.threeDLayer = true;")
        jsx.append(f"{layer_var}.shy = true;")
        jsx.append(f"{layer_var}.label = 13;")  # 13 = yellow in AE

        # Collect animation data
        times, pos, rotX, rotY, rotZ, scale = self._collect_animation_data(reader, loc_obj, frame_count, fps)

        # Check if animated or static
        if len(times) > 0 and self._is_animated(times, pos, rotX, rotY, rotZ, scale):
            # Animated
            jsx.append(f"var timesArray = new Array();")
            jsx.append(f"var posArray = new Array();")
            jsx.append(f"var rotXArray = new Array();")
            jsx.append(f"var rotYArray = new Array();")
            jsx.append(f"var rotZArray = new Array();")

            comp_center_x = comp_width / 2
            comp_center_y = comp_height / 2

            for i in range(len(times)):
                x_ae = pos[i][0] * 10 + comp_center_x
                y_ae = -pos[i][1] * 10 + comp_center_y
                z_ae = -pos[i][2] * 10

                jsx.append(f"timesArray.push({times[i]:.10f});")
                jsx.append(f"posArray.push([{x_ae:.10f}, {y_ae:.10f}, {z_ae:.10f}]);")
                jsx.append(f"rotXArray.push({-rotX[i]:.10f});")
                jsx.append(f"rotYArray.push({rotY[i]:.10f});")
                jsx.append(f"rotZArray.push({rotZ[i]:.10f});")

            jsx.append(f"{layer_var}.position.setValuesAtTimes(timesArray, posArray);")
            jsx.append(f"{layer_var}.rotationX.setValuesAtTimes(timesArray, rotXArray);")
            jsx.append(f"{layer_var}.rotationY.setValuesAtTimes(timesArray, rotYArray);")
            jsx.append(f"{layer_var}.rotationZ.setValuesAtTimes(timesArray, rotZArray);")
        elif len(times) > 0:
            # Static
            comp_center_x = comp_width / 2
            comp_center_y = comp_height / 2

            x_ae = pos[0][0] * 10 + comp_center_x
            y_ae = -pos[0][1] * 10 + comp_center_y
            z_ae = -pos[0][2] * 10

            jsx.append(f"{layer_var}.position.setValue([{x_ae:.10f}, {y_ae:.10f}, {z_ae:.10f}]);")
            jsx.append(f"{layer_var}.property('Anchor Point').setValue([0.00, 0.00, 0.00]);")
            jsx.append(f"{layer_var}.scale.setValue([{scale[0][0]:.10f}, {scale[0][1]:.10f}, {scale[0][2]:.10f}]);")

        jsx.append("")
        return jsx

    def _export_mesh_to_obj(self, mesh_obj, obj_path):
        """Export a PolyMesh to OBJ file"""
        try:
            poly = IPolyMesh(mesh_obj, WrapExistingFlag.kWrapExisting)
            schema = poly.getSchema()

            # Get mesh data at first sample
            sample = schema.getValue()
            positions = sample.getPositions()
            indices = sample.getFaceIndices()
            counts = sample.getFaceCounts()

            with open(obj_path, 'w') as f:
                f.write(f"# Exported from Alembic\n")
                f.write(f"# Object: {mesh_obj.getName()}\n\n")

                # Write vertices
                for v in positions:
                    f.write(f"v {v[0]} {v[1]} {v[2]}\n")

                # Write faces
                f.write("\n")
                idx = 0
                for count in counts:
                    # OBJ indices are 1-based
                    face_verts = [str(indices[idx + i] + 1) for i in range(count)]
                    f.write(f"f {' '.join(face_verts)}\n")
                    idx += count

            return True
        except Exception as e:
            self.log(f"Warning: Could not export mesh to OBJ: {e}")
            return False

    def _should_skip_object(self, name, parent_name):
        """Check if object should be skipped based on naming conventions"""
        if "Screen" in name or (parent_name and "Screen" in parent_name):
            return True
        if "Trackers" in name and not name.startswith("Tracker"):
            return True
        organizational_names = ["Meshes", "Cameras", "ReadGeo", "root", "persp", "top", "front", "side"]
        if name in organizational_names or any(name.startswith(prefix) for prefix in ["ReadGeo", "Scene"]):
            return True
        return False

    def _is_organizational_group(self, obj):
        """Detect if an IXform is just an organizational container"""
        if not IXform.matches(obj.getHeader()):
            return False

        xform = IXform(obj, WrapExistingFlag.kWrapExisting)
        schema = xform.getSchema()

        num_samples = schema.getNumSamples()
        if num_samples <= 1:
            has_direct_shape = False
            has_children = False
            for child in obj.children:
                has_children = True
                if ICamera.matches(child.getHeader()) or IPolyMesh.matches(child.getHeader()):
                    has_direct_shape = True
                    break

            if has_children and not has_direct_shape:
                return True

        return False

    def _find_camera_recursive(self, obj, depth=0, max_depth=2):
        """Find a camera child recursively (handles Nuke-style nesting)"""
        for child in obj.children:
            if ICamera.matches(child.getHeader()):
                return child
            if depth < max_depth and IXform.matches(child.getHeader()):
                cam = self._find_camera_recursive(child, depth + 1, max_depth)
                if cam:
                    return cam
        return None

    def _find_mesh_recursive(self, obj, depth=0, max_depth=2):
        """Find a mesh child recursively (handles Nuke-style nesting)"""
        for child in obj.children:
            if IPolyMesh.matches(child.getHeader()):
                return child
            if depth < max_depth and IXform.matches(child.getHeader()):
                mesh = self._find_mesh_recursive(child, depth + 1, max_depth)
                if mesh:
                    return mesh
        return None
