#!/usr/bin/env python3
"""
Alembic Reader Module
Centralized Alembic reading utilities shared across all exporters
"""

import numpy as np
from pathlib import Path

# Import Alembic libraries
from alembic.Abc import IArchive, ISampleSelector, WrapExistingFlag
from alembic.AbcGeom import IXform, ICamera, IPolyMesh
import imath


class AlembicReader:
    """Centralized Alembic file reading and data extraction

    This class handles all Alembic file I/O operations and provides a clean
    interface for exporters to access scene data without duplicating code.

    Key principle: Read the Alembic file ONCE, then share data across all exporters.
    """

    def __init__(self, abc_file):
        """Open Alembic archive and initialize

        Args:
            abc_file: Path to Alembic (.abc) file
        """
        self.abc_file = Path(abc_file)
        self.archive = IArchive(str(abc_file))
        self.top = self.archive.getTop()
        self._objects_cache = None
        self._parent_map_cache = None

    def get_archive(self):
        """Get the Alembic IArchive object"""
        return self.archive

    def get_top(self):
        """Get the top-level Alembic object"""
        return self.top

    def get_all_objects(self):
        """Get all objects in the Alembic hierarchy (cached)

        Returns:
            list: All Alembic objects in the scene
        """
        if self._objects_cache is None:
            self._objects_cache = []
            self._collect_objects_recursive(self.top, self._objects_cache)
        return self._objects_cache

    def _collect_objects_recursive(self, obj, objects_list):
        """Recursively collect all objects in hierarchy"""
        objects_list.append(obj)
        for child in obj.children:
            self._collect_objects_recursive(child, objects_list)

    def get_cameras(self):
        """Get all camera objects in the scene

        Returns:
            list: ICamera objects
        """
        cameras = []
        for obj in self.get_all_objects():
            if ICamera.matches(obj.getHeader()):
                cameras.append(obj)
        return cameras

    def get_meshes(self):
        """Get all mesh objects in the scene

        Returns:
            list: IPolyMesh objects
        """
        meshes = []
        for obj in self.get_all_objects():
            if IPolyMesh.matches(obj.getHeader()):
                meshes.append(obj)
        return meshes

    def get_transforms(self):
        """Get all transform objects in the scene

        Returns:
            list: IXform objects
        """
        transforms = []
        for obj in self.get_all_objects():
            if IXform.matches(obj.getHeader()):
                transforms.append(obj)
        return transforms

    def get_parent_map(self):
        """Build parent-child relationship map (cached)

        Returns:
            dict: Mapping of child name -> parent object
        """
        if self._parent_map_cache is None:
            self._parent_map_cache = {}
            for obj in self.get_all_objects():
                for child in obj.children:
                    self._parent_map_cache[child.getName()] = obj
        return self._parent_map_cache

    def detect_frame_count(self, fps=24):
        """Auto-detect frame count from Alembic time sampling

        Args:
            fps: Frames per second (used for fallback calculation)

        Returns:
            int: Number of frames in the animation
        """
        try:
            # Get time sampling
            num_time_samplings = self.archive.getNumTimeSamplings()
            if num_time_samplings > 1:
                # Use the first non-uniform time sampling (index 1)
                time_sampling = self.archive.getTimeSampling(1)
                num_samples = self.archive.getMaxNumSamplesForTimeSamplingIndex(1)

                if num_samples > 0:
                    return num_samples

            # Fallback: assume 120 frames if we can't detect
            return 120
        except Exception:
            return 120

    def get_transform_at_time(self, obj, time_seconds):
        """Get transform data (position, rotation, scale) at a specific time

        This extracts scale from the LOCAL transform matrix, then gets world position/rotation.
        SynthEyes stores per-object scale in the local matrix.

        Args:
            obj: Alembic object (should be IXform or have parent IXform)
            time_seconds: Time in seconds to sample

        Returns:
            tuple: (translation, rotation, scale) where:
                - translation: [x, y, z] in Alembic units (cm)
                - rotation: [rx, ry, rz] in degrees (XYZ Euler)
                - scale: [sx, sy, sz] as multipliers (NOT multiplied by 100)
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
        pos, rot, world_scale = self._decompose_matrix(world_matrix)

        # Use local scale (from the object's own matrix), not world scale
        # This prevents parent scales from affecting the object's scale
        final_scale = local_scale if local_scale is not None else world_scale

        return pos, rot, final_scale

    def get_mesh_data_at_time(self, mesh_obj, time_seconds):
        """Get mesh geometry data at a specific time

        Args:
            mesh_obj: IPolyMesh object
            time_seconds: Time in seconds to sample

        Returns:
            dict: Mesh data with keys:
                - 'positions': Vertex positions as list of [x, y, z]
                - 'indices': Face vertex indices
                - 'counts': Face vertex counts
        """
        poly = IPolyMesh(mesh_obj, WrapExistingFlag.kWrapExisting)
        schema = poly.getSchema()

        sample_sel = ISampleSelector(time_seconds)
        sample = schema.getValue(sample_sel)

        positions = sample.getPositions()
        indices = sample.getFaceIndices()
        counts = sample.getFaceCounts()

        return {
            'positions': positions,
            'indices': indices,
            'counts': counts
        }

    def get_camera_properties(self, cam_obj, time_seconds=None):
        """Get camera properties at a specific time

        Args:
            cam_obj: ICamera object
            time_seconds: Time in seconds (None for first sample)

        Returns:
            dict: Camera properties with keys:
                - 'focal_length': Focal length in mm
                - 'h_aperture': Horizontal aperture in cm
                - 'v_aperture': Vertical aperture in cm
        """
        camera = ICamera(cam_obj, WrapExistingFlag.kWrapExisting)
        schema = camera.getSchema()

        if time_seconds is not None:
            sample_sel = ISampleSelector(time_seconds)
            sample = schema.getValue(sample_sel)
        else:
            sample = schema.getValue()

        return {
            'focal_length': sample.getFocalLength(),
            'h_aperture': sample.getHorizontalAperture(),
            'v_aperture': sample.getVerticalAperture()
        }

    def extract_footage_path(self):
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

            camera_obj = find_camera(self.top)
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
                                    val = prop.getValue()
                                    if val and isinstance(val, str):
                                        return val
                        except:
                            pass

                # Check user properties
                if schema.getUserProperties():
                    user_props = schema.getUserProperties()
                    for prop_name in ['footagePath', 'footage', 'sourceFile', 'imagePath',
                                     'videoFile', 'mediaPath', 'sourceImage', 'backgroundImage']:
                        try:
                            if user_props.getPropertyHeader(prop_name):
                                prop = user_props.getProperty(prop_name)
                                if prop.valid():
                                    val = prop.getValue()
                                    if val and isinstance(val, str):
                                        return val
                        except:
                            pass

        except Exception:
            pass

        return None

    def extract_render_resolution(self):
        """Extract render resolution from Alembic camera metadata

        Returns:
            tuple: (width, height) in pixels, or (1920, 1080) as fallback
        """
        try:
            # Search for camera to extract resolution
            def find_camera(obj):
                if ICamera.matches(obj.getHeader()):
                    return obj
                for child in obj.children:
                    cam = find_camera(child)
                    if cam:
                        return cam
                return None

            camera_obj = find_camera(self.top)
            if camera_obj:
                camera = ICamera(camera_obj, WrapExistingFlag.kWrapExisting)
                schema = camera.getSchema()
                cam_sample = schema.getValue()

                # Get aperture (film back dimensions)
                h_aperture_cm = cam_sample.getHorizontalAperture()
                v_aperture_cm = cam_sample.getVerticalAperture()

                # Use standard HD resolution as default
                return (1920, 1080)

        except Exception:
            pass

        # Fallback to HD resolution
        return (1920, 1080)

    def _decompose_matrix(self, matrix):
        """Decompose a 4x4 matrix into translation, rotation (XYZ Euler), and scale

        Args:
            matrix: 4x4 transformation matrix

        Returns:
            tuple: (translation, rotation, scale) where:
                - translation: [x, y, z]
                - rotation: [rx, ry, rz] in degrees
                - scale: [sx, sy, sz]
        """
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
