from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import torch
import yaml
from PIL import Image, ImageDraw, ImageFont
from torch.utils.data import DataLoader

from src.data.dataset import ImageClassificationDataset
from src.data.transforms import get_eval_transforms
from src.model.model import build_model, create_model


LESION_ROUTING_CLASS = "Lesion — dermoscopic review recommended"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the Clinical V2 EfficientNet-B0 image classifier."
    )
    parser.add_argument(
        "--config",
        default="config/clinical_v2_config.yaml",
        help="Path to the Clinical V2 YAML config file.",
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
    parser.add_argument(
        "--output-prefix",
        type=str,
        default=None,
        help="Optional prefix for output filenames (e.g. 'clinical_v2_aug_mild'). "
             "Defaults to 'clinical_v2'.",
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


def get_class_names(class_to_idx: dict[str, int]) -> list[str]:
    return [
        class_name
        for class_name, _ in sorted(class_to_idx.items(), key=lambda item: item[1])
    ]


def validate_class_names(config: dict, class_names: list[str]) -> None:
    configured_class_names = config["dataset"]["class_names"]
    if configured_class_names != class_names:
        raise ValueError(
            "class_to_idx.json class order does not match config clinical_v2 class_names."
        )


def read_source_datasets(test_csv_path: Path) -> list[str]:
    if not test_csv_path.exists():
        raise FileNotFoundError(f"Test CSV not found: {test_csv_path}")

    with test_csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if "source_dataset" not in (reader.fieldnames or []):
            raise KeyError("Clinical V2 test CSV is missing `source_dataset`.")
        return [(row.get("source_dataset") or "unknown").strip() for row in reader]


def create_test_loader(
    config: dict,
    class_to_idx: dict[str, int],
    args: argparse.Namespace,
    device: torch.device,
):
    dataset_config = config["dataset"]
    training_config = config["training"]
    test_csv_path = Path(dataset_config["test_csv"])
    image_size = dataset_config.get("image_size") or training_config.get("image_size")
    batch_size = args.batch_size or training_config["batch_size"]
    num_workers = (
        args.num_workers
        if args.num_workers is not None
        else training_config.get("num_workers", 0)
    )

    test_dataset = ImageClassificationDataset(
        csv_path=test_csv_path,
        class_to_idx=class_to_idx,
        transform=get_eval_transforms(image_size),
        label_column=dataset_config.get("label_column", "target_label"),
        class_idx_column=dataset_config.get("class_idx_column", "class_idx"),
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=device.type == "cuda",
    )

    return test_dataset, test_loader


def load_model(model_path: Path, num_classes: int, device: torch.device, backbone_name: str = "efficientnet_b0"):
    if not model_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {model_path}")

    checkpoint = torch.load(model_path, map_location="cpu")
    if "model_state_dict" not in checkpoint:
        raise KeyError("Checkpoint is missing `model_state_dict`.")

    model = build_model(backbone_name=backbone_name, num_classes=num_classes, pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model, checkpoint


def run_inference(model, loader, device: torch.device) -> tuple[list[int], list[int]]:
    true_labels: list[int] = []
    predicted_labels: list[int] = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            logits = model(images)
            predictions = logits.argmax(dim=1)

            true_labels.extend(labels.tolist())
            predicted_labels.extend(predictions.cpu().tolist())

    return true_labels, predicted_labels


def compute_confusion_matrix(
    true_labels: list[int],
    predicted_labels: list[int],
    num_classes: int,
) -> list[list[int]]:
    matrix = [[0 for _ in range(num_classes)] for _ in range(num_classes)]
    for true_label, predicted_label in zip(true_labels, predicted_labels):
        matrix[true_label][predicted_label] += 1
    return matrix


def compute_accuracy(true_labels: list[int], predicted_labels: list[int]) -> float:
    if not true_labels:
        return 0.0
    correct = sum(
        int(true_label == predicted_label)
        for true_label, predicted_label in zip(true_labels, predicted_labels)
    )
    return correct / len(true_labels)


def compute_classification_report(
    confusion_matrix: list[list[int]],
    class_names: list[str],
) -> tuple[list[dict[str, float | int | str]], float, float]:
    num_classes = len(class_names)
    class_rows: list[dict[str, float | int | str]] = []
    f1_scores: list[float] = []
    recalls: list[float] = []

    for class_index, class_name in enumerate(class_names):
        true_positive = confusion_matrix[class_index][class_index]
        false_positive = sum(
            confusion_matrix[row_index][class_index]
            for row_index in range(num_classes)
            if row_index != class_index
        )
        false_negative = sum(
            confusion_matrix[class_index][column_index]
            for column_index in range(num_classes)
            if column_index != class_index
        )
        support = sum(confusion_matrix[class_index])

        precision_denominator = true_positive + false_positive
        recall_denominator = true_positive + false_negative
        precision = (
            true_positive / precision_denominator
            if precision_denominator > 0
            else 0.0
        )
        recall = (
            true_positive / recall_denominator if recall_denominator > 0 else 0.0
        )
        f1_score = (
            0.0
            if precision + recall == 0
            else 2 * precision * recall / (precision + recall)
        )

        f1_scores.append(f1_score)
        recalls.append(recall)
        class_rows.append(
            {
                "class_name": class_name,
                "precision": precision,
                "recall": recall,
                "f1": f1_score,
                "support": support,
            }
        )

    macro_f1 = sum(f1_scores) / num_classes if num_classes > 0 else 0.0
    balanced_accuracy = sum(recalls) / num_classes if num_classes > 0 else 0.0
    return class_rows, macro_f1, balanced_accuracy


def compute_metric_bundle(
    true_labels: list[int],
    predicted_labels: list[int],
    class_names: list[str],
) -> dict:
    confusion_matrix = compute_confusion_matrix(
        true_labels=true_labels,
        predicted_labels=predicted_labels,
        num_classes=len(class_names),
    )
    class_report, macro_f1, balanced_accuracy = compute_classification_report(
        confusion_matrix=confusion_matrix,
        class_names=class_names,
    )
    return {
        "support": len(true_labels),
        "accuracy": compute_accuracy(true_labels, predicted_labels),
        "macro_f1": macro_f1,
        "balanced_accuracy": balanced_accuracy,
        "class_report": class_report,
        "confusion_matrix": confusion_matrix,
    }


def compute_source_metrics(
    sources: list[str],
    true_labels: list[int],
    predicted_labels: list[int],
    class_names: list[str],
) -> list[dict[str, float | int | str]]:
    if not (len(sources) == len(true_labels) == len(predicted_labels)):
        raise ValueError("sources, true_labels, and predicted_labels must align.")

    source_rows: list[dict[str, float | int | str]] = []
    for source_name in ["combined", "google_scin", "fitzpatrick17k"]:
        if source_name == "combined":
            source_true_labels = true_labels
            source_predicted_labels = predicted_labels
        else:
            selected_indices = [
                index for index, source in enumerate(sources) if source == source_name
            ]
            source_true_labels = [true_labels[index] for index in selected_indices]
            source_predicted_labels = [
                predicted_labels[index] for index in selected_indices
            ]

        metric_bundle = compute_metric_bundle(
            source_true_labels,
            source_predicted_labels,
            class_names,
        )
        source_rows.append(
            {
                "source_dataset": source_name,
                "support": metric_bundle["support"],
                "accuracy": metric_bundle["accuracy"],
                "macro_f1": metric_bundle["macro_f1"],
                "balanced_accuracy": metric_bundle["balanced_accuracy"],
            }
        )

    return source_rows


def get_lesion_metrics(class_report: list[dict[str, float | int | str]]) -> dict:
    for row in class_report:
        if row["class_name"] == LESION_ROUTING_CLASS:
            return {
                "class_name": LESION_ROUTING_CLASS,
                "precision": row["precision"],
                "recall": row["recall"],
                "f1": row["f1"],
                "support": row["support"],
            }
    raise KeyError(f"Lesion routing class not found: {LESION_ROUTING_CLASS}")


def save_metrics_json(
    output_path: Path,
    metrics: dict,
    source_metrics: list[dict[str, float | int | str]],
    class_names: list[str],
    checkpoint: dict,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model_context": {
            "task": "clinical image classification with lesion routing",
            "non_diagnostic_note": (
                "Outputs are educational model evaluations. The lesion class is a "
                "routing class for dermoscopic review, not cancer detection."
            ),
        },
        "checkpoint": {
            "epoch": int(checkpoint.get("epoch", -1)),
            "val_macro_f1": float(checkpoint.get("val_macro_f1", 0.0)),
        },
        "class_names": class_names,
        "test_accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "balanced_accuracy": metrics["balanced_accuracy"],
        "num_test_examples": metrics["support"],
        "lesion_routing_class": get_lesion_metrics(metrics["class_report"]),
        "class_report": metrics["class_report"],
        "confusion_matrix": metrics["confusion_matrix"],
        "source_metrics": source_metrics,
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_classification_report_csv(
    output_path: Path,
    class_report: list[dict[str, float | int | str]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["class_name", "precision", "recall", "f1", "support"]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in class_report:
            writer.writerow(
                {
                    "class_name": row["class_name"],
                    "precision": f"{row['precision']:.6f}",
                    "recall": f"{row['recall']:.6f}",
                    "f1": f"{row['f1']:.6f}",
                    "support": row["support"],
                }
            )


def save_source_metrics_csv(
    output_path: Path,
    source_metrics: list[dict[str, float | int | str]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_dataset",
        "support",
        "accuracy",
        "macro_f1",
        "balanced_accuracy",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in source_metrics:
            writer.writerow(
                {
                    "source_dataset": row["source_dataset"],
                    "support": row["support"],
                    "accuracy": f"{row['accuracy']:.6f}",
                    "macro_f1": f"{row['macro_f1']:.6f}",
                    "balanced_accuracy": f"{row['balanced_accuracy']:.6f}",
                }
            )


def save_confusion_matrix_png(
    output_path: Path,
    confusion_matrix: list[list[int]],
    class_names: list[str],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    num_classes = len(class_names)
    cell_size = 112
    left_margin = 320
    top_margin = 160
    right_margin = 60
    bottom_margin = 60
    image_width = left_margin + num_classes * cell_size + right_margin
    image_height = top_margin + num_classes * cell_size + bottom_margin

    image = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    max_value = max(max(row) for row in confusion_matrix) if confusion_matrix else 0

    draw.text((24, 20), "Clinical V2 Confusion Matrix", fill="black", font=font)
    draw.text(
        (24, 48),
        "Rows = true labels, columns = model outputs. Non-diagnostic evaluation.",
        fill="black",
        font=font,
    )

    short_names = [shorten_class_name(class_name) for class_name in class_names]
    for class_index, class_name in enumerate(short_names):
        x = left_margin + class_index * cell_size + 8
        y = top_margin - 70
        draw.text((x, y), class_name, fill="black", font=font)

        row_y = top_margin + class_index * cell_size + cell_size / 2 - 8
        draw.text((24, row_y), class_name, fill="black", font=font)

    for row_index in range(num_classes):
        for column_index in range(num_classes):
            value = confusion_matrix[row_index][column_index]
            intensity = 255 if max_value == 0 else int(255 - (value / max_value) * 180)
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
            draw.text(
                (
                    x0 + (cell_size - text_width) / 2,
                    y0 + (cell_size - text_height) / 2,
                ),
                text,
                fill="black",
                font=font,
            )

    image.save(output_path)


def shorten_class_name(class_name: str) -> str:
    replacements = {
        "Eczema / dermatitis": "Eczema",
        "Urticaria / allergic reaction": "Urticaria",
        "Folliculitis / acne-like": "Folliculitis",
        "Psoriasis / papulosquamous": "Psoriasis",
        LESION_ROUTING_CLASS: "Lesion routing",
    }
    return replacements.get(class_name, class_name)


def save_evaluation_summary(
    output_path: Path,
    metrics: dict,
    source_metrics: list[dict[str, float | int | str]],
    output_paths: dict[str, Path],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lesion_metrics = get_lesion_metrics(metrics["class_report"])
    lines = [
        "# Clinical V2 Evaluation Summary",
        "",
        "This evaluation is for the clinical-image EfficientNet-B0 baseline. "
        "It is educational model evaluation only and must not be presented as diagnosis.",
        "",
        "The lesion class is a routing class for dermoscopic review, not cancer detection.",
        "",
        "## Combined Test Metrics",
        "",
        f"- Test examples: {metrics['support']}",
        f"- Test accuracy: {metrics['accuracy']:.4f}",
        f"- Macro-F1: {metrics['macro_f1']:.4f}",
        f"- Balanced accuracy: {metrics['balanced_accuracy']:.4f}",
        "",
        "## Lesion Routing Class",
        "",
        f"- Precision: {lesion_metrics['precision']:.4f}",
        f"- Recall: {lesion_metrics['recall']:.4f}",
        f"- F1: {lesion_metrics['f1']:.4f}",
        f"- Support: {lesion_metrics['support']}",
        "",
        "## Source-Specific Metrics",
        "",
        "| Source | Support | Accuracy | Macro-F1 | Balanced accuracy |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for row in source_metrics:
        lines.append(
            f"| {row['source_dataset']} | {row['support']} | "
            f"{row['accuracy']:.4f} | {row['macro_f1']:.4f} | "
            f"{row['balanced_accuracy']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Saved Artifacts",
            "",
            f"- Metrics JSON: `{output_paths['metrics_json']}`",
            f"- Classification report CSV: `{output_paths['classification_report']}`",
            f"- Source metrics CSV: `{output_paths['source_metrics']}`",
            f"- Confusion matrix PNG: `{output_paths['confusion_matrix']}`",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def print_metrics(
    metrics: dict,
    source_metrics: list[dict[str, float | int | str]],
    class_names: list[str],
) -> None:
    lesion_metrics = get_lesion_metrics(metrics["class_report"])
    print("Clinical V2 evaluation results")
    print("Non-diagnostic model evaluation; lesion output is routing for review.")
    print("")
    print(f"  Test examples:       {metrics['support']}")
    print(f"  Test accuracy:       {metrics['accuracy']:.4f}")
    print(f"  Macro-F1:            {metrics['macro_f1']:.4f}")
    print(f"  Balanced accuracy:   {metrics['balanced_accuracy']:.4f}")
    print("")
    print("Lesion routing class:")
    print(f"  Precision:           {lesion_metrics['precision']:.4f}")
    print(f"  Recall:              {lesion_metrics['recall']:.4f}")
    print(f"  F1:                  {lesion_metrics['f1']:.4f}")
    print(f"  Support:             {lesion_metrics['support']}")
    print("")
    print("Class-wise metrics:")
    for row in metrics["class_report"]:
        print(
            f"  - {row['class_name']}: "
            f"precision={row['precision']:.4f}, "
            f"recall={row['recall']:.4f}, "
            f"f1={row['f1']:.4f}, "
            f"support={row['support']}"
        )
    print("")
    print("Source-specific metrics:")
    for row in source_metrics:
        print(
            f"  - {row['source_dataset']}: "
            f"support={row['support']}, "
            f"accuracy={row['accuracy']:.4f}, "
            f"macro_f1={row['macro_f1']:.4f}, "
            f"balanced_accuracy={row['balanced_accuracy']:.4f}"
        )
    print("")
    print("Confusion matrix:")
    header = "true\\pred".ljust(18) + "".join(
        shorten_class_name(name)[:14].ljust(16) for name in class_names
    )
    print(header)
    for class_name, row in zip(class_names, metrics["confusion_matrix"]):
        row_text = shorten_class_name(class_name)[:14].ljust(18)
        row_text += "".join(str(value).ljust(16) for value in row)
        print(row_text)


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))

    require_keys(config, ["dataset", "training"], "root")
    require_keys(
        config["dataset"],
        ["test_csv", "image_size", "class_names", "label_column", "class_idx_column"],
        "dataset",
    )
    require_keys(config["training"], ["batch_size", "output_dir"], "training")

    device = select_device()
    model_dir = Path(config["training"]["output_dir"])
    model_path = model_dir / "best_model.pth"
    class_to_idx_path = model_dir / "class_to_idx.json"

    class_to_idx = load_class_to_idx(class_to_idx_path)
    class_names = get_class_names(class_to_idx)
    validate_class_names(config, class_names)
    num_classes = len(class_names)

    test_dataset, test_loader = create_test_loader(
        config=config,
        class_to_idx=class_to_idx,
        args=args,
        device=device,
    )
    sources = read_source_datasets(Path(config["dataset"]["test_csv"]))
    if len(sources) != len(test_dataset):
        raise ValueError("source_dataset rows do not match the test dataset length.")

    backbone_name = config.get("model", {}).get("architecture", "efficientnet_b0")
    model, checkpoint = load_model(
        model_path=model_path,
        num_classes=num_classes,
        device=device,
        backbone_name=backbone_name,
    )
    true_labels, predicted_labels = run_inference(model, test_loader, device)

    metrics = compute_metric_bundle(true_labels, predicted_labels, class_names)
    source_metrics = compute_source_metrics(
        sources=sources,
        true_labels=true_labels,
        predicted_labels=predicted_labels,
        class_names=class_names,
    )

    prefix = args.output_prefix or "clinical_v2"
    output_paths = {
        "metrics_json": Path(f"outputs/metrics/{prefix}_test_metrics.json"),
        "classification_report": Path(f"outputs/metrics/{prefix}_classification_report.csv"),
        "source_metrics": Path(f"outputs/metrics/{prefix}_source_metrics.csv"),
        "confusion_matrix": Path(f"outputs/plots/{prefix}_confusion_matrix.png"),
        "summary": Path(f"docs/model/{prefix}_evaluation_summary.md"),
    }

    save_metrics_json(
        output_paths["metrics_json"],
        metrics,
        source_metrics,
        class_names,
        checkpoint,
    )
    save_classification_report_csv(
        output_paths["classification_report"],
        metrics["class_report"],
    )
    save_source_metrics_csv(output_paths["source_metrics"], source_metrics)
    save_confusion_matrix_png(
        output_paths["confusion_matrix"],
        metrics["confusion_matrix"],
        class_names,
    )
    save_evaluation_summary(
        output_paths["summary"],
        metrics,
        source_metrics,
        output_paths,
    )

    print_metrics(metrics, source_metrics, class_names)
    print("")
    print(f"Saved metrics JSON: {output_paths['metrics_json']}")
    print(f"Saved classification report CSV: {output_paths['classification_report']}")
    print(f"Saved source metrics CSV: {output_paths['source_metrics']}")
    print(f"Saved confusion matrix PNG: {output_paths['confusion_matrix']}")
    print(f"Saved evaluation summary: {output_paths['summary']}")


if __name__ == "__main__":
    main()
