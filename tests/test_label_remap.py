"""
Fixture-based tests for the T1.2 label remap. Deterministic, no dataset / no torch —
this is the reproducible-fixture test the build skill asks for. It verifies the mapping
*logic* is correct; the real per-frame "visually correct masks" check happens once IDD
frames are available in the notebook.

Run:  ./.venv/bin/python -m pytest tests/ -q      (or)      ./.venv/bin/python tests/test_label_remap.py
"""
import numpy as np
from perception.label_remap import (
    BACKGROUND, ROAD, SIDEWALK, VEHICLE, HUMAN,
    IDD_SPLIT, remap_name, build_id_lut, remap_id_array,
)


def test_idd_split_pinned():
    assert IDD_SPLIT == {"train": 6991, "val": 1912, "test": 957}


def test_key_idd_classes_map_correctly():
    # The Indian-specific and safety-critical classes must land in the right bucket.
    assert remap_name("road", "idd") == ROAD
    assert remap_name("drivable fallback", "idd") == ROAD          # IDD's informal road edge
    assert remap_name("sidewalk", "idd") == SIDEWALK
    assert remap_name("person", "idd") == HUMAN
    assert remap_name("rider", "idd") == HUMAN
    assert remap_name("autorickshaw", "idd") == VEHICLE            # IDD-specific agent
    assert remap_name("car", "idd") == VEHICLE
    assert remap_name("bus", "idd") == VEHICLE
    assert remap_name("sky", "idd") == BACKGROUND
    assert remap_name("non-drivable fallback", "idd") == BACKGROUND


def test_case_insensitive_and_unknown_defaults_background():
    assert remap_name("ROAD", "idd") == ROAD
    assert remap_name("  Autorickshaw ", "idd") == VEHICLE
    assert remap_name("something-never-seen", "idd") == BACKGROUND  # safe default


def test_nuscenes_scheme():
    assert remap_name("flat.driveable_surface", "nuscenes") == ROAD
    assert remap_name("vehicle.car", "nuscenes") == VEHICLE
    assert remap_name("human.pedestrian.adult", "nuscenes") == HUMAN
    assert remap_name("static.vegetation", "nuscenes") == BACKGROUND  # unlisted -> bg


def test_remap_id_array_preserves_shape_and_range():
    # Synthetic IDD-style label image with a tiny id->name table.
    id_to_name = {0: "road", 1: "sidewalk", 2: "car", 3: "person", 4: "sky"}
    lut = build_id_lut(id_to_name, "idd")
    assert list(lut) == [ROAD, SIDEWALK, VEHICLE, HUMAN, BACKGROUND]

    label_img = np.array([[0, 1, 2],
                          [3, 4, 2],
                          [0, 3, 1]], dtype=np.int32)
    out = remap_id_array(label_img, id_to_name, "idd")

    assert out.shape == label_img.shape
    assert out.dtype == np.uint8
    assert set(np.unique(out)).issubset({BACKGROUND, ROAD, SIDEWALK, VEHICLE, HUMAN})
    # spot-check a couple of cells
    assert out[0, 0] == ROAD and out[1, 0] == HUMAN and out[0, 2] == VEHICLE


def test_out_of_range_ids_collapse_to_background():
    id_to_name = {0: "road", 1: "car"}
    img = np.array([[0, 1, 99]], dtype=np.int32)   # 99 is an unseen id
    out = remap_id_array(img, id_to_name, "idd")
    assert out[0, 2] == BACKGROUND


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"PASS  {fn.__name__}")
    print(f"\n{len(fns)} passed")
