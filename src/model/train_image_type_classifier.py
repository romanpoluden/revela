"""
Train a 2-class image-type classifier (clinical_macroscopic vs dermoscopic).

Reads the master dataset index produced by Stage 1, splits by the 'split'
column, and trains a lightweight EfficientNet-B0 backbone.

Example
-------
python -m src.model.train_image_type_classifier \\
    --dataset-index outputs/model/image_type_classifier_dataset_index.csv \\
    --output-dir models/image_type_classifier_v1 \\
    --epochs 10 --batch-size 32 --lr 0.0001 --seed 42
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader

from src.data.dataset import ImageClassificationDataset
from src.data.transforms import get_eval_transforms, get_train_transforms
from src.model.model import build_model, count_trainable_parameters
from src.model.train import (
    compute_balanced_accuracy,
    compute_macro_f1,
    compute_per_class_recalls,
    select_device,
)

CLASS_NAMES = ["clinical_macroscopic", "dermoscopic"]
LABEL_COLUMN = "image_type"
IMAGE_COLUMN = "image_path"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train 2-class image-type classifier.")
    parser.add_argument(
        "--dataset-index",
        default="outputs/model/image_type_classifier_dataset_index.csv",
    )
    parser.add_argument("--output-dir", default="models/image_type_classifier_v1")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.0001)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--backbone", default="efficientnet_b0")
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--augmentation", default="mild_clinical",
                        help="Augmentation strategy: baseline | mild_clinical | robust_clinical")
    parser.add_argument("--max-train-batches", type=int, default=None,
                        help="Limit train batches/epoch for rapid iteration (None = full epoch).")
    parser.add_argument("--max-val-batches", type=int, default=None,
                        help="Limit val batches/epoch for rapid iteration (None = full val set).")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def write_split_csv(rows: pd.DataFrame, path: Path) -> None:
    """Write a minimal split CSV with only the columns the dataset loader needs."""
    rows[[IMAGE_COLUMN, LABEL_COLUMN, "source_dataset"]].to_csv(path, index=False)


def prepare_split_csvs(index_path: Path, output_dir: Path, seed: int = 42) -> dict[str, Path]:
    """Read master index, filter readable, write per-split CSVs. Return paths.

    Rows are shuffled within each split so that class-limited batch evaluation
    (--max-val-batches) samples both classes proportionally rather than hitting
    only the first class in the sorted index.
    """
    idx = pd.read_csv(index_path)
    readable = idx[idx["readable"]].copy()

    split_paths: dict[str, Path] = {}
    for split in ("train", "val", "test"):
        subset = readable[readable["split"] == split].sample(frac=1, random_state=seed)
        dest = output_dir / f"{split}.csv"
        write_split_csv(subset, dest)
        split_paths[split] = dest
        print(f"  {split}: {len(subset)} images "
              f"(clinical={len(subset[subset[LABEL_COLUMN]=='clinical_macroscopic'])}, "
              f"dermoscopic={len(subset[subset[LABEL_COLUMN]=='dermoscopic'])})")

    return split_paths


def compute_class_weights_from_csv(csv_path: Path, class_to_idx: dict[str, int]) -> torch.Tensor:
    df = pd.read_csv(csv_path)
    counts = df[LABEL_COLUMN].value_counts()
    total = len(df)
    num_classes = len(class_to_idx)
    weights = []
    for class_name in CLASS_NAMES:
        n = counts.get(class_name, 0)
        if n == 0:
            raise ValueError(f"Class '{class_name}' has 0 samples in {csv_path}")
        weights.append(total / (num_classes * n))
    return torch.tensor(weights, dtype=torch.float32)


def train_one_epoch(model, loader, criterion, optimizer, device, max_batches=None):
    model.train()
    running_loss = total_correct = total_examples = 0

    for i, (images, labels) in enumerate(loader):
        if max_batches is not None and i >= max_batches:
            break
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        bs = labels.size(0)
        running_loss += loss.item() * bs
        total_correct += (logits.argmax(dim=1) == labels).sum().item()
        total_examples += bs

    return running_loss / max(total_examples, 1), total_correct / max(total_examples, 1)


def evaluate(model, loader, criterion, device, num_classes, max_batches=None):
    model.eval()
    running_loss = total_correct = total_examples = 0
    all_preds: list[int] = []
    all_labels: list[int] = []

    with torch.no_grad():
        for i, (images, labels) in enumerate(loader):
            if max_batches is not None and i >= max_batches:
                break
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            loss = criterion(logits, labels)

            bs = labels.size(0)
            running_loss += loss.item() * bs
            preds = logits.argmax(dim=1)
            total_correct += (preds == labels).sum().item()
            total_examples += bs
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    avg_loss = running_loss / max(total_examples, 1)
    accuracy = total_correct / max(total_examples, 1)
    macro_f1 = compute_macro_f1(all_labels, all_preds, num_classes)
    balanced_acc = compute_balanced_accuracy(all_labels, all_preds, num_classes)
    per_class_recall = compute_per_class_recalls(all_labels, all_preds, num_classes)
    return avg_loss, accuracy, macro_f1, balanced_acc, per_class_recall


def save_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    class_to_idx = {name: idx for idx, name in enumerate(CLASS_NAMES)}
    num_classes = len(CLASS_NAMES)
    device = select_device()

    # ── Prepare split CSVs ───────────────────────────────────────────────────
    print(f"Loading dataset index: {args.dataset_index}")
    split_paths = prepare_split_csvs(Path(args.dataset_index), output_dir, seed=args.seed)

    # ── Datasets & loaders ───────────────────────────────────────────────────
    train_ds = ImageClassificationDataset(
        csv_path=split_paths["train"],
        class_to_idx=class_to_idx,
        transform=get_train_transforms(args.image_size, strategy=args.augmentation),
        image_column=IMAGE_COLUMN,
        label_column=LABEL_COLUMN,
    )
    val_ds = ImageClassificationDataset(
        csv_path=split_paths["val"],
        class_to_idx=class_to_idx,
        transform=get_eval_transforms(args.image_size),
        image_column=IMAGE_COLUMN,
        label_column=LABEL_COLUMN,
    )

    pin_memory = device.type == "cuda"
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              num_workers=args.num_workers, pin_memory=pin_memory)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            num_workers=args.num_workers, pin_memory=pin_memory)

    # ── Model ────────────────────────────────────────────────────────────────
    model = build_model(backbone_name=args.backbone, num_classes=num_classes,
                        pretrained=True).to(device)

    class_weights = compute_class_weights_from_csv(split_paths["train"], class_to_idx).to(device)
    print(f"Class weights: {dict(zip(CLASS_NAMES, [round(w, 4) for w in class_weights.tolist()]))}")

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    # ── Save config ──────────────────────────────────────────────────────────
    config_dict = vars(args)
    config_dict["class_names"] = CLASS_NAMES
    config_dict["class_to_idx"] = class_to_idx
    config_dict["device"] = str(device)
    config_dict["trainable_params"] = count_trainable_parameters(model)
    config_dict["train_examples"] = len(train_ds)
    config_dict["val_examples"] = len(val_ds)
    save_json(output_dir / "training_config.json", config_dict)
    save_json(output_dir / "class_to_idx.json", class_to_idx)

    print(f"\nTraining on {device}")
    print(f"  backbone: {args.backbone}  params: {count_trainable_parameters(model):,}")
    print(f"  train: {len(train_ds)}  val: {len(val_ds)}")
    print(f"  epochs: {args.epochs}  batch_size: {args.batch_size}  lr: {args.lr}")
    print()

    # ── Training loop ────────────────────────────────────────────────────────
    history: list[dict] = []
    best_val_f1 = float("-inf")
    best_epoch = -1

    for epoch in range(1, args.epochs + 1):
        lr = optimizer.param_groups[0]["lr"]

        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device, args.max_train_batches
        )
        val_loss, val_acc, val_f1, val_bal_acc, per_class_recall = evaluate(
            model, val_loader, criterion, device, num_classes, args.max_val_batches
        )

        row = {
            "epoch": epoch,
            "learning_rate": round(lr, 8),
            "train_loss": round(train_loss, 6),
            "train_accuracy": round(train_acc, 6),
            "val_loss": round(val_loss, 6),
            "val_accuracy": round(val_acc, 6),
            "val_macro_f1": round(val_f1, 6),
            "val_balanced_accuracy": round(val_bal_acc, 6),
        }
        for i, name in enumerate(CLASS_NAMES):
            row[f"val_recall_{name}"] = round(per_class_recall[i], 6)
        history.append(row)

        _write_history_csv(output_dir / "training_history.csv", history)

        print(f"Epoch {epoch}/{args.epochs} (lr={lr:.2e})")
        print(f"  train  loss={train_loss:.4f}  acc={train_acc:.4f}")
        print(f"  val    loss={val_loss:.4f}  acc={val_acc:.4f}  macro_f1={val_f1:.4f}  bal_acc={val_bal_acc:.4f}")
        for i, name in enumerate(CLASS_NAMES):
            print(f"    {name}: recall={per_class_recall[i]:.4f}")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "class_to_idx": class_to_idx,
                "val_macro_f1": val_f1,
                "val_accuracy": val_acc,
                "val_balanced_accuracy": val_bal_acc,
                "backbone": args.backbone,
                "num_classes": num_classes,
                "image_size": args.image_size,
            }, output_dir / "best_model.pth")
            print(f"  → saved best model (val_macro_f1={val_f1:.4f})")
        print()

    # ── Final metrics ────────────────────────────────────────────────────────
    best_row = next(r for r in history if r["epoch"] == best_epoch)
    metrics = {
        "best_epoch": best_epoch,
        "best_val_macro_f1": best_val_f1,
        "best_val_accuracy": best_row["val_accuracy"],
        "best_val_balanced_accuracy": best_row["val_balanced_accuracy"],
        **{k: v for k, v in best_row.items() if k.startswith("val_recall_")},
        "total_epochs": args.epochs,
    }
    save_json(output_dir / "training_metrics.json", metrics)

    print(f"Training complete. Best val macro-F1: {best_val_f1:.4f} (epoch {best_epoch})")
    print(f"Artifacts: {output_dir}")


def _write_history_csv(path: Path, history: list[dict]) -> None:
    if not history:
        return
    fieldnames = list(history[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(history)


if __name__ == "__main__":
    main()
