#!/usr/bin/env python3
"""
USD Exporter Module
Exports SceneData to USD (.usdc binary format) with vertex animation support

v2.5.0 - Refactored to use SceneData instead of reader objects.
         Now format-agnostic - works with any input format.
"""

from pathlib import Path

from .base_exporter import BaseExporter
from core.scene_data import SceneData, AnimationType


class USDExporter(BaseExporter):
    """USD exporter with full animation support

    Exports to USD (.usdc binary "crate" format) with:
    - Animated cameras (transform + focal length)
    - Meshes with transform-only animation
    - Meshes with vertex animation (time-sampled point positions)

    USD uses Y-up coordinate system (same as Alembic), so no conversion needed!

    v2.5.0: Now works with SceneData instead of reader objects - format-agnostic.
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
                "Install with: pip install usd-core or download from NVIDIA (https://developer.nvidia.com/usd)"
            )

    def get_format_name(self):
        return "USD"

    def get_file_extension(self):
        return "usdc"

    def export(self, scene_data: SceneData, output_path, shot_name):
        """Export to USD format

        Args:
            scene_data: SceneData instance with pre-extracted animation and geometry
            output_path: Output directory path
            shot_name: Shot name for file naming

        Returns:
            dict: Export results with keys:
                - 'success': bool
                - 'usd_file': Path to created USD file
                - 'vertex_animated_count': Number of meshes with vertex animation
                - 'message': Status message
        """
        try:
            # Extract info from SceneData
            fps = scene_data.metadata.fps
            frame_count = scene_data.metadata.frame_count

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

            # Create root transform
            root_xform = self.UsdGeom.Xform.Define(stage, "/World")

            # Process cameras
            for camera in scene_data.cameras:
                cam_name = camera.parent_name if camera.parent_name else camera.name
                self.log(f"Exporting camera: {cam_name}")
                self._export_camera(stage, camera, cam_name, frame_count)

            # Track used names to avoid conflicts
            used_names = set()

            # Process meshes
            vertex_animated_count = 0
            for mesh in scene_data.meshes:
                mesh_name = mesh.parent_name if mesh.parent_name else mesh.name
                used_names.add(self._sanitize_name(mesh_name))

                if mesh.animation_type == AnimationType.VERTEX_ANIMATED:
                    self.log(f"Exporting mesh with vertex animation: {mesh_name}")
                    self._export_mesh_with_vertex_anim(stage, mesh, mesh_name, frame_count)
                    vertex_animated_count += 1
                else:
                    self.log(f"Exporting mesh (transform only): {mesh_name}")
                    self._export_mesh_transform_only(stage, mesh, mesh_name, frame_count)

            # Also track camera names
            for camera in scene_data.cameras:
                cam_name = camera.parent_name if camera.parent_name else camera.name
                used_names.add(self._sanitize_name(cam_name))

            # Process transforms (locators/trackers) - skip if name conflicts
            # NOTE: Unlike cameras/meshes, locators use their own name (not parent_name)
            # because parent_name for locators is the organizational group (e.g. "trackers")
            locator_count = 0
            for transform in scene_data.transforms:
                xform_name = transform.name  # Always use locator's own name
                sanitized = self._sanitize_name(xform_name)

                # Skip if name conflicts with existing camera/mesh
                if sanitized in used_names:
                    self.log(f"Skipping locator (name conflict): {xform_name}")
                    continue

                # Skip if no keyframes
                if not transform.keyframes:
                    self.log(f"Skipping locator (no keyframes): {xform_name}")
                    continue

                try:
                    self.log(f"Exporting locator: {xform_name}")
                    self._export_locator(stage, transform, xform_name, frame_count)
                    used_names.add(sanitized)
                    locator_count += 1
                except Exception as e:
                    self.log(f"Warning: Failed to export locator {xform_name}: {e}")

            # Save stage
            stage.Save()
            self.log(f"\n✓ USD file saved: {usd_file}")
            self.log(f"✓ Exported {len(scene_data.cameras)} cameras, {len(scene_data.meshes)} meshes, {locator_count} locators")
            self.log(f"✓ Vertex-animated meshes: {vertex_animated_count}")

            return {
                'success': True,
                'usd_file': str(usd_file),
                'vertex_animated_count': vertex_animated_count,
                'message': f"Exported {len(scene_data.cameras)} cameras, {len(scene_data.meshes)} meshes",
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

    def _export_camera(self, stage, camera, name, frame_count):
        """Export animated camera to USD

        Args:
            stage: USD stage
            camera: CameraData instance from SceneData
            name: Camera name for USD path
            frame_count: Total frames
        """
        # Create camera prim path
        cam_path = f"/World/{self._sanitize_name(name)}"

        # Define camera
        usd_camera = self.UsdGeom.Camera.Define(stage, cam_path)

        # Set camera properties from CameraData.properties
        focal_length = camera.properties.focal_length
        h_aperture = camera.properties.h_aperture * 10  # cm to mm
        v_aperture = camera.properties.v_aperture * 10  # cm to mm

        usd_camera.GetFocalLengthAttr().Set(focal_length)
        usd_camera.GetHorizontalApertureAttr().Set(h_aperture)
        usd_camera.GetVerticalApertureAttr().Set(v_aperture)

        # Animate camera transform
        xformable = self.UsdGeom.Xformable(usd_camera)

        # Create transform ops with EXPLICIT precision for Maya compatibility
        translate_op = xformable.AddTranslateOp(self.UsdGeom.XformOp.PrecisionDouble)
        rotate_op = xformable.AddRotateXYZOp(self.UsdGeom.XformOp.PrecisionFloat)
        scale_op = xformable.AddScaleOp(self.UsdGeom.XformOp.PrecisionFloat)

        # Set default values FIRST to establish attributes (required for animation)
        if camera.keyframes:
            kf = camera.keyframes[0]
            translate_op.Set(self.Gf.Vec3d(kf.position[0], kf.position[1], kf.position[2]))
            rotate_op.Set(self.Gf.Vec3f(kf.rotation_maya[0], kf.rotation_maya[1], kf.rotation_maya[2]))
            scale_op.Set(self.Gf.Vec3f(kf.scale[0], kf.scale[1], kf.scale[2]))

            # Log first frame values for debugging
            self.log(f"  Camera {name} frame 1: pos={kf.position}, rot={kf.rotation_maya}")

        # THEN set time-sampled animation from pre-extracted keyframes
        first_kf, last_kf = None, None
        for kf in camera.keyframes:
            if kf.frame == 1:
                first_kf = kf
            if kf.frame == frame_count:
                last_kf = kf

            # USD uses same Y-up coordinate system - direct copy!
            # Use float for time code (matches USD convention)
            translate_op.Set(self.Gf.Vec3d(kf.position[0], kf.position[1], kf.position[2]), time=float(kf.frame))
            rotate_op.Set(self.Gf.Vec3f(kf.rotation_maya[0], kf.rotation_maya[1], kf.rotation_maya[2]), time=float(kf.frame))
            scale_op.Set(self.Gf.Vec3f(kf.scale[0], kf.scale[1], kf.scale[2]), time=float(kf.frame))

        # Log animation range to verify data changes
        if first_kf and last_kf:
            self.log(f"  Camera {name} animation check:")
            self.log(f"    Frame 1: pos={first_kf.position}, rot={first_kf.rotation_maya}")
            self.log(f"    Frame {frame_count}: pos={last_kf.position}, rot={last_kf.rotation_maya}")
            pos_changed = first_kf.position != last_kf.position
            rot_changed = first_kf.rotation_maya != last_kf.rotation_maya
            self.log(f"    Position animated: {pos_changed}, Rotation animated: {rot_changed}")

    def _export_mesh_transform_only(self, stage, mesh, name, frame_count):
        """Export mesh with static geometry and animated transform

        Args:
            stage: USD stage
            mesh: MeshData instance from SceneData
            name: Mesh name for USD path
            frame_count: Total frames
        """
        # Create mesh prim path
        mesh_path = f"/World/{self._sanitize_name(name)}"

        # Define mesh
        usd_mesh = self.UsdGeom.Mesh.Define(stage, mesh_path)

        # Set orientation to handle winding order difference from Alembic
        usd_mesh.GetOrientationAttr().Set("leftHanded")

        # Get mesh data from pre-extracted geometry
        geometry = mesh.geometry

        # Set static topology
        # Convert positions to USD format
        points = self.Vt.Vec3fArray([self.Gf.Vec3f(p[0], p[1], p[2]) for p in geometry.positions])
        usd_mesh.GetPointsAttr().Set(points)

        # Set face vertex indices
        indices = self.Vt.IntArray([int(i) for i in geometry.indices])
        usd_mesh.GetFaceVertexIndicesAttr().Set(indices)

        # Set face vertex counts
        counts = self.Vt.IntArray([int(c) for c in geometry.counts])
        usd_mesh.GetFaceVertexCountsAttr().Set(counts)

        # Animate transform
        xformable = self.UsdGeom.Xformable(usd_mesh)

        # Create transform ops with EXPLICIT precision for Maya compatibility
        translate_op = xformable.AddTranslateOp(self.UsdGeom.XformOp.PrecisionDouble)
        rotate_op = xformable.AddRotateXYZOp(self.UsdGeom.XformOp.PrecisionFloat)
        scale_op = xformable.AddScaleOp(self.UsdGeom.XformOp.PrecisionFloat)

        # Set default values FIRST to establish attributes (required for animation)
        if mesh.keyframes:
            kf = mesh.keyframes[0]
            translate_op.Set(self.Gf.Vec3d(kf.position[0], kf.position[1], kf.position[2]))
            rotate_op.Set(self.Gf.Vec3f(kf.rotation_maya[0], kf.rotation_maya[1], kf.rotation_maya[2]))
            scale_op.Set(self.Gf.Vec3f(kf.scale[0], kf.scale[1], kf.scale[2]))

        # THEN set time-sampled animation from pre-extracted keyframes
        for kf in mesh.keyframes:
            # Y-up coordinate system - direct copy from source
            # Use float for time code (matches USD convention)
            translate_op.Set(self.Gf.Vec3d(kf.position[0], kf.position[1], kf.position[2]), time=float(kf.frame))
            rotate_op.Set(self.Gf.Vec3f(kf.rotation_maya[0], kf.rotation_maya[1], kf.rotation_maya[2]), time=float(kf.frame))
            scale_op.Set(self.Gf.Vec3f(kf.scale[0], kf.scale[1], kf.scale[2]), time=float(kf.frame))

    def _export_mesh_with_vertex_anim(self, stage, mesh, name, frame_count):
        """Export mesh with vertex animation (time-sampled point positions)

        Args:
            stage: USD stage
            mesh: MeshData instance from SceneData
            name: Mesh name for USD path
            frame_count: Total frames
        """
        # Create mesh prim path
        mesh_path = f"/World/{self._sanitize_name(name)}"

        # Define mesh
        usd_mesh = self.UsdGeom.Mesh.Define(stage, mesh_path)

        # Set orientation to handle winding order difference from Alembic
        usd_mesh.GetOrientationAttr().Set("leftHanded")

        # Get static topology from pre-extracted geometry
        geometry = mesh.geometry

        # Set static topology (indices and counts don't change)
        indices = self.Vt.IntArray([int(i) for i in geometry.indices])
        usd_mesh.GetFaceVertexIndicesAttr().Set(indices)

        counts = self.Vt.IntArray([int(c) for c in geometry.counts])
        usd_mesh.GetFaceVertexCountsAttr().Set(counts)

        # Get points attribute for time-sampled animation
        points_attr = usd_mesh.GetPointsAttr()

        # Sample vertex positions from pre-extracted per-frame data
        if mesh.vertex_positions_per_frame:
            for frame, positions in mesh.vertex_positions_per_frame.items():
                # Convert positions to USD format
                points = self.Vt.Vec3fArray([self.Gf.Vec3f(p[0], p[1], p[2]) for p in positions])

                # Set time-sampled point positions (use float for time code)
                points_attr.Set(points, time=float(frame))
        else:
            # Fallback to static geometry if vertex_positions_per_frame not available
            points = self.Vt.Vec3fArray([self.Gf.Vec3f(p[0], p[1], p[2]) for p in geometry.positions])
            points_attr.Set(points)

        # Animate transform (if transform is also animated)
        xformable = self.UsdGeom.Xformable(usd_mesh)

        # Create transform ops with EXPLICIT precision for Maya compatibility
        translate_op = xformable.AddTranslateOp(self.UsdGeom.XformOp.PrecisionDouble)
        rotate_op = xformable.AddRotateXYZOp(self.UsdGeom.XformOp.PrecisionFloat)
        scale_op = xformable.AddScaleOp(self.UsdGeom.XformOp.PrecisionFloat)

        # Set default values FIRST to establish attributes (required for animation)
        if mesh.keyframes:
            kf = mesh.keyframes[0]
            translate_op.Set(self.Gf.Vec3d(kf.position[0], kf.position[1], kf.position[2]))
            rotate_op.Set(self.Gf.Vec3f(kf.rotation_maya[0], kf.rotation_maya[1], kf.rotation_maya[2]))
            scale_op.Set(self.Gf.Vec3f(kf.scale[0], kf.scale[1], kf.scale[2]))

        # THEN set time-sampled animation from pre-extracted keyframes
        for kf in mesh.keyframes:
            # Y-up coordinate system - direct copy from source
            # Use float for time code (matches USD convention)
            translate_op.Set(self.Gf.Vec3d(kf.position[0], kf.position[1], kf.position[2]), time=float(kf.frame))
            rotate_op.Set(self.Gf.Vec3f(kf.rotation_maya[0], kf.rotation_maya[1], kf.rotation_maya[2]), time=float(kf.frame))
            scale_op.Set(self.Gf.Vec3f(kf.scale[0], kf.scale[1], kf.scale[2]), time=float(kf.frame))

    def _export_locator(self, stage, transform, name, frame_count):
        """Export animated locator/tracker to USD as Xform with small sphere

        Creates a UsdGeomXform with animated transforms and a tiny UsdGeomSphere
        child for visibility. This ensures locators are visible in Maya and
        other DCC applications.

        Args:
            stage: USD stage
            transform: TransformData instance from SceneData
            name: Locator name for USD path
            frame_count: Total frames
        """
        sanitized_name = self._sanitize_name(name)
        xform_path = f"/World/{sanitized_name}"

        # Define Xform (transform node for animation)
        usd_xform = self.UsdGeom.Xform.Define(stage, xform_path)

        # Add a tiny sphere as visible marker (0.5cm radius)
        sphere_path = f"{xform_path}/{sanitized_name}Shape"
        usd_sphere = self.UsdGeom.Sphere.Define(stage, sphere_path)
        usd_sphere.GetRadiusAttr().Set(0.5)  # Small sphere for locator marker

        # Get xformable for adding transform ops
        xformable = self.UsdGeom.Xformable(usd_xform)

        # Create transform ops with EXPLICIT precision for Maya compatibility
        translate_op = xformable.AddTranslateOp(self.UsdGeom.XformOp.PrecisionDouble)
        rotate_op = xformable.AddRotateXYZOp(self.UsdGeom.XformOp.PrecisionFloat)
        scale_op = xformable.AddScaleOp(self.UsdGeom.XformOp.PrecisionFloat)

        # Set default values FIRST to establish attributes
        if transform.keyframes:
            kf = transform.keyframes[0]
            translate_op.Set(self.Gf.Vec3d(kf.position[0], kf.position[1], kf.position[2]))
            rotate_op.Set(self.Gf.Vec3f(kf.rotation_maya[0], kf.rotation_maya[1], kf.rotation_maya[2]))
            scale_op.Set(self.Gf.Vec3f(kf.scale[0], kf.scale[1], kf.scale[2]))

        # Set time-sampled animation
        for kf in transform.keyframes:
            translate_op.Set(self.Gf.Vec3d(kf.position[0], kf.position[1], kf.position[2]), time=float(kf.frame))
            rotate_op.Set(self.Gf.Vec3f(kf.rotation_maya[0], kf.rotation_maya[1], kf.rotation_maya[2]), time=float(kf.frame))
            scale_op.Set(self.Gf.Vec3f(kf.scale[0], kf.scale[1], kf.scale[2]), time=float(kf.frame))

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
