"""V2.18 — Build the Clinical V2 backbone comparison table, plots, and summary.

Loads the per-backbone eval JSON produced by ``evaluate_clinical_v2.py``, measures
inference latency on the frozen test split, computes safety-relevant confusion
metrics, applies the issue #159 promotion criteria, and writes:

- outputs/metrics/clinical_v2_backbone_comparison_table.csv
- outputs/plots/clinical_v2_backbone_comparison_cm.png
- outputs/plots/clinical_v2_backbone_training_curves.png
- docs/model/clinical_v2_backbone_comparison_summary.md

This is an educational model-evaluation utility. The lesion class is a routing
output for dermoscopic review, not cancer detection. No model is promoted in code.
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path

import torch
import yaml
from torch.utils.data import DataLoader

from src.data.dataset import ImageClassificationDataset
from src.data.transforms import get_eval_transforms
from src.model.evaluate_clinical_v2 import load_class_to_idx, select_device
from src.model.model import build_model

TEST_PATH = Path("data/processed/clinical_v2/test.csv")
CLASS_NAMES = [
    "Eczema / dermatitis",
    "Urticaria / allergic reaction",
    "Folliculitis / acne-like",
    "Psoriasis / papulosquamous",
    "Lesion — dermoscopic review recommended",
]
LESION_IDX = CLASS_NAMES.index("Lesion — dermoscopic review recommended")
ECZEMA_IDX = CLASS_NAMES.index("Eczema / dermatitis")
URTICARIA_IDX = CLASS_NAMES.index("Urticaria / allergic reaction")

# Frozen baseline thresholds from issue #159 (no rounding).
BASELINE_THRESHOLDS = {
    "combined_macro_f1": 0.6420,
    "balanced_accuracy": 0.6571,
    "scin_macro_f1": 0.4028,
    "scin_error_rate": 0.4278,
    "fitzpatrick_macro_f1": 0.6366,
    "lesion_routing_fn": 76,
}

VARIANTS = {
    "effnet_b0_baseline": {
        "config": "config/clinical_v2_config.yaml",
        "prefix": "clinical_v2_effnet_b0_baseline",
        "backbone": "efficientnet_b0",
        "image_size": 224,
        "checkpoint": "models/clinical_v2_effnet_b0/best_model.pth",
    },
    "effnet_b2": {
        "config": "config/clinical_v2_effnet_b2_config.yaml",
        "prefix": "clinical_v2_effnet_b2",
        "backbone": "efficientnet_b2",
        "image_size": 260,
        "checkpoint": "models/clinical_v2_effnet_b2/best_model.pth",
    },
    "convnext_tiny": {
        "config": "config/clinical_v2_convnext_tiny_config.yaml",
        "prefix": "clinical_v2_convnext_tiny",
        "backbone": "convnext_tiny",
        "image_size": 224,
        "checkpoint": "models/clinical_v2_convnext_tiny/best_model.pth",
    },
}


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def load_eval_json(prefix: str) -> dict:
    path = Path(f"outputs/metrics/{prefix}_test_metrics.json")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def source_macro_f1(eval_json: dict, source_name: str) -> float:
    for row in eval_json["source_metrics"]:
        if row["source_dataset"] == source_name:
            return float(row["macro_f1"])
    raise KeyError(source_name)


def source_error_rate(eval_json: dict, source_name: str) -> float:
    for row in eval_json["source_metrics"]:
        if row["source_dataset"] == source_name:
            return 1.0 - float(row["accuracy"])
    raise KeyError(source_name)


def confusion_derived(cm: list[list[int]]) -> dict:
    lesion_row = cm[LESION_IDX]
    lesion_fn = sum(lesion_row) - lesion_row[LESION_IDX]
    eczema_to_urticaria = cm[ECZEMA_IDX][URTICARIA_IDX]
    urticaria_fp = sum(cm[r][URTICARIA_IDX] for r in range(len(cm))) - cm[URTICARIA_IDX][URTICARIA_IDX]
    return {
        "lesion_routing_fn": int(lesion_fn),
        "eczema_to_urticaria": int(eczema_to_urticaria),
        "urticaria_fp": int(urticaria_fp),
    }


def measure_inference_ms(vcfg: dict, device: torch.device, num_classes: int) -> tuple[float, int]:
    config = yaml.safe_load(Path(vcfg["config"]).read_text(encoding="utf-8"))
    model_dir = Path(config["training"]["output_dir"])
    class_to_idx = load_class_to_idx(model_dir / "class_to_idx.json")

    dataset = ImageClassificationDataset(
        csv_path=TEST_PATH,
        class_to_idx=class_to_idx,
        transform=get_eval_transforms(vcfg["image_size"]),
        label_column="target_label",
        class_idx_column="class_idx",
    )
    loader = DataLoader(dataset, batch_size=config["training"]["batch_size"], shuffle=False, num_workers=0)

    checkpoint = torch.load(vcfg["checkpoint"], map_location="cpu")
    model = build_model(backbone_name=vcfg["backbone"], num_classes=num_classes, pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    # Warm-up batch (MPS/GPU kernels compile lazily).
    with torch.no_grad():
        for images, _ in loader:
            model(images.to(device))
            break

    count = 0
    start = time.time()
    with torch.no_grad():
        for images, _ in loader:
            model(images.to(device))
            count += images.size(0)
    if device.type == "mps":
        torch.mps.synchronize()
    elapsed = time.time() - start
    return (elapsed / count) * 1000.0, count


def build_results() -> dict:
    test_hash = file_hash(TEST_PATH)
    device = select_device()
    num_classes = len(CLASS_NAMES)
    results: dict[str, dict] = {}

    for name, vcfg in VARIANTS.items():
        eval_json = load_eval_json(vcfg["prefix"])
        cm = eval_json["confusion_matrix"]
        derived = confusion_derived(cm)
        ms_per_image, count = measure_inference_ms(vcfg, device, num_classes)
        assert file_hash(TEST_PATH) == test_hash, f"Test hash changed during {name} timing — STOP"
        assert count == 1515, f"Prediction count mismatch for {name}: {count}"

        results[name] = {
            "combined_accuracy": eval_json["test_accuracy"],
            "combined_macro_f1": eval_json["macro_f1"],
            "balanced_accuracy": eval_json["balanced_accuracy"],
            "scin_macro_f1": source_macro_f1(eval_json, "google_scin"),
            "scin_error_rate": source_error_rate(eval_json, "google_scin"),
            "fitzpatrick_macro_f1": source_macro_f1(eval_json, "fitzpatrick17k"),
            "fitzpatrick_error_rate": source_error_rate(eval_json, "fitzpatrick17k"),
            "lesion_routing_fn": derived["lesion_routing_fn"],
            "eczema_to_urticaria": derived["eczema_to_urticaria"],
            "urticaria_fp": derived["urticaria_fp"],
            "inference_ms_per_image": round(ms_per_image, 2),
            "confusion_matrix": cm,
            "class_report": eval_json["class_report"],
        }
    return results, test_hash, device


def param_counts() -> dict:
    counts = {}
    for name, vcfg in VARIANTS.items():
        m = build_model(backbone_name=vcfg["backbone"], num_classes=len(CLASS_NAMES), pretrained=False)
        total = sum(p.numel() for p in m.parameters()) / 1e6
        counts[name] = {"params_m": round(total, 1), "image_size": vcfg["image_size"]}
    return counts


def write_comparison_csv(results: dict) -> None:
    metrics = [
        "combined_accuracy", "combined_macro_f1", "balanced_accuracy",
        "scin_macro_f1", "scin_error_rate", "fitzpatrick_macro_f1",
        "fitzpatrick_error_rate", "lesion_routing_fn", "eczema_to_urticaria",
        "urticaria_fp", "inference_ms_per_image",
    ]
    base = results["effnet_b0_baseline"]
    variant_names = [v for v in results if v != "effnet_b0_baseline"]
    out = Path("outputs/metrics/clinical_v2_backbone_comparison_table.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        header = ["metric", "effnet_b0_baseline"] + variant_names + [f"{v}_delta_vs_b0" for v in variant_names]
        writer.writerow(header)
        for metric in metrics:
            row = [metric, base[metric]]
            row += [results[v][metric] for v in variant_names]
            row += [round(results[v][metric] - base[metric], 4) for v in variant_names]
            writer.writerow(row)
    print(f"Saved: {out}")


def promotion_verdict(results: dict) -> dict:
    verdicts = {}
    for name in results:
        if name == "effnet_b0_baseline":
            continue
        r = results[name]
        checks = {
            "combined_macro_f1 >= 0.6420": r["combined_macro_f1"] >= BASELINE_THRESHOLDS["combined_macro_f1"] - 0.005,
            "balanced_accuracy >= 0.6571": r["balanced_accuracy"] >= BASELINE_THRESHOLDS["balanced_accuracy"] - 0.005,
            "scin improves (macro_f1>0.4028 or err<0.4278)": (
                r["scin_macro_f1"] > BASELINE_THRESHOLDS["scin_macro_f1"]
                or r["scin_error_rate"] < BASELINE_THRESHOLDS["scin_error_rate"]
            ),
            "lesion_routing_fn <= 76": r["lesion_routing_fn"] <= BASELINE_THRESHOLDS["lesion_routing_fn"],
        }
        verdicts[name] = {
            "checks": checks,
            "promotable": all(checks.values()),
        }
    return verdicts


def plot_confusion_grid(results: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    names = list(results.keys())
    fig, axes = plt.subplots(1, len(names), figsize=(7 * len(names), 6))
    short = ["Eczema", "Urticaria", "Follic.", "Psoriasis", "Lesion"]
    for ax, name in zip(axes, names):
        cm = np.array(results[name]["confusion_matrix"], dtype=float)
        cm_norm = cm / cm.sum(axis=1, keepdims=True)
        im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
        for i in range(len(short)):
            for j in range(len(short)):
                ax.text(j, i, f"{cm_norm[i, j]:.2f}", ha="center", va="center",
                        color="white" if cm_norm[i, j] > 0.5 else "black", fontsize=8)
        ax.set_xticks(range(len(short))); ax.set_xticklabels(short, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(short))); ax.set_yticklabels(short, fontsize=8)
        r = results[name]
        ax.set_title(f"{name}\nmacro-F1={r['combined_macro_f1']:.4f} | FN={r['lesion_routing_fn']} | "
                     f"{r['inference_ms_per_image']}ms/img", fontsize=9)
        ax.set_ylabel("True"); ax.set_xlabel("Predicted")
    fig.suptitle("Clinical V2 Backbone Comparison — Row-Normalized Confusion Matrices "
                 "(non-diagnostic; lesion = routing)", fontsize=11, y=1.02)
    plt.tight_layout()
    out = Path("outputs/plots/clinical_v2_backbone_comparison_cm.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Saved: {out}")


def plot_training_curves() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    histories = {
        "effnet_b0_baseline": "models/clinical_v2_effnet_b0/training_history.csv",
        "effnet_b2": "models/clinical_v2_effnet_b2/training_history.csv",
        "convnext_tiny": "models/clinical_v2_convnext_tiny/training_history.csv",
    }
    colors = {"effnet_b0_baseline": "gray", "effnet_b2": "blue", "convnext_tiny": "orange"}
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for name, path in histories.items():
        if not Path(path).exists():
            continue
        log = pd.read_csv(path)
        axes[0].plot(log["epoch"], log["val_loss"], label=name, color=colors.get(name), marker="o")
        axes[1].plot(log["epoch"], log["val_macro_f1"], label=name, color=colors.get(name), marker="o")
    axes[0].set_title("Val Loss per Epoch"); axes[0].set_xlabel("epoch"); axes[0].legend()
    axes[1].set_title("Val Macro-F1 per Epoch (promotion metric)"); axes[1].set_xlabel("epoch")
    axes[1].axhline(y=0.6420, color="red", linestyle="--", linewidth=1, label="B0 baseline 0.6420")
    axes[1].legend()
    fig.suptitle("Clinical V2 Backbone Training Curves")
    plt.tight_layout()
    out = Path("outputs/plots/clinical_v2_backbone_training_curves.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Saved: {out}")


def main() -> None:
    results, test_hash, device = build_results()
    counts = param_counts()
    verdicts = promotion_verdict(results)

    print(f"\nTest hash: {test_hash} (1515 rows)")
    print(f"Device: {device}\n")
    for name, r in results.items():
        print(f"{name}: macro-F1={r['combined_macro_f1']:.4f} | bal_acc={r['balanced_accuracy']:.4f} | "
              f"SCIN={r['scin_macro_f1']:.4f} | Fitz={r['fitzpatrick_macro_f1']:.4f} | "
              f"lesion_FN={r['lesion_routing_fn']} | ecz->urt={r['eczema_to_urticaria']} | "
              f"urt_FP={r['urticaria_fp']} | {r['inference_ms_per_image']}ms/img")
    print()
    for name, v in verdicts.items():
        print(f"{name}: {'PROMOTABLE CANDIDATE' if v['promotable'] else 'NOT PROMOTABLE'}")
        for check, ok in v["checks"].items():
            print(f"    [{'PASS' if ok else 'FAIL'}] {check}")

    write_comparison_csv(results)
    plot_confusion_grid(results)
    plot_training_curves()

    # Persist a machine-readable bundle next to the CSV for the summary writer.
    bundle = {
        "test_hash": test_hash,
        "device": str(device),
        "param_counts": counts,
        "results": {k: {m: v for m, v in r.items() if m not in ("confusion_matrix", "class_report")}
                    for k, r in results.items()},
        "verdicts": verdicts,
    }
    Path("outputs/metrics/clinical_v2_backbone_comparison_bundle.json").write_text(
        json.dumps(bundle, indent=2), encoding="utf-8"
    )
    print("Saved: outputs/metrics/clinical_v2_backbone_comparison_bundle.json")


if __name__ == "__main__":
    main()
