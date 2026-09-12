"""
metrics.py  —  SIH 26037  —  Phase 1 prerequisite tooling for T1.1 / T1.3 / T1.6

The measured-number harness. Given predicted and ground-truth 5-class masks it returns
mIoU, per-class IoU, and the binary drivable-space IoU that planning actually depends on
(Bible §Part IX). Pure numpy so it runs anywhere and is unit-testable on fixtures — but
it computes numbers from REAL masks; it never invents them. Drop it into the FusionSegNet
notebook and feed it argmax predictions + labels.
"""
from __future__ import annotations
import numpy as np
from .label_remap import BACKGROUND, ROAD, SIDEWALK, VEHICLE, HUMAN, CLASS_NAMES_5

NUM_CLASSES = 5


def confusion_matrix(pred: np.ndarray, gt: np.ndarray, num_classes: int = NUM_CLASSES,
                     ignore_index: int | None = None) -> np.ndarray:
    """Row = ground truth, col = prediction. Accumulate over a batch by summing these."""
    pred = np.asarray(pred).reshape(-1)
    gt = np.asarray(gt).reshape(-1)
    if pred.shape != gt.shape:
        raise ValueError(f"pred/gt size mismatch: {pred.shape} vs {gt.shape}")
    mask = np.ones_like(gt, dtype=bool)
    if ignore_index is not None:
        mask = gt != ignore_index
    k = num_classes
    idx = gt[mask].astype(np.int64) * k + pred[mask].astype(np.int64)
    return np.bincount(idx, minlength=k * k).reshape(k, k)


def iou_from_confusion(cm: np.ndarray) -> np.ndarray:
    """Per-class IoU = TP / (TP + FP + FN). Classes absent from union return NaN."""
    tp = np.diag(cm).astype(np.float64)
    fp = cm.sum(axis=0) - tp
    fn = cm.sum(axis=1) - tp
    union = tp + fp + fn
    with np.errstate(divide="ignore", invalid="ignore"):
        iou = np.where(union > 0, tp / union, np.nan)
    return iou


def per_class_iou(pred: np.ndarray, gt: np.ndarray) -> dict[str, float]:
    iou = iou_from_confusion(confusion_matrix(pred, gt))
    return {CLASS_NAMES_5[i]: float(iou[i]) for i in range(NUM_CLASSES)}


def mean_iou(pred: np.ndarray, gt: np.ndarray) -> float:
    """mIoU over classes present in the data (NaN classes excluded), as is standard."""
    iou = iou_from_confusion(confusion_matrix(pred, gt))
    return float(np.nanmean(iou))


def drivable_iou(pred: np.ndarray, gt: np.ndarray) -> float:
    """
    Binary drivable-space IoU (ROAD vs not-ROAD) — the single number the planner's cost
    map depends on, so we report it separately from mIoU (Bible §Part IX).
    """
    p = (np.asarray(pred) == ROAD)
    g = (np.asarray(gt) == ROAD)
    inter = np.logical_and(p, g).sum()
    union = np.logical_or(p, g).sum()
    return float(inter / union) if union > 0 else float("nan")


def kpi_dict(pred: np.ndarray, gt: np.ndarray) -> dict:
    """One call → the perception KPI block for a split. Real inputs, real outputs."""
    return {
        "mIoU": mean_iou(pred, gt),
        "per_class_IoU": per_class_iou(pred, gt),
        "drivable_IoU": drivable_iou(pred, gt),
    }
