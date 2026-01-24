#!/usr/bin/env python3
"""
Scene Data Module
Format-agnostic data structures for scene representation.

This module defines the intermediate data structures that decouple
readers (Alembic, USD) from exporters (AE, USD, Maya MA). Readers
extract scene data into these structures, and exporters consume them
without knowledge of the source format.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class AnimationType(Enum):
    """Animation classification for mesh objects"""
    STATIC = "static"
    TRANSFORM_ONLY = "transform_only"
    VERTEX_ANIMATED = "vertex_animated"
    BLEND_SHAPE = "blend_shape"  # Vertex animation via blend shapes (exportable to FBX)


@dataclass
class Keyframe:
    """Single animation keyframe with transform data

    Stores both AE-compatible and Maya-compatible rotation decompositions
    to avoid re-extraction in exporters.

    Attributes:
        frame: 1-based frame number
        position: [x, y, z] translation in scene units
        rotation_ae: [rx, ry, rz] degrees - After Effects compatible decomposition
        rotation_maya: [rx, ry, rz] degrees - Maya/USD compatible decomposition
        scale: [sx, sy, sz] scale multipliers
    """
    frame: int
    position: Tuple[float, float, float]
    rotation_ae: Tuple[float, float, float]
    rotation_maya: Tuple[float, float, float]
    scale: Tuple[float, float, float]


@dataclass
class CameraProperties:
    """Camera-specific optical properties

    Attributes:
        focal_length: Focal length in mm
        h_aperture: Horizontal aperture in cm (Alembic convention)
        v_aperture: Vertical aperture in cm (Alembic convention)
    """
    focal_length: float
    h_aperture: float
    v_aperture: float


@dataclass
class CameraData:
    """Complete camera data with animation

    Attributes:
        name: Camera object name
        parent_name: Parent transform name if camera is nested, None otherwise
        full_path: Full hierarchy path (e.g., "/World/Camera/CameraShape")
        properties: Camera optical properties (focal length, apertures)
        keyframes: Pre-extracted animation keyframes for all frames
    """
    name: str
    parent_name: Optional[str]
    full_path: str
    properties: CameraProperties
    keyframes: List[Keyframe]


@dataclass
class MeshGeometry:
    """Static mesh geometry data (first frame)

    Attributes:
        positions: List of vertex positions as [x, y, z] tuples
        indices: Face vertex indices (flattened)
        counts: Number of vertices per face
    """
    positions: List[Tuple[float, float, float]]
    indices: List[int]
    counts: List[int]


@dataclass
class BlendShapeTarget:
    """Single blend shape target with delta positions

    Attributes:
        name: Target name (e.g., "smile", "blink")
        vertex_indices: List of affected vertex indices (sparse storage)
        deltas: Delta positions for each affected vertex [(dx,dy,dz), ...]
        full_weight: Weight value at which target is fully applied (default 1.0)
    """
    name: str
    vertex_indices: List[int]
    deltas: List[Tuple[float, float, float]]
    full_weight: float = 1.0


@dataclass
class BlendShapeWeightKey:
    """Keyframe for blend shape weight animation

    Attributes:
        frame: Frame number
        weight: Weight value (0.0 to 1.0)
    """
    frame: int
    weight: float


@dataclass
class BlendShapeChannel:
    """Blend shape channel controlling one or more targets

    A channel represents a single animatable weight that controls one target
    (or multiple targets for in-between/progressive morphs).

    Attributes:
        name: Channel name (often same as target name)
        targets: List of shape targets (usually 1, multiple for in-betweens)
        weight_animation: Optional animated weights, None if static
        default_weight: Static weight if not animated (0.0 to 1.0)
    """
    name: str
    targets: List[BlendShapeTarget]
    weight_animation: Optional[List[BlendShapeWeightKey]] = None
    default_weight: float = 0.0


@dataclass
class BlendShapeDeformer:
    """Complete blend shape deformer with all channels

    Attributes:
        name: Deformer node name
        channels: All blend shape channels
        base_mesh_name: Name of the mesh being deformed
    """
    name: str
    channels: List[BlendShapeChannel]
    base_mesh_name: str


@dataclass
class MeshData:
    """Complete mesh data with animation and geometry

    Attributes:
        name: Mesh object name
        parent_name: Parent transform name if mesh is nested
        full_path: Full hierarchy path
        animation_type: Classification (STATIC, TRANSFORM_ONLY, VERTEX_ANIMATED, BLEND_SHAPE)
        keyframes: Transform animation keyframes (empty if static)
        geometry: First frame geometry (positions, indices, counts)
        vertex_positions_per_frame: Per-frame vertex positions if vertex-animated
        blend_shapes: Blend shape deformer data if mesh has blend shapes
    """
    name: str
    parent_name: Optional[str]
    full_path: str
    animation_type: AnimationType
    keyframes: List[Keyframe]
    geometry: MeshGeometry
    vertex_positions_per_frame: Optional[Dict[int, List[Tuple[float, float, float]]]] = None
    blend_shapes: Optional[BlendShapeDeformer] = None


@dataclass
class TransformData:
    """Transform/locator data with animation

    Used for pure transforms that don't have camera or mesh shapes attached.
    These become nulls/locators in the exported scene.

    Attributes:
        name: Transform object name
        parent_name: Parent transform name if nested
        full_path: Full hierarchy path
        keyframes: Animation keyframes for all frames
    """
    name: str
    parent_name: Optional[str]
    full_path: str
    keyframes: List[Keyframe]


@dataclass
class SceneMetadata:
    """Scene-level metadata

    Attributes:
        width: Render width in pixels
        height: Render height in pixels
        fps: Frames per second
        frame_count: Total number of frames
        footage_path: Path to associated footage file (if embedded in scene)
        source_file_path: Absolute path to the source file
        source_format_name: Human-readable format name ("Alembic" or "USD")
    """
    width: int
    height: int
    fps: float
    frame_count: int
    footage_path: Optional[str]
    source_file_path: str
    source_format_name: str


@dataclass
class AnimationCategories:
    """Pre-categorized mesh names by animation type

    This mirrors the output of AnimationDetector.analyze_scene() for
    backward compatibility and easy access.

    Attributes:
        vertex_animated: List of mesh names with raw vertex deformation (not exportable to FBX)
        blend_shape: List of mesh names with blend shape deformation (exportable to FBX)
        transform_only: List of mesh names with only transform animation
        static: List of mesh names with no animation
    """
    vertex_animated: List[str] = field(default_factory=list)
    blend_shape: List[str] = field(default_factory=list)
    transform_only: List[str] = field(default_factory=list)
    static: List[str] = field(default_factory=list)


@dataclass
class SceneData:
    """Complete scene data extracted from input file

    This is the format-agnostic intermediate representation that decouples
    readers from exporters. All animation is pre-extracted for all frames.

    Attributes:
        metadata: Scene-level information (resolution, fps, source file)
        cameras: All cameras with animation and properties
        meshes: All meshes with animation, geometry, and categorization
        transforms: Pure transforms/locators without shapes
        animation_categories: Quick lookup for mesh animation types
    """
    metadata: SceneMetadata
    cameras: List[CameraData]
    meshes: List[MeshData]
    transforms: List[TransformData]
    animation_categories: AnimationCategories

    def get_mesh_by_name(self, name: str) -> Optional[MeshData]:
        """Find mesh by name

        Args:
            name: Mesh name to find

        Returns:
            MeshData if found, None otherwise
        """
        for mesh in self.meshes:
            if mesh.name == name:
                return mesh
        return None

    def get_camera_by_name(self, name: str) -> Optional[CameraData]:
        """Find camera by name

        Args:
            name: Camera name to find

        Returns:
            CameraData if found, None otherwise
        """
        for cam in self.cameras:
            if cam.name == name:
                return cam
        return None

    def get_transform_by_name(self, name: str) -> Optional[TransformData]:
        """Find transform by name

        Args:
            name: Transform name to find

        Returns:
            TransformData if found, None otherwise
        """
        for xform in self.transforms:
            if xform.name == name:
                return xform
        return None
