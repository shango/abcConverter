#!/usr/bin/env python3
"""
Alembic to After Effects JSX Converter - GUI Version
User-friendly interface for converting Alembic files to AE compatible JSX with OBJ export
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import sys
import os

# Import core conversion functions
from alembic.Abc import IArchive, ISampleSelector, WrapExistingFlag
from alembic.AbcGeom import IXform, ICamera, IPolyMesh
import imath
import numpy as np


class AlembicToJSXConverter:
    """Core conversion logic with OBJ export"""

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback

    def log(self, message):
        """Send progress updates to callback"""
        if self.progress_callback:
            self.progress_callback(message)
        print(message)

    def detect_frame_count(self, abc_file, fps=24):
        """Detect frame count from Alembic file"""
        try:
            archive = IArchive(str(abc_file))
            # Get time sampling
            num_time_samplings = archive.getNumTimeSamplings()
            if num_time_samplings > 1:
                # Use the first non-uniform time sampling (index 1)
                time_sampling = archive.getTimeSampling(1)
                num_samples = archive.getMaxNumSamplesForTimeSamplingIndex(1)

                if num_samples > 0:
                    return num_samples

            # Fallback: assume 120 frames if we can't detect
            return 120
        except Exception as e:
            self.log(f"Warning: Could not detect frame count: {e}")
            return 120

    def decompose_matrix(self, matrix):
        """Decompose a 4x4 matrix into translation, rotation (XYZ Euler), and scale"""
        m = np.array(matrix)

        # Extract translation (Y-up preserved)
        translation = [m[3][0], m[3][1], m[3][2]]

        # Extract scale
        sx = np.linalg.norm([m[0][0], m[0][1], m[0][2]])
        sy = np.linalg.norm([m[1][0], m[1][1], m[1][2]])
        sz = np.linalg.norm([m[2][0], m[2][1], m[2][2]])
        scale = [sx, sy, sz]

        # Normalize rotation matrix
        rot = m.copy()
        rot[0][0:3] /= sx if sx > 0 else 1
        rot[1][0:3] /= sy if sy > 0 else 1
        rot[2][0:3] /= sz if sz > 0 else 1

        # Extract rotation (XYZ Euler angles in degrees)
        sy_test = np.sqrt(rot[0][0]**2 + rot[1][0]**2)

        if sy_test > 1e-6:
            x = np.arctan2(rot[2][1], rot[2][2])
            y = np.arctan2(-rot[2][0], sy_test)
            z = np.arctan2(rot[1][0], rot[0][0])
        else:
            x = np.arctan2(-rot[1][2], rot[1][1])
            y = np.arctan2(-rot[2][0], sy_test)
            z = 0

        rotation = [np.degrees(x), np.degrees(y), np.degrees(z)]

        return translation, rotation, scale

    def extract_footage_path(self, archive, top):
        """Extract footage file path from Alembic camera metadata

        Returns:
            str: Footage file path, or None if not found
        """
        try:
            # Search for camera objects to extract footage path from metadata
            def find_camera(obj):
                if ICamera.matches(obj.getHeader()):
                    return obj
                for child in obj.children:
                    cam = find_camera(child)
                    if cam:
                        return cam
                return None

            camera_obj = find_camera(top)
            if camera_obj:
                camera = ICamera(camera_obj, WrapExistingFlag.kWrapExisting)
                schema = camera.getSchema()

                # Check for arbGeomParams (custom properties)
                if schema.getArbGeomParams():
                    arb_params = schema.getArbGeomParams()
                    # Try common property names for footage file paths
                    for prop_name in ['footagePath', 'footage', 'sourceFile', 'imagePath',
                                     'videoFile', 'mediaPath', 'sourceImage', 'backgroundImage']:
                        try:
                            if arb_params.getPropertyHeader(prop_name):
                                prop = arb_params.getProperty(prop_name)
                                if prop.valid():
                                    # Try to get string value
                                    val = prop.getValue()
                                    if val and isinstance(val, str):
                                        self.log(f"Found footage path in property '{prop_name}': {val}")
                                        return val
                        except:
                            pass

                # Check user properties
                if schema.getUserProperties():
                    user_props = schema.getUserProperties()
                    # Try common property names for footage file paths
                    for prop_name in ['footagePath', 'footage', 'sourceFile', 'imagePath',
                                     'videoFile', 'mediaPath', 'sourceImage', 'backgroundImage']:
                        try:
                            if user_props.getPropertyHeader(prop_name):
                                prop = user_props.getProperty(prop_name)
                                if prop.valid():
                                    # Try to get string value
                                    val = prop.getValue()
                                    if val and isinstance(val, str):
                                        self.log(f"Found footage path in user property '{prop_name}': {val}")
                                        return val
                        except:
                            pass

        except Exception as e:
            self.log(f"Could not extract footage path from Alembic: {e}")

        return None

    def extract_render_resolution(self, archive, top):
        """Extract render resolution from Alembic camera metadata

        Returns:
            tuple: (width, height) in pixels, or (1920, 1080) as fallback
        """
        try:
            # Search for camera objects to extract resolution from metadata
            def find_camera(obj):
                if ICamera.matches(obj.getHeader()):
                    return obj
                for child in obj.children:
                    cam = find_camera(child)
                    if cam:
                        return cam
                return None

            camera_obj = find_camera(top)
            if camera_obj:
                camera = ICamera(camera_obj, WrapExistingFlag.kWrapExisting)
                schema = camera.getSchema()

                # Check for arbGeomParams (custom properties)
                if schema.getArbGeomParams():
                    arb_params = schema.getArbGeomParams()
                    # Try common property names used by tracking software
                    for prop_name in ['filmWidth', 'filmHeight', 'imageWidth', 'imageHeight',
                                     'renderWidth', 'renderHeight', 'resolutionX', 'resolutionY']:
                        if arb_params.getPropertyHeader(prop_name):
                            self.log(f"Found custom property: {prop_name}")

                # Check user properties
                if schema.getUserProperties():
                    user_props = schema.getUserProperties()
                    self.log(f"Camera has user properties")

                # Get camera sample to check metadata
                cam_sample = schema.getValue()

                # SynthEyes often stores resolution in film back dimensions
                # Aperture is in cm, convert directly to pixels
                h_aperture_cm = cam_sample.getHorizontalAperture()  # cm
                v_aperture_cm = cam_sample.getVerticalAperture()    # cm

                # Common aspect ratios and resolutions
                aspect_ratio = h_aperture_cm / v_aperture_cm if v_aperture_cm > 0 else 1.777

                # Use standard 1920x1080 (HD) resolution
                # Note: SynthEyes may add padding for lens distortion compensation,
                # but we're using the base footage resolution for simplicity
                h_aperture_mm = h_aperture_cm * 10  # Convert cm to mm for logging
                v_aperture_mm = v_aperture_cm * 10

                self.log(f"Using standard HD resolution: 1920x1080")
                self.log(f"  (Camera aperture: {h_aperture_mm:.2f}mm × {v_aperture_mm:.2f}mm)")
                return (1920, 1080)

        except Exception as e:
            self.log(f"Could not extract render resolution from Alembic: {e}")

        # Fallback to HD resolution
        self.log(f"Using default resolution: 1920x1080")
        return (1920, 1080)

    def get_transform_data_at_time(self, obj, time_seconds):
        """Get transform data (position, rotation, scale) at a specific time

        This extracts scale from the LOCAL transform matrix, then gets world position/rotation.
        SynthEyes stores per-object scale in the local matrix.

        Returns:
            tuple: (translation, rotation, scale) where scale is NOT multiplied by 100 yet
        """
        # First, get the LOCAL matrix of this object to extract scale
        local_scale = None
        if IXform.matches(obj.getHeader()):
            xform = IXform(obj, WrapExistingFlag.kWrapExisting)
            schema = xform.getSchema()

            sample_sel = ISampleSelector(time_seconds)
            xf_sample = schema.getValue(sample_sel)
            local_matrix = xf_sample.getMatrix()

            # Extract scale from LOCAL matrix (this is where SynthEyes stores it)
            m = np.array(local_matrix)
            sx = np.linalg.norm([m[0][0], m[0][1], m[0][2]])
            sy = np.linalg.norm([m[1][0], m[1][1], m[1][2]])
            sz = np.linalg.norm([m[2][0], m[2][1], m[2][2]])
            local_scale = [sx, sy, sz]

        # Now accumulate world matrix for position and rotation
        matrices = []
        current = obj

        while current:
            if IXform.matches(current.getHeader()):
                xform = IXform(current, WrapExistingFlag.kWrapExisting)
                schema = xform.getSchema()

                sample_sel = ISampleSelector(time_seconds)
                xf_sample = schema.getValue(sample_sel)
                matrices.append(xf_sample.getMatrix())

            parent = current.getParent()
            if parent and parent.getName() != "ABC":
                current = parent
            else:
                break

        # Combine transforms for world matrix
        world_matrix = imath.M44d()
        world_matrix.makeIdentity()

        for mat in reversed(matrices):
            world_matrix = world_matrix * mat

        # Decompose world matrix for position and rotation
        pos, rot, world_scale = self.decompose_matrix(world_matrix)

        # Use local scale (from the object's own matrix), not world scale
        # This prevents parent scales from affecting the object's scale
        final_scale = local_scale if local_scale is not None else world_scale

        return pos, rot, final_scale

    def get_world_matrix_at_time(self, obj, time_seconds):
        """Get the accumulated world matrix for an object at a specific time

        DEPRECATED: Use get_transform_data_at_time() instead for better scale handling
        """
        matrices = []
        current = obj

        while current:
            if IXform.matches(current.getHeader()):
                xform = IXform(current, WrapExistingFlag.kWrapExisting)
                schema = xform.getSchema()

                sample_sel = ISampleSelector(time_seconds)
                xf_sample = schema.getValue(sample_sel)
                matrices.append(xf_sample.getMatrix())

            parent = current.getParent()
            if parent and parent.getName() != "ABC":
                current = parent
            else:
                break

        world_matrix = imath.M44d()
        world_matrix.makeIdentity()

        for mat in reversed(matrices):
            world_matrix = world_matrix * mat

        return world_matrix

    def export_mesh_to_obj(self, mesh_obj, obj_path):
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

                # Write vertices directly from Alembic
                # Vertices have scale baked in from the Alembic geometry
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

    def collect_animation_data(self, obj, frame_count, fps):
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

            # Use new method that extracts XformOp scale directly
            pos, rot, scale = self.get_transform_data_at_time(obj, time_seconds)

            times_array.append(time_seconds)
            pos_array.append(pos)
            rotX_array.append(rot[0])
            rotY_array.append(rot[1])
            rotZ_array.append(rot[2])
            # AE scale is in percent
            # OBJ vertices are in world-scale cm (not normalized like SynthEyes ±0.5)
            # Scale factor of 2 accounts for the difference between world-scale vertices
            # and the expected final size in After Effects
            scale_array.append([s * 2 for s in scale])  # Compensated for world-scale OBJ vertices

        return times_array, pos_array, rotX_array, rotY_array, rotZ_array, scale_array

    def process_camera(self, cam_obj, transform_obj, name, frame_count, fps, comp_width, comp_height):
        """Process camera and return JSX with array-based animation

        Args:
            cam_obj: ICamera object for camera properties (focal length, aperture)
            transform_obj: IXform object for transform animation (position, rotation)
            name: Layer name
            frame_count: Number of frames
            fps: Frames per second
            comp_width: Composition width in pixels (needed for zoom and position calculation)
            comp_height: Composition height in pixels (needed for position calculation)
        """
        jsx = []
        camera = ICamera(cam_obj, WrapExistingFlag.kWrapExisting)
        cam_schema = camera.getSchema()
        cam_sample = cam_schema.getValue()

        focal_length = cam_sample.getFocalLength()
        h_aperture = cam_sample.getHorizontalAperture() * 10  # cm to mm

        # Calculate AE zoom value
        # AE uses default aperture of 36mm when not explicitly set
        # zoom = focal_length * comp_width / alembic_aperture
        # This scales focal_length to match what it would be with 36mm aperture
        ae_zoom = focal_length * comp_width / h_aperture

        layer_var = f"camera_{name.replace(' ', '_').replace('-', '_')}"

        # Create camera with point of interest at [0, 0] to match SynthEyes coordinate system
        jsx.append(f"var {layer_var} = comp.layers.addCamera('{name}', [0, 0]);")
        jsx.append(f"{layer_var}.autoOrient = AutoOrientType.NO_AUTO_ORIENT;")

        # Collect animation data from transform object (parent IXform)
        times, pos, rotX, rotY, rotZ, scale = self.collect_animation_data(transform_obj, frame_count, fps)

        # Generate array definitions
        jsx.append(f"var timesArray = new Array();")
        jsx.append(f"var posArray = new Array();")
        jsx.append(f"var rotXArray = new Array();")
        jsx.append(f"var rotYArray = new Array();")
        jsx.append(f"var rotZArray = new Array();")

        # Populate arrays with coordinate system transformation
        # Alembic (Y-up): X=lateral, Y=up, Z=depth
        # After Effects 3D: X=lateral, Y=up, Z=depth
        # However, composition Y coordinates use Y=0 at top (screen convention)
        # Transformation to composition space:
        #   X_ae = X_alembic × 10 + (comp_width / 2)
        #   Y_ae = -Y_alembic × 10 + (comp_height / 2)  [negate for comp Y-down convention]
        #   Z_ae = -Z_alembic × 10                       [negate for AE depth convention]
        comp_center_x = comp_width / 2
        comp_center_y = comp_height / 2

        for i in range(len(times)):
            # Apply Y-up world to AE composition space transformation
            x_ae = pos[i][0] * 10 + comp_center_x
            y_ae = -pos[i][1] * 10 + comp_center_y
            z_ae = -pos[i][2] * 10

            jsx.append(f"timesArray.push({times[i]:.10f});")
            jsx.append(f"posArray.push([{x_ae:.10f}, {y_ae:.10f}, {z_ae:.10f}]);")
            jsx.append(f"rotXArray.push({-rotX[i]:.10f});")
            jsx.append(f"rotYArray.push({rotY[i]:.10f});")
            jsx.append(f"rotZArray.push({rotZ[i]:.10f});")

        # Apply arrays to properties using shorthand
        jsx.append(f"{layer_var}.position.setValuesAtTimes(timesArray, posArray);")
        jsx.append(f"{layer_var}.rotationX.setValuesAtTimes(timesArray, rotXArray);")
        jsx.append(f"{layer_var}.rotationY.setValuesAtTimes(timesArray, rotYArray);")
        jsx.append(f"{layer_var}.rotationZ.setValuesAtTimes(timesArray, rotZArray);")

        # Set camera zoom only (don't set aperture - let AE use default 36mm)
        # This matches SynthEyes export behavior
        jsx.append(f"{layer_var}.zoom.setValue({ae_zoom:.10f});")

        return jsx

    def process_geometry(self, mesh_obj, transform_obj, name, parent_name, frame_count, fps, obj_output_dir, jsx_dir, comp_width, comp_height):
        """Process geometry mesh with OBJ export and transform

        Args:
            mesh_obj: IPolyMesh object for mesh geometry
            transform_obj: IXform object for transform animation (position, rotation)
            name: Mesh shape name
            parent_name: Parent transform name (used for layer name)
            frame_count: Number of frames
            fps: Frames per second
            obj_output_dir: Directory for OBJ export
            jsx_dir: Directory for JSX file
            comp_width: Composition width in pixels (needed for position calculation)
            comp_height: Composition height in pixels (needed for position calculation)
        """
        jsx = []
        # Use parent name for layer and OBJ file
        layer_name = parent_name if parent_name else name
        layer_var = f"mesh_{layer_name.replace(' ', '_').replace('-', '_')}"

        # Export OBJ with parent name
        obj_filename = f"{layer_name}.obj"
        obj_path = os.path.join(obj_output_dir, obj_filename)

        self.export_mesh_to_obj(mesh_obj, obj_path)
        self.log(f"Exported OBJ: {obj_filename}")

        # Generate OBJ import code (relative path from JSX location)
        jsx.append(f"var importOptions = new ImportOptions();")
        jsx.append(f"importOptions.file = File(new File($.fileName).parent.fsName + '/{obj_filename}');")
        jsx.append(f"var objFootage = app.project.importFile(importOptions);")
        jsx.append(f"objFootage.selected = false;")
        jsx.append(f"app.beginSuppressDialogs();")
        jsx.append(f"var {layer_var} = comp.layers.add(objFootage);")
        jsx.append(f"{layer_var}.name = '{layer_name}';")
        jsx.append(f"app.endSuppressDialogs(true);")

        # Set anchor point to [0,0,0] to match object origin
        # This prevents position shifts when scaling
        jsx.append(f"{layer_var}.anchorPoint.setValue([0, 0, 0]);")

        # Collect animation data from transform object (parent IXform)
        times, pos, rotX, rotY, rotZ, scale = self.collect_animation_data(transform_obj, frame_count, fps)

        # Check if animated or static
        if len(times) > 0 and self.is_animated(times, pos, rotX, rotY, rotZ, scale):
            # Animated - use setValuesAtTimes
            jsx.append(f"var timesArray = new Array();")
            jsx.append(f"var posArray = new Array();")
            jsx.append(f"var rotXArray = new Array();")
            jsx.append(f"var rotYArray = new Array();")
            jsx.append(f"var rotZArray = new Array();")
            jsx.append(f"var scaleArray = new Array();")

            # Apply coordinate system transformation (same as camera)
            # Alembic Y-up to AE composition space
            # Note: scale is already in percent from collect_animation_data
            comp_center_x = comp_width / 2
            comp_center_y = comp_height / 2

            for i in range(len(times)):
                # Apply Y-up world to AE composition space transformation
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

    def process_locator(self, loc_obj, name, frame_count, fps, comp_width, comp_height):
        """Process locator/transform as 3D null"""
        jsx = []
        layer_var = f"locator_{name.replace(' ', '_').replace('-', '_')}"

        jsx.append(f"var {layer_var} = comp.layers.addNull();")
        jsx.append(f"{layer_var}.name = '{name}';")
        jsx.append(f"{layer_var}.threeDLayer = true;")
        jsx.append(f"{layer_var}.shy = true;")
        jsx.append(f"{layer_var}.label = 13;")  # 13 = yellow in AE

        # Collect animation data
        times, pos, rotX, rotY, rotZ, scale = self.collect_animation_data(loc_obj, frame_count, fps)

        # Check if animated or static
        if len(times) > 0 and self.is_animated(times, pos, rotX, rotY, rotZ, scale):
            # Animated - use setValuesAtTimes
            jsx.append(f"var timesArray = new Array();")
            jsx.append(f"var posArray = new Array();")
            jsx.append(f"var rotXArray = new Array();")
            jsx.append(f"var rotYArray = new Array();")
            jsx.append(f"var rotZArray = new Array();")

            # Apply coordinate system transformation (same as camera)
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
            # Static - use setValue with first frame values
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

    def collect_objects(self, obj, objects_list):
        """Recursively collect all objects in hierarchy"""
        objects_list.append(obj)
        for child in obj.children:
            self.collect_objects(child, objects_list)

    def has_shape_child(self, obj, depth=0, max_depth=2):
        """Check if this object has a camera or mesh child (checks recursively for Nuke-style nesting)"""
        for child in obj.children:
            if ICamera.matches(child.getHeader()) or IPolyMesh.matches(child.getHeader()):
                return True
            # Check one level deeper for Nuke-style extra IXform nesting
            if depth < max_depth and IXform.matches(child.getHeader()):
                if self.has_shape_child(child, depth + 1, max_depth):
                    return True
        return False

    def find_mesh_recursive(self, obj, depth=0, max_depth=2):
        """Find a mesh child recursively (handles Nuke-style extra IXform nesting)"""
        for child in obj.children:
            if IPolyMesh.matches(child.getHeader()):
                return child
            # Check deeper for Nuke-style nesting
            if depth < max_depth and IXform.matches(child.getHeader()):
                mesh = self.find_mesh_recursive(child, depth + 1, max_depth)
                if mesh:
                    return mesh
        return None

    def find_camera_recursive(self, obj, depth=0, max_depth=2):
        """Find a camera child recursively (handles Nuke-style extra IXform nesting)"""
        for child in obj.children:
            if ICamera.matches(child.getHeader()):
                return child
            # Check deeper for Nuke-style nesting
            if depth < max_depth and IXform.matches(child.getHeader()):
                cam = self.find_camera_recursive(child, depth + 1, max_depth)
                if cam:
                    return cam
        return None

    def is_organizational_group(self, obj):
        """Detect if an IXform is just an organizational container with no meaningful transform"""
        if not IXform.matches(obj.getHeader()):
            return False

        # Check if it's animated - if it has significant animation, it's not just organizational
        xform = IXform(obj, WrapExistingFlag.kWrapExisting)
        schema = xform.getSchema()

        # If it has 0 or 1 samples and only contains other IXforms (no direct shapes), it's organizational
        num_samples = schema.getNumSamples()
        if num_samples <= 1:
            # Check if it only contains IXforms (no direct cameras/meshes)
            has_direct_shape = False
            has_children = False
            for child in obj.children:
                has_children = True
                if ICamera.matches(child.getHeader()) or IPolyMesh.matches(child.getHeader()):
                    has_direct_shape = True
                    break

            # If it has children but no direct shapes, likely organizational
            if has_children and not has_direct_shape:
                return True

        return False

    def should_skip_object(self, name, parent_name):
        """Check if object should be skipped based on naming conventions"""
        # Skip objects with "Screen" in the name (helper geometry)
        if "Screen" in name or (parent_name and "Screen" in parent_name):
            return True
        # Skip group/organizational objects like "Camera01Trackers" (but not individual trackers)
        if "Trackers" in name and not name.startswith("Tracker"):
            return True
        # Common organizational group names from various DCCs
        organizational_names = ["Meshes", "Cameras", "ReadGeo", "root", "persp", "top", "front", "side"]
        if name in organizational_names or any(name.startswith(prefix) for prefix in ["ReadGeo", "Scene"]):
            return True
        return False

    def is_animated(self, times, pos, rotX, rotY, rotZ, scale):
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

    def convert(self, abc_file, jsx_file, fps=24, frame_count=120, comp_name="AlembicScene"):
        """Main conversion function with OBJ export"""
        try:
            self.log(f"Opening Alembic file: {abc_file}")
            archive = IArchive(str(abc_file))
            top = archive.getTop()

            # Extract render resolution from Alembic camera
            comp_width, comp_height = self.extract_render_resolution(archive, top)

            # Extract footage file path from Alembic metadata
            footage_path = self.extract_footage_path(archive, top)
            if footage_path:
                self.log(f"Found footage reference: {footage_path}")
            else:
                self.log(f"No footage reference found in Alembic metadata")

            objects = []
            self.collect_objects(top, objects)
            self.log(f"Found {len(objects)} objects in Alembic file")

            # Calculate duration in seconds from frame count and fps
            duration = frame_count / fps

            # Create output directory for OBJ files (same directory as JSX)
            jsx_path = Path(jsx_file)
            obj_output_dir = jsx_path.parent
            jsx_dir = jsx_path.parent

            # Create OBJ directory if needed
            os.makedirs(obj_output_dir, exist_ok=True)

            jsx_lines = []

            # Header with helper functions
            jsx_lines.append("// Auto-generated JSX from Alembic")
            jsx_lines.append(f"// Exported from: {Path(abc_file).name}")
            jsx_lines.append("// Y-up coordinate system, 1:1 scale")
            jsx_lines.append("")
            jsx_lines.append("app.activate();")
            jsx_lines.append("")

            # Add helper functions matching reference file
            jsx_lines.append("function findComp(nm) {")
            jsx_lines.append("    var i, n, prjitm;")
            jsx_lines.append("")
            jsx_lines.append("    prjitm = app.project.items;")
            jsx_lines.append("    n = prjitm.length;")
            jsx_lines.append("    for (i = 1; i <= n; i++) {")
            jsx_lines.append("        if (prjitm[i].name == nm)")
            jsx_lines.append("            return prjitm[i];")
            jsx_lines.append("    }")
            jsx_lines.append("    return null;")
            jsx_lines.append("}")
            jsx_lines.append("")
            jsx_lines.append("function firstComp() {")
            jsx_lines.append("    var i, n, prjitm;")
            jsx_lines.append("")
            jsx_lines.append("    if (app.project.activeItem.typeName == \"Composition\")")
            jsx_lines.append("        return app.project.activeItem;")
            jsx_lines.append("")
            jsx_lines.append("    prjitm = app.project.items;")
            jsx_lines.append("    n = prjitm.length;")
            jsx_lines.append("    for (i = 1; i <= n; i++) {")
            jsx_lines.append("        if (prjitm[i].typeName == \"Composition\")")
            jsx_lines.append("            return prjitm[i];")
            jsx_lines.append("    }")
            jsx_lines.append("    return null;")
            jsx_lines.append("}")
            jsx_lines.append("")
            jsx_lines.append("function firstSelectedComp(items) {")
            jsx_lines.append("    var i, itm, subitm;")
            jsx_lines.append("")
            jsx_lines.append("    for (i = 1; i <= items.length; i++) {")
            jsx_lines.append("        itm = items[i];")
            jsx_lines.append("        if (itm instanceof CompItem && itm.selected)")
            jsx_lines.append("            return itm;")
            jsx_lines.append("        if (itm instanceof FolderItem) {")
            jsx_lines.append("            subitm = firstSelectedComp(itm.items);")
            jsx_lines.append("            if (subitm)")
            jsx_lines.append("                return subitm;")
            jsx_lines.append("        }")
            jsx_lines.append("    };")
            jsx_lines.append("    return null;")
            jsx_lines.append("}")
            jsx_lines.append("")
            jsx_lines.append("function deselectAll(items) {")
            jsx_lines.append("    var i, itm;")
            jsx_lines.append("")
            jsx_lines.append("    for (i = 1; i <= items.length; i++) {")
            jsx_lines.append("        itm = items[i];")
            jsx_lines.append("        if (itm instanceof FolderItem)")
            jsx_lines.append("            deselectAll(itm.items);")
            jsx_lines.append("        itm.selected = false;")
            jsx_lines.append("    };")
            jsx_lines.append("}")
            jsx_lines.append("")

            # Main export function
            jsx_lines.append("function SceneImportFunction() {")
            jsx_lines.append("")
            jsx_lines.append("app.exitAfterLaunchAndEval = false;")
            jsx_lines.append("")
            jsx_lines.append("app.beginUndoGroup('Scene Import');")
            jsx_lines.append("")

            # Create composition
            jsx_lines.append(f"var comp = app.project.items.addComp('{comp_name}', {comp_width}, {comp_height}, 1.0, {duration}, {fps});")
            jsx_lines.append("comp.displayStartFrame = 1;")
            jsx_lines.append("")

            # Import footage file if path was found in Alembic metadata
            if footage_path:
                jsx_lines.append("// Import footage file from Alembic metadata")
                jsx_lines.append(f"var footagePath = '{footage_path.replace(chr(92), '/')}';")
                jsx_lines.append("var footageFile = new File(footagePath);")
                jsx_lines.append("if (footageFile.exists) {")
                jsx_lines.append("    var footageImportOptions = new ImportOptions(footageFile);")
                jsx_lines.append("    var footageItem = app.project.importFile(footageImportOptions);")
                jsx_lines.append("    footageItem.selected = false;")
                jsx_lines.append(f"    footageItem.name = '{comp_name}_Footage';")
                jsx_lines.append("    // Add footage to composition as background layer")
                jsx_lines.append("    var footageLayer = comp.layers.add(footageItem);")
                jsx_lines.append(f"    footageLayer.name = '{comp_name}_Footage';")
                jsx_lines.append("    footageLayer.moveToEnd();  // Move to bottom of layer stack")
                jsx_lines.append("} else {")
                jsx_lines.append(f"    alert('Warning: Footage file not found at path: ' + footagePath);")
                jsx_lines.append("}")
                jsx_lines.append("")

            # Build parent map
            parent_map = {}
            for obj in objects:
                for child in obj.children:
                    parent_map[child.getName()] = obj

            # Process each object
            processed_names = set()  # Track processed objects to avoid duplicates

            for obj in objects:
                name = obj.getName()

                if name == "ABC" or not name:
                    continue

                # Skip if already processed
                if name in processed_names:
                    continue

                # Skip helper/organizational objects (Screen, Trackers groups, etc.)
                parent = parent_map.get(name)
                parent_name_for_check = parent.getName() if parent else None
                if self.should_skip_object(name, parent_name_for_check):
                    self.log(f"Skipping helper object: {name}")
                    continue

                # Skip organizational container groups (detected automatically)
                if IXform.matches(obj.getHeader()) and self.is_organizational_group(obj):
                    self.log(f"Skipping organizational group: {name}")
                    continue

                if ICamera.matches(obj.getHeader()):
                    # Use parent for transforms, child for camera properties
                    parent = parent_map.get(name)
                    if parent and IXform.matches(parent.getHeader()):
                        parent_name = parent.getName()
                        transform_obj = parent  # Read transform from parent IXform
                    else:
                        parent_name = name
                        transform_obj = obj

                    self.log(f"Processing camera: {parent_name}")
                    camera_jsx = self.process_camera(obj, transform_obj, parent_name, frame_count, fps, comp_width, comp_height)
                    jsx_lines.extend(camera_jsx)
                    jsx_lines.append("")
                    processed_names.add(name)
                    if parent_name != name:
                        processed_names.add(parent_name)

                elif IPolyMesh.matches(obj.getHeader()):
                    # Use parent for both naming and transforms
                    parent = parent_map.get(name)
                    if parent and IXform.matches(parent.getHeader()):
                        parent_name = parent.getName()
                        transform_obj = parent  # Read transform from parent IXform
                    else:
                        parent_name = None
                        transform_obj = obj

                    self.log(f"Processing geometry: {parent_name or name}")
                    geom_jsx = self.process_geometry(obj, transform_obj, name, parent_name, frame_count, fps, obj_output_dir, jsx_dir, comp_width, comp_height)
                    jsx_lines.extend(geom_jsx)
                    jsx_lines.append("")
                    processed_names.add(name)
                    if parent_name:
                        processed_names.add(parent_name)

                elif IXform.matches(obj.getHeader()):
                    # Check for deeply nested camera (Nuke-style)
                    nested_camera = self.find_camera_recursive(obj)
                    if nested_camera:
                        # Process as camera with this IXform as transform parent
                        camera_name = nested_camera.getName()
                        self.log(f"Processing camera (Nuke-style): {name} -> {camera_name}")
                        camera_jsx = self.process_camera(nested_camera, obj, name, frame_count, fps, comp_width, comp_height)
                        jsx_lines.extend(camera_jsx)
                        jsx_lines.append("")
                        processed_names.add(name)
                        processed_names.add(camera_name)
                        # Also mark intermediate nodes as processed
                        for child in obj.children:
                            if IXform.matches(child.getHeader()):
                                processed_names.add(child.getName())
                    # Check for deeply nested mesh (Nuke-style)
                    elif self.find_mesh_recursive(obj):
                        nested_mesh = self.find_mesh_recursive(obj)
                        # Process as geometry with this IXform as transform parent
                        mesh_name = nested_mesh.getName()
                        # Use better naming for generic "mesh" names
                        if mesh_name == "mesh" or not mesh_name:
                            display_name = name
                        else:
                            display_name = mesh_name

                        self.log(f"Processing geometry (Nuke-style): {name} -> {mesh_name}")
                        geom_jsx = self.process_geometry(nested_mesh, obj, mesh_name, name, frame_count, fps, obj_output_dir, jsx_dir, comp_width, comp_height)
                        jsx_lines.extend(geom_jsx)
                        jsx_lines.append("")
                        processed_names.add(name)
                        processed_names.add(mesh_name)
                        # Also mark intermediate nodes as processed
                        for child in obj.children:
                            if IXform.matches(child.getHeader()):
                                processed_names.add(child.getName())
                    else:
                        # Only process IXform as locator if it doesn't have camera/mesh children
                        self.log(f"Processing locator: {name}")
                        loc_jsx = self.process_locator(obj, name, frame_count, fps, comp_width, comp_height)
                        jsx_lines.extend(loc_jsx)
                        jsx_lines.append("")
                        processed_names.add(name)

            # Footer - make comp active and open in viewer
            jsx_lines.append("// Make comp the current open composition")
            jsx_lines.append("comp.selected = true;")
            jsx_lines.append("deselectAll(app.project.items);")
            jsx_lines.append("comp.selected = true;")
            jsx_lines.append("comp.openInViewer();")
            jsx_lines.append("")
            jsx_lines.append("app.endUndoGroup();")
            jsx_lines.append("alert('Scene import complete!');")
            jsx_lines.append("")
            jsx_lines.append("} // End SceneImportFunction")
            jsx_lines.append("")
            jsx_lines.append("SceneImportFunction();")

            # Write JSX file
            with open(jsx_file, 'w') as f:
                f.write("\n".join(jsx_lines))

            self.log(f"\n✓ JSX written to: {jsx_file}")
            self.log(f"✓ Frame count: {frame_count}")
            self.log(f"✓ Duration: {duration}s @ {fps} fps")
            self.log(f"✓ OBJ files exported to: {obj_output_dir}")

            return True

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            raise


class AlembicToJSXGUI:
    """GUI Application"""

    def __init__(self, root):
        self.root = root
        self.root.title("Alembic to After Effects JSX Converter v1.0.0")
        self.root.geometry("650x820")
        self.root.resizable(False, False)

        # Grayscale theme colors
        self.colors = {
            'bg': '#2a2a2a',           # Dark gray background
            'bg_light': '#3a3a3a',     # Slightly lighter gray
            'accent': '#4a4a4a',       # Medium gray accent
            'highlight': '#7a7a7a',    # Light gray highlight
            'text': '#ffffff',         # White text for better visibility
            'text_dim': '#a0a0a0',     # Dimmed gray text
            'entry_bg': '#1a1a1a',     # Very dark gray entry background
            'entry_text': '#ffffff',   # White text in entries
            'button_bg': '#555555',    # Medium-dark gray button
            'button_hover': '#666666', # Lighter gray on hover
            'button_text': '#ffffff',  # White button text
        }

        # Configure root window
        self.root.configure(bg=self.colors['bg'])

        # Variables
        self.abc_file = tk.StringVar()
        self.jsx_file = tk.StringVar()
        self.fps = tk.IntVar(value=24)
        self.frame_count = tk.IntVar(value=120)  # Default to 120 frames (5 seconds at 24fps)
        self.comp_name = tk.StringVar(value="AlembicScene")

        self.setup_theme()
        self.setup_ui()

    def setup_theme(self):
        """Configure dark theme for ttk widgets"""
        style = ttk.Style()

        # Configure TFrame
        style.configure('Dark.TFrame', background=self.colors['bg'])
        style.configure('Accent.TFrame', background=self.colors['accent'])

        # Configure TLabel
        style.configure('Dark.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 9))
        style.configure('Title.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['highlight'],
                       font=('Segoe UI', 18, 'bold'))
        style.configure('Subtitle.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['text_dim'],
                       font=('Segoe UI', 10))

        # Configure TEntry
        style.configure('Dark.TEntry',
                       fieldbackground=self.colors['entry_bg'],
                       foreground=self.colors['entry_text'],
                       insertcolor=self.colors['entry_text'],
                       borderwidth=1,
                       relief='flat')
        style.map('Dark.TEntry',
                 fieldbackground=[('readonly', self.colors['entry_bg'])],
                 foreground=[('readonly', self.colors['entry_text'])])

        # Configure TButton
        style.configure('Dark.TButton',
                       background=self.colors['accent'],
                       foreground=self.colors['button_text'],
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10))
        style.map('Dark.TButton',
                 background=[('active', self.colors['bg_light'])],
                 foreground=[('active', self.colors['button_text'])])

        # Configure Convert button (larger and highlighted)
        style.configure('Convert.TButton',
                       background=self.colors['button_bg'],
                       foreground=self.colors['button_text'],
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 12, 'bold'),
                       padding=(20, 10))
        style.map('Convert.TButton',
                 background=[('active', self.colors['button_hover'])],
                 foreground=[('active', self.colors['button_text'])])

        # Configure TLabelframe
        style.configure('Dark.TLabelframe',
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       borderwidth=1,
                       relief='solid')
        style.configure('Dark.TLabelframe.Label',
                       background=self.colors['bg'],
                       foreground=self.colors['highlight'],
                       font=('Segoe UI', 10, 'bold'))

        # Configure Progressbar
        style.configure('Dark.Horizontal.TProgressbar',
                       background=self.colors['highlight'],
                       troughcolor=self.colors['accent'],
                       borderwidth=0,
                       thickness=8)

    def setup_ui(self):
        """Create the user interface"""
        # Title
        title = ttk.Label(self.root, text="Alembic to After Effects Converter",
                         style='Title.TLabel')
        title.pack(pady=(25, 5))

        version = ttk.Label(self.root, text="v1.0.0",
                           style='Subtitle.TLabel')
        version.pack(pady=(0, 5))

        subtitle = ttk.Label(self.root, text="Convert .abc files to .jsx for After Effects 2025",
                            style='Subtitle.TLabel')
        subtitle.pack(pady=(0, 15))

        # Main frame
        main_frame = ttk.Frame(self.root, padding="20", style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=False)

        # Input file
        ttk.Label(main_frame, text="Input Alembic File (.abc):", style='Dark.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        abc_entry = tk.Entry(main_frame, textvariable=self.abc_file, width=45,
                            bg=self.colors['entry_bg'], fg=self.colors['entry_text'],
                            insertbackground=self.colors['entry_text'], relief='flat', borderwidth=2)
        abc_entry.grid(row=1, column=0, pady=5, ipady=3)
        browse_abc_btn = tk.Button(main_frame, text="Browse...", command=self.browse_abc,
                                   bg=self.colors['accent'], fg=self.colors['button_text'],
                                   activebackground=self.colors['bg_light'], activeforeground=self.colors['button_text'],
                                   relief='flat', borderwidth=0, padx=15, pady=5, cursor='hand2')
        browse_abc_btn.grid(row=1, column=1, padx=5)

        # Output file
        ttk.Label(main_frame, text="Output JSX File (.jsx):", style='Dark.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        jsx_entry = tk.Entry(main_frame, textvariable=self.jsx_file, width=45,
                            bg=self.colors['entry_bg'], fg=self.colors['entry_text'],
                            insertbackground=self.colors['entry_text'], relief='flat', borderwidth=2)
        jsx_entry.grid(row=3, column=0, pady=5, ipady=3)
        browse_jsx_btn = tk.Button(main_frame, text="Browse...", command=self.browse_jsx,
                                   bg=self.colors['accent'], fg=self.colors['button_text'],
                                   activebackground=self.colors['bg_light'], activeforeground=self.colors['button_text'],
                                   relief='flat', borderwidth=0, padx=15, pady=5, cursor='hand2')
        browse_jsx_btn.grid(row=3, column=1, padx=5)

        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Composition Settings", padding="10", style='Dark.TLabelframe')
        settings_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)

        ttk.Label(settings_frame, text="Composition Name:", style='Dark.TLabel').grid(row=0, column=0, sticky=tk.W, pady=3)
        comp_name_entry = tk.Entry(settings_frame, textvariable=self.comp_name, width=30,
                                   bg=self.colors['entry_bg'], fg=self.colors['entry_text'],
                                   insertbackground=self.colors['entry_text'], relief='flat', borderwidth=1)
        comp_name_entry.grid(row=0, column=1, pady=3, padx=5, ipady=2)

        ttk.Label(settings_frame, text="Frame Rate (fps):", style='Dark.TLabel').grid(row=1, column=0, sticky=tk.W, pady=3)
        fps_entry = tk.Entry(settings_frame, textvariable=self.fps, width=15,
                            bg=self.colors['entry_bg'], fg=self.colors['entry_text'],
                            insertbackground=self.colors['entry_text'], relief='flat', borderwidth=1)
        fps_entry.grid(row=1, column=1, sticky=tk.W, pady=3, padx=5, ipady=2)

        ttk.Label(settings_frame, text="Duration (frames):", style='Dark.TLabel').grid(row=2, column=0, sticky=tk.W, pady=3)
        frame_entry = tk.Entry(settings_frame, textvariable=self.frame_count, width=15,
                              bg=self.colors['entry_bg'], fg=self.colors['entry_text'],
                              insertbackground=self.colors['entry_text'], relief='flat', borderwidth=1)
        frame_entry.grid(row=2, column=1, sticky=tk.W, pady=3, padx=5, ipady=2)

        # Note: Width and Height are now auto-extracted from Alembic camera metadata

        # Convert button (larger and prominent)
        self.convert_btn = tk.Button(main_frame, text="⚡ Convert to JSX", command=self.start_conversion,
                                     bg=self.colors['button_bg'], fg=self.colors['button_text'],
                                     activebackground=self.colors['button_hover'], activeforeground=self.colors['button_text'],
                                     relief='flat', borderwidth=0, padx=30, pady=12,
                                     font=('Segoe UI', 12, 'bold'), cursor='hand2')
        self.convert_btn.grid(row=5, column=0, columnspan=2, pady=20)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', style='Dark.Horizontal.TProgressbar')
        self.progress.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Log text area
        log_frame = ttk.LabelFrame(main_frame, text="Progress Log", padding="5", style='Dark.TLabelframe')
        log_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        self.log_text = tk.Text(log_frame, height=12, width=63, wrap=tk.WORD,
                                bg=self.colors['entry_bg'],
                                fg=self.colors['entry_text'],
                                insertbackground=self.colors['entry_text'],
                                font=('Consolas', 9),
                                relief='flat',
                                borderwidth=0)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def browse_abc(self):
        """Browse for input Alembic file"""
        filename = filedialog.askopenfilename(
            title="Select Alembic File",
            filetypes=[("Alembic Files", "*.abc"), ("All Files", "*.*")]
        )
        if filename:
            self.abc_file.set(filename)
            # Auto-suggest output filename
            if not self.jsx_file.get():
                jsx_path = Path(filename).with_suffix('.jsx')
                self.jsx_file.set(str(jsx_path))
            # Auto-set composition name to ABC filename (without extension)
            abc_name = Path(filename).stem
            self.comp_name.set(abc_name)
            # Auto-detect frame count from ABC file
            try:
                converter = AlembicToJSXConverter()
                detected_frames = converter.detect_frame_count(filename, self.fps.get())
                self.frame_count.set(detected_frames)
                self.log(f"Detected {detected_frames} frames from Alembic file")
            except Exception as e:
                self.log(f"Could not auto-detect frame count: {e}")

    def browse_jsx(self):
        """Browse for output JSX file"""
        filename = filedialog.asksaveasfilename(
            title="Save JSX File As",
            defaultextension=".jsx",
            filetypes=[("JSX Files", "*.jsx"), ("All Files", "*.*")]
        )
        if filename:
            self.jsx_file.set(filename)

    def log(self, message):
        """Add message to log text area"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_conversion(self):
        """Start the conversion process in a separate thread"""
        # Validate inputs
        if not self.abc_file.get():
            messagebox.showerror("Error", "Please select an input Alembic file")
            return

        if not self.jsx_file.get():
            messagebox.showerror("Error", "Please specify an output JSX file")
            return

        if not Path(self.abc_file.get()).exists():
            messagebox.showerror("Error", "Input file does not exist")
            return

        # Clear log
        self.log_text.delete(1.0, tk.END)

        # Disable button and start progress
        self.convert_btn.config(state='disabled', bg=self.colors['accent'])
        self.progress.start()

        # Run conversion in separate thread
        thread = threading.Thread(target=self.run_conversion)
        thread.daemon = True
        thread.start()

    def run_conversion(self):
        """Run the actual conversion"""
        try:
            converter = AlembicToJSXConverter(progress_callback=self.log)

            success = converter.convert(
                abc_file=self.abc_file.get(),
                jsx_file=self.jsx_file.get(),
                fps=self.fps.get(),
                frame_count=self.frame_count.get(),
                comp_name=self.comp_name.get()
            )

            if success:
                jsx_dir = Path(self.jsx_file.get()).parent
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success",
                    f"Conversion complete!\n\n"
                    f"JSX file: {self.jsx_file.get()}\n"
                    f"OBJ files: {jsx_dir}\n\n"
                    "Import in After Effects:\nFile > Scripts > Run Script File"
                ))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Conversion failed:\n{str(e)}"))

        finally:
            self.root.after(0, self.conversion_complete)

    def conversion_complete(self):
        """Re-enable UI after conversion"""
        self.progress.stop()
        self.convert_btn.config(state='normal', bg=self.colors['button_bg'])


def main():
    root = tk.Tk()
    app = AlembicToJSXGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
