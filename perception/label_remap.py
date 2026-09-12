"""
label_remap.py  —  SIH 26037  —  Phase 1 / Token T1.2

Collapse each source dataset's label scheme into FusionSegNet's 5-class scheme so
nuScenes-trained predictions and IDD ground truth are directly comparable (the
domain-gap experiment, Bible §2.2 / Idea G). This module is the *definition* of the
mapping; the actual per-frame IoU numbers are produced in the FusionSegNet notebook
(T1.1/T1.3) once real masks are available. Pure-numpy, no torch, no dataset download —
so the mapping logic is unit-testable on synthetic label arrays today.

CLASS LEVEL REPORTED (per T1.2 Validation — state it explicitly):
  - IDD side: we map from **IDD level-3 label *names*** (the ~26-class "level 3" of
    IDD's 4-level hierarchy). Keying by name, not integer id, keeps the mapping robust
    to devkit id changes and makes it auditable.
  - Standard IDD split used for reporting: 6991 / 1912 / 957 (train/val/test), the
    common public split (Bible §2.2, Appendix B).

The 5 target classes match bridge_starter.py exactly, so downstream code (occupancy,
cost map) is unchanged.
"""

from __future__ import annotations
import numpy as np

# ---------------------------------------------------------------------------
# 5-class target scheme — MUST match bridge_starter.py (BACKGROUND..HUMAN = 0..4)
# ---------------------------------------------------------------------------
BACKGROUND, ROAD, SIDEWALK, VEHICLE, HUMAN = 0, 1, 2, 3, 4

CLASS_NAMES_5 = {
    BACKGROUND: "background",
    ROAD: "road",
    SIDEWALK: "sidewalk",
    VEHICLE: "vehicle",
    HUMAN: "human",
}

# Standard IDD split (train/val/test) used across public IDD repos (Bible §2.2).
IDD_SPLIT = {"train": 6991, "val": 1912, "test": 957}

# ---------------------------------------------------------------------------
# IDD level-3 label NAME -> 5-class id.
#
# Rationale for each bucket:
#   ROAD      : anything the vehicle may drive on (carriageway + IDD's signature
#               "drivable fallback", the informal road edge that structured datasets lack).
#   SIDEWALK  : pedestrian walkway.
#   HUMAN     : vulnerable road users on foot / two-wheeler riders (person + rider).
#   VEHICLE   : every motorised/human-powered vehicle, incl. IDD-specific autorickshaw
#               and the catch-all "vehicle fallback".
#   BACKGROUND: everything else (structures, vegetation, sky, non-drivable fallback,
#               street furniture) — not free space, not an agent we track by class.
#
# Any IDD name not listed here falls back to BACKGROUND (see remap_name), which is the
# safe default for the planner (unknown => not drivable, not an agent).
# ---------------------------------------------------------------------------
IDD_LEVEL3_TO_5CLASS = {
    # --- drivable ---
    "road": ROAD,
    "drivable fallback": ROAD,
    "parking": ROAD,
    # --- walkway ---
    "sidewalk": SIDEWALK,
    # --- humans (on foot / riders) ---
    "person": HUMAN,
    "rider": HUMAN,
    "animal": HUMAN,               # treated as a vulnerable dynamic agent, not scenery
    # --- vehicles ---
    "motorcycle": VEHICLE,
    "bicycle": VEHICLE,
    "autorickshaw": VEHICLE,
    "car": VEHICLE,
    "truck": VEHICLE,
    "bus": VEHICLE,
    "caravan": VEHICLE,
    "trailer": VEHICLE,
    "train": VEHICLE,
    "vehicle fallback": VEHICLE,
    # --- background / structures / street furniture / nature ---
    "curb": BACKGROUND,
    "wall": BACKGROUND,
    "fence": BACKGROUND,
    "guard rail": BACKGROUND,
    "billboard": BACKGROUND,
    "traffic sign": BACKGROUND,
    "traffic light": BACKGROUND,
    "pole": BACKGROUND,
    "polegroup": BACKGROUND,
    "obs-str-bar-fallback": BACKGROUND,
    "building": BACKGROUND,
    "bridge": BACKGROUND,
    "tunnel": BACKGROUND,
    "vegetation": BACKGROUND,
    "sky": BACKGROUND,
    "fallback background": BACKGROUND,
    "non-drivable fallback": BACKGROUND,
    "unlabeled": BACKGROUND,
    "ego vehicle": BACKGROUND,
    "rectification border": BACKGROUND,
    "out of roi": BACKGROUND,
    "license plate": BACKGROUND,
}

# ---------------------------------------------------------------------------
# nuScenes side. FusionSegNet is already TRAINED to output these 5 classes, so a
# predicted mask needs no remap (identity). This map is only for the rarer case of
# collapsing raw nuScenes-general semantic category names into the 5-class scheme
# (e.g. when re-deriving ground truth). Names follow nuScenes' `*.general` categories.
# ---------------------------------------------------------------------------
NUSCENES_GENERAL_TO_5CLASS = {
    "flat.driveable_surface": ROAD,
    "flat.sidewalk": SIDEWALK,
    "human.pedestrian.adult": HUMAN,
    "human.pedestrian.child": HUMAN,
    "human.pedestrian.construction_worker": HUMAN,
    "human.pedestrian.police_officer": HUMAN,
    "vehicle.bicycle": VEHICLE,
    "vehicle.motorcycle": VEHICLE,
    "vehicle.car": VEHICLE,
    "vehicle.truck": VEHICLE,
    "vehicle.bus.bendy": VEHICLE,
    "vehicle.bus.rigid": VEHICLE,
    "vehicle.trailer": VEHICLE,
    "vehicle.construction": VEHICLE,
    "vehicle.emergency.ambulance": VEHICLE,
    "vehicle.emergency.police": VEHICLE,
    # everything else (flat.terrain, static.*, vegetation, sky, noise, ...) -> BACKGROUND
}

_SCHEMES = {
    "idd": IDD_LEVEL3_TO_5CLASS,
    "idd_level3": IDD_LEVEL3_TO_5CLASS,
    "nuscenes": NUSCENES_GENERAL_TO_5CLASS,
    "nuscenes_general": NUSCENES_GENERAL_TO_5CLASS,
}


def remap_name(label_name: str, scheme: str = "idd") -> int:
    """Map one source class *name* to a 5-class id. Unknown -> BACKGROUND (safe default)."""
    table = _SCHEMES.get(scheme.lower())
    if table is None:
        raise KeyError(f"unknown scheme {scheme!r}; known: {sorted(_SCHEMES)}")
    return table.get(label_name.strip().lower(), BACKGROUND)


def build_id_lut(id_to_name: dict[int, str], scheme: str = "idd") -> np.ndarray:
    """
    Build an integer lookup table LUT such that LUT[source_id] = 5-class id, given the
    source dataset's own {id: name} mapping (from its devkit / labels.py). Returning a
    LUT lets you remap a whole label image with one vectorised `LUT[label_array]`.
    """
    if not id_to_name:
        raise ValueError("id_to_name is empty")
    size = max(id_to_name) + 1
    lut = np.full(size, BACKGROUND, dtype=np.uint8)
    for src_id, name in id_to_name.items():
        if src_id < 0:
            raise ValueError(f"negative source id {src_id}")
        lut[src_id] = remap_name(name, scheme)
    return lut


def remap_id_array(label_array: np.ndarray, id_to_name: dict[int, str],
                   scheme: str = "idd") -> np.ndarray:
    """
    Vectorised remap of a 2-D label image (source ids) into the 5-class scheme.
    Shape is preserved; output dtype uint8 with values in {0..4}. Ids beyond the LUT
    (unseen) collapse to BACKGROUND rather than raising, matching remap_name's default.
    """
    lut = build_id_lut(id_to_name, scheme)
    a = np.asarray(label_array)
    idx = np.clip(a, 0, len(lut) - 1).astype(np.intp)
    out = lut[idx]
    out[a >= len(lut)] = BACKGROUND
    out[a < 0] = BACKGROUND
    return out.astype(np.uint8)
