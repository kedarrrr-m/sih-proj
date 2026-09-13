"""
planner/perception_bridge.py — T2.1 (SWAP 1: Perception Ingestion Interface)

Provides a unified interface to ingest BEV semantic segmentation masks and per-cell
confidence maps into the planning pipeline. Supports:
1. "synthetic": Stand-in fake perception for deterministic local development and tests.
2. "array": Direct in-memory numpy arrays (seg, conf).
3. "numpy": Serialized .npy files exported from Colab / offline eval.
4. "torchscript": TorchScript FusionSegNet model inference (when PyTorch is available).
"""

from typing import Tuple, Optional
import os
import numpy as np

# Class IDs — identical to FusionSegNet 5-class scheme
BACKGROUND: int = 0
ROAD: int = 1
SIDEWALK: int = 2
VEHICLE: int = 3
HUMAN: int = 4

CLASS_NAMES = {
    BACKGROUND: "background",
    ROAD: "road",
    SIDEWALK: "sidewalk",
    VEHICLE: "vehicle",
    HUMAN: "human",
}

# Standard ego BEV grid defaults (30m longitudinal x 20m lateral)
GRID_H: int = 120
GRID_W: int = 80
CELL_M: float = 0.25


def generate_synthetic_perception(seed: int = 0,
                                   grid_h: int = GRID_H,
                                   grid_w: int = GRID_W) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates a synthetic BEV semantic map and confidence map standing in for
    FusionSegNet after Inverse Perspective Mapping (IPM).
    
    Returns:
        seg: (grid_h, grid_w) int8 array with values in [0, 4].
        conf: (grid_h, grid_w) float32 array with values in [0.0, 1.0].
    """
    rng = np.random.default_rng(seed)
    seg = np.full((grid_h, grid_w), BACKGROUND, dtype=np.int8)

    # Drivable road corridor down the center with slight curvature
    for y in range(grid_h):
        cx = grid_w // 2 + int(6 * np.sin(y / 25.0))
        half = 12 + int(3 * np.sin(y / 9.0))
        x_min = max(0, cx - half)
        x_max = min(grid_w, cx + half)
        seg[y, x_min:x_max] = ROAD

        # Sidewalks flanking the road
        seg[y, max(0, x_min - 3):x_min] = SIDEWALK
        seg[y, x_max:min(grid_w, x_max + 3)] = SIDEWALK

    # Static parked vehicles along road margin
    seg[70:78, 44:52] = VEHICLE
    seg[30:36, 30:37] = VEHICLE

    # Confidence: high on road center, drops at class boundaries & far rows (y < 20)
    conf = np.full((grid_h, grid_w), 0.92, dtype=np.float32)
    grad_y, grad_x = np.gradient(seg.astype(float))
    edges = np.abs(grad_y) + np.abs(grad_x)
    conf[edges > 0] = 0.40
    conf[:20, :] = 0.50
    conf += rng.normal(0, 0.02, conf.shape).astype(np.float32)
    conf = np.clip(conf, 0.05, 1.0).astype(np.float32)

    return seg, conf


def seg_to_occupancy(seg: np.ndarray, drivable_classes=(ROAD,)) -> np.ndarray:
    """
    Converts 5-class semantic segmentation into binary occupancy.
    0 = free (drivable road), 1 = obstacle (non-drivable).
    """
    occ = np.ones_like(seg, dtype=np.uint8)
    for c in drivable_classes:
        occ[seg == c] = 0
    return occ


def load_perception(source: str = "synthetic",
                    seg_array: Optional[np.ndarray] = None,
                    conf_array: Optional[np.ndarray] = None,
                    seg_path: Optional[str] = None,
                    conf_path: Optional[str] = None,
                    model_path: Optional[str] = None,
                    seed: int = 0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Loads or generates BEV segmentation and confidence arrays.
    
    Args:
        source: "synthetic", "array", "numpy", or "torchscript".
        seg_array: 2D numpy array if source=="array".
        conf_array: 2D numpy array if source=="array".
        seg_path: Path to .npy file if source=="numpy".
        conf_path: Path to .npy file if source=="numpy".
        model_path: Path to TorchScript .pt model if source=="torchscript".
        seed: Random seed for synthetic generation.
        
    Returns:
        seg: (H, W) ndarray of int8.
        conf: (H, W) ndarray of float32 in [0.0, 1.0].
    """
    if source == "synthetic":
        return generate_synthetic_perception(seed=seed)

    if source == "array":
        if seg_array is None or conf_array is None:
            raise ValueError("seg_array and conf_array must both be provided when source='array'.")
        if seg_array.shape != conf_array.shape:
            raise ValueError(f"Shape mismatch: seg {seg_array.shape} != conf {conf_array.shape}")
        return seg_array.astype(np.int8), np.clip(conf_array, 0.0, 1.0).astype(np.float32)

    if source == "numpy":
        if not seg_path or not os.path.exists(seg_path):
            raise FileNotFoundError(f"seg_path not found: {seg_path}")
        if not conf_path or not os.path.exists(conf_path):
            raise FileNotFoundError(f"conf_path not found: {conf_path}")
        seg = np.load(seg_path).astype(np.int8)
        conf = np.clip(np.load(conf_path), 0.0, 1.0).astype(np.float32)
        if seg.shape != conf.shape:
            raise ValueError(f"Shape mismatch in loaded files: seg {seg.shape} != conf {conf.shape}")
        return seg, conf

    if source == "torchscript":
        try:
            import torch  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "PyTorch is not installed in this environment. "
                "Install torch or use source='synthetic' / source='numpy'."
            ) from e
        if not model_path or not os.path.exists(model_path):
            raise FileNotFoundError(f"TorchScript model path not found: {model_path}")
        model = torch.jit.load(model_path)
        model.eval()
        raise NotImplementedError("Live camera tensor -> BEV inference adapter requires raw camera inputs.")

    raise ValueError(f"Unknown perception source: {source}")
