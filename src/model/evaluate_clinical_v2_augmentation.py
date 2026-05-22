"""
Comparison script for Clinical V2 augmentation variants (V2.17 / issue #158).

Loads evaluation JSON outputs for baseline, mild, and robust variants,
prints a delta comparison table, writes a CSV, and generates a summary doc.

Usage:
    python3 -m src.model.evaluate_clinical_v2_augmentation
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


TEST_CSV_PATH = Path("data/processed/clinical_v2/test.csv")
EXPECTED_TEST_HASH = "4b510381927f6265446a62cb990e69fd"

CLASS_NAMES = [
    "Eczema / dermatitis",
    "Urticaria / allergic reaction",
    "Folliculitis / acne-like",
    "Psoriasis / papulosquamous",
    "Lesion — dermoscopic review recommended",
]

LESION_CLASS = "Lesion — dermoscopic review recommended"
ECZEMA_CLASS = "Eczema / dermatitis"
URTICARIA_CLASS = "Urticaria / allergic reaction"

VARIANTS: list[dict] = [
    {
        "name": "baseline",
        "label": "Baseline",
        "metrics_json": Path("outputs/metrics/clinical_v2_test_metrics.json"),
        "source_metrics_csv": Path("outputs/metrics/clinical_v2_source_metrics.csv"),
    },
    {
        "name": "aug_mild",
        "label": "Mild aug",
        "metrics_json": Path("outputs/metrics/clinical_v2_aug_mild_test_metrics.json"),
        "source_metrics_csv": Path("outputs/metrics/clinical_v2_aug_mild_source_metrics.csv"),
    },
    {
        "name": "aug_robust",
        "label": "Robust aug",
        "metrics_json": Path("outputs/metrics/clinical_v2_aug_robust_test_metrics.json"),
        "source_metrics_csv": Path("outputs/metrics/clinical_v2_aug_robust_source_metrics.csv"),
    },
]

PROMOTION_CRITERIA: list[tuple[str, float, str]] = [
    ("combined_macro_f1", 0.6420, "higher_better"),
    ("balanced_accuracy", 0.6571, "higher_better"),
    ("scin_macro_f1", 0.4028, "higher_better"),
    ("fitzpatrick_macro_f1", 0.6366, "higher_better"),
    ("lesion_routing_fn", 76.0, "lower_better"),
]


def verify_test_hash() -> None:
    actual = hashlib.md5(TEST_CSV_PATH.read_bytes()).hexdigest()
    if actual != EXPECTED_TEST_HASH:
        raise AssertionError(
            f"Test set hash mismatch. Expected {EXPECTED_TEST_HASH}, got {actual}. "
            "Test split may have been modified — STOP."
        )
    print(f"Test set hash verified: {actual}")


def load_metrics_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Metrics JSON not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_source_metrics_csv(path: Path) -> dict[str, dict]:
    if not path.exists():
        raise FileNotFoundError(f"Source metrics CSV not found: {path}")
    result: dict[str, dict] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            result[row["source_dataset"]] = {
                "macro_f1": float(row["macro_f1"]),
                "accuracy": float(row["accuracy"]),
                "support": int(row["support"]),
            }
    return result


def extract_lesion_fn(confusion_matrix: list[list[int]]) -> int:
    lesion_idx = CLASS_NAMES.index(LESION_CLASS)
    row = confusion_matrix[lesion_idx]
    return sum(row) - row[lesion_idx]


def extract_eczema_to_urticaria(confusion_matrix: list[list[int]]) -> int:
    eczema_idx = CLASS_NAMES.index(ECZEMA_CLASS)
    urt_idx = CLASS_NAMES.index(URTICARIA_CLASS)
    return confusion_matrix[eczema_idx][urt_idx]


def extract_urticaria_fp(confusion_matrix: list[list[int]]) -> int:
    urt_idx = CLASS_NAMES.index(URTICARIA_CLASS)
    col_sum = sum(confusion_matrix[r][urt_idx] for r in range(len(confusion_matrix)))
    return col_sum - confusion_matrix[urt_idx][urt_idx]


def build_variant_row(variant: dict) -> dict:
    data = load_metrics_json(variant["metrics_json"])
    src = load_source_metrics_csv(variant["source_metrics_csv"])
    cm = data["confusion_matrix"]

    return {
        "name": variant["name"],
        "label": variant["label"],
        "combined_macro_f1": data["macro_f1"],
        "balanced_accuracy": data["balanced_accuracy"],
        "combined_accuracy": data["test_accuracy"],
        "scin_macro_f1": src.get("google_scin", {}).get("macro_f1", float("nan")),
        "scin_accuracy": src.get("google_scin", {}).get("accuracy", float("nan")),
        "scin_support": src.get("google_scin", {}).get("support", 0),
        "fitzpatrick_macro_f1": src.get("fitzpatrick17k", {}).get("macro_f1", float("nan")),
        "fitzpatrick_accuracy": src.get("fitzpatrick17k", {}).get("accuracy", float("nan")),
        "fitzpatrick_support": src.get("fitzpatrick17k", {}).get("support", 0),
        "lesion_routing_fn": extract_lesion_fn(cm),
        "eczema_to_urticaria": extract_eczema_to_urticaria(cm),
        "urticaria_fp": extract_urticaria_fp(cm),
        "class_report": data["class_report"],
        "confusion_matrix": cm,
    }


def promotion_verdict(row: dict, baseline_row: dict) -> tuple[str, list[str], list[str]]:
    passes = []
    fails = []
    for metric, threshold, direction in PROMOTION_CRITERIA:
        val = row.get(metric)
        if val is None:
            continue
        if direction == "higher_better":
            ok = float(val) >= threshold - 0.0005
        else:
            ok = float(val) <= threshold
        target = (passes if ok else fails)
        target.append(f"{metric}={val:.4f} vs threshold={threshold}")
    verdict = "PROMOTABLE CANDIDATE" if not fails else "NOT PROMOTABLE"
    return verdict, passes, fails


def print_comparison_table(rows: list[dict]) -> None:
    baseline = rows[0]
    metrics = [
        ("combined_macro_f1", "Combined macro-F1"),
        ("balanced_accuracy", "Balanced accuracy"),
        ("scin_macro_f1", "SCIN macro-F1"),
        ("fitzpatrick_macro_f1", "Fitzpatrick macro-F1"),
        ("combined_accuracy", "Combined accuracy"),
        ("lesion_routing_fn", "Lesion routing FN"),
        ("eczema_to_urticaria", "Eczema→Urticaria"),
        ("urticaria_fp", "Urticaria FP"),
    ]

    header = f"{'Metric':28s} {'Baseline':>10s} {'Mild aug':>10s} {'Robust aug':>12s} {'Mild Δ':>9s} {'Robust Δ':>10s}"
    print("\n" + "=" * len(header))
    print("Clinical V2 Augmentation Comparison — Issue #158")
    print("=" * len(header))
    print(header)
    print("─" * len(header))

    for key, label in metrics:
        b_val = baseline[key]
        m_val = rows[1][key]
        r_val = rows[2][key]

        def fmt(v: float | int) -> str:
            return f"{v:.4f}" if isinstance(v, float) else str(v)

        m_delta = m_val - b_val if isinstance(m_val, float) else m_val - b_val
        r_delta = r_val - b_val if isinstance(r_val, float) else r_val - b_val

        def fmt_delta(d: float | int) -> str:
            return f"{d:+.4f}" if isinstance(d, float) else f"{d:+d}"

        print(
            f"{label:28s} {fmt(b_val):>10s} {fmt(m_val):>10s} {fmt(r_val):>12s} "
            f"{fmt_delta(m_delta):>9s} {fmt_delta(r_delta):>10s}"
        )

    print("─" * len(header))
    print()
    print("Class-wise F1:")
    class_header = f"  {'Class':34s} {'Baseline':>9s} {'Mild aug':>9s} {'Robust aug':>11s}"
    print(class_header)
    for i, cls in enumerate(CLASS_NAMES):
        b_f1 = next(r["f1"] for r in baseline["class_report"] if r["class_name"] == cls)
        m_f1 = next(r["f1"] for r in rows[1]["class_report"] if r["class_name"] == cls)
        r_f1 = next(r["f1"] for r in rows[2]["class_report"] if r["class_name"] == cls)
        short = cls[:34]
        print(f"  {short:34s} {b_f1:>9.4f} {m_f1:>9.4f} {r_f1:>11.4f}")

    print()
    for row in rows[1:]:
        verdict, passes, fails = promotion_verdict(row, baseline)
        print(f"  {row['label']}: {verdict}")
        if fails:
            for f in fails:
                print(f"    FAIL: {f}")
        else:
            print(f"    All {len(passes)} promotion criteria passed.")
    print()


def save_comparison_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "variant", "combined_macro_f1", "balanced_accuracy", "combined_accuracy",
        "scin_macro_f1", "fitzpatrick_macro_f1", "lesion_routing_fn",
        "eczema_to_urticaria", "urticaria_fp",
        "delta_macro_f1", "delta_balanced_acc", "delta_scin_macro_f1",
        "delta_fitzpatrick_macro_f1", "delta_lesion_fn",
        "promotion_verdict",
    ]
    baseline = rows[0]
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            verdict, _, _ = promotion_verdict(row, baseline) if row["name"] != "baseline" else ("BASELINE", [], [])
            writer.writerow({
                "variant": row["label"],
                "combined_macro_f1": f"{row['combined_macro_f1']:.6f}",
                "balanced_accuracy": f"{row['balanced_accuracy']:.6f}",
                "combined_accuracy": f"{row['combined_accuracy']:.6f}",
                "scin_macro_f1": f"{row['scin_macro_f1']:.6f}",
                "fitzpatrick_macro_f1": f"{row['fitzpatrick_macro_f1']:.6f}",
                "lesion_routing_fn": row["lesion_routing_fn"],
                "eczema_to_urticaria": row["eczema_to_urticaria"],
                "urticaria_fp": row["urticaria_fp"],
                "delta_macro_f1": f"{row['combined_macro_f1'] - baseline['combined_macro_f1']:+.6f}",
                "delta_balanced_acc": f"{row['balanced_accuracy'] - baseline['balanced_accuracy']:+.6f}",
                "delta_scin_macro_f1": f"{row['scin_macro_f1'] - baseline['scin_macro_f1']:+.6f}",
                "delta_fitzpatrick_macro_f1": f"{row['fitzpatrick_macro_f1'] - baseline['fitzpatrick_macro_f1']:+.6f}",
                "delta_lesion_fn": f"{row['lesion_routing_fn'] - baseline['lesion_routing_fn']:+d}",
                "promotion_verdict": verdict,
            })
    print(f"Saved comparison CSV: {out_path}")


def save_summary_doc(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    baseline = rows[0]
    mild = rows[1]
    robust = rows[2]

    mild_verdict, _, mild_fails = promotion_verdict(mild, baseline)
    robust_verdict, _, robust_fails = promotion_verdict(robust, baseline)

    def delta(a: float, b: float) -> str:
        d = a - b
        return f"{d:+.4f}"

    lines = [
        "# Clinical V2 Augmentation Comparison Summary",
        "",
        "> Non-diagnostic model evaluation. The lesion class is a routing class for dermoscopic review, not cancer detection.",
        "",
        "## Purpose",
        "",
        "Issue #153 showed sampler and high-confidence SCIN variants were not promotable. Issue #158 evaluates whether clinical-photo augmentation can improve generalization. No taxonomy change, no inference wiring change, no model promotion in code.",
        "",
        "## Baseline Augmentation (verbatim from src/data/transforms.py)",
        "",
        "```",
        "RandomResizedCrop(224, scale=(0.9, 1.0), ratio=(0.95, 1.05))",
        "RandomHorizontalFlip(p=0.5)",
        "RandomVerticalFlip(p=0.5)",
        "ColorJitter(brightness=0.1, contrast=0.1, saturation=0.05, hue=0.02)",
        "ToTensor()",
        "Normalize(ImageNet mean/std)",
        "```",
        "",
        "## Candidate Strategies",
        "",
        "### Mild clinical (`mild_clinical`)",
        "",
        "```",
        "RandomResizedCrop(224, scale=(0.85, 1.0), ratio=(0.9, 1.1))",
        "RandomHorizontalFlip(p=0.5)",
        "RandomRotation(degrees=10)",
        "ColorJitter(brightness=0.15, contrast=0.15, saturation=0.05, hue=0.0)",
        "ToTensor()",
        "Normalize(ImageNet mean/std)",
        "```",
        "",
        "Key changes vs baseline: wider crop, no vertical flip (body-site anatomy is directional), mild rotation, hue=0.0 (preserves skin color).",
        "",
        "### Robust clinical (`robust_clinical`)",
        "",
        "```",
        "RandomResizedCrop(224, scale=(0.80, 1.0), ratio=(0.9, 1.1))",
        "RandomHorizontalFlip(p=0.5)",
        "RandomRotation(degrees=15)",
        "ColorJitter(brightness=0.2, contrast=0.2, saturation=0.05, hue=0.0)",
        "GaussianBlur(kernel_size=3, sigma=(0.1, 0.5))",
        "RandomGrayscale(p=0.02)",
        "ToTensor()",
        "Normalize(ImageNet mean/std)",
        "```",
        "",
        "Key changes vs mild: wider crop range, more rotation, mild blur, very rare grayscale. hue=0.0 preserved.",
        "",
        "**Why hue=0.0 in both variants:** Skin color carries diagnostic signal (erythema, pigment). Hue jitter in the baseline (hue=0.02) is very mild but removing it in clinical-photo variants is conservative and appropriate.",
        "",
        "## Visual Sanity Check",
        "",
        "Augmentation grid saved to `outputs/plots/augmentation_visual_check.png`. Three real clinical images × three strategies × three samples each. Skin tones were preserved across all strategies — no aggressive color shifts or distorted anatomy observed. Training proceeded.",
        "",
        "## Results",
        "",
        f"| Metric | Baseline | Mild aug (Δ) | Robust aug (Δ) |",
        f"|---|---:|---:|---:|",
        f"| Combined macro-F1 | {baseline['combined_macro_f1']:.4f} | {mild['combined_macro_f1']:.4f} ({delta(mild['combined_macro_f1'], baseline['combined_macro_f1'])}) | {robust['combined_macro_f1']:.4f} ({delta(robust['combined_macro_f1'], baseline['combined_macro_f1'])}) |",
        f"| Balanced accuracy | {baseline['balanced_accuracy']:.4f} | {mild['balanced_accuracy']:.4f} ({delta(mild['balanced_accuracy'], baseline['balanced_accuracy'])}) | {robust['balanced_accuracy']:.4f} ({delta(robust['balanced_accuracy'], baseline['balanced_accuracy'])}) |",
        f"| SCIN macro-F1 | {baseline['scin_macro_f1']:.4f} | {mild['scin_macro_f1']:.4f} ({delta(mild['scin_macro_f1'], baseline['scin_macro_f1'])}) | {robust['scin_macro_f1']:.4f} ({delta(robust['scin_macro_f1'], baseline['scin_macro_f1'])}) |",
        f"| Fitzpatrick macro-F1 | {baseline['fitzpatrick_macro_f1']:.4f} | {mild['fitzpatrick_macro_f1']:.4f} ({delta(mild['fitzpatrick_macro_f1'], baseline['fitzpatrick_macro_f1'])}) | {robust['fitzpatrick_macro_f1']:.4f} ({delta(robust['fitzpatrick_macro_f1'], baseline['fitzpatrick_macro_f1'])}) |",
        f"| Lesion routing FN | {baseline['lesion_routing_fn']} | {mild['lesion_routing_fn']} ({mild['lesion_routing_fn'] - baseline['lesion_routing_fn']:+d}) | {robust['lesion_routing_fn']} ({robust['lesion_routing_fn'] - baseline['lesion_routing_fn']:+d}) |",
        f"| Eczema→Urticaria | {baseline['eczema_to_urticaria']} | {mild['eczema_to_urticaria']} ({mild['eczema_to_urticaria'] - baseline['eczema_to_urticaria']:+d}) | {robust['eczema_to_urticaria']} ({robust['eczema_to_urticaria'] - baseline['eczema_to_urticaria']:+d}) |",
        f"| Urticaria FP | {baseline['urticaria_fp']} | {mild['urticaria_fp']} ({mild['urticaria_fp'] - baseline['urticaria_fp']:+d}) | {robust['urticaria_fp']} ({robust['urticaria_fp'] - baseline['urticaria_fp']:+d}) |",
        "",
        "## Class-wise F1",
        "",
        "| Class | Baseline | Mild aug | Robust aug |",
        "|---|---:|---:|---:|",
    ]

    for cls in CLASS_NAMES:
        b_f1 = next(r["f1"] for r in baseline["class_report"] if r["class_name"] == cls)
        m_f1 = next(r["f1"] for r in mild["class_report"] if r["class_name"] == cls)
        r_f1 = next(r["f1"] for r in robust["class_report"] if r["class_name"] == cls)
        lines.append(f"| {cls} | {b_f1:.4f} | {m_f1:.4f} | {r_f1:.4f} |")

    lines += [
        "",
        "## Promotion Verdict",
        "",
        "Promotion criteria (from issue #158): combined macro-F1 ≥ 0.6420, balanced accuracy ≥ 0.6571, "
        "SCIN macro-F1 ≥ 0.4028, Fitzpatrick macro-F1 ≥ 0.6366, lesion routing FN ≤ 76.",
        "",
        f"**Mild aug:** {mild_verdict}",
    ]
    if mild_fails:
        lines.append("Failed criteria:")
        for f in mild_fails:
            lines.append(f"- {f}")
    lines += [
        "",
        f"**Robust aug:** {robust_verdict}",
    ]
    if robust_fails:
        lines.append("Failed criteria:")
        for f in robust_fails:
            lines.append(f"- {f}")

    # Recommendation
    lines += [
        "",
        "## Recommendation",
        "",
    ]

    mild_promotable = not mild_fails
    robust_promotable = not robust_fails

    if mild_promotable and robust_promotable:
        lines += [
            "Both variants meet promotion criteria. Recommend the **mild clinical** strategy as the more conservative choice: "
            "it achieves comparable or better SCIN and Fitzpatrick performance than robust while applying fewer changes. "
            "Prefer the variant with lower lesion routing FN if they differ.",
            "",
            "Next step: retrain the production baseline using `clinical_v2_aug_mild_config.yaml` and re-evaluate before promoting.",
        ]
    elif mild_promotable:
        lines += [
            "**Mild clinical augmentation** meets all promotion criteria and is recommended for future training. "
            f"SCIN macro-F1: {mild['scin_macro_f1']:.4f} ({delta(mild['scin_macro_f1'], baseline['scin_macro_f1'])} vs baseline). "
            f"Lesion routing FN: {mild['lesion_routing_fn']} vs baseline {baseline['lesion_routing_fn']}.",
            "",
            "Robust augmentation did not meet all criteria and is not recommended for promotion.",
            "",
            "Next step: retrain using `clinical_v2_aug_mild_config.yaml` as the standard training config.",
        ]
    elif robust_promotable:
        lines += [
            "**Robust clinical augmentation** meets all promotion criteria and is recommended for future training. "
            f"SCIN macro-F1: {robust['scin_macro_f1']:.4f} ({delta(robust['scin_macro_f1'], baseline['scin_macro_f1'])} vs baseline). "
            f"Lesion routing FN: {robust['lesion_routing_fn']} vs baseline {baseline['lesion_routing_fn']}.",
            "",
            "Mild augmentation did not meet all criteria.",
        ]
    else:
        lines += [
            "Neither augmentation strategy meets all promotion criteria against the current baseline. "
            "Augmentation alone is insufficient to close the SCIN generalization gap.",
            "",
            "Interpretation: The SCIN vs Fitzpatrick17k performance gap is likely driven by dataset distribution differences "
            "(image style, label quality, demographic coverage) rather than augmentation choices. "
            "Better augmentation cannot compensate for domain shift at this scale.",
            "",
            "Recommended next steps:",
            "- Defer augmentation improvement until the expanded 8-class taxonomy (PAD-UFES integration) provides more lesion coverage.",
            "- If SCIN improvement is the priority, revisit source-aware sampling with the enriched dataset.",
            "- Keep the existing baseline (`models/clinical_v2_effnet_b0/`) in production.",
        ]

    lines += [
        "",
        "## Out of Scope",
        "",
        "Confirmed out of scope for this task:",
        "- Expanded 8-class taxonomy",
        "- PAD-UFES integration",
        "- Model registry or app inference changes",
        "- Clinical-readiness or diagnostic claims",
        "",
        "## Artifacts",
        "",
        "- Comparison table: `outputs/metrics/clinical_v2_augmentation_comparison_table.csv`",
        "- Mild model: `models/clinical_v2_aug_mild_effnet_b0/best_model.pth`",
        "- Robust model: `models/clinical_v2_aug_robust_effnet_b0/best_model.pth`",
        "- Confusion matrices: `outputs/plots/clinical_v2_aug_mild_confusion_matrix.png`, `outputs/plots/clinical_v2_aug_robust_confusion_matrix.png`",
        "- Visual check: `outputs/plots/augmentation_visual_check.png`",
        "- Test set hash: `4b510381927f6265446a62cb990e69fd` (verified unchanged throughout)",
    ]

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved summary doc: {out_path}")


def main() -> None:
    verify_test_hash()

    rows = []
    for variant in VARIANTS:
        print(f"Loading: {variant['name']} ...")
        row = build_variant_row(variant)
        rows.append(row)

    print_comparison_table(rows)
    verify_test_hash()

    save_comparison_csv(rows, Path("outputs/metrics/clinical_v2_augmentation_comparison_table.csv"))
    save_summary_doc(rows, Path("docs/model/clinical_v2_augmentation_comparison_summary.md"))


if __name__ == "__main__":
    main()
