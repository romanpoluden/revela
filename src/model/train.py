from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import torch
import yaml
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, ReduceLROnPlateau
from torch.utils.data import DataLoader

from src.data.samplers import build_weighted_sampler, summarize_sampler_groups

from src.data.dataset import ImageClassificationDataset
from src.data.transforms import get_eval_transforms, get_train_transforms
from src.model.model import (
    build_model,
    count_trainable_parameters,
    create_model,
    get_head_parameters,
    set_backbone_requires_grad,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train an EfficientNet-B0 image classifier.")
    parser.add_argument(
        "--config",
        default="config/bcn20000_config.yaml",
        help="Path to the YAML config file.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Optional override for the number of training epochs.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Optional override for the DataLoader batch size.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=None,
        help="Optional override for the DataLoader worker count.",
    )
    parser.add_argument(
        "--max-train-batches",
        type=int,
        default=None,
        help="Optional limit for train batches per epoch for smoke tests.",
    )
    parser.add_argument(
        "--max-val-batches",
        type=int,
        default=None,
        help="Optional limit for validation batches per epoch for smoke tests.",
    )
    return parser.parse_args()


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    if not isinstance(config, dict):
        raise ValueError("Config file must contain a YAML dictionary.")

    return config


def require_keys(mapping: dict, required_keys: list[str], section_name: str) -> None:
    missing_keys = [key for key in required_keys if key not in mapping]
    if missing_keys:
        missing_text = ", ".join(missing_keys)
        raise KeyError(f"Missing required keys in `{section_name}`: {missing_text}")


def select_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def build_class_to_idx(class_names: list[str]) -> dict[str, int]:
    if not class_names:
        raise ValueError("class_names must not be empty.")
    return {class_name: index for index, class_name in enumerate(class_names)}


def get_class_names(config: dict) -> list[str]:
    if "class_names" in config:
        return config["class_names"]
    return config["dataset"]["class_names"]


def get_image_size(config: dict) -> int:
    return config["training"].get("image_size") or config["dataset"]["image_size"]


def get_train_csv_path(config: dict) -> Path:
    dataset_config = config["dataset"]
    if "train_csv" in dataset_config:
        return Path(dataset_config["train_csv"])
    return Path(dataset_config["output_dir"]) / config["files"]["train"]


def get_val_csv_path(config: dict) -> Path:
    dataset_config = config["dataset"]
    if "val_csv" in dataset_config:
        return Path(dataset_config["val_csv"])
    return Path(dataset_config["output_dir"]) / config["files"]["val"]


def get_output_dir(config: dict) -> Path:
    configured_output_dir = config["training"].get("output_dir")
    if configured_output_dir:
        return Path(configured_output_dir)
    if config["dataset"].get("name") == "clinical_v2":
        return Path("models/clinical_v2_effnet_b0")
    return Path("models/effnet_b0")


def get_weight_decay(config: dict) -> float:
    return config["training"].get("weight_decay", 0.0)


def get_scheduler_config(config: dict) -> dict:
    """Scheduler block. Absent or type 'none' means no scheduler (baseline behavior)."""
    return config["training"].get("scheduler", {}) or {}


def get_staged_finetune_config(config: dict) -> dict:
    """Staged fine-tuning block. Absent or enabled=False means single-phase (baseline)."""
    return config["training"].get("staged_finetune", {}) or {}


def build_optimizer(parameters, learning_rate: float, weight_decay: float) -> AdamW:
    return AdamW(parameters, lr=learning_rate, weight_decay=weight_decay)


def build_scheduler(optimizer, scheduler_config: dict, phase_epochs: int):
    """Return (scheduler, step_mode).

    step_mode is one of:
      - "epoch":   call scheduler.step() once per epoch (cosine).
      - "plateau": call scheduler.step(val_macro_f1) once per epoch.
      - None:      no scheduler.
    """
    scheduler_type = (scheduler_config.get("type") or "none").lower()

    if scheduler_type in ("", "none"):
        return None, None

    if scheduler_type == "cosine":
        eta_min = scheduler_config.get("eta_min", 0.0)
        return CosineAnnealingLR(optimizer, T_max=max(phase_epochs, 1), eta_min=eta_min), "epoch"

    if scheduler_type in ("reduce_on_plateau", "reduce_lr_on_plateau", "plateau"):
        return (
            ReduceLROnPlateau(
                optimizer,
                mode="max",  # we monitor val_macro_f1, which we want to maximize
                factor=scheduler_config.get("factor", 0.5),
                patience=scheduler_config.get("patience", 1),
            ),
            "plateau",
        )

    raise ValueError(f"Unknown scheduler type: {scheduler_type}")


def get_num_workers(config: dict, args: argparse.Namespace) -> int:
    if args.num_workers is not None:
        return args.num_workers
    return config["training"].get("num_workers", 0)


def get_label_columns(config: dict) -> tuple[str, str | None]:
    dataset_config = config["dataset"]
    label_column = dataset_config.get("label_column", "target_label")
    class_idx_column = dataset_config.get("class_idx_column", "class_idx")

    if "files" in config and "class_names" in config:
        label_column = dataset_config.get("label_column", "class_label")
        class_idx_column = dataset_config.get("class_idx_column")

    return label_column, class_idx_column


def create_dataloaders(config: dict, class_to_idx: dict[str, int], args: argparse.Namespace):
    training_config = config["training"]

    batch_size = args.batch_size or training_config["batch_size"]
    num_workers = get_num_workers(config, args)
    image_size = get_image_size(config)
    label_column, class_idx_column = get_label_columns(config)

    strategy = config.get("augmentation_strategy", "baseline")
    train_dataset = ImageClassificationDataset(
        csv_path=get_train_csv_path(config),
        class_to_idx=class_to_idx,
        transform=get_train_transforms(image_size, strategy=strategy),
        label_column=label_column,
        class_idx_column=class_idx_column,
    )
    val_dataset = ImageClassificationDataset(
        csv_path=get_val_csv_path(config),
        class_to_idx=class_to_idx,
        transform=get_eval_transforms(image_size),
        label_column=label_column,
        class_idx_column=class_idx_column,
    )

    device = select_device()
    pin_memory = device.type == "cuda"

    sampler_config = training_config.get("sampler", {})
    sampler_mode = sampler_config.get("mode", "none")
    sampler_class_column = sampler_config.get("class_column", label_column)
    sampler_source_column = sampler_config.get("source_column", "source_dataset")
    sampler_replacement = sampler_config.get("replacement", True)

    train_sampler = build_weighted_sampler(
        rows=train_dataset.rows,
        mode=sampler_mode,
        class_column=sampler_class_column,
        source_column=sampler_source_column,
        replacement=sampler_replacement,
    )

    if train_sampler is not None:
        print(f"Using training sampler mode: {sampler_mode}")
        sampler_groups = summarize_sampler_groups(
            rows=train_dataset.rows,
            mode=sampler_mode,
            class_column=sampler_class_column,
            source_column=sampler_source_column,
        )
        print("Sampler group counts:")
        for group_name, group_count in sampler_groups.items():
            print(f"  - {group_name}: {group_count}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=train_sampler is None,
        sampler=train_sampler,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    return train_dataset, val_dataset, train_loader, val_loader


def compute_class_weights(train_dataset: ImageClassificationDataset, class_to_idx: dict[str, int]) -> torch.Tensor:
    label_counts = {class_name: 0 for class_name in class_to_idx}
    for row in train_dataset.rows:
        label_counts[row["class_label"]] += 1

    total_samples = len(train_dataset)
    num_classes = len(class_to_idx)
    weights = []
    for class_name in class_to_idx:
        count = label_counts[class_name]
        if count == 0:
            raise ValueError(f"Class `{class_name}` has zero samples in the training split.")
        weight = total_samples / (num_classes * count)
        weights.append(weight)

    return torch.tensor(weights, dtype=torch.float32)


def train_one_epoch(model, loader, criterion, optimizer, device, max_batches=None):
    model.train()
    running_loss = 0.0
    total_examples = 0
    total_correct = 0

    for batch_index, (images, labels) in enumerate(loader):
        if max_batches is not None and batch_index >= max_batches:
            break

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        batch_size = labels.size(0)
        running_loss += loss.item() * batch_size
        predictions = logits.argmax(dim=1)
        total_examples += batch_size
        total_correct += (predictions == labels).sum().item()

    average_loss = running_loss / max(total_examples, 1)
    accuracy = total_correct / max(total_examples, 1)
    return average_loss, accuracy


def evaluate(model, loader, criterion, device, num_classes, max_batches=None):
    model.eval()
    running_loss = 0.0
    total_examples = 0
    total_correct = 0
    all_predictions: list[int] = []
    all_labels: list[int] = []

    with torch.no_grad():
        for batch_index, (images, labels) in enumerate(loader):
            if max_batches is not None and batch_index >= max_batches:
                break

            images = images.to(device)
            labels = labels.to(device)

            logits = model(images)
            loss = criterion(logits, labels)

            batch_size = labels.size(0)
            running_loss += loss.item() * batch_size

            predictions = logits.argmax(dim=1)
            total_examples += batch_size
            total_correct += (predictions == labels).sum().item()

            all_predictions.extend(predictions.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    average_loss = running_loss / max(total_examples, 1)
    accuracy = total_correct / max(total_examples, 1)
    macro_f1 = compute_macro_f1(all_labels, all_predictions, num_classes)
    balanced_accuracy = compute_balanced_accuracy(all_labels, all_predictions, num_classes)
    return average_loss, accuracy, macro_f1, balanced_accuracy


def compute_macro_f1(true_labels: list[int], predicted_labels: list[int], num_classes: int) -> float:
    if len(true_labels) != len(predicted_labels):
        raise ValueError("true_labels and predicted_labels must have the same length.")
    if not true_labels:
        return 0.0

    per_class_f1_scores = []
    for class_index in range(num_classes):
        true_positive = 0
        false_positive = 0
        false_negative = 0

        for true_label, predicted_label in zip(true_labels, predicted_labels):
            if true_label == class_index and predicted_label == class_index:
                true_positive += 1
            elif true_label != class_index and predicted_label == class_index:
                false_positive += 1
            elif true_label == class_index and predicted_label != class_index:
                false_negative += 1

        precision_denominator = true_positive + false_positive
        recall_denominator = true_positive + false_negative
        precision = true_positive / precision_denominator if precision_denominator > 0 else 0.0
        recall = true_positive / recall_denominator if recall_denominator > 0 else 0.0

        if precision + recall == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * precision * recall / (precision + recall)

        per_class_f1_scores.append(f1_score)

    return sum(per_class_f1_scores) / num_classes


def compute_per_class_recalls(true_labels: list[int], predicted_labels: list[int], num_classes: int) -> list[float]:
    recalls = []
    for class_index in range(num_classes):
        class_total = 0
        class_correct = 0
        for true_label, predicted_label in zip(true_labels, predicted_labels):
            if true_label == class_index:
                class_total += 1
                if predicted_label == class_index:
                    class_correct += 1
        recalls.append(class_correct / class_total if class_total > 0 else 0.0)
    return recalls


def compute_balanced_accuracy(true_labels: list[int], predicted_labels: list[int], num_classes: int) -> float:
    if len(true_labels) != len(predicted_labels):
        raise ValueError("true_labels and predicted_labels must have the same length.")
    if not true_labels:
        return 0.0
    return sum(compute_per_class_recalls(true_labels, predicted_labels, num_classes)) / num_classes


_CANCER_CLASS_NAMES = {"Melanoma", "Non-melanoma skin cancer"}


def compute_cancer_recall(
    true_labels: list[int], predicted_labels: list[int], class_to_idx: dict[str, int]
) -> float | None:
    cancer_indices = {idx for cls, idx in class_to_idx.items() if cls in _CANCER_CLASS_NAMES}
    if len(cancer_indices) < 2:
        return None
    total = sum(1 for t in true_labels if t in cancer_indices)
    correct = sum(1 for t, p in zip(true_labels, predicted_labels) if t in cancer_indices and p in cancer_indices)
    return correct / total if total > 0 else 0.0


def save_class_to_idx(output_dir: Path, class_to_idx: dict[str, int]) -> None:
    path = output_dir / "class_to_idx.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(class_to_idx, handle, indent=2)


def save_training_history(output_dir: Path, history_rows: list[dict[str, float]]) -> None:
    path = output_dir / "training_history.csv"
    fieldnames = [
        "epoch",
        "phase",
        "learning_rate",
        "train_loss",
        "train_accuracy",
        "val_loss",
        "val_accuracy",
        "val_macro_f1",
        "val_balanced_accuracy",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(history_rows)


def save_best_model(output_dir: Path, model, class_to_idx: dict[str, int], epoch: int, val_macro_f1: float) -> None:
    checkpoint = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "class_to_idx": class_to_idx,
        "val_macro_f1": val_macro_f1,
    }
    torch.save(checkpoint, output_dir / "best_model.pth")


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))

    require_keys(config, ["dataset", "training"], "root")
    require_keys(
        config["training"],
        [
            "batch_size",
            "learning_rate",
            "epochs",
            "use_class_weights",
        ],
        "training",
    )

    class_to_idx = build_class_to_idx(get_class_names(config))
    device = select_device()
    num_classes = len(class_to_idx)

    train_dataset, val_dataset, train_loader, val_loader = create_dataloaders(
        config, class_to_idx, args
    )

    pretrained = config.get("model", {}).get("pretrained", True)
    backbone_name = config.get("model", {}).get("architecture", "efficientnet_b0")
    model = build_model(backbone_name=backbone_name, num_classes=num_classes, pretrained=pretrained).to(device)

    class_weights = None
    if config["training"]["use_class_weights"]:
        class_weights = compute_class_weights(train_dataset, class_to_idx).to(device)
        print("Using class weights:", [round(weight, 4) for weight in class_weights.cpu().tolist()])

    criterion = nn.CrossEntropyLoss(weight=class_weights)

    weight_decay = get_weight_decay(config)
    base_learning_rate = config["training"]["learning_rate"]
    epochs = args.epochs or config["training"]["epochs"]
    scheduler_config = get_scheduler_config(config)
    staged_config = get_staged_finetune_config(config)
    staged_enabled = bool(staged_config.get("enabled", False))

    output_dir = get_output_dir(config)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_class_to_idx(output_dir, class_to_idx)

    # Build the training phases. The default (non-staged) path is a single phase
    # over the full model, reproducing the baseline schedule exactly.
    phases: list[dict] = []
    if staged_enabled:
        head_epochs = staged_config.get("head_epochs", 2)
        head_learning_rate = staged_config.get("head_learning_rate", base_learning_rate)
        # Phase 1: freeze backbone, warm up the classifier head only.
        set_backbone_requires_grad(model, backbone_name, requires_grad=False)
        phases.append(
            {
                "name": "head",
                "epochs": head_epochs,
                "optimizer": build_optimizer(
                    get_head_parameters(model, backbone_name), head_learning_rate, weight_decay
                ),
                "scheduler_config": {},  # no scheduler during the short head warmup
                "learning_rate": head_learning_rate,
                "unfreeze_first": False,
            }
        )
        # Phase 2: unfreeze the full model and fine-tune at the base LR.
        phases.append(
            {
                "name": "finetune",
                "epochs": epochs,
                "optimizer": None,  # built after unfreezing, below
                "scheduler_config": scheduler_config,
                "learning_rate": base_learning_rate,
                "unfreeze_first": True,
            }
        )
    else:
        phases.append(
            {
                "name": "full",
                "epochs": epochs,
                "optimizer": build_optimizer(model.parameters(), base_learning_rate, weight_decay),
                "scheduler_config": scheduler_config,
                "learning_rate": base_learning_rate,
                "unfreeze_first": False,
            }
        )

    total_epochs = sum(phase["epochs"] for phase in phases)

    print("Training configuration:")
    print(f"  - device: {device}")
    print(f"  - num_classes: {num_classes}")
    print(f"  - train_examples: {len(train_dataset)}")
    print(f"  - val_examples: {len(val_dataset)}")
    print(f"  - staged_finetune: {staged_enabled}")
    print(f"  - scheduler: {(scheduler_config.get('type') or 'none')}")
    print(f"  - total_epochs: {total_epochs}")
    print(f"  - output_dir: {output_dir}")
    print("")

    history_rows: list[dict[str, float]] = []
    best_val_macro_f1 = float("-inf")
    global_epoch = 0

    for phase in phases:
        if phase["unfreeze_first"]:
            set_backbone_requires_grad(model, backbone_name, requires_grad=True)
            phase["optimizer"] = build_optimizer(
                model.parameters(), phase["learning_rate"], weight_decay
            )

        optimizer = phase["optimizer"]
        scheduler, scheduler_step_mode = build_scheduler(
            optimizer, phase["scheduler_config"], phase["epochs"]
        )

        print(
            f"=== Phase '{phase['name']}': {phase['epochs']} epoch(s), "
            f"lr={phase['learning_rate']}, "
            f"trainable_params={count_trainable_parameters(model)}, "
            f"scheduler={(phase['scheduler_config'].get('type') or 'none')} ==="
        )

        for _ in range(1, phase["epochs"] + 1):
            global_epoch += 1
            current_lr = optimizer.param_groups[0]["lr"]

            train_loss, train_accuracy = train_one_epoch(
                model=model,
                loader=train_loader,
                criterion=criterion,
                optimizer=optimizer,
                device=device,
                max_batches=args.max_train_batches,
            )
            val_loss, val_accuracy, val_macro_f1, val_balanced_accuracy = evaluate(
                model=model,
                loader=val_loader,
                criterion=criterion,
                device=device,
                num_classes=num_classes,
                max_batches=args.max_val_batches,
            )

            history_row = {
                "epoch": global_epoch,
                "phase": phase["name"],
                "learning_rate": round(current_lr, 8),
                "train_loss": round(train_loss, 6),
                "train_accuracy": round(train_accuracy, 6),
                "val_loss": round(val_loss, 6),
                "val_accuracy": round(val_accuracy, 6),
                "val_macro_f1": round(val_macro_f1, 6),
                "val_balanced_accuracy": round(val_balanced_accuracy, 6),
            }
            history_rows.append(history_row)
            save_training_history(output_dir, history_rows)

            print(f"Epoch {global_epoch}/{total_epochs} [{phase['name']}] (lr={current_lr:.2e})")
            print(f"  Train loss:      {train_loss:.4f}")
            print(f"  Train accuracy:  {train_accuracy:.4f}")
            print(f"  Val loss:        {val_loss:.4f}")
            print(f"  Val accuracy:    {val_accuracy:.4f}")
            print(f"  Val macro-F1:    {val_macro_f1:.4f}")
            print(f"  Val balanced acc:{val_balanced_accuracy:.4f}")

            if val_macro_f1 > best_val_macro_f1:
                best_val_macro_f1 = val_macro_f1
                save_best_model(output_dir, model, class_to_idx, global_epoch, val_macro_f1)
                print("  Saved new best model.")

            if scheduler_step_mode == "epoch":
                scheduler.step()
            elif scheduler_step_mode == "plateau":
                scheduler.step(val_macro_f1)

            print("")

    print("Training finished.")
    print(f"Best validation macro-F1: {best_val_macro_f1:.4f}")
    print(f"Best model path: {output_dir / 'best_model.pth'}")
    print(f"History path: {output_dir / 'training_history.csv'}")


if __name__ == "__main__":
    main()
