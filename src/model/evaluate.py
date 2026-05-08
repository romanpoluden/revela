from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import torch
import yaml
from PIL import Image, ImageDraw, ImageFont
from torch.utils.data import DataLoader

from src.data.dataset import BCN20000Dataset
from src.data.transforms import get_eval_transforms
from src.model.model import create_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate EfficientNet-B0 on BCN20000 test data.")
    parser.add_argument(
        "--config",
        default="config/bcn20000_config.yaml",
        help="Path to the YAML config file.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Optional override for the evaluation batch size.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=None,
        help="Optional override for the DataLoader worker count.",
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


def load_class_to_idx(path: Path) -> dict[str, int]:
    if not path.exists():
        raise FileNotFoundError(f"class_to_idx file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        class_to_idx = json.load(handle)

    if not isinstance(class_to_idx, dict) or not class_to_idx:
        raise ValueError("class_to_idx.json must contain a non-empty mapping.")

    return {str(class_name): int(index) for class_name, index in class_to_idx.items()}


def create_test_loader(config: dict, class_to_idx: dict[str, int], args: argparse.Namespace):
    dataset_output_dir = Path(config["dataset"]["output_dir"])
    test_csv_path = dataset_output_dir / config["files"]["test"]
    image_size = config["training"]["image_size"]
    batch_size = args.batch_size or config["training"]["batch_size"]
    num_workers = args.num_workers if args.num_workers is not None else config["training"]["num_workers"]

    test_dataset = BCN20000Dataset(
        csv_path=test_csv_path,
        class_to_idx=class_to_idx,
        transform=get_eval_transforms(image_size),
    )

    device = select_device()
    pin_memory = device.type == "cuda"

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    return test_dataset, test_loader


def load_model(model_path: Path, num_classes: int, device: torch.device):
    if not model_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {model_path}")

    checkpoint = torch.load(model_path, map_location=device)
    if "model_state_dict" not in checkpoint:
        raise KeyError("Checkpoint is missing `model_state_dict`.")

    model = create_model(num_classes=num_classes, pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model, checkpoint


def run_inference(model, loader, device):
    all_labels: list[int] = []
    all_top1_predictions: list[int] = []
    all_top3_predictions: list[list[int]] = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            logits = model(images)

            top1_predictions = logits.argmax(dim=1)
            topk_count = min(3, logits.shape[1])
            top3_predictions = torch.topk(logits, k=topk_count, dim=1).indices

            all_labels.extend(labels.tolist())
            all_top1_predictions.extend(top1_predictions.cpu().tolist())
            all_top3_predictions.extend(top3_predictions.cpu().tolist())

    return all_labels, all_top1_predictions, all_top3_predictions


def compute_confusion_matrix(true_labels: list[int], predicted_labels: list[int], num_classes: int) -> list[list[int]]:
    matrix = [[0 for _ in range(num_classes)] for _ in range(num_classes)]
    for true_label, predicted_label in zip(true_labels, predicted_labels):
        matrix[true_label][predicted_label] += 1
    return matrix


def compute_top1_accuracy(true_labels: list[int], predicted_labels: list[int]) -> float:
    if not true_labels:
        return 0.0
    correct = sum(int(true_label == predicted_label) for true_label, predicted_label in zip(true_labels, predicted_labels))
    return correct / len(true_labels)


def compute_top3_accuracy(true_labels: list[int], top3_predictions: list[list[int]]) -> float:
    if not true_labels:
        return 0.0
    correct = sum(int(true_label in predicted_top3) for true_label, predicted_top3 in zip(true_labels, top3_predictions))
    return correct / len(true_labels)


def compute_classification_metrics(confusion_matrix: list[list[int]], class_names: list[str]) -> tuple[list[dict[str, float]], float, float]:
    num_classes = len(class_names)
    total_samples = sum(sum(row) for row in confusion_matrix)
    per_class_rows: list[dict[str, float]] = []
    per_class_f1_scores: list[float] = []
    per_class_recalls: list[float] = []

    for class_index, class_name in enumerate(class_names):
        true_positive = confusion_matrix[class_index][class_index]
        false_positive = sum(confusion_matrix[row_index][class_index] for row_index in range(num_classes) if row_index != class_index)
        false_negative = sum(confusion_matrix[class_index][column_index] for column_index in range(num_classes) if column_index != class_index)
        support = sum(confusion_matrix[class_index])

        precision_denominator = true_positive + false_positive
        recall_denominator = true_positive + false_negative

        precision = true_positive / precision_denominator if precision_denominator > 0 else 0.0
        recall = true_positive / recall_denominator if recall_denominator > 0 else 0.0
        f1_score = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)

        per_class_f1_scores.append(f1_score)
        per_class_recalls.append(recall)
        per_class_rows.append(
            {
                "class_name": class_name,
                "precision": precision,
                "recall": recall,
                "f1": f1_score,
                "support": support,
            }
        )

    macro_f1 = sum(per_class_f1_scores) / num_classes if num_classes > 0 else 0.0
    balanced_accuracy = sum(per_class_recalls) / num_classes if num_classes > 0 else 0.0

    if total_samples == 0:
        macro_f1 = 0.0
        balanced_accuracy = 0.0

    return per_class_rows, macro_f1, balanced_accuracy


def save_metrics_json(
    output_path: Path,
    metrics: dict,
    confusion_matrix: list[list[int]],
    class_metrics: list[dict[str, float]],
    class_names: list[str],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "top1_accuracy": metrics["top1_accuracy"],
        "top3_accuracy": metrics["top3_accuracy"],
        "macro_f1": metrics["macro_f1"],
        "balanced_accuracy": metrics["balanced_accuracy"],
        "num_test_examples": metrics["num_test_examples"],
        "checkpoint_epoch": metrics["checkpoint_epoch"],
        "checkpoint_val_macro_f1": metrics["checkpoint_val_macro_f1"],
        "class_names": class_names,
        "class_metrics": class_metrics,
        "confusion_matrix": confusion_matrix,
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_classification_report_csv(output_path: Path, class_metrics: list[dict[str, float]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["class_name", "precision", "recall", "f1", "support"]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in class_metrics:
            writer.writerow(
                {
                    "class_name": row["class_name"],
                    "precision": f"{row['precision']:.6f}",
                    "recall": f"{row['recall']:.6f}",
                    "f1": f"{row['f1']:.6f}",
                    "support": row["support"],
                }
            )


def save_confusion_matrix_png(output_path: Path, confusion_matrix: list[list[int]], class_names: list[str]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    num_classes = len(class_names)
    cell_size = 120
    left_margin = 220
    top_margin = 120
    right_margin = 40
    bottom_margin = 40

    image_width = left_margin + num_classes * cell_size + right_margin
    image_height = top_margin + num_classes * cell_size + bottom_margin

    image = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(image)

    max_value = max(max(row) for row in confusion_matrix) if confusion_matrix else 0
    font = ImageFont.load_default()

    title = "BCN20000 Confusion Matrix"
    draw.text((20, 20), title, fill="black", font=font)
    draw.text((20, 55), "Rows = true labels, columns = predicted labels", fill="black", font=font)

    for class_index, class_name in enumerate(class_names):
        x = left_margin + class_index * cell_size
        y = top_margin + class_index * cell_size

        draw.text((x + 10, 85), class_name, fill="black", font=font)
        draw.text((20, y + cell_size / 2 - 8), class_name, fill="black", font=font)

    for row_index in range(num_classes):
        for column_index in range(num_classes):
            value = confusion_matrix[row_index][column_index]
            intensity = 0 if max_value == 0 else int(255 - (value / max_value) * 180)
            fill_color = (intensity, intensity, 255)

            x0 = left_margin + column_index * cell_size
            y0 = top_margin + row_index * cell_size
            x1 = x0 + cell_size
            y1 = y0 + cell_size

            draw.rectangle([x0, y0, x1, y1], fill=fill_color, outline="black", width=1)

            text = str(value)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = x0 + (cell_size - text_width) / 2
            text_y = y0 + (cell_size - text_height) / 2
            draw.text((text_x, text_y), text, fill="black", font=font)

    image.save(output_path)


def print_metrics(metrics: dict, class_metrics: list[dict[str, float]], class_names: list[str], confusion_matrix: list[list[int]]) -> None:
    print("Evaluation results:")
    print(f"  - test_examples:       {metrics['num_test_examples']}")
    print(f"  - top1_accuracy:       {metrics['top1_accuracy']:.4f}")
    print(f"  - top3_accuracy:       {metrics['top3_accuracy']:.4f}")
    print(f"  - macro_f1:            {metrics['macro_f1']:.4f}")
    print(f"  - balanced_accuracy:   {metrics['balanced_accuracy']:.4f}")
    print("")
    print("Class-wise metrics:")
    for row in class_metrics:
        print(
            f"  - {row['class_name']}: "
            f"precision={row['precision']:.4f}, "
            f"recall={row['recall']:.4f}, "
            f"f1={row['f1']:.4f}, "
            f"support={row['support']}"
        )
    print("")
    print("Confusion matrix:")
    header = "true\\pred".ljust(18) + "".join(name[:16].ljust(18) for name in class_names)
    print(header)
    for class_name, row in zip(class_names, confusion_matrix):
        row_text = class_name[:16].ljust(18) + "".join(str(value).ljust(18) for value in row)
        print(row_text)


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))

    require_keys(config, ["dataset", "files", "class_names", "training"], "root")
    require_keys(config["dataset"], ["output_dir"], "dataset")
    require_keys(config["files"], ["test"], "files")
    require_keys(config["training"], ["image_size", "batch_size", "num_workers", "output_dir"], "training")

    device = select_device()
    model_dir = Path(config["training"]["output_dir"])
    model_path = model_dir / "best_model.pth"
    class_to_idx_path = model_dir / "class_to_idx.json"
    class_to_idx = load_class_to_idx(class_to_idx_path)

    class_names = [class_name for class_name, _ in sorted(class_to_idx.items(), key=lambda item: item[1])]
    num_classes = len(class_names)

    test_dataset, test_loader = create_test_loader(config, class_to_idx, args)
    model, checkpoint = load_model(model_path, num_classes=num_classes, device=device)

    true_labels, top1_predictions, top3_predictions = run_inference(model, test_loader, device)
    confusion_matrix = compute_confusion_matrix(true_labels, top1_predictions, num_classes)
    class_metrics, macro_f1, balanced_accuracy = compute_classification_metrics(confusion_matrix, class_names)

    metrics = {
        "num_test_examples": len(test_dataset),
        "top1_accuracy": compute_top1_accuracy(true_labels, top1_predictions),
        "top3_accuracy": compute_top3_accuracy(true_labels, top3_predictions),
        "macro_f1": macro_f1,
        "balanced_accuracy": balanced_accuracy,
        "checkpoint_epoch": int(checkpoint.get("epoch", -1)),
        "checkpoint_val_macro_f1": float(checkpoint.get("val_macro_f1", 0.0)),
    }

    metrics_json_path = Path("outputs/metrics/bcn20000_test_metrics.json")
    report_csv_path = Path("outputs/metrics/bcn20000_classification_report.csv")
    confusion_png_path = Path("outputs/plots/bcn20000_confusion_matrix.png")

    save_metrics_json(metrics_json_path, metrics, confusion_matrix, class_metrics, class_names)
    save_classification_report_csv(report_csv_path, class_metrics)
    save_confusion_matrix_png(confusion_png_path, confusion_matrix, class_names)

    print_metrics(metrics, class_metrics, class_names, confusion_matrix)
    print("")
    print(f"Saved metrics JSON: {metrics_json_path}")
    print(f"Saved classification report CSV: {report_csv_path}")
    print(f"Saved confusion matrix PNG: {confusion_png_path}")


if __name__ == "__main__":
    main()
