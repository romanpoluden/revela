from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import torch
import yaml
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader

from src.data.dataset import BCN20000Dataset
from src.data.transforms import get_eval_transforms, get_train_transforms
from src.model.model import count_trainable_parameters, create_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train EfficientNet-B0 on BCN20000.")
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


def create_dataloaders(config: dict, class_to_idx: dict[str, int], args: argparse.Namespace):
    dataset_config = config["dataset"]
    training_config = config["training"]
    files_config = config["files"]
    output_dir = Path(dataset_config["output_dir"])

    batch_size = args.batch_size or training_config["batch_size"]
    num_workers = args.num_workers if args.num_workers is not None else training_config["num_workers"]
    image_size = training_config["image_size"]

    train_dataset = BCN20000Dataset(
        csv_path=output_dir / files_config["train"],
        class_to_idx=class_to_idx,
        transform=get_train_transforms(image_size),
    )
    val_dataset = BCN20000Dataset(
        csv_path=output_dir / files_config["val"],
        class_to_idx=class_to_idx,
        transform=get_eval_transforms(image_size),
    )

    device = select_device()
    pin_memory = device.type == "cuda"

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
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


def compute_class_weights(train_dataset: BCN20000Dataset, class_to_idx: dict[str, int]) -> torch.Tensor:
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
    return average_loss, accuracy, macro_f1


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


def save_class_to_idx(output_dir: Path, class_to_idx: dict[str, int]) -> None:
    path = output_dir / "class_to_idx.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(class_to_idx, handle, indent=2)


def save_training_history(output_dir: Path, history_rows: list[dict[str, float]]) -> None:
    path = output_dir / "training_history.csv"
    fieldnames = [
        "epoch",
        "train_loss",
        "train_accuracy",
        "val_loss",
        "val_accuracy",
        "val_macro_f1",
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

    require_keys(config, ["dataset", "files", "class_names", "training"], "root")
    require_keys(config["dataset"], ["output_dir"], "dataset")
    require_keys(config["files"], ["train", "val"], "files")
    require_keys(
        config["training"],
        [
            "image_size",
            "batch_size",
            "num_workers",
            "learning_rate",
            "weight_decay",
            "epochs",
            "use_class_weights",
            "output_dir",
        ],
        "training",
    )

    class_to_idx = build_class_to_idx(config["class_names"])
    device = select_device()
    num_classes = len(class_to_idx)

    train_dataset, val_dataset, train_loader, val_loader = create_dataloaders(
        config, class_to_idx, args
    )

    model = create_model(num_classes=num_classes).to(device)

    class_weights = None
    if config["training"]["use_class_weights"]:
        class_weights = compute_class_weights(train_dataset, class_to_idx).to(device)
        print("Using class weights:", [round(weight, 4) for weight in class_weights.cpu().tolist()])

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = AdamW(
        model.parameters(),
        lr=config["training"]["learning_rate"],
        weight_decay=config["training"]["weight_decay"],
    )

    epochs = args.epochs or config["training"]["epochs"]
    output_dir = Path(config["training"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    save_class_to_idx(output_dir, class_to_idx)

    print("Training configuration:")
    print(f"  - device: {device}")
    print(f"  - num_classes: {num_classes}")
    print(f"  - train_examples: {len(train_dataset)}")
    print(f"  - val_examples: {len(val_dataset)}")
    print(f"  - trainable_parameters: {count_trainable_parameters(model)}")
    print(f"  - epochs: {epochs}")
    print(f"  - output_dir: {output_dir}")
    print("")

    history_rows: list[dict[str, float]] = []
    best_val_macro_f1 = float("-inf")

    for epoch in range(1, epochs + 1):
        train_loss, train_accuracy = train_one_epoch(
            model=model,
            loader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
            max_batches=args.max_train_batches,
        )
        val_loss, val_accuracy, val_macro_f1 = evaluate(
            model=model,
            loader=val_loader,
            criterion=criterion,
            device=device,
            num_classes=num_classes,
            max_batches=args.max_val_batches,
        )

        history_row = {
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "train_accuracy": round(train_accuracy, 6),
            "val_loss": round(val_loss, 6),
            "val_accuracy": round(val_accuracy, 6),
            "val_macro_f1": round(val_macro_f1, 6),
        }
        history_rows.append(history_row)
        save_training_history(output_dir, history_rows)

        print(f"Epoch {epoch}/{epochs}")
        print(f"  Train loss:      {train_loss:.4f}")
        print(f"  Train accuracy:  {train_accuracy:.4f}")
        print(f"  Val loss:        {val_loss:.4f}")
        print(f"  Val accuracy:    {val_accuracy:.4f}")
        print(f"  Val macro-F1:    {val_macro_f1:.4f}")

        if val_macro_f1 > best_val_macro_f1:
            best_val_macro_f1 = val_macro_f1
            save_best_model(output_dir, model, class_to_idx, epoch, val_macro_f1)
            print("  Saved new best model.")

        print("")

    print("Training finished.")
    print(f"Best validation macro-F1: {best_val_macro_f1:.4f}")
    print(f"Best model path: {output_dir / 'best_model.pth'}")
    print(f"History path: {output_dir / 'training_history.csv'}")


if __name__ == "__main__":
    main()
