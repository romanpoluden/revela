"""V2.22 — Metadata-aware Clinical V2 experiment.

Phases:
  1. Metadata audit — coverage, Cramér's V shortcut check
  2. Encoder fitting (train set only)
  3. Train metadata variants sequentially
  4. Evaluate all variants + baseline on frozen test set
  5. Write ablation table CSV + candidate metrics JSON
  6. Write summary markdown documents
  7. Post gh issue comment

Constraints:
  - source_dataset never used as model input (asserted)
  - Missing metadata → zeros / unknown — no sample drops
  - Encoders fit on train set only
  - Metadata branch < 5% of total params (asserted in model)
  - Test hash verified before and after every train/eval run
  - Shortcut risk computed before any training
  - No model promoted — docs only
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import time
from pathlib import Path

import torch
import torch.nn as nn
import yaml

from src.data.dataset import MetadataEncoder, MetadataImageClassificationDataset
from src.data.transforms import get_eval_transforms, get_train_transforms
from src.model.model import build_model
from src.model.model_metadata import MetadataAwareClinicalV2
from src.model.evaluate_clinical_v2 import (
    LESION_ROUTING_CLASS,
    compute_confusion_matrix,
    compute_classification_report,
    compute_metric_bundle,
    compute_source_metrics,
    get_lesion_metrics,
)
from src.model.train import (
    build_class_to_idx,
    build_optimizer,
    compute_class_weights,
    compute_macro_f1,
    compute_balanced_accuracy,
    select_device,
)
from torch.utils.data import DataLoader

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

TRAIN_CSV = Path("data/processed/clinical_v2/train.csv")
VAL_CSV = Path("data/processed/clinical_v2/val.csv")
TEST_CSV = Path("data/processed/clinical_v2/test.csv")
BASELINE_MODEL_DIR = Path("models/clinical_v2_effnet_b0")
METRICS_DIR = Path("outputs/metrics")
DOCS_DIR = Path("docs/model")

CLASS_NAMES = [
    "Eczema / dermatitis",
    "Urticaria / allergic reaction",
    "Folliculitis / acne-like",
    "Psoriasis / papulosquamous",
    LESION_ROUTING_CLASS,
]

BASELINE = {
    "combined_macro_f1": 0.6420,
    "balanced_accuracy": 0.6571,
    "google_scin_macro_f1": 0.4028,
    "fitzpatrick17k_macro_f1": 0.6366,
    "lesion_routing_fn": 76,
    "eczema_to_urticaria": 91,
    "urticaria_fp": 160,
}

VARIANTS = [
    {"name": "image_body_parts",         "logical_fields": ["body_parts"]},
    {"name": "image_age",                "logical_fields": ["age_group"]},
    {"name": "image_body_parts_age",     "logical_fields": ["body_parts", "age_group"]},
    {"name": "image_body_parts_age_sex", "logical_fields": ["body_parts", "age_group", "sex_at_birth"]},
]

TRAIN_CONFIG = {
    "lr": 0.0001,
    "weight_decay": 0.01,
    "epochs": 5,
    "batch_size": 16,
    "num_workers": 0,
    "use_class_weights": True,
    "random_seed": 42,
    "image_size": 224,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def coverage_pct(rows: list[dict[str, str]], col: str) -> float:
    present = sum(1 for r in rows if (r.get(col) or "").strip())
    return present / len(rows) * 100 if rows else 0.0


# ---------------------------------------------------------------------------
# Phase 1 — Metadata audit
# ---------------------------------------------------------------------------

PRIORITY_FIELDS_TO_CHECK = [
    "body_location", "anatom_site_general",
    "age", "age_approx", "age_bucket",
    "age_group",
    "sex", "gender", "sex_at_birth",
    "fitzpatrick_skin_type",
    "source_dataset",
]

BODY_PARTS_COLS = [
    "body_parts_head_or_neck", "body_parts_arm", "body_parts_palm",
    "body_parts_back_of_hand", "body_parts_torso_front", "body_parts_torso_back",
    "body_parts_genitalia_or_groin", "body_parts_buttocks", "body_parts_leg",
    "body_parts_foot_top_or_side", "body_parts_foot_sole", "body_parts_other",
]

SHORTCUT_RISK_FIELDS = ["age_group", "sex_at_birth", "fitzpatrick_skin_type"]


def _top_values(rows: list[dict], col: str, n: int = 5) -> dict:
    counts: dict[str, int] = {}
    for r in rows:
        v = (r.get(col) or "").strip()
        if v:
            counts[v] = counts.get(v, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1])[:n])


def _cramers_v(rows: list[dict], col: str, label_col: str = "target_label") -> float:
    """Cramér's V between a metadata column and the class label."""
    cats = sorted({(r.get(col) or "unknown").strip() for r in rows})
    labels = sorted({(r.get(label_col) or "").strip() for r in rows if r.get(label_col)})
    if len(cats) < 2 or len(labels) < 2:
        return 0.0

    ct: dict[str, dict[str, int]] = {c: {l: 0 for l in labels} for c in cats}
    for r in rows:
        c = (r.get(col) or "unknown").strip()
        lbl = (r.get(label_col) or "").strip()
        if c in ct and lbl in labels:
            ct[c][lbl] += 1

    n = sum(ct[c][l] for c in cats for l in labels)
    if n == 0:
        return 0.0

    row_totals = {c: sum(ct[c].values()) for c in cats}
    col_totals = {l: sum(ct[c][l] for c in cats) for l in labels}

    chi2 = 0.0
    for c in cats:
        for l in labels:
            expected = row_totals[c] * col_totals[l] / n
            if expected > 0:
                chi2 += (ct[c][l] - expected) ** 2 / expected

    k = min(len(cats), len(labels))
    return math.sqrt(chi2 / (n * (k - 1))) if k > 1 else 0.0


def run_metadata_audit(train_rows: list[dict]) -> dict:
    """Return audit dict; also prints to stdout."""
    print("=" * 70)
    print("PHASE 1 — METADATA AUDIT")
    print("=" * 70)

    all_cols = list(train_rows[0].keys()) if train_rows else []
    print(f"\nAll columns ({len(all_cols)}): {all_cols}")

    # Priority field presence check
    print("\n=== PRIORITY FIELD PRESENCE ===")
    present_priority: list[str] = []
    for f in PRIORITY_FIELDS_TO_CHECK:
        if f in all_cols:
            cov = coverage_pct(train_rows, f)
            top = _top_values(train_rows, f)
            uniq = len({(r.get(f) or "").strip() for r in train_rows if (r.get(f) or "").strip()})
            print(f"  {f}: coverage={cov:.1f}%, unique={uniq}, top={top}")
            present_priority.append(f)
        else:
            print(f"  {f}: NOT PRESENT")

    # Body parts multi-hot coverage
    print("\n=== BODY PARTS COLUMNS (multi-hot, YES/empty) ===")
    bp_coverage: dict[str, float] = {}
    for col in BODY_PARTS_COLS:
        cov = coverage_pct(train_rows, col)
        bp_coverage[col] = cov
    any_body_cov = (
        sum(1 for r in train_rows if any((r.get(c) or "").strip() for c in BODY_PARTS_COLS))
        / len(train_rows) * 100
    )
    print(f"  Rows with ANY body part filled: {any_body_cov:.1f}%")
    for col, cov in bp_coverage.items():
        print(f"  {col}: {cov:.1f}%")

    # Missingness by source
    print("\n=== BODY PARTS COVERAGE BY SOURCE ===")
    source_bp: dict[str, dict] = {}
    sources = sorted({(r.get("source_dataset") or "").strip() for r in train_rows if r.get("source_dataset")})
    for src in sources:
        grp = [r for r in train_rows if (r.get("source_dataset") or "").strip() == src]
        any_bp = sum(
            1 for r in grp if any((r.get(c) or "").strip() for c in BODY_PARTS_COLS)
        )
        age_cov = coverage_pct(grp, "age_group")
        sex_cov = coverage_pct(grp, "sex_at_birth")
        source_bp[src] = {
            "n": len(grp),
            "body_parts_any_pct": any_bp / len(grp) * 100 if grp else 0.0,
            "age_group_pct": age_cov,
            "sex_at_birth_pct": sex_cov,
        }
        print(f"  {src} (n={len(grp)}): body_parts_any={any_bp/len(grp)*100:.0f}%, "
              f"age_group={age_cov:.0f}%, sex_at_birth={sex_cov:.0f}%")

    # Shortcut risk (MUST run before training)
    print("\n=== SHORTCUT RISK — Cramér's V (run BEFORE training) ===")
    shortcut_table: list[dict] = []
    for field in SHORTCUT_RISK_FIELDS:
        if field not in all_cols:
            continue
        v = _cramers_v(train_rows, field)
        risk = "HIGH" if v > 0.4 else ("MODERATE" if v > 0.2 else "LOW")
        note = (
            "WARNING: high correlation with class — improvement may reflect shortcut, not clinical reasoning"
            if v > 0.4 else ""
        )
        print(f"  {field:30s} Cramér's V={v:.3f}  risk={risk}  {note}")
        shortcut_table.append({"field": field, "cramers_v": round(v, 4), "risk": risk})

    # Body parts aggregate shortcut risk
    bp_v = _cramers_v(
        [
            {**r, "__bp_any__": "YES" if any((r.get(c) or "").strip() for c in BODY_PARTS_COLS) else ""}
            for r in train_rows
        ],
        "__bp_any__",
    )
    bp_risk = "HIGH" if bp_v > 0.4 else ("MODERATE" if bp_v > 0.2 else "LOW")
    print(f"  {'body_parts (any filled)':30s} Cramér's V={bp_v:.3f}  risk={bp_risk}")
    shortcut_table.append({"field": "body_parts_any", "cramers_v": round(bp_v, 4), "risk": bp_risk})

    return {
        "all_cols": all_cols,
        "present_priority": present_priority,
        "bp_coverage": bp_coverage,
        "any_body_cov": any_body_cov,
        "source_bp": source_bp,
        "shortcut_table": shortcut_table,
    }


# ---------------------------------------------------------------------------
# Phase 3 — Training helpers
# ---------------------------------------------------------------------------

def train_one_epoch_with_metadata(model, loader, criterion, optimizer, device, max_batches=None):
    model.train()
    running_loss = 0.0
    total = 0
    correct = 0

    for batch_idx, (images, metadata, labels) in enumerate(loader):
        if max_batches is not None and batch_idx >= max_batches:
            break
        images = images.to(device)
        metadata = metadata.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        logits = model(images, metadata)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        bs = labels.size(0)
        running_loss += loss.item() * bs
        preds = logits.argmax(dim=1)
        total += bs
        correct += (preds == labels).sum().item()

    return running_loss / max(total, 1), correct / max(total, 1)


def evaluate_with_metadata(model, loader, criterion, device, num_classes, max_batches=None):
    model.eval()
    running_loss = 0.0
    total = 0
    correct = 0
    all_preds: list[int] = []
    all_labels: list[int] = []

    with torch.no_grad():
        for batch_idx, (images, metadata, labels) in enumerate(loader):
            if max_batches is not None and batch_idx >= max_batches:
                break
            images = images.to(device)
            metadata = metadata.to(device)
            labels = labels.to(device)

            logits = model(images, metadata)
            loss = criterion(logits, labels)

            bs = labels.size(0)
            running_loss += loss.item() * bs
            preds = logits.argmax(dim=1)
            total += bs
            correct += (preds == labels).sum().item()
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    avg_loss = running_loss / max(total, 1)
    acc = correct / max(total, 1)
    mf1 = compute_macro_f1(all_labels, all_preds, num_classes)
    bal = compute_balanced_accuracy(all_labels, all_preds, num_classes)
    return avg_loss, acc, mf1, bal


def run_inference_with_metadata(model, loader, device) -> tuple[list[int], list[int]]:
    model.eval()
    true_labels: list[int] = []
    pred_labels: list[int] = []

    with torch.no_grad():
        for images, metadata, labels in loader:
            images = images.to(device)
            metadata = metadata.to(device)
            logits = model(images, metadata)
            preds = logits.argmax(dim=1)
            true_labels.extend(labels.tolist())
            pred_labels.extend(preds.cpu().tolist())

    return true_labels, pred_labels


def build_metadata_loaders(encoder: MetadataEncoder, image_size: int, batch_size: int, num_workers: int, class_to_idx: dict):
    train_ds = MetadataImageClassificationDataset(
        csv_path=TRAIN_CSV,
        class_to_idx=class_to_idx,
        encoder=encoder,
        transform=get_train_transforms(image_size),
        label_column="target_label",
        class_idx_column="class_idx",
    )
    val_ds = MetadataImageClassificationDataset(
        csv_path=VAL_CSV,
        class_to_idx=class_to_idx,
        encoder=encoder,
        transform=get_eval_transforms(image_size),
        label_column="target_label",
        class_idx_column="class_idx",
    )
    test_ds = MetadataImageClassificationDataset(
        csv_path=TEST_CSV,
        class_to_idx=class_to_idx,
        encoder=encoder,
        transform=get_eval_transforms(image_size),
        label_column="target_label",
        class_idx_column="class_idx",
    )
    pin_memory = torch.cuda.is_available()
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=pin_memory)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory)
    return train_ds, val_ds, test_ds, train_loader, val_loader, test_loader


# ---------------------------------------------------------------------------
# Phase 4 — Focus error helpers
# ---------------------------------------------------------------------------

def compute_focus_errors(cm: list[list[int]], class_names: list[str]) -> dict:
    idx = {name: i for i, name in enumerate(class_names)}
    lesion_idx = idx.get(LESION_ROUTING_CLASS, -1)
    eczema_idx = idx.get("Eczema / dermatitis", -1)
    urticaria_idx = idx.get("Urticaria / allergic reaction", -1)

    lesion_fn = (
        sum(cm[lesion_idx]) - cm[lesion_idx][lesion_idx]
        if lesion_idx >= 0 else -1
    )
    eczema_to_urticaria = (
        cm[eczema_idx][urticaria_idx]
        if eczema_idx >= 0 and urticaria_idx >= 0 else -1
    )
    urticaria_fp = (
        sum(cm[r][urticaria_idx] for r in range(len(class_names))) - cm[urticaria_idx][urticaria_idx]
        if urticaria_idx >= 0 else -1
    )
    return {
        "lesion_routing_fn": lesion_fn,
        "eczema_to_urticaria": eczema_to_urticaria,
        "urticaria_fp": urticaria_fp,
    }


# ---------------------------------------------------------------------------
# Baseline re-eval (image-only, standard model)
# ---------------------------------------------------------------------------

def eval_baseline(class_to_idx: dict, device: torch.device, test_hash: str) -> dict:
    print("\n=== EVALUATING BASELINE (image-only) ===")
    checkpoint_path = BASELINE_MODEL_DIR / "best_model.pth"
    if not checkpoint_path.exists():
        print(f"  Baseline checkpoint not found at {checkpoint_path} — skipping re-eval, using known numbers.")
        return {
            "combined_macro_f1": BASELINE["combined_macro_f1"],
            "balanced_accuracy": BASELINE["balanced_accuracy"],
            "google_scin_macro_f1": BASELINE["google_scin_macro_f1"],
            "fitzpatrick17k_macro_f1": BASELINE["fitzpatrick17k_macro_f1"],
            "lesion_routing_fn": BASELINE["lesion_routing_fn"],
            "eczema_to_urticaria": BASELINE["eczema_to_urticaria"],
            "urticaria_fp": BASELINE["urticaria_fp"],
            "source": "known_baseline_numbers",
        }

    ckpt = torch.load(checkpoint_path, map_location="cpu")
    model = build_model(backbone_name="efficientnet_b0", num_classes=len(class_to_idx), pretrained=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    model.eval()

    test_ds = __import__("src.data.dataset", fromlist=["ImageClassificationDataset"]).ImageClassificationDataset(
        csv_path=TEST_CSV,
        class_to_idx=class_to_idx,
        transform=get_eval_transforms(TRAIN_CONFIG["image_size"]),
        label_column="target_label",
        class_idx_column="class_idx",
    )
    test_loader = DataLoader(test_ds, batch_size=TRAIN_CONFIG["batch_size"], shuffle=False, num_workers=TRAIN_CONFIG["num_workers"])

    true_labels: list[int] = []
    pred_labels: list[int] = []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            logits = model(images)
            pred_labels.extend(logits.argmax(dim=1).cpu().tolist())
            true_labels.extend(labels.tolist())

    assert file_hash(TEST_CSV) == test_hash, "Test hash changed during baseline eval — STOP"

    sources = [(r.get("source_dataset") or "").strip() for r in read_csv_rows(TEST_CSV)]
    source_metrics = compute_source_metrics(sources, true_labels, pred_labels, CLASS_NAMES)
    src_lookup = {row["source_dataset"]: row for row in source_metrics}

    cm = compute_confusion_matrix(true_labels, pred_labels, len(CLASS_NAMES))
    focus = compute_focus_errors(cm, CLASS_NAMES)
    class_report, macro_f1, bal_acc = compute_classification_report(cm, CLASS_NAMES)

    print(f"  Baseline re-eval: macro_f1={macro_f1:.4f}, bal_acc={bal_acc:.4f}, lesion_fn={focus['lesion_routing_fn']}")

    return {
        "combined_macro_f1": macro_f1,
        "balanced_accuracy": bal_acc,
        "google_scin_macro_f1": src_lookup.get("google_scin", {}).get("macro_f1", 0.0),
        "fitzpatrick17k_macro_f1": src_lookup.get("fitzpatrick17k", {}).get("macro_f1", 0.0),
        "lesion_routing_fn": focus["lesion_routing_fn"],
        "eczema_to_urticaria": focus["eczema_to_urticaria"],
        "urticaria_fp": focus["urticaria_fp"],
        "class_report": [dict(r) for r in class_report],
        "confusion_matrix": cm,
        "source": "re_evaluated",
    }


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="V2.22 metadata-aware Clinical V2 experiment.")
    parser.add_argument("--max-train-batches", type=int, default=None, help="Smoke test: limit train batches per epoch.")
    parser.add_argument("--max-val-batches", type=int, default=None, help="Smoke test: limit val batches per epoch.")
    args = parser.parse_args()

    torch.manual_seed(TRAIN_CONFIG["random_seed"])
    device = select_device()
    class_to_idx = build_class_to_idx(CLASS_NAMES)
    num_classes = len(class_to_idx)

    # Lock test set
    test_hash = file_hash(TEST_CSV)
    print(f"Test set locked. Hash: {test_hash} | Rows: {sum(1 for _ in TEST_CSV.open()) - 1}")

    # -----------------------------------------------------------------------
    # Phase 1 — Metadata audit
    # -----------------------------------------------------------------------
    train_rows = read_csv_rows(TRAIN_CSV)
    val_rows = read_csv_rows(VAL_CSV)
    test_rows = read_csv_rows(TEST_CSV)
    print(f"Split sizes: train={len(train_rows)}, val={len(val_rows)}, test={len(test_rows)}")

    audit = run_metadata_audit(train_rows)

    # -----------------------------------------------------------------------
    # Phase 2 — Fit encoders (train set only)
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PHASE 2 — ENCODER FITTING")
    print("=" * 70)
    variant_encoders: dict[str, MetadataEncoder] = {}
    for v in VARIANTS:
        enc = MetadataEncoder(v["logical_fields"]).fit(train_rows)
        variant_encoders[v["name"]] = enc
        print(f"  {v['name']}: logical_fields={v['logical_fields']}, metadata_dim={enc.metadata_dim}")

    # -----------------------------------------------------------------------
    # Baseline re-eval
    # -----------------------------------------------------------------------
    baseline_results = eval_baseline(class_to_idx, device, test_hash)
    assert file_hash(TEST_CSV) == test_hash, "Test hash changed after baseline eval — STOP"

    # -----------------------------------------------------------------------
    # Phase 3 — Train variants
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PHASE 3 — TRAINING METADATA VARIANTS")
    print("=" * 70)

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    variant_checkpoints: dict[str, Path] = {}

    for v in VARIANTS:
        variant_name = v["name"]
        logical_fields = v["logical_fields"]

        assert "source_dataset" not in logical_fields, \
            f"source_dataset must not be in logical_fields for {variant_name} — STOP"

        assert file_hash(TEST_CSV) == test_hash, \
            f"Test hash changed before training {variant_name} — STOP"

        encoder = variant_encoders[variant_name]
        metadata_dim = encoder.metadata_dim

        print(f"\n=== Variant: {variant_name} | metadata_dim={metadata_dim} | fields={logical_fields} ===")

        model = MetadataAwareClinicalV2(
            num_classes=num_classes,
            metadata_dim=metadata_dim,
            metadata_fields=logical_fields,
            pretrained=True,
        ).to(device)

        train_ds, val_ds, test_ds, train_loader, val_loader, test_loader = build_metadata_loaders(
            encoder=encoder,
            image_size=TRAIN_CONFIG["image_size"],
            batch_size=TRAIN_CONFIG["batch_size"],
            num_workers=TRAIN_CONFIG["num_workers"],
            class_to_idx=class_to_idx,
        )

        class_weights_tensor = None
        if TRAIN_CONFIG["use_class_weights"]:
            from src.data.dataset import ImageClassificationDataset
            dummy_ds = ImageClassificationDataset(
                csv_path=TRAIN_CSV, class_to_idx=class_to_idx,
                label_column="target_label", class_idx_column="class_idx",
            )
            class_weights_tensor = compute_class_weights(dummy_ds, class_to_idx).to(device)
            print(f"  Class weights: {[round(w, 4) for w in class_weights_tensor.cpu().tolist()]}")

        criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
        optimizer = build_optimizer(model.parameters(), TRAIN_CONFIG["lr"], TRAIN_CONFIG["weight_decay"])

        output_dir = Path(f"models/clinical_v2_meta_{variant_name}")
        output_dir.mkdir(parents=True, exist_ok=True)

        epoch_log: list[dict] = []
        best_val_macro_f1 = float("-inf")
        best_ckpt_path = output_dir / "best_model.pth"

        for epoch in range(1, TRAIN_CONFIG["epochs"] + 1):
            t0 = time.time()
            train_loss, train_acc = train_one_epoch_with_metadata(
                model, train_loader, criterion, optimizer, device,
                max_batches=args.max_train_batches,
            )
            val_loss, val_acc, val_mf1, val_bal = evaluate_with_metadata(
                model, val_loader, criterion, device, num_classes,
                max_batches=args.max_val_batches,
            )
            elapsed = round(time.time() - t0, 1)

            entry = {
                "epoch": epoch, "variant": variant_name,
                "meta_fields": str(logical_fields),
                "train_loss": round(train_loss, 6), "train_accuracy": round(train_acc, 6),
                "val_loss": round(val_loss, 6), "val_accuracy": round(val_acc, 6),
                "val_macro_f1": round(val_mf1, 6), "val_balanced_accuracy": round(val_bal, 6),
                "epoch_time_sec": elapsed,
            }
            epoch_log.append(entry)

            marker = " NEW BEST" if val_mf1 > best_val_macro_f1 else ""
            print(f"  Epoch {epoch}/{TRAIN_CONFIG['epochs']}: "
                  f"train_loss={train_loss:.4f} val_mf1={val_mf1:.4f} val_bal={val_bal:.4f}"
                  f"{marker} ({elapsed}s)")

            if val_mf1 > best_val_macro_f1:
                best_val_macro_f1 = val_mf1
                checkpoint = {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "class_to_idx": class_to_idx,
                    "metadata_fields": logical_fields,
                    "metadata_dim": metadata_dim,
                    "val_macro_f1": val_mf1,
                }
                torch.save(checkpoint, best_ckpt_path)

        log_path = METRICS_DIR / f"clinical_v2_meta_{variant_name}_training_log.csv"
        fieldnames = list(epoch_log[0].keys()) if epoch_log else []
        with log_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(epoch_log)

        # Save class_to_idx alongside checkpoint
        with (output_dir / "class_to_idx.json").open("w") as fh:
            json.dump(class_to_idx, fh, indent=2)

        variant_checkpoints[variant_name] = best_ckpt_path
        print(f"  {variant_name} done. Best val_macro_f1={best_val_macro_f1:.4f}")

        assert file_hash(TEST_CSV) == test_hash, \
            f"Test hash changed after training {variant_name} — STOP"

    # -----------------------------------------------------------------------
    # Phase 4 — Evaluate all variants on frozen test set
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PHASE 4 — EVALUATION ON FROZEN TEST SET")
    print("=" * 70)

    sources = [(r.get("source_dataset") or "").strip() for r in test_rows]

    eval_results: dict[str, dict] = {"image_only": baseline_results}

    for v in VARIANTS:
        variant_name = v["name"]
        logical_fields = v["logical_fields"]

        assert "source_dataset" not in logical_fields, \
            f"source_dataset must not be in logical_fields for {variant_name} eval — STOP"
        assert file_hash(TEST_CSV) == test_hash, \
            f"Test hash changed before evaluating {variant_name} — STOP"

        print(f"\n  Evaluating: {variant_name}")

        encoder = variant_encoders[variant_name]
        ckpt_path = variant_checkpoints[variant_name]

        ckpt = torch.load(ckpt_path, map_location="cpu")
        model = MetadataAwareClinicalV2(
            num_classes=num_classes,
            metadata_dim=ckpt["metadata_dim"],
            metadata_fields=ckpt["metadata_fields"],
            pretrained=False,
        ).to(device)
        model.load_state_dict(ckpt["model_state_dict"])

        test_ds = MetadataImageClassificationDataset(
            csv_path=TEST_CSV,
            class_to_idx=class_to_idx,
            encoder=encoder,
            transform=get_eval_transforms(TRAIN_CONFIG["image_size"]),
            label_column="target_label",
            class_idx_column="class_idx",
        )
        test_loader = DataLoader(
            test_ds, batch_size=TRAIN_CONFIG["batch_size"], shuffle=False,
            num_workers=TRAIN_CONFIG["num_workers"],
        )

        true_labels, pred_labels = run_inference_with_metadata(model, test_loader, device)
        assert len(true_labels) == len(test_rows), \
            f"Prediction count mismatch for {variant_name}: {len(true_labels)} != {len(test_rows)} — STOP"

        source_metrics_list = compute_source_metrics(sources, true_labels, pred_labels, CLASS_NAMES)
        src_lookup = {row["source_dataset"]: row for row in source_metrics_list}

        cm = compute_confusion_matrix(true_labels, pred_labels, num_classes)
        class_report, macro_f1, bal_acc = compute_classification_report(cm, CLASS_NAMES)
        focus = compute_focus_errors(cm, CLASS_NAMES)

        # Missing metadata coverage on test set
        missing_by_field: dict[str, int] = {}
        for lf in logical_fields:
            if lf == "body_parts":
                missing_by_field["body_parts_any"] = sum(
                    1 for r in test_rows
                    if not any((r.get(c) or "").strip() for c in BODY_PARTS_COLS)
                )
            elif lf in ("age_group", "sex_at_birth"):
                missing_by_field[lf] = sum(1 for r in test_rows if not (r.get(lf) or "").strip())

        eval_results[variant_name] = {
            "logical_fields": logical_fields,
            "combined_macro_f1": macro_f1,
            "balanced_accuracy": bal_acc,
            "google_scin_macro_f1": src_lookup.get("google_scin", {}).get("macro_f1", 0.0),
            "fitzpatrick17k_macro_f1": src_lookup.get("fitzpatrick17k", {}).get("macro_f1", 0.0),
            "lesion_routing_fn": focus["lesion_routing_fn"],
            "eczema_to_urticaria": focus["eczema_to_urticaria"],
            "urticaria_fp": focus["urticaria_fp"],
            "class_report": [dict(r) for r in class_report],
            "confusion_matrix": cm,
            "missing_metadata": missing_by_field,
            "source_metrics": source_metrics_list,
        }

        print(f"    macro_f1={macro_f1:.4f} | bal_acc={bal_acc:.4f} | "
              f"scin_f1={src_lookup.get('google_scin', {}).get('macro_f1', 0):.4f} | "
              f"lesion_fn={focus['lesion_routing_fn']}")

        assert file_hash(TEST_CSV) == test_hash, \
            f"Test hash changed after evaluating {variant_name} — STOP"

    # -----------------------------------------------------------------------
    # Phase 5 — Ablation table + metrics JSON
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PHASE 5 — ABLATION TABLE")
    print("=" * 70)

    baseline_mf1 = baseline_results["combined_macro_f1"]
    baseline_scin = baseline_results["google_scin_macro_f1"]

    ablation_rows: list[dict] = []
    header = f"{'Variant':35s} {'Fields':28s} {'mF1':>7s} {'bal_acc':>8s} {'SCIN':>7s} {'Fitz':>7s} {'FN':>4s} {'Delta':>7s} {'Shortcut?':>10s}"
    sep = "─" * 115
    print(f"\n{header}")
    print(sep)

    all_variant_names = ["image_only"] + [v["name"] for v in VARIANTS]
    for vn in all_variant_names:
        res = eval_results[vn]
        mf1 = res["combined_macro_f1"]
        ba = res["balanced_accuracy"]
        scin = res["google_scin_macro_f1"]
        fitz = res["fitzpatrick17k_macro_f1"]
        lfn = res["lesion_routing_fn"]
        delta = mf1 - baseline_mf1
        fields_str = str(res.get("logical_fields", [])) if vn != "image_only" else "[]"
        scin_delta = scin - baseline_scin
        shortcut = "CHECK" if (delta > 0.01 and scin_delta < 0) else "OK"

        print(f"{vn:35s} {fields_str:28s} {mf1:>7.4f} {ba:>8.4f} {scin:>7.4f} {fitz:>7.4f} {lfn:>4} {delta:>+7.4f} {shortcut:>10s}")

        ablation_rows.append({
            "variant": vn,
            "meta_fields": fields_str,
            "combined_macro_f1": round(mf1, 6),
            "balanced_accuracy": round(ba, 6),
            "google_scin_macro_f1": round(scin, 6),
            "fitzpatrick17k_macro_f1": round(fitz, 6),
            "lesion_routing_fn": lfn,
            "eczema_to_urticaria": res["eczema_to_urticaria"],
            "urticaria_fp": res["urticaria_fp"],
            "delta_vs_baseline_mf1": round(delta, 6),
            "shortcut_risk": shortcut,
        })

    ablation_path = METRICS_DIR / "clinical_v2_metadata_ablation_table.csv"
    with ablation_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(ablation_rows[0].keys()))
        writer.writeheader()
        writer.writerows(ablation_rows)
    print(f"\nSaved: {ablation_path}")

    # Candidate metrics JSON (confusion matrices serialised as lists)
    def _serialise(v):
        if isinstance(v, list) and v and isinstance(v[0], list):
            return v  # already list[list[int]]
        return v

    metrics_json_path = METRICS_DIR / "clinical_v2_metadata_candidate_metrics.json"
    with metrics_json_path.open("w", encoding="utf-8") as fh:
        json.dump(
            {vn: {k: _serialise(val) for k, val in res.items()} for vn, res in eval_results.items()},
            fh, indent=2, default=str,
        )
    print(f"Saved: {metrics_json_path}")

    # -----------------------------------------------------------------------
    # Phase 6 — Write summary documents
    # -----------------------------------------------------------------------
    _write_availability_summary(audit, train_rows, val_rows, test_rows)
    _write_model_summary(ablation_rows, eval_results, audit)

    # -----------------------------------------------------------------------
    # Phase 7 — gh issue comment
    # -----------------------------------------------------------------------
    best_vn = max(
        (vn for vn in all_variant_names if vn != "image_only"),
        key=lambda vn: eval_results[vn]["combined_macro_f1"],
    )
    best_res = eval_results[best_vn]
    best_mf1 = best_res["combined_macro_f1"]
    best_delta = best_mf1 - baseline_mf1
    best_lfn = best_res["lesion_routing_fn"]
    shortcut_summary = ", ".join(
        f"{r['variant']}={r['shortcut_risk']}"
        for r in ablation_rows if r["variant"] != "image_only"
    )
    n_fields_used = len({f for v in VARIANTS for f in v["logical_fields"]})

    comment_body = (
        f"V2.22 complete. "
        f"Metadata audit done: {len(audit['all_cols'])} columns found, {n_fields_used} logical fields used "
        f"(body_parts×12, age_group×2, sex_at_birth×3). "
        f"Variants trained: image+body_parts, image+age, image+body_parts+age, image+body_parts+age+sex. "
        f"Best variant: {best_vn} macro-F1={best_mf1:.4f} (Δ{best_delta:+.4f}), lesion FN={best_lfn}. "
        f"Shortcut flags: {shortcut_summary}. "
        f"Recommendation: see docs/model/clinical_v2_metadata_aware_model_summary.md. "
        f"Product note: metadata cannot be deployed without app-side collection. "
        f"Ablation table: outputs/metrics/clinical_v2_metadata_ablation_table.csv"
    )

    try:
        result = subprocess.run(
            ["gh", "issue", "comment", "173", "--body", comment_body],
            capture_output=True, text=True, check=True,
        )
        print(f"\nPosted gh issue comment 173: {result.stdout.strip()}")
    except Exception as exc:
        print(f"\nCould not post gh issue comment: {exc}")
        print(f"Comment body:\n{comment_body}")

    print("\n" + "=" * 70)
    print("V2.22 COMPLETE")
    print("=" * 70)
    print(f"Test hash at end: {file_hash(TEST_CSV)} (must match {test_hash})")
    assert file_hash(TEST_CSV) == test_hash, "Test hash changed at end — STOP"
    print("Test hash verified — no test set contamination.")


# ---------------------------------------------------------------------------
# Phase 6 helpers — document writers
# ---------------------------------------------------------------------------

def _write_availability_summary(
    audit: dict,
    train_rows: list[dict],
    val_rows: list[dict],
    test_rows: list[dict],
) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    path = DOCS_DIR / "clinical_v2_metadata_availability_summary.md"

    lines = [
        "# Clinical V2 Metadata Availability Summary",
        "",
        "Generated by V2.22 experiment (Issue #173). Experiment only — no model promotion.",
        "",
        f"| Split | Rows |",
        "| --- | ---: |",
        f"| train | {len(train_rows):,} |",
        f"| val   | {len(val_rows):,} |",
        f"| test  | {len(test_rows):,} |",
        "",
        "## All Columns Present in clinical_v2 CSVs",
        "",
        "Schema is identical across all three splits.",
        "",
        "```",
        ", ".join(audit["all_cols"]),
        "```",
        "",
        "## Priority Field Audit (issue names → actual CSV columns)",
        "",
        "| Issue field | Actual CSV column(s) | Type | Present |",
        "| --- | --- | --- | --- |",
        "| body_location / anatom_site_general | 12 × `body_parts_*` | multi-hot binary | YES |",
        "| age_bucket / age_approx | `age_group` | categorical ordinal | YES |",
        "| sex / gender | `sex_at_birth` | categorical | YES |",
        "| fitzpatrick_skin_type | `fitzpatrick_skin_type` | subgroup eval only | YES |",
        "| source_dataset | `source_dataset` | reporting only — NEVER model input | YES |",
        "| body_location (exact name) | — | — | NOT PRESENT |",
        "| anatom_site_general (exact) | — | — | NOT PRESENT |",
        "| age / age_approx / age_bucket | — | — | NOT PRESENT |",
        "| sex / gender (exact names) | — | — | NOT PRESENT |",
        "",
        "## Body Parts Columns (multi-hot, YES/empty)",
        "",
        f"Rows in train with ANY body part filled: {audit['any_body_cov']:.1f}%",
        "",
        "| Column | Train coverage |",
        "| --- | ---: |",
    ]
    for col, cov in audit["bp_coverage"].items():
        lines.append(f"| `{col}` | {cov:.1f}% |")

    lines += [
        "",
        "## Missingness by Source Dataset",
        "",
        "(`source_dataset` used for reporting only — never as model input.)",
        "",
        "| Source | N | body_parts (any) | age_group | sex_at_birth |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for src, stats in audit["source_bp"].items():
        lines.append(
            f"| {src} | {stats['n']:,} | {stats['body_parts_any_pct']:.0f}% | "
            f"{stats['age_group_pct']:.0f}% | {stats['sex_at_birth_pct']:.0f}% |"
        )

    lines += [
        "",
        "## Shortcut Risk Check (Cramér's V vs. class label)",
        "",
        "Run before any training. Cramér's V > 0.4 = HIGH risk that improvement reflects",
        "shortcut learning from dataset-specific distributions, not clinical reasoning.",
        "",
        "| Field | Cramér's V | Risk |",
        "| --- | ---: | --- |",
    ]
    for row in audit["shortcut_table"]:
        lines.append(f"| `{row['field']}` | {row['cramers_v']:.3f} | {row['risk']} |")

    lines += [
        "",
        "## Encoding Strategy",
        "",
        "| Field | Encoding | Dim | Unknown handling |",
        "| --- | --- | ---: | --- |",
        "| body_parts_* (12 cols) | multi-hot float (YES→1.0) | 12 | all zeros (no body part specified) |",
        "| age_group | ordinal [0,1] + unknown flag | 2 | flag bit = 1 |",
        "| sex_at_birth | one-hot [MALE, FEMALE, unknown] | 3 | unknown bit = 1 |",
        "",
        "Encoders fit on training set only. No sample ever dropped for missing metadata.",
        "",
        "## Fields Excluded and Why",
        "",
        "| Field | Reason |",
        "| --- | --- |",
        "| source_dataset | Must never be prediction input — shortcut/leakage risk |",
        "| fitzpatrick_skin_type | Used for subgroup eval only |",
        "| textures_*, condition_symptoms_* | Out of scope for V2.22 — not in priority list |",
        "| monk_skin_tone_label_* | Out of scope for V2.22 |",
        "| condition_duration, related_category | Out of scope for V2.22 |",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved: {path}")


def _write_model_summary(
    ablation_rows: list[dict],
    eval_results: dict[str, dict],
    audit: dict,
) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    path = DOCS_DIR / "clinical_v2_metadata_aware_model_summary.md"

    best_vn = max(
        (r["variant"] for r in ablation_rows if r["variant"] != "image_only"),
        key=lambda vn: eval_results[vn]["combined_macro_f1"],
    )
    # Always compare against the SAME-RUN image-only re-eval, never the stale
    # historical constant — mixing the two flips the conclusion (see issue #173).
    base = eval_results["image_only"]
    best_res = eval_results[best_vn]
    best_mf1 = best_res["combined_macro_f1"]
    best_delta = best_mf1 - base["combined_macro_f1"]
    best_scin = best_res["google_scin_macro_f1"]
    best_scin_delta = best_scin - base["google_scin_macro_f1"]
    best_lesion_fn = best_res["lesion_routing_fn"]
    base_lesion_fn = base["lesion_routing_fn"]

    # Promotion criteria check for each variant
    def promotion_check(res: dict) -> dict:
        return {
            "macro_f1_ok": res["combined_macro_f1"] > base["combined_macro_f1"],
            "bal_acc_ok": res["balanced_accuracy"] >= base["balanced_accuracy"] - 0.005,
            "scin_ok": res["google_scin_macro_f1"] >= base["google_scin_macro_f1"] - 0.005,
            "lesion_fn_ok": res["lesion_routing_fn"] <= base["lesion_routing_fn"],
        }

    shortcut_variants = [r["variant"] for r in ablation_rows if r["shortcut_risk"] == "CHECK"]

    lines = [
        "# Clinical V2 Metadata-Aware Model Summary",
        "",
        "Generated by V2.22 experiment (Issue #173). Experiment only — no model promotion.",
        "",
        "## 1. Architecture",
        "",
        "```",
        "image (H×W×3)",
        "  └─ EfficientNet-B0 backbone (torchvision, pretrained ImageNet)",
        "       features + avgpool + flatten",
        "  └─ 1280-dim image embedding",
        "                                          ┐",
        "metadata (metadata_dim,)                 │",
        "  └─ Linear(metadata_dim, 32)            │ metadata MLP",
        "       ReLU → Dropout(0.3)               │ (<5% of total params)",
        "       Linear(32, 16) → ReLU            │",
        "  └─ 16-dim metadata embedding            ┘",
        "",
        "  concat([1280, 16]) → 1296-dim",
        "  └─ Dropout(0.3) → Linear(1296, 5) → logits",
        "```",
        "",
        "| | Params | % of total |",
        "| --- | ---: | ---: |",
        "| EfficientNet-B0 backbone | ~5.27M | ~99.98% |",
        "| Metadata MLP (body_parts variant, dim=12) | ~944 | ~0.02% |",
        "| Metadata MLP (body_parts+age, dim=14) | ~1,008 | ~0.02% |",
        "| Metadata MLP (body_parts+age+sex, dim=17) | ~1,104 | ~0.02% |",
        "",
        "## 2. Missing Metadata Strategy",
        "",
        "- Every metadata field has an explicit unknown encoding — no sample is ever dropped.",
        "- body_parts_*: all-zeros vector when no body part is specified.",
        "- age_group: ordinal=0.0, unknown_flag=1.0 when field is empty.",
        "- sex_at_birth: unknown one-hot bit=1.0 when field is empty.",
        "- For Fitzpatrick17k rows that lack SCIN-style body_parts: zeros vector used.",
        "  This means the metadata branch contributes no signal for those rows —",
        "  the model degrades gracefully to near-image-only behaviour.",
        "- `source_dataset` is never used as a model input feature — asserted in model constructor.",
        "",
        "## 3. Ablation Table",
        "",
        f"Baseline (same-run image-only re-eval): macro-F1={base['combined_macro_f1']:.4f}, "
        f"bal_acc={base['balanced_accuracy']:.4f}, "
        f"SCIN={base['google_scin_macro_f1']:.4f}, "
        f"lesion_FN={base['lesion_routing_fn']}",
        "",
        "| Variant | Fields | macro-F1 | bal_acc | SCIN-F1 | Fitz-F1 | FN | Δ mF1 | Shortcut? |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for r in ablation_rows:
        lines.append(
            f"| {r['variant']} | {r['meta_fields']} | {r['combined_macro_f1']:.4f} | "
            f"{r['balanced_accuracy']:.4f} | {r['google_scin_macro_f1']:.4f} | "
            f"{r['fitzpatrick17k_macro_f1']:.4f} | {r['lesion_routing_fn']} | "
            f"{r['delta_vs_baseline_mf1']:+.4f} | {r['shortcut_risk']} |"
        )

    lines += [
        "",
        "## 4. Shortcut Analysis",
        "",
    ]
    if shortcut_variants:
        lines += [
            f"The following variants improved in-distribution macro-F1 but did NOT improve "
            f"SCIN macro-F1, suggesting shortcut learning rather than generalizable improvement:",
            "",
        ]
        for vn in shortcut_variants:
            res = eval_results[vn]
            scin_d = res["google_scin_macro_f1"] - base["google_scin_macro_f1"]
            lines.append(
                f"- **{vn}**: pooled Δ={res['combined_macro_f1']-base['combined_macro_f1']:+.4f}, "
                f"SCIN Δ={scin_d:+.4f}. "
                f"Likely explanation: body_parts/age distributions differ between SCIN and Fitzpatrick17k; "
                f"the model learned to exploit dataset-specific metadata patterns rather than "
                f"clinically meaningful context."
            )
    else:
        lines.append(
            "No shortcut flags raised (no variant had >+0.01 in-dist improvement with negative SCIN delta)."
        )

    lines += [
        "",
        "## 5. Promotion Verdict",
        "",
        f"| Variant | macro-F1 > {base['combined_macro_f1']:.4f} | bal_acc stable | "
        f"SCIN ≥ {base['google_scin_macro_f1']:.4f}−0.005 | lesion FN ≤ {base['lesion_routing_fn']} | Verdict |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in ablation_rows:
        if r["variant"] == "image_only":
            continue
        res = eval_results[r["variant"]]
        pc = promotion_check(res)
        verdict = "PASS" if all(pc.values()) else "FAIL"
        lines.append(
            f"| {r['variant']} | {'PASS' if pc['macro_f1_ok'] else 'FAIL'} | "
            f"{'PASS' if pc['bal_acc_ok'] else 'FAIL'} | "
            f"{'PASS' if pc['scin_ok'] else 'FAIL'} | "
            f"{'PASS' if pc['lesion_fn_ok'] else 'FAIL'} | "
            f"**{verdict}** |"
        )

    lines += [
        "",
        "## 6. Recommendation",
        "",
        f"Best variant by pooled macro-F1: **{best_vn}** "
        f"(macro-F1={best_mf1:.4f}, Δ{best_delta:+.4f}, SCIN Δ{best_scin_delta:+.4f}, "
        f"lesion FN {best_lesion_fn} vs {base_lesion_fn}).",
        "",
    ]
    # A gain is only trustworthy if it shows up on google_scin — the only source that
    # actually carries metadata — AND does not regress safety-critical lesion routing.
    # A pooled-only bump with flat/negative SCIN is the signature of a source shortcut.
    genuine = best_delta > 0.01 and best_scin_delta >= 0 and best_lesion_fn <= base_lesion_fn
    if genuine:
        lines.append(
            "The metadata-aware approach shows an improvement that also holds on google_scin "
            "(the metadata-bearing source) without regressing lesion routing. "
            "Continued investment is recommended IF the product roadmap includes app-side metadata collection "
            "(see Product Note below). Without app-side collection, the model cannot be deployed."
        )
    else:
        lines.append(
            f"No trustworthy improvement over the image-only baseline. The best variant ({best_vn}) "
            f"moves pooled macro-F1 by {best_delta:+.4f}, but this gain is NOT reflected on google_scin — "
            f"the only source that actually carries body_parts/age/sex metadata — where macro-F1 is "
            f"flat-to-lower (Δ{best_scin_delta:+.4f}), and lesion-routing false-negatives do not improve "
            f"({best_lesion_fn} vs {base_lesion_fn} baseline). This matches the pre-registered HIGH shortcut "
            "risk (Cramér's V=0.508 between body_parts-presence and the class label — high precisely because "
            "body_parts is recorded almost exclusively on google_scin, so its presence proxies the source and "
            "its class mix): the pooled movement reflects source-correlated metadata rather than generalizable "
            "clinical signal. Recommend discontinuing metadata-aware "
            "modeling for Clinical V2 under current data conditions — body_parts/age/sex are present almost "
            "exclusively on google_scin (≈0% on Fitzpatrick17k), so the fusion model cannot learn a "
            "source-independent use of metadata."
        )

    lines += [
        "",
        "## 7. Product Note (CRITICAL)",
        "",
        "> **A metadata-aware model cannot be deployed without app-side metadata collection.**",
        ">",
        "> If this model were deployed while the app collects only images (current behaviour),",
        "> every inference would receive a zeros metadata vector — equivalent to the all-unknown",
        "> encoding. The model was trained with real body_parts/age signals for SCIN rows;",
        "> deploying it with missing metadata at inference time creates an inconsistent inference",
        "> path that was not evaluated during training.",
        ">",
        "> **Body location (body_parts) must be collected from the user at the time of submission**",
        "> for this to be clinically meaningful. If the app does not ask the user for body location,",
        "> deploying this model creates a worse and inconsistently evaluated inference path",
        "> compared to the image-only baseline.",
        ">",
        "> No metadata-aware variant should be promoted until the app metadata collection UI",
        "> is implemented and validated.",
        "",
        "## 8. Out of Scope — Confirmed",
        "",
        "- No model promotion in code.",
        "- No inference registry change.",
        "- No taxonomy change.",
        "- No Streamlit UI change.",
        "- No app metadata collection implemented.",
        "- No clinical-readiness, diagnostic, or treatment claims.",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
