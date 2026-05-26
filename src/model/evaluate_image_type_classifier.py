"""
Evaluate the trained 2-class image-type classifier on a reserved split.

Produces:
  outputs/metrics/image_type_classifier_predictions.csv
  outputs/metrics/image_type_classifier_metrics.json
  outputs/metrics/image_type_classifier_confusion_matrix.csv
  outputs/metrics/image_type_classifier_threshold_analysis.csv
  outputs/metrics/image_type_classifier_misclassified_examples.csv

Example
-------
python -m src.model.evaluate_image_type_classifier \\
    --model-dir models/image_type_classifier_v1 \\
    --split test \\
    --batch-size 32 \\
    --thresholds 0.70 0.80 0.85 0.90 0.95 \\
    --output-dir outputs/metrics
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
from PIL import Image

from src.data.transforms import get_eval_transforms
from src.model.model import build_model
from src.model.train import (
    compute_balanced_accuracy,
    compute_macro_f1,
    compute_per_class_recalls,
    select_device,
)

CLASS_NAMES = ["clinical_macroscopic", "dermoscopic"]
DATASET_INDEX = "outputs/model/image_type_classifier_dataset_index.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate 2-class image-type classifier."
    )
    parser.add_argument("--model-dir", default="models/image_type_classifier_v1")
    parser.add_argument(
        "--split", default="test", choices=["train", "val", "test"],
        help="Which split CSV from model-dir to evaluate."
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default="auto",
                        help="'auto', 'cpu', 'cuda', or 'mps'.")
    parser.add_argument(
        "--thresholds", nargs="+", type=float,
        default=[0.70, 0.80, 0.85, 0.90, 0.95],
    )
    parser.add_argument("--output-dir", default="outputs/metrics")
    parser.add_argument("--num-workers", type=int, default=0)
    return parser.parse_args()


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_model_artifacts(model_dir: Path):
    """Load class_to_idx, training_config, and best checkpoint."""
    class_to_idx_path = model_dir / "class_to_idx.json"
    config_path = model_dir / "training_config.json"
    checkpoint_path = model_dir / "best_model.pth"

    for p in (class_to_idx_path, config_path, checkpoint_path):
        if not p.exists():
            raise FileNotFoundError(f"Required artifact not found: {p}")

    with class_to_idx_path.open() as f:
        class_to_idx: dict[str, int] = json.load(f)
    with config_path.open() as f:
        train_config: dict = json.load(f)

    return class_to_idx, train_config, checkpoint_path


def resolve_device(device_arg: str) -> torch.device:
    if device_arg == "auto":
        return select_device()
    return torch.device(device_arg)


# ---------------------------------------------------------------------------
# Inline dataset (no subclassing) — keeps eval self-contained
# ---------------------------------------------------------------------------

class _EvalDataset(Dataset):
    """Minimal dataset for inference: reads image_path + label from a DataFrame."""

    def __init__(self, rows: pd.DataFrame, class_to_idx: dict[str, int], transform):
        self._rows = rows.reset_index(drop=True)
        self._class_to_idx = class_to_idx
        self._transform = transform

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, idx: int):
        row = self._rows.iloc[idx]
        image_path = Path(row["image_path"])
        label_idx = self._class_to_idx[row["image_type"]]
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            tensor = self._transform(img)
        return tensor, label_idx, idx  # return row index for joining back


# ---------------------------------------------------------------------------
# Metrics helpers
# ---------------------------------------------------------------------------

def precision_recall_f1(true_labels, pred_labels, class_idx: int):
    tp = sum(t == class_idx and p == class_idx for t, p in zip(true_labels, pred_labels))
    fp = sum(t != class_idx and p == class_idx for t, p in zip(true_labels, pred_labels))
    fn = sum(t == class_idx and p != class_idx for t, p in zip(true_labels, pred_labels))
    prec = tp / (tp + fp) if tp + fp > 0 else 0.0
    rec = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec > 0 else 0.0
    return prec, rec, f1


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    sorted_v = sorted(values)
    idx = (len(sorted_v) - 1) * p / 100.0
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_v) - 1)
    return sorted_v[lo] + (sorted_v[hi] - sorted_v[lo]) * (idx - lo)


def confidence_distribution(confidences: list[float]) -> dict:
    return {
        "min": round(min(confidences), 6),
        "p1": round(percentile(confidences, 1), 6),
        "p5": round(percentile(confidences, 5), 6),
        "p25": round(percentile(confidences, 25), 6),
        "median": round(percentile(confidences, 50), 6),
        "p75": round(percentile(confidences, 75), 6),
        "p95": round(percentile(confidences, 95), 6),
        "p99": round(percentile(confidences, 99), 6),
        "max": round(max(confidences), 6),
        "mean": round(sum(confidences) / len(confidences), 6),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    model_dir = Path(args.model_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load artifacts ────────────────────────────────────────────────────────
    class_to_idx, train_config, checkpoint_path = load_model_artifacts(model_dir)
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    num_classes = len(class_to_idx)
    backbone = train_config.get("backbone", "efficientnet_b0")
    image_size = train_config.get("image_size", 224)

    device = resolve_device(args.device)
    print(f"Device: {device}")
    print(f"Backbone: {backbone}  image_size: {image_size}")

    # ── Load model ────────────────────────────────────────────────────────────
    model = build_model(backbone_name=backbone, num_classes=num_classes, pretrained=False)
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    model.eval()
    print(f"Loaded checkpoint: {checkpoint_path}  (epoch {ckpt.get('epoch','?')}, "
          f"val_macro_f1={ckpt.get('val_macro_f1', float('nan')):.4f})")

    # ── Load split CSV and merge width/height from dataset index ─────────────
    split_csv = model_dir / f"{args.split}.csv"
    if not split_csv.exists():
        raise FileNotFoundError(f"Split CSV not found: {split_csv}")

    split_df = pd.read_csv(split_csv)
    print(f"Evaluating split: {args.split}  ({len(split_df)} rows)")
    print("  Classes:", split_df["image_type"].value_counts().to_dict())
    print("  Sources:", split_df["source_dataset"].value_counts().to_dict())

    # Merge width/height from the master dataset index
    if Path(DATASET_INDEX).exists():
        idx_df = pd.read_csv(DATASET_INDEX, usecols=["image_path", "width", "height"])
        split_df = split_df.merge(idx_df, on="image_path", how="left")
    else:
        split_df["width"] = None
        split_df["height"] = None

    # ── Build DataLoader ──────────────────────────────────────────────────────
    transform = get_eval_transforms(image_size)
    dataset = _EvalDataset(split_df, class_to_idx, transform)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
    )

    # ── Inference ─────────────────────────────────────────────────────────────
    all_row_indices: list[int] = []
    all_probs: list[list[float]] = []   # [n, num_classes]
    all_true: list[int] = []

    t_start = time.perf_counter()
    with torch.no_grad():
        for images, labels, row_indices in loader:
            images = images.to(device)
            logits = model(images)
            probs = torch.softmax(logits, dim=1).cpu()
            all_probs.extend(probs.tolist())
            all_true.extend(labels.tolist())
            all_row_indices.extend(row_indices.tolist())
    t_elapsed = time.perf_counter() - t_start
    ms_per_image = t_elapsed / len(dataset) * 1000

    # Reconstruct in original row order
    order = sorted(range(len(all_row_indices)), key=lambda i: all_row_indices[i])
    all_probs = [all_probs[i] for i in order]
    all_true = [all_true[i] for i in order]

    confidences = [max(p) for p in all_probs]
    predicted = [int(p.index(max(p))) for p in all_probs]

    print(f"Inference complete: {len(dataset)} images in {t_elapsed:.1f}s "
          f"({ms_per_image:.1f} ms/image)")

    # ── Per-class names ───────────────────────────────────────────────────────
    clin_idx = class_to_idx["clinical_macroscopic"]
    derm_idx = class_to_idx["dermoscopic"]

    # ── Core metrics ──────────────────────────────────────────────────────────
    n = len(all_true)
    correct_mask = [p == t for p, t in zip(predicted, all_true)]
    accuracy = sum(correct_mask) / n
    macro_f1 = compute_macro_f1(all_true, predicted, num_classes)
    bal_acc = compute_balanced_accuracy(all_true, predicted, num_classes)
    per_class_recall = compute_per_class_recalls(all_true, predicted, num_classes)

    clin_prec, clin_rec, clin_f1 = precision_recall_f1(all_true, predicted, clin_idx)
    derm_prec, derm_rec, derm_f1 = precision_recall_f1(all_true, predicted, derm_idx)

    # Confusion matrix: [true_clin→pred_clin, true_clin→pred_derm, true_derm→pred_clin, true_derm→pred_derm]
    tp_clin = sum(t == clin_idx and p == clin_idx for t, p in zip(all_true, predicted))
    fp_clin = sum(t == derm_idx and p == clin_idx for t, p in zip(all_true, predicted))  # derm→clin (wrong)
    fn_clin = sum(t == clin_idx and p == derm_idx for t, p in zip(all_true, predicted))  # clin→derm (wrong)
    tp_derm = sum(t == derm_idx and p == derm_idx for t, p in zip(all_true, predicted))

    # ── Confidence distribution ───────────────────────────────────────────────
    conf_all = confidence_distribution(confidences)
    clin_confs = [confidences[i] for i, t in enumerate(all_true) if t == clin_idx]
    derm_confs = [confidences[i] for i, t in enumerate(all_true) if t == derm_idx]
    conf_clin = confidence_distribution(clin_confs) if clin_confs else {}
    conf_derm = confidence_distribution(derm_confs) if derm_confs else {}

    # ── Save predictions CSV ──────────────────────────────────────────────────
    pred_rows = []
    for i in range(n):
        row = split_df.iloc[i]
        pred_rows.append({
            "image_path": row["image_path"],
            "source_dataset": row.get("source_dataset", ""),
            "true_image_type": idx_to_class[all_true[i]],
            "predicted_image_type": idx_to_class[predicted[i]],
            "confidence": round(confidences[i], 6),
            "clinical_macroscopic_probability": round(all_probs[i][clin_idx], 6),
            "dermoscopic_probability": round(all_probs[i][derm_idx], 6),
            "correct": correct_mask[i],
            "width": row.get("width", ""),
            "height": row.get("height", ""),
        })

    pred_csv_path = output_dir / "image_type_classifier_predictions.csv"
    _write_csv(pred_csv_path, pred_rows)
    print(f"Saved predictions: {pred_csv_path}")

    # ── Save misclassified examples ───────────────────────────────────────────
    misclassified = [r for r in pred_rows if not r["correct"]]
    misc_path = output_dir / "image_type_classifier_misclassified_examples.csv"
    _write_csv(misc_path, misclassified, fieldnames=_MISCLASSIFIED_FIELDNAMES)
    print(f"Misclassified examples: {len(misclassified)} → {misc_path}")

    # ── Save confusion matrix CSV ─────────────────────────────────────────────
    cm_rows = [
        {"true \\ predicted": "clinical_macroscopic",
         "clinical_macroscopic": tp_clin, "dermoscopic": fn_clin},
        {"true \\ predicted": "dermoscopic",
         "clinical_macroscopic": fp_clin, "dermoscopic": tp_derm},
    ]
    cm_path = output_dir / "image_type_classifier_confusion_matrix.csv"
    _write_csv(cm_path, cm_rows)

    # ── Threshold analysis ────────────────────────────────────────────────────
    threshold_rows = []
    for thresh in sorted(args.thresholds):
        accepted_mask = [c >= thresh for c in confidences]
        accepted_indices = [i for i, a in enumerate(accepted_mask) if a]
        rejected_indices = [i for i, a in enumerate(accepted_mask) if not a]

        accepted_count = len(accepted_indices)
        rejected_count = len(rejected_indices)
        coverage = accepted_count / n if n > 0 else 0.0

        if accepted_count > 0:
            acc_true = [all_true[i] for i in accepted_indices]
            acc_pred = [predicted[i] for i in accepted_indices]
            acc_correct = sum(t == p for t, p in zip(acc_true, acc_pred))
            acc_accuracy = acc_correct / accepted_count
            acc_macro_f1 = compute_macro_f1(acc_true, acc_pred, num_classes)
            wrong_clin_to_derm = sum(
                t == clin_idx and p == derm_idx for t, p in zip(acc_true, acc_pred)
            )
            wrong_derm_to_clin = sum(
                t == derm_idx and p == clin_idx for t, p in zip(acc_true, acc_pred)
            )
        else:
            acc_accuracy = float("nan")
            acc_macro_f1 = float("nan")
            wrong_clin_to_derm = 0
            wrong_derm_to_clin = 0

        rej_correct = sum(correct_mask[i] for i in rejected_indices)
        rej_incorrect = sum(not correct_mask[i] for i in rejected_indices)

        threshold_rows.append({
            "threshold": thresh,
            "total": n,
            "accepted_count": accepted_count,
            "rejected_as_uncertain_or_unsupported_count": rejected_count,
            "accepted_coverage": round(coverage, 6),
            "accepted_accuracy": round(acc_accuracy, 6) if acc_count_ok(accepted_count) else "",
            "accepted_macro_f1": round(acc_macro_f1, 6) if acc_count_ok(accepted_count) else "",
            "wrong_accepted_clinical_to_dermoscopic": wrong_clin_to_derm,
            "wrong_accepted_dermoscopic_to_clinical": wrong_derm_to_clin,
            "rejected_correct_count": rej_correct,
            "rejected_incorrect_count": rej_incorrect,
            "notes": _threshold_note(thresh, coverage, wrong_clin_to_derm + wrong_derm_to_clin),
        })

    thresh_path = output_dir / "image_type_classifier_threshold_analysis.csv"
    _write_csv(thresh_path, threshold_rows)
    print(f"Saved threshold analysis: {thresh_path}")

    # ── Print threshold table ─────────────────────────────────────────────────
    print("\nThreshold analysis:")
    print(f"{'thresh':>8}  {'accepted':>9}  {'coverage':>9}  {'acc_acc':>8}  "
          f"{'macro_f1':>9}  {'wrong':>6}  {'rejected':>9}")
    for r in threshold_rows:
        print(f"{r['threshold']:>8.2f}  {r['accepted_count']:>9}  "
              f"{r['accepted_coverage']:>9.4f}  "
              f"{r['accepted_accuracy'] if r['accepted_accuracy'] != '' else 'N/A':>8}  "
              f"{r['accepted_macro_f1'] if r['accepted_macro_f1'] != '' else 'N/A':>9}  "
              f"{r['wrong_accepted_clinical_to_dermoscopic'] + r['wrong_accepted_dermoscopic_to_clinical']:>6}  "
              f"{r['rejected_as_uncertain_or_unsupported_count']:>9}")

    # ── Save metrics JSON ─────────────────────────────────────────────────────
    metrics = {
        "model_dir": str(model_dir),
        "checkpoint_path": str(checkpoint_path),
        "evaluated_split": args.split,
        "test_row_count": n,
        "class_counts": split_df["image_type"].value_counts().to_dict(),
        "source_counts": split_df["source_dataset"].value_counts().to_dict(),
        "accuracy": round(accuracy, 6),
        "macro_f1": round(macro_f1, 6),
        "balanced_accuracy": round(bal_acc, 6),
        "per_class": {
            "clinical_macroscopic": {
                "precision": round(clin_prec, 6),
                "recall": round(clin_rec, 6),
                "f1": round(clin_f1, 6),
            },
            "dermoscopic": {
                "precision": round(derm_prec, 6),
                "recall": round(derm_rec, 6),
                "f1": round(derm_f1, 6),
            },
        },
        "confusion_matrix": {
            "true_clinical_pred_clinical": tp_clin,
            "true_clinical_pred_dermoscopic": fn_clin,
            "true_dermoscopic_pred_clinical": fp_clin,
            "true_dermoscopic_pred_dermoscopic": tp_derm,
        },
        "false_clinical_to_dermoscopic": fn_clin,
        "false_dermoscopic_to_clinical": fp_clin,
        "total_misclassified": len(misclassified),
        "runtime_ms_per_image": round(ms_per_image, 3),
        "confidence_distribution_all": conf_all,
        "confidence_distribution_by_class": {
            "clinical_macroscopic": conf_clin,
            "dermoscopic": conf_derm,
        },
    }
    metrics_path = output_dir / "image_type_classifier_metrics.json"
    with metrics_path.open("w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics: {metrics_path}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n── Test results ──────────────────────────────────────────────────")
    print(f"  accuracy:        {accuracy:.4f}")
    print(f"  macro_f1:        {macro_f1:.4f}")
    print(f"  balanced_acc:    {bal_acc:.4f}")
    print(f"  clinical prec/rec/f1: {clin_prec:.4f} / {clin_rec:.4f} / {clin_f1:.4f}")
    print(f"  dermoscopic prec/rec/f1: {derm_prec:.4f} / {derm_rec:.4f} / {derm_f1:.4f}")
    print(f"  confusion matrix:  TP_clin={tp_clin}  FN_clin→derm={fn_clin}  "
          f"FP_derm→clin={fp_clin}  TP_derm={tp_derm}")
    print(f"  misclassified:   {len(misclassified)}")
    print(f"  runtime:         {ms_per_image:.1f} ms/image")
    print()


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def acc_count_ok(count: int) -> bool:
    return count > 0 and count == count  # always True when count > 0


def _threshold_note(thresh: float, coverage: float, wrong: int) -> str:
    if coverage == 0.0:
        return "rejects all"
    if coverage == 1.0:
        return "accepts all"
    if wrong == 0:
        return f"zero wrong accepted at {thresh:.0%} coverage {coverage:.2%}"
    return f"{wrong} wrong accepted"


_MISCLASSIFIED_FIELDNAMES = [
    "image_path", "source_dataset", "true_image_type", "predicted_image_type",
    "confidence", "clinical_macroscopic_probability", "dermoscopic_probability",
    "correct", "width", "height",
]


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    cols = fieldnames or (list(rows[0].keys()) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        if rows:
            writer.writerows(rows)


if __name__ == "__main__":
    main()
