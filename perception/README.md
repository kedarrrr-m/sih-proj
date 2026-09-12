# perception/ — Phase 1 tooling (SIH 26037)

Deterministic, dataset-free helpers that turn **real** FusionSegNet masks into the
Phase-1 numbers. They compute nothing until you feed them actual predictions/labels —
no fabricated mIoU (Bible Part XVI). Local deps: numpy only (`requirements.txt`). The
model itself needs `requirements-perception.txt` in Colab/GPU.

| File | Token | What it does |
|---|---|---|
| `label_remap.py` | **T1.2** | IDD level-3 names + nuScenes-general → 5-class scheme; pinned IDD split 6991/1912/957. |
| `metrics.py` | T1.1 / T1.3 / T1.6 | mIoU, per-class IoU, binary drivable-space IoU from real masks. |
| `domain_gap.py` | T1.3 (Idea G) | Renders the §2.2 table from measured mIoU values, with the IndiVNet comparability caveat. |

## Run the fixture tests (local, ~1s)
```bash
PYTHONPATH=. ./.venv/bin/python tests/test_label_remap.py
PYTHONPATH=. ./.venv/bin/python tests/test_metrics.py
```

## Drop-in eval cell for FusionSegNet_v5.ipynb (unblocks T1.1/T1.3/T1.6)
Copy `perception/` into the notebook's working dir, then:
```python
from perception.metrics import kpi_dict
from perception.label_remap import remap_id_array, IDD_SPLIT
from perception.domain_gap import domain_gap_table

# 1) nuScenes-val: pred = argmax(model(img)) already in the 5-class scheme
nus = kpi_dict(pred_nuscenes, gt_nuscenes)              # -> real mIoU / per-class / drivable

# 2) IDD-val: remap IDD gt into 5 classes first (supply IDD devkit's {id:name})
gt_idd_5 = remap_id_array(gt_idd_raw, IDD_DEVKIT_ID_TO_NAME, scheme="idd")
idd_before = kpi_dict(pred_idd, gt_idd_5)               # BEFORE adaptation (T1.3)

# 3) the honest table (fill idd_after once you've fine-tuned, T1.4)
print(domain_gap_table(nus["mIoU"]*100, idd_before["mIoU"]*100))
```
`IDD_DEVKIT_ID_TO_NAME` comes from the IDD devkit's `labels.py`; confirm the names match
this repo's `IDD_LEVEL3_TO_5CLASS` keys for the devkit version you use.
