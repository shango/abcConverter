#!/usr/bin/env python3
"""
USD Exporter Module
Exports Alembic data to USD (.usdc binary format) with vertex animation support
"""

from pathlib import Path

from alembic.Abc import WrapExistingFlag
from alembic.AbcGeom import IXform, ICamera, IPolyMesh

from .base_exporter import BaseExporter


class USDExporter(BaseExporter):
    """USD exporter with full animation support

    Exports to USD (.usdc binary "crate" format) with:
    - Animated cameras (transform + focal length)
    - Meshes with transform-only animation
    - Meshes with vertex animation (time-sampled point positions)

    USD uses Y-up coordinate system (same as Alembic), so no conversion needed!
    """

    def __init__(self, progress_callback=None):
        super().__init__(progress_callback)

        # Lazy import USD - only import when actually creating exporter instance
        # This avoids module-level import issues
        try:
            from pxr import Usd, UsdGeom, Gf, Vt, Sdf
            # Store in instance for use throughout the class
            self.Usd = Usd
            self.UsdGeom = UsdGeom
            self.Gf = Gf
            self.Vt = Vt
            self.Sdf = Sdf
        except ImportError as e:
            raise ImportError(
                f"USD Python library (pxr) not found: {e}\n"
                "Install with: brew install usd-python (macOS) or download from NVIDIA (Windows)"
            )

    def get_format_name(self):
        return "USD"

    def get_file_extension(self):
        return "usdc"

    def export(self, reader, output_path, shot_name, fps, frame_count, animation_data):
        """Export to USD format

        Args:
            reader: AlembicReader instance
            output_path: Output directory path
            shot_name: Shot name for file naming
            fps: Frames per second
            frame_count: Total number of frames
            animation_data: Animation analysis with keys 'vertex_animated', 'transform_only', 'static'

        Returns:
            dict: Export results with keys:
                - 'success': bool
                - 'usd_file': Path to created USD file
                - 'vertex_animated_count': Number of meshes with vertex animation
                - 'message': Status message
        """
        try:
            output_dir = self.validate_output_path(output_path)
            usd_file = output_dir / f"{shot_name}.usdc"

            self.log(f"Creating USD stage: {usd_file}")

            # Create USD stage (.usdc = binary crate format)
            stage = self.Usd.Stage.CreateNew(str(usd_file))

            # Set stage metadata
            stage.SetStartTimeCode(1)
            stage.SetEndTimeCode(frame_count)
            stage.SetTimeCodesPerSecond(fps)
            stage.SetFramesPerSecond(fps)

            # Set Y-up axis (same as Alembic!)
            self.UsdGeom.SetStageUpAxis(stage, self.UsdGeom.Tokens.y)

            self.log(f"Stage setup: {frame_count} frames @ {fps} fps, Y-up axis")

            # Build parent map
            parent_map = reader.get_parent_map()
            objects = reader.get_all_objects()

            # Track processed objects
            processed_names = set()

            # Create root transform
            root_xform = self.UsdGeom.Xform.Define(stage, "/World")

            # Process cameras
            cameras = reader.get_cameras()
            for cam_obj in cameras:
                cam_name = cam_obj.getName()
                if cam_name in processed_names:
                    continue

                parent = parent_map.get(cam_name)
                if parent and IXform.matches(parent.getHeader()):
                    parent_name = parent.getName()
                    transform_obj = parent
                else:
                    parent_name = cam_name
                    transform_obj = cam_obj

                self.log(f"Exporting camera: {parent_name}")
                self._export_camera(stage, reader, cam_obj, transform_obj, parent_name, frame_count, fps)
                processed_names.add(cam_name)
                if parent_name != cam_name:
                    processed_names.add(parent_name)

            # Process meshes
            vertex_animated_meshes = set(animation_data['vertex_animated'])

            for mesh_obj in reader.get_meshes():
                mesh_name = mesh_obj.getName()
                if mesh_name in processed_names:
                    continue

                parent = parent_map.get(mesh_name)
                if parent and IXform.matches(parent.getHeader()):
                    parent_name = parent.getName()
                    transform_obj = parent
                else:
                    parent_name = mesh_name
                    transform_obj = mesh_obj

                # Check if mesh has vertex animation
                has_vertex_anim = mesh_name in vertex_animated_meshes

                if has_vertex_anim:
                    self.log(f"Exporting mesh with vertex animation: {parent_name}")
                    self._export_mesh_with_vertex_anim(stage, reader, mesh_obj, transform_obj,
                                                       parent_name, frame_count, fps)
                else:
                    self.log(f"Exporting mesh (transform only): {parent_name}")
                    self._export_mesh_transform_only(stage, reader, mesh_obj, transform_obj,
                                                     parent_name, frame_count, fps)

                processed_names.add(mesh_name)
                if parent_name != mesh_name:
                    processed_names.add(parent_name)

            # Save stage
            stage.Save()
            self.log(f"\n✓ USD file saved: {usd_file}")
            self.log(f"✓ Exported {len(cameras)} cameras, {len(reader.get_meshes())} meshes")
            self.log(f"✓ Vertex-animated meshes: {len(vertex_animated_meshes)}")

            return {
                'success': True,
                'usd_file': str(usd_file),
                'vertex_animated_count': len(vertex_animated_meshes),
                'message': f"Exported {len(cameras)} cameras, {len(reader.get_meshes())} meshes",
                'files': [str(usd_file)]
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

    def _export_camera(self, stage, reader, cam_obj, transform_obj, name, frame_count, fps):
        """Export animated camera to USD

        Args:
            stage: USD stage
            reader: AlembicReader instance
            cam_obj: ICamera object
            transform_obj: Transform parent object
            name: Camera name
            frame_count: Total frames
            fps: Frames per second
        """
        # Create camera prim path
        cam_path = f"/World/{self._sanitize_name(name)}"

        # Define camera
        usd_camera = self.UsdGeom.Camera.Define(stage, cam_path)

        # Get camera properties (first frame)
        cam_props = reader.get_camera_properties(cam_obj, time_seconds=1.0/fps)
        focal_length = cam_props['focal_length']
        h_aperture = cam_props['h_aperture'] * 10  # cm to mm
        v_aperture = cam_props['v_aperture'] * 10  # cm to mm

        # Set camera properties
        usd_camera.GetFocalLengthAttr().Set(focal_length)
        usd_camera.GetHorizontalApertureAttr().Set(h_aperture)
        usd_camera.GetVerticalApertureAttr().Set(v_aperture)

        # Animate camera transform
        xformable = self.UsdGeom.Xformable(usd_camera)

        # Create transform ops (order: translate, rotate, scale)
        translate_op = xformable.AddTranslateOp()
        rotateX_op = xformable.AddRotateXOp()
        rotateY_op = xformable.AddRotateYOp()
        rotateZ_op = xformable.AddRotateZOp()
        scale_op = xformable.AddScaleOp()

        # Sample each frame
        for frame in range(1, frame_count + 1):
            time_seconds = frame / fps
            pos, rot, scale = reader.get_transform_at_time(transform_obj, time_seconds)

            # USD uses same Y-up coordinate system as Alembic - direct copy!
            translate_op.Set(self.Gf.Vec3d(pos[0], pos[1], pos[2]), time=frame)
            rotateX_op.Set(rot[0], time=frame)
            rotateY_op.Set(rot[1], time=frame)
            rotateZ_op.Set(rot[2], time=frame)
            scale_op.Set(self.Gf.Vec3f(scale[0], scale[1], scale[2]), time=frame)

    def _export_mesh_transform_only(self, stage, reader, mesh_obj, transform_obj, name, frame_count, fps):
        """Export mesh with static geometry and animated transform

        Args:
            stage: USD stage
            reader: AlembicReader instance
            mesh_obj: IPolyMesh object
            transform_obj: Transform parent object
            name: Mesh name
            frame_count: Total frames
            fps: Frames per second
        """
        # Create mesh prim path
        mesh_path = f"/World/{self._sanitize_name(name)}"

        # Define mesh
        usd_mesh = self.UsdGeom.Mesh.Define(stage, mesh_path)

        # Get mesh data (first frame only - static topology)
        mesh_data = reader.get_mesh_data_at_time(mesh_obj, time_seconds=1.0/fps)

        # Set static topology
        # Convert positions to USD format
        points = self.Vt.Vec3fArray([self.Gf.Vec3f(p[0], p[1], p[2]) for p in mesh_data['positions']])
        usd_mesh.GetPointsAttr().Set(points)

        # Set face vertex indices
        indices = self.Vt.IntArray([int(i) for i in mesh_data['indices']])
        usd_mesh.GetFaceVertexIndicesAttr().Set(indices)

        # Set face vertex counts
        counts = self.Vt.IntArray([int(c) for c in mesh_data['counts']])
        usd_mesh.GetFaceVertexCountsAttr().Set(counts)

        # Animate transform
        xformable = self.UsdGeom.Xformable(usd_mesh)

        # Create transform ops
        translate_op = xformable.AddTranslateOp()
        rotateX_op = xformable.AddRotateXOp()
        rotateY_op = xformable.AddRotateYOp()
        rotateZ_op = xformable.AddRotateZOp()
        scale_op = xformable.AddScaleOp()

        # Sample each frame
        for frame in range(1, frame_count + 1):
            time_seconds = frame / fps
            pos, rot, scale = reader.get_transform_at_time(transform_obj, time_seconds)

            # Y-up coordinate system - direct copy from Alembic
            translate_op.Set(self.Gf.Vec3d(pos[0], pos[1], pos[2]), time=frame)
            rotateX_op.Set(rot[0], time=frame)
            rotateY_op.Set(rot[1], time=frame)
            rotateZ_op.Set(rot[2], time=frame)
            scale_op.Set(self.Gf.Vec3f(scale[0], scale[1], scale[2]), time=frame)

    def _export_mesh_with_vertex_anim(self, stage, reader, mesh_obj, transform_obj, name, frame_count, fps):
        """Export mesh with vertex animation (time-sampled point positions)

        Args:
            stage: USD stage
            reader: AlembicReader instance
            mesh_obj: IPolyMesh object
            transform_obj: Transform parent object
            name: Mesh name
            frame_count: Total frames
            fps: Frames per second
        """
        # Create mesh prim path
        mesh_path = f"/World/{self._sanitize_name(name)}"

        # Define mesh
        usd_mesh = self.UsdGeom.Mesh.Define(stage, mesh_path)

        # Get mesh data for first frame (topology)
        mesh_data_frame1 = reader.get_mesh_data_at_time(mesh_obj, time_seconds=1.0/fps)

        # Set static topology (indices and counts don't change)
        indices = self.Vt.IntArray([int(i) for i in mesh_data_frame1['indices']])
        usd_mesh.GetFaceVertexIndicesAttr().Set(indices)

        counts = self.Vt.IntArray([int(c) for c in mesh_data_frame1['counts']])
        usd_mesh.GetFaceVertexCountsAttr().Set(counts)

        # Get points attribute for time-sampled animation
        points_attr = usd_mesh.GetPointsAttr()

        # Sample vertex positions for each frame
        for frame in range(1, frame_count + 1):
            time_seconds = frame / fps
            mesh_data = reader.get_mesh_data_at_time(mesh_obj, time_seconds)

            # Convert positions to USD format
            points = self.Vt.Vec3fArray([self.Gf.Vec3f(p[0], p[1], p[2]) for p in mesh_data['positions']])

            # Set time-sampled point positions
            points_attr.Set(points, time=frame)

        # Animate transform (if transform is also animated)
        xformable = self.UsdGeom.Xformable(usd_mesh)

        # Create transform ops
        translate_op = xformable.AddTranslateOp()
        rotateX_op = xformable.AddRotateXOp()
        rotateY_op = xformable.AddRotateYOp()
        rotateZ_op = xformable.AddRotateZOp()
        scale_op = xformable.AddScaleOp()

        # Sample each frame
        for frame in range(1, frame_count + 1):
            time_seconds = frame / fps
            pos, rot, scale = reader.get_transform_at_time(transform_obj, time_seconds)

            # Y-up coordinate system - direct copy from Alembic
            translate_op.Set(self.Gf.Vec3d(pos[0], pos[1], pos[2]), time=frame)
            rotateX_op.Set(rot[0], time=frame)
            rotateY_op.Set(rot[1], time=frame)
            rotateZ_op.Set(rot[2], time=frame)
            scale_op.Set(self.Gf.Vec3f(scale[0], scale[1], scale[2]), time=frame)

    def _sanitize_name(self, name):
        """Sanitize name for USD prim path

        Args:
            name: Original name

        Returns:
            str: Sanitized name safe for USD paths
        """
        # Replace spaces and special characters
        sanitized = name.replace(' ', '_').replace('-', '_')
        # Remove other problematic characters
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '_')
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = 'mesh_' + sanitized
        return sanitized or 'mesh'
