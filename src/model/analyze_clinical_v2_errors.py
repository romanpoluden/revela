from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import torch

from src.model.evaluate_clinical_v2 import (
    LESION_ROUTING_CLASS,
    create_test_loader,
    get_class_names,
    load_class_to_idx,
    load_config,
    load_model,
    require_keys,
    select_device,
    validate_class_names,
)


DEFAULT_CONFIG_PATH = Path("config/clinical_v2_config.yaml")
DEFAULT_OUTPUT_DIR = Path("outputs/error_analysis")
DEFAULT_SUMMARY_PATH = Path("docs/model/clinical_v2_error_analysis.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze Clinical V2 test-set prediction errors."
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the Clinical V2 YAML config file.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Optional override for the inference batch size.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=None,
        help="Optional override for the DataLoader worker count.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for CSV error-analysis artifacts.",
    )
    parser.add_argument(
        "--summary-path",
        default=str(DEFAULT_SUMMARY_PATH),
        help="Path for the markdown error-analysis summary.",
    )
    return parser.parse_args()


def read_test_rows(test_csv_path: Path) -> list[dict[str, str]]:
    if not test_csv_path.exists():
        raise FileNotFoundError(f"Test CSV not found: {test_csv_path}")

    required_columns = [
        "image_path",
        "source_dataset",
        "raw_label",
        "target_label",
        "class_idx",
    ]
    with test_csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_columns = [
            column for column in required_columns if column not in fieldnames
        ]
        if missing_columns:
            missing_text = ", ".join(missing_columns)
            raise KeyError(f"Clinical V2 test CSV is missing: {missing_text}")
        return [clean_metadata_row(row) for row in reader]


def clean_metadata_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "image_path": (row.get("image_path") or "").strip(),
        "source_dataset": (row.get("source_dataset") or "unknown").strip()
        or "unknown",
        "raw_label": (row.get("raw_label") or "unknown").strip() or "unknown",
        "target_label": (row.get("target_label") or "").strip(),
        "class_idx": (row.get("class_idx") or "").strip(),
    }


def safe_probability_column(class_name: str) -> str:
    safe_name = class_name.lower()
    safe_name = safe_name.replace("&", " and ")
    safe_name = re.sub(r"[^a-z0-9]+", "_", safe_name)
    safe_name = safe_name.strip("_")
    return f"prob_{safe_name or 'class'}"


def run_inference_with_probabilities(
    model,
    loader,
    device: torch.device,
) -> tuple[list[int], list[int], list[float], list[list[float]]]:
    true_labels: list[int] = []
    predicted_labels: list[int] = []
    predicted_confidences: list[float] = []
    probabilities_by_row: list[list[float]] = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            logits = model(images)
            probabilities = torch.softmax(logits, dim=1)
            confidences, predictions = probabilities.max(dim=1)

            true_labels.extend(labels.tolist())
            predicted_labels.extend(predictions.cpu().tolist())
            predicted_confidences.extend(confidences.cpu().tolist())
            probabilities_by_row.extend(probabilities.cpu().tolist())

    return true_labels, predicted_labels, predicted_confidences, probabilities_by_row


def build_prediction_rows(
    metadata_rows: list[dict[str, str]],
    true_labels: list[int],
    predicted_labels: list[int],
    predicted_confidences: list[float],
    probabilities_by_row: list[list[float]],
    class_names: list[str],
) -> list[dict[str, Any]]:
    if not (
        len(metadata_rows)
        == len(true_labels)
        == len(predicted_labels)
        == len(predicted_confidences)
        == len(probabilities_by_row)
    ):
        raise ValueError("Metadata rows and model outputs must have the same length.")

    probability_columns = [safe_probability_column(name) for name in class_names]
    if len(set(probability_columns)) != len(probability_columns):
        raise ValueError("Class names produced duplicate probability column names.")

    rows: list[dict[str, Any]] = []
    for index, metadata in enumerate(metadata_rows):
        true_label = class_names[true_labels[index]]
        predicted_label = class_names[predicted_labels[index]]
        row: dict[str, Any] = {
            "image_path": metadata["image_path"],
            "source_dataset": metadata["source_dataset"],
            "raw_label": metadata["raw_label"],
            "target_label": true_label,
            "predicted_label": predicted_label,
            "predicted_confidence": predicted_confidences[index],
            "is_correct": true_label == predicted_label,
        }
        for column_name, probability in zip(
            probability_columns,
            probabilities_by_row[index],
        ):
            row[column_name] = probability
        rows.append(row)

    return rows


def compute_error_rows_by_raw_label(
    prediction_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"total_examples": 0, "error_count": 0}
    )
    for row in prediction_rows:
        key = (row["raw_label"], row["source_dataset"])
        grouped[key]["total_examples"] += 1
        grouped[key]["error_count"] += int(not row["is_correct"])

    return sorted(
        build_error_rate_rows(grouped, ["raw_label", "source_dataset"]),
        key=lambda row: (-row["error_count"], -row["total_examples"], row["raw_label"]),
    )


def compute_error_rows_by_source(
    prediction_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str], dict[str, Any]] = defaultdict(
        lambda: {"total_examples": 0, "error_count": 0}
    )
    for row in prediction_rows:
        key = (row["source_dataset"],)
        grouped[key]["total_examples"] += 1
        grouped[key]["error_count"] += int(not row["is_correct"])

    return sorted(
        build_error_rate_rows(grouped, ["source_dataset"]),
        key=lambda row: row["source_dataset"],
    )


def compute_error_rows_by_true_class(
    prediction_rows: list[dict[str, Any]],
    class_names: list[str],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str], dict[str, Any]] = defaultdict(
        lambda: {"total_examples": 0, "error_count": 0}
    )
    for row in prediction_rows:
        key = (row["target_label"],)
        grouped[key]["total_examples"] += 1
        grouped[key]["error_count"] += int(not row["is_correct"])

    rows_by_class = {
        row["target_label"]: row
        for row in build_error_rate_rows(grouped, ["target_label"])
    }
    return [
        rows_by_class.get(
            class_name,
            {
                "target_label": class_name,
                "total_examples": 0,
                "error_count": 0,
                "error_rate": 0.0,
            },
        )
        for class_name in class_names
    ]


def build_error_rate_rows(
    grouped: dict[tuple[str, ...], dict[str, Any]],
    key_names: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, counts in grouped.items():
        total_examples = counts["total_examples"]
        error_count = counts["error_count"]
        row = {name: value for name, value in zip(key_names, key)}
        row.update(
            {
                "total_examples": total_examples,
                "error_count": error_count,
                "error_rate": error_count / total_examples if total_examples else 0.0,
            }
        )
        rows.append(row)
    return rows


def compute_confusion_pairs(
    prediction_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors = [row for row in prediction_rows if not row["is_correct"]]
    pair_counts = Counter(
        (row["target_label"], row["predicted_label"]) for row in errors
    )
    total_errors = len(errors)

    rows = []
    for (target_label, predicted_label), count in pair_counts.most_common():
        rows.append(
            {
                "target_label": target_label,
                "predicted_label": predicted_label,
                "count": count,
                "percentage_of_all_errors": (
                    count / total_errors if total_errors else 0.0
                ),
            }
        )
    return rows


def save_csv(
    output_path: Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    field: format_csv_value(row.get(field, ""))
                    for field in fieldnames
                }
            )


def format_csv_value(value: Any) -> Any:
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, bool):
        return str(value).lower()
    return value


def summarize_focus_notes(prediction_rows: list[dict[str, Any]]) -> dict[str, Any]:
    urticaria_class = "Urticaria / allergic reaction"
    eczema_class = "Eczema / dermatitis"

    urticaria_false_positives = [
        row
        for row in prediction_rows
        if row["predicted_label"] == urticaria_class
        and row["target_label"] != urticaria_class
    ]
    eczema_false_negatives = [
        row
        for row in prediction_rows
        if row["target_label"] == eczema_class
        and row["predicted_label"] != eczema_class
    ]
    scin_errors = [
        row
        for row in prediction_rows
        if row["source_dataset"] == "google_scin" and not row["is_correct"]
    ]
    lesion_false_negatives = [
        row
        for row in prediction_rows
        if row["target_label"] == LESION_ROUTING_CLASS
        and row["predicted_label"] != LESION_ROUTING_CLASS
    ]

    return {
        "urticaria_false_positives": len(urticaria_false_positives),
        "eczema_false_negatives": len(eczema_false_negatives),
        "scin_errors": len(scin_errors),
        "lesion_false_negatives": len(lesion_false_negatives),
        "urticaria_fp_predictions": top_counter_values(
            row["target_label"] for row in urticaria_false_positives
        ),
        "eczema_fn_predictions": top_counter_values(
            row["predicted_label"] for row in eczema_false_negatives
        ),
        "scin_error_predictions": top_counter_values(
            row["predicted_label"] for row in scin_errors
        ),
        "lesion_fn_predictions": top_counter_values(
            row["predicted_label"] for row in lesion_false_negatives
        ),
    }


def top_counter_values(
    values: Iterable[str],
    limit: int = 3,
) -> list[tuple[str, int]]:
    return Counter(values).most_common(limit)


def save_markdown_summary(
    output_path: Path,
    artifact_paths: dict[str, Path],
    prediction_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    true_class_rows: list[dict[str, Any]],
    confusion_pair_rows: list[dict[str, Any]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_examples = len(prediction_rows)
    error_count = sum(int(not row["is_correct"]) for row in prediction_rows)
    error_rate = error_count / total_examples if total_examples else 0.0
    focus_notes = summarize_focus_notes(prediction_rows)

    lines = [
        "# Clinical V2 Error Analysis",
        "",
        "This summarizes test-set prediction errors for the Clinical V2 "
        "EfficientNet-B0 classifier with lesion-routing output. It is a "
        "non-diagnostic model analysis for understanding model behavior.",
        "",
        "## Artifacts",
        "",
        f"- Per-image predictions: `{artifact_paths['predictions']}`",
        f"- Errors by raw label: `{artifact_paths['raw_label_errors']}`",
        f"- Errors by source: `{artifact_paths['source_errors']}`",
        f"- Confusion pairs: `{artifact_paths['confusion_pairs']}`",
        "",
        "## Overall Errors",
        "",
        f"- Test examples: {total_examples}",
        f"- Error count: {error_count}",
        f"- Error rate: {error_rate:.4f}",
        "",
        "## Errors by Source",
        "",
        "| Source | Total examples | Error count | Error rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in source_rows:
        lines.append(
            f"| {row['source_dataset']} | {row['total_examples']} | "
            f"{row['error_count']} | {row['error_rate']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Errors by True Class",
            "",
            "| True class | Total examples | Error count | Error rate |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in true_class_rows:
        lines.append(
            f"| {row['target_label']} | {row['total_examples']} | "
            f"{row['error_count']} | {row['error_rate']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Top Confusion Pairs",
            "",
            "| True class | Predicted class | Count | Share of all errors |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for row in confusion_pair_rows[:10]:
        lines.append(
            f"| {row['target_label']} | {row['predicted_label']} | "
            f"{row['count']} | {row['percentage_of_all_errors']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            f"- Urticaria false positives: {focus_notes['urticaria_false_positives']}. "
            f"Most common true classes: {format_top_values(focus_notes['urticaria_fp_predictions'])}.",
            f"- Eczema false negatives: {focus_notes['eczema_false_negatives']}. "
            f"Most common predicted classes: {format_top_values(focus_notes['eczema_fn_predictions'])}.",
            f"- SCIN-specific errors: {focus_notes['scin_errors']}. "
            f"Most common predicted classes in those errors: {format_top_values(focus_notes['scin_error_predictions'])}.",
            f"- Lesion-routing false negatives: {focus_notes['lesion_false_negatives']}. "
            f"Most common predicted classes: {format_top_values(focus_notes['lesion_fn_predictions'])}.",
            "",
            "## Limitation",
            "",
            "This is educational model analysis only. It is not diagnosis, clinical "
            "guidance, or a claim of clinical readiness.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def format_top_values(values: list[tuple[str, int]]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{label} ({count})" for label, count in values)


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
    test_rows = read_test_rows(Path(config["dataset"]["test_csv"]))

    test_dataset, test_loader = create_test_loader(
        config=config,
        class_to_idx=class_to_idx,
        args=args,
        device=device,
    )
    if len(test_rows) != len(test_dataset):
        raise ValueError("Test CSV metadata rows do not match the test dataset length.")

    model, _checkpoint = load_model(
        model_path=model_path,
        num_classes=len(class_names),
        device=device,
    )
    (
        true_labels,
        predicted_labels,
        predicted_confidences,
        probabilities_by_row,
    ) = run_inference_with_probabilities(model, test_loader, device)

    prediction_rows = build_prediction_rows(
        metadata_rows=test_rows,
        true_labels=true_labels,
        predicted_labels=predicted_labels,
        predicted_confidences=predicted_confidences,
        probabilities_by_row=probabilities_by_row,
        class_names=class_names,
    )
    raw_label_rows = compute_error_rows_by_raw_label(prediction_rows)
    source_rows = compute_error_rows_by_source(prediction_rows)
    true_class_rows = compute_error_rows_by_true_class(prediction_rows, class_names)
    confusion_pair_rows = compute_confusion_pairs(prediction_rows)

    output_dir = Path(args.output_dir)
    artifact_paths = {
        "predictions": output_dir / "clinical_v2_test_predictions.csv",
        "raw_label_errors": output_dir / "clinical_v2_errors_by_raw_label.csv",
        "source_errors": output_dir / "clinical_v2_errors_by_source.csv",
        "confusion_pairs": output_dir / "clinical_v2_confusion_pairs.csv",
    }

    probability_columns = [safe_probability_column(name) for name in class_names]
    save_csv(
        artifact_paths["predictions"],
        prediction_rows,
        [
            "image_path",
            "source_dataset",
            "raw_label",
            "target_label",
            "predicted_label",
            "predicted_confidence",
            *probability_columns,
            "is_correct",
        ],
    )
    save_csv(
        artifact_paths["raw_label_errors"],
        raw_label_rows,
        [
            "raw_label",
            "source_dataset",
            "total_examples",
            "error_count",
            "error_rate",
        ],
    )
    save_csv(
        artifact_paths["source_errors"],
        source_rows,
        ["source_dataset", "total_examples", "error_count", "error_rate"],
    )
    save_csv(
        artifact_paths["confusion_pairs"],
        confusion_pair_rows,
        [
            "target_label",
            "predicted_label",
            "count",
            "percentage_of_all_errors",
        ],
    )
    save_markdown_summary(
        Path(args.summary_path),
        artifact_paths,
        prediction_rows,
        source_rows,
        true_class_rows,
        confusion_pair_rows,
    )

    total_examples = len(prediction_rows)
    error_count = sum(int(not row["is_correct"]) for row in prediction_rows)
    error_rate = error_count / total_examples if total_examples else 0.0
    print("Clinical V2 error analysis complete")
    print(f"  Test examples: {total_examples}")
    print(f"  Error count:   {error_count}")
    print(f"  Error rate:    {error_rate:.4f}")
    print("")
    print(f"Saved per-image predictions: {artifact_paths['predictions']}")
    print(f"Saved errors by raw label:   {artifact_paths['raw_label_errors']}")
    print(f"Saved errors by source:      {artifact_paths['source_errors']}")
    print(f"Saved confusion pairs:       {artifact_paths['confusion_pairs']}")
    print(f"Saved markdown summary:      {Path(args.summary_path)}")


if __name__ == "__main__":
    main()
