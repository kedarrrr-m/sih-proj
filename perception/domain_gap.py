"""
domain_gap.py  —  SIH 26037  —  Phase 1 prerequisite tooling for T1.3 / T1.6 (Idea G)

Assembles the §2.2 domain-gap table from MEASURED numbers you pass in. It does not
compute or guess any mIoU — you hand it real values from metrics.kpi_dict on each split,
and it renders the honest table with the comparability caveat baked in (IndiVNet's
69.98% is context, NOT like-for-like, because it uses IDD's own class set).
"""
from __future__ import annotations

INDIVNET_IDD_MIOU = 69.98  # Sci. Reports 2025 — reference bar, different class set.


def domain_gap_table(nuscenes_val_miou: float,
                     idd_val_miou_before: float,
                     idd_val_miou_after: float | None = None,
                     class_level: str = "5-class (custom FusionSegNet scheme)") -> str:
    """Return a markdown table. Percentages are whatever you measured (0-100 scale)."""
    gap = nuscenes_val_miou - idd_val_miou_before
    rows = [
        "| Model | nuScenes-val mIoU | IDD-val mIoU | Δ |",
        "|---|---|---|---|",
        f"| FusionSegNet (nuScenes-trained only) | {nuscenes_val_miou:.2f} | "
        f"{idd_val_miou_before:.2f} | **{gap:+.2f} (the gap)** |",
    ]
    if idd_val_miou_after is not None:
        recovery = idd_val_miou_after - idd_val_miou_before
        rows.append(
            f"| + IDD fine-tuning / domain adaptation | — | {idd_val_miou_after:.2f} | "
            f"**{recovery:+.2f} (the recovery)** |"
        )
    rows.append(
        f"| *SOTA reference: IndiVNet (Sci. Reports 2025)* | — | *{INDIVNET_IDD_MIOU}* | "
        f"*the bar (context only)* |"
    )
    caveat = (
        f"\n\n> **Comparability caveat:** mIoU is only like-for-like over the same class "
        f"set. We report **{class_level}**; IndiVNet's {INDIVNET_IDD_MIOU}% uses IDD's own "
        f"hierarchy, so it is an *aspirational reference, not a head-to-head figure* "
        f"(Bible §2.2). Our contribution is zero-annotation fusion labelling + adaptive "
        f"planning, not raw segmentation accuracy."
    )
    return "\n".join(rows) + caveat


if __name__ == "__main__":
    # Illustration with PLACEHOLDER inputs so you can see the format. Replace with
    # metrics.kpi_dict(...) outputs from real runs before putting this in a slide.
    print(domain_gap_table(nuscenes_val_miou=0.0, idd_val_miou_before=0.0))
    print("\n[placeholder demo — feed real measured mIoU values]")
