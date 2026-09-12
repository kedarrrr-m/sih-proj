"""Fixture tests for perception/metrics.py — deterministic, no dataset/torch."""
import numpy as np
from perception.metrics import (
    confusion_matrix, per_class_iou, mean_iou, drivable_iou, kpi_dict,
)
from perception.label_remap import ROAD, HUMAN, BACKGROUND


def test_perfect_prediction_gives_iou_one():
    gt = np.array([[ROAD, ROAD], [HUMAN, BACKGROUND]])
    assert mean_iou(gt, gt) == 1.0
    assert drivable_iou(gt, gt) == 1.0
    pc = per_class_iou(gt, gt)
    assert pc["road"] == 1.0 and pc["human"] == 1.0


def test_confusion_matrix_counts():
    gt = np.array([ROAD, ROAD, HUMAN])
    pred = np.array([ROAD, HUMAN, HUMAN])
    cm = confusion_matrix(pred, gt)
    assert cm[ROAD, ROAD] == 1      # one road correct
    assert cm[ROAD, HUMAN] == 1     # one road predicted human
    assert cm[HUMAN, HUMAN] == 1


def test_drivable_iou_half():
    # gt road = 2 cells, pred road = 2 cells, overlap = 1  -> IoU = 1/3
    gt = np.array([ROAD, ROAD, BACKGROUND])
    pred = np.array([ROAD, BACKGROUND, ROAD])
    assert abs(drivable_iou(pred, gt) - (1 / 3)) < 1e-9


def test_absent_class_is_nan_not_zero():
    # SIDEWALK/VEHICLE never appear -> excluded from mIoU (NaN), not dragging it down.
    gt = np.array([ROAD, HUMAN])
    pred = np.array([ROAD, HUMAN])
    from perception.metrics import iou_from_confusion
    iou = iou_from_confusion(confusion_matrix(pred, gt))
    assert np.isnan(iou[2]) and np.isnan(iou[3])   # sidewalk, vehicle
    assert mean_iou(pred, gt) == 1.0               # NaNs excluded


def test_kpi_dict_shape():
    gt = np.random.default_rng(0).integers(0, 5, size=(16, 16))
    pred = gt.copy()
    k = kpi_dict(pred, gt)
    assert set(k) == {"mIoU", "per_class_IoU", "drivable_IoU"}
    assert k["mIoU"] == 1.0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"PASS  {fn.__name__}")
    print(f"\n{len(fns)} passed")
