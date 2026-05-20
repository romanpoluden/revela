from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from src.data.dataset import ImageClassificationDataset
from src.data.transforms import get_eval_transforms
from src.model.evaluate_clinical_v2 import (
    get_class_names,
    load_class_to_idx,
    load_config,
    load_model,
    require_keys,
    select_device,
    validate_class_names,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fit temperature scaling for the frozen Clinical V2 model and evaluate "
            "test-set calibration before and after scaling."
        )
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
        help="Optional override for calibration/evaluation batch size.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=None,
        help="Optional override for the DataLoader worker count.",
    )
    parser.add_argument(
        "--num-bins",
        type=int,
        default=10,
        help="Number of confidence bins for ECE and reliability tables.",
    )
    return parser.parse_args()


def create_split_loader(
    config: dict,
    class_to_idx: dict[str, int],
    split: str,
    args: argparse.Namespace,
    device: torch.device,
) -> tuple[ImageClassificationDataset, DataLoader]:
    dataset_config = config["dataset"]
    training_config = config["training"]
    csv_key = f"{split}_csv"
    csv_path = Path(dataset_config[csv_key])
    image_size = dataset_config.get("image_size") or training_config.get("image_size")
    batch_size = args.batch_size or training_config["batch_size"]
    num_workers = (
        args.num_workers
        if args.num_workers is not None
        else training_config.get("num_workers", 0)
    )

    dataset = ImageClassificationDataset(
        csv_path=csv_path,
        class_to_idx=class_to_idx,
        transform=get_eval_transforms(image_size),
        label_column=dataset_config.get("label_column", "target_label"),
        class_idx_column=dataset_config.get("class_idx_column", "class_idx"),
    )
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=device.type == "cuda",
    )
    return dataset, loader


def collect_logits_and_labels(
    model,
    loader: DataLoader,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    logits_batches: list[torch.Tensor] = []
    label_batches: list[torch.Tensor] = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            logits = model(images)
            logits_batches.append(logits.cpu())
            label_batches.append(labels.cpu())

    if not logits_batches:
        raise ValueError("Cannot calibrate or evaluate on an empty split.")

    return torch.cat(logits_batches), torch.cat(label_batches).long()


def compute_nll(logits: torch.Tensor, labels: torch.Tensor) -> float:
    return float(F.cross_entropy(logits, labels).item())


def compute_brier_score(probabilities: torch.Tensor, labels: torch.Tensor) -> float:
    one_hot_labels = F.one_hot(labels, num_classes=probabilities.shape[1]).float()
    squared_error = (probabilities - one_hot_labels).pow(2).sum(dim=1)
    return float(squared_error.mean().item())


def compute_reliability_bins(
    probabilities: torch.Tensor,
    labels: torch.Tensor,
    num_bins: int,
) -> tuple[float, list[dict[str, float | int]]]:
    if num_bins <= 0:
        raise ValueError("--num-bins must be greater than 0.")

    confidences, predictions = probabilities.max(dim=1)
    correctness = predictions.eq(labels).float()
    total_examples = labels.numel()
    bin_rows: list[dict[str, float | int]] = []
    ece = 0.0

    for bin_index in range(num_bins):
        bin_lower = bin_index / num_bins
        bin_upper = (bin_index + 1) / num_bins
        if bin_index == num_bins - 1:
            in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
        else:
            in_bin = (confidences >= bin_lower) & (confidences < bin_upper)

        bin_count = int(in_bin.sum().item())
        if bin_count > 0:
            bin_accuracy = float(correctness[in_bin].mean().item())
            bin_confidence = float(confidences[in_bin].mean().item())
        else:
            bin_accuracy = 0.0
            bin_confidence = 0.0

        bin_weight = bin_count / total_examples if total_examples else 0.0
        calibration_gap = abs(bin_accuracy - bin_confidence)
        ece += bin_weight * calibration_gap
        bin_rows.append(
            {
                "bin_index": bin_index,
                "bin_lower": bin_lower,
                "bin_upper": bin_upper,
                "count": bin_count,
                "accuracy": bin_accuracy,
                "avg_confidence": bin_confidence,
                "calibration_gap": calibration_gap,
            }
        )

    return float(ece), bin_rows


def compute_confidence_summary(probabilities: torch.Tensor) -> dict[str, float]:
    confidences = probabilities.max(dim=1).values
    return {
        "mean": float(confidences.mean().item()),
        "std": float(confidences.std(unbiased=False).item()),
        "min": float(confidences.min().item()),
        "p25": float(torch.quantile(confidences, 0.25).item()),
        "median": float(torch.quantile(confidences, 0.50).item()),
        "p75": float(torch.quantile(confidences, 0.75).item()),
        "max": float(confidences.max().item()),
    }


def compute_calibration_metrics(
    logits: torch.Tensor,
    labels: torch.Tensor,
    num_bins: int,
) -> tuple[dict[str, float | int | bool | dict[str, float]], list[dict[str, float | int]]]:
    probabilities = F.softmax(logits, dim=1)
    predictions = probabilities.argmax(dim=1)
    ece, bins = compute_reliability_bins(probabilities, labels, num_bins)
    accuracy = float(predictions.eq(labels).float().mean().item())
    metrics = {
        "support": int(labels.numel()),
        "accuracy": accuracy,
        "ece": ece,
        "nll": compute_nll(logits, labels),
        "brier_score": compute_brier_score(probabilities, labels),
        "confidence_summary": compute_confidence_summary(probabilities),
    }
    return metrics, bins


def fit_temperature(
    validation_logits: torch.Tensor,
    validation_labels: torch.Tensor,
) -> tuple[float, float]:
    log_temperature = torch.nn.Parameter(torch.zeros(1))
    optimizer = torch.optim.LBFGS(
        [log_temperature],
        lr=0.1,
        max_iter=50,
        line_search_fn="strong_wolfe",
    )

    def closure() -> torch.Tensor:
        optimizer.zero_grad()
        temperature = log_temperature.exp().clamp(min=1e-4, max=100.0)
        loss = F.cross_entropy(validation_logits / temperature, validation_labels)
        loss.backward()
        return loss

    optimizer.step(closure)
    with torch.no_grad():
        temperature = float(log_temperature.exp().clamp(min=1e-4, max=100.0).item())
        scaled_nll = compute_nll(validation_logits / temperature, validation_labels)
    return temperature, scaled_nll


def with_temperature(logits: torch.Tensor, temperature: float) -> torch.Tensor:
    if temperature <= 0:
        raise ValueError("temperature must be greater than 0.")
    return logits / temperature


def assert_predictions_unchanged(
    original_logits: torch.Tensor,
    calibrated_logits: torch.Tensor,
) -> bool:
    original_predictions = original_logits.argmax(dim=1)
    calibrated_predictions = calibrated_logits.argmax(dim=1)
    return bool(original_predictions.eq(calibrated_predictions).all().item())


def save_temperature_json(
    output_path: Path,
    temperature: float,
    validation_nll_before: float,
    validation_nll_after: float,
    config_path: Path,
    model_path: Path,
    class_to_idx_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "temperature": temperature,
        "method": "scalar_temperature_scaling",
        "fit_split": "validation",
        "objective": "negative_log_likelihood",
        "validation_nll_before": validation_nll_before,
        "validation_nll_after": validation_nll_after,
        "model_path": str(model_path),
        "class_to_idx_path": str(class_to_idx_path),
        "config_path": str(config_path),
        "notes": [
            "The classifier checkpoint is frozen; no model weights are retrained.",
            "Predicted classes are unchanged by positive scalar temperature scaling.",
            "Calibrated confidence is model confidence, not clinical or diagnostic certainty.",
        ],
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_metrics_json(
    output_path: Path,
    payload: dict,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_reliability_bins_csv(
    output_path: Path,
    before_bins: list[dict[str, float | int]],
    after_bins: list[dict[str, float | int]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "split",
        "calibration",
        "bin_index",
        "bin_lower",
        "bin_upper",
        "count",
        "accuracy",
        "avg_confidence",
        "calibration_gap",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for calibration_name, rows in [
            ("before_temperature_scaling", before_bins),
            ("after_temperature_scaling", after_bins),
        ]:
            for row in rows:
                writer.writerow(
                    {
                        "split": "test",
                        "calibration": calibration_name,
                        "bin_index": row["bin_index"],
                        "bin_lower": f"{row['bin_lower']:.6f}",
                        "bin_upper": f"{row['bin_upper']:.6f}",
                        "count": row["count"],
                        "accuracy": f"{row['accuracy']:.6f}",
                        "avg_confidence": f"{row['avg_confidence']:.6f}",
                        "calibration_gap": f"{row['calibration_gap']:.6f}",
                    }
                )


def save_summary(
    output_path: Path,
    temperature: float,
    validation_metrics_before: dict,
    validation_metrics_after: dict,
    test_metrics_before: dict,
    test_metrics_after: dict,
    predictions_unchanged: bool,
    output_paths: dict[str, Path],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Clinical V2 Confidence Calibration Summary",
        "",
        "This calibration analysis fits a single scalar temperature on the Clinical V2 "
        "validation split and evaluates the frozen test split before and after scaling.",
        "",
        "The classifier weights are not retrained, the taxonomy is unchanged, and the "
        "app/model registry wiring is unchanged.",
        "",
        "Model confidence is not clinical certainty. Calibrated confidence is still not "
        "diagnostic certainty. These results do not support any diagnosis, treatment, "
        "clinical-readiness, or autonomous decision-making claim.",
        "",
        "## Temperature",
        "",
        f"- Fitted temperature: {temperature:.6f}",
        f"- Validation NLL before scaling: {validation_metrics_before['nll']:.6f}",
        f"- Validation NLL after scaling: {validation_metrics_after['nll']:.6f}",
        "",
        "## Frozen Test Split",
        "",
        f"- Test examples: {test_metrics_before['support']}",
        f"- Predictions unchanged after calibration: {predictions_unchanged}",
        "",
        "| Metric | Before | After |",
        "| --- | ---: | ---: |",
        f"| Accuracy | {test_metrics_before['accuracy']:.6f} | {test_metrics_after['accuracy']:.6f} |",
        f"| ECE | {test_metrics_before['ece']:.6f} | {test_metrics_after['ece']:.6f} |",
        f"| NLL | {test_metrics_before['nll']:.6f} | {test_metrics_after['nll']:.6f} |",
        f"| Brier score | {test_metrics_before['brier_score']:.6f} | {test_metrics_after['brier_score']:.6f} |",
        "",
        "## Confidence Distribution",
        "",
        "| Statistic | Before | After |",
        "| --- | ---: | ---: |",
    ]

    before_summary = test_metrics_before["confidence_summary"]
    after_summary = test_metrics_after["confidence_summary"]
    for key in ["mean", "std", "min", "p25", "median", "p75", "max"]:
        lines.append(f"| {key} | {before_summary[key]:.6f} | {after_summary[key]:.6f} |")

    lines.extend(
        [
            "",
            "## Saved Artifacts",
            "",
            f"- Temperature JSON: `{output_paths['temperature_json']}`",
            f"- Metrics JSON: `{output_paths['metrics_json']}`",
            f"- Reliability bins CSV: `{output_paths['reliability_bins']}`",
            "",
            "Reliability bins compare average model confidence with empirical accuracy "
            "within confidence intervals. They describe model calibration on this test "
            "split only, not clinical certainty.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def print_summary(
    temperature: float,
    validation_metrics_before: dict,
    validation_metrics_after: dict,
    test_metrics_before: dict,
    test_metrics_after: dict,
    predictions_unchanged: bool,
) -> None:
    print("Clinical V2 confidence calibration")
    print("Non-diagnostic model-confidence analysis only.")
    print("")
    print(f"  Temperature:                 {temperature:.6f}")
    print(f"  Validation NLL before:       {validation_metrics_before['nll']:.6f}")
    print(f"  Validation NLL after:        {validation_metrics_after['nll']:.6f}")
    print("")
    print("Frozen test split:")
    print(f"  Test examples:               {test_metrics_before['support']}")
    print(f"  Predictions unchanged:       {predictions_unchanged}")
    print(f"  ECE before -> after:         {test_metrics_before['ece']:.6f} -> {test_metrics_after['ece']:.6f}")
    print(f"  NLL before -> after:         {test_metrics_before['nll']:.6f} -> {test_metrics_after['nll']:.6f}")
    print(f"  Brier before -> after:       {test_metrics_before['brier_score']:.6f} -> {test_metrics_after['brier_score']:.6f}")


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)

    require_keys(config, ["dataset", "training"], "root")
    require_keys(
        config["dataset"],
        [
            "val_csv",
            "test_csv",
            "image_size",
            "class_names",
            "label_column",
            "class_idx_column",
        ],
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

    _, validation_loader = create_split_loader(
        config=config,
        class_to_idx=class_to_idx,
        split="val",
        args=args,
        device=device,
    )
    _, test_loader = create_split_loader(
        config=config,
        class_to_idx=class_to_idx,
        split="test",
        args=args,
        device=device,
    )

    model, checkpoint = load_model(
        model_path=model_path,
        num_classes=num_classes,
        device=device,
    )
    validation_logits, validation_labels = collect_logits_and_labels(
        model,
        validation_loader,
        device,
    )
    test_logits, test_labels = collect_logits_and_labels(model, test_loader, device)

    validation_metrics_before, _ = compute_calibration_metrics(
        validation_logits,
        validation_labels,
        args.num_bins,
    )
    temperature, validation_nll_after = fit_temperature(
        validation_logits,
        validation_labels,
    )
    validation_logits_after = with_temperature(validation_logits, temperature)
    validation_metrics_after, _ = compute_calibration_metrics(
        validation_logits_after,
        validation_labels,
        args.num_bins,
    )
    validation_metrics_after["nll"] = validation_nll_after

    test_logits_after = with_temperature(test_logits, temperature)
    predictions_unchanged = assert_predictions_unchanged(test_logits, test_logits_after)
    test_metrics_before, test_bins_before = compute_calibration_metrics(
        test_logits,
        test_labels,
        args.num_bins,
    )
    test_metrics_after, test_bins_after = compute_calibration_metrics(
        test_logits_after,
        test_labels,
        args.num_bins,
    )

    output_paths = {
        "temperature_json": model_dir / "calibration_temperature.json",
        "metrics_json": Path("outputs/metrics/clinical_v2_calibration_metrics.json"),
        "reliability_bins": Path("outputs/metrics/clinical_v2_reliability_bins.csv"),
        "summary": Path("docs/model/clinical_v2_confidence_calibration_summary.md"),
    }
    save_temperature_json(
        output_paths["temperature_json"],
        temperature,
        validation_metrics_before["nll"],
        validation_metrics_after["nll"],
        config_path,
        model_path,
        class_to_idx_path,
    )
    metrics_payload = {
        "model_context": {
            "task": "clinical image classification with lesion routing",
            "non_diagnostic_note": (
                "Confidence is model confidence, not clinical certainty. Temperature "
                "scaling calibrates confidence interpretation only; it is not diagnosis, "
                "treatment guidance, or a clinical-readiness claim."
            ),
        },
        "checkpoint": {
            "epoch": int(checkpoint.get("epoch", -1)),
            "val_macro_f1": float(checkpoint.get("val_macro_f1", 0.0)),
        },
        "class_names": class_names,
        "temperature": temperature,
        "num_bins": args.num_bins,
        "validation": {
            "before_temperature_scaling": validation_metrics_before,
            "after_temperature_scaling": validation_metrics_after,
        },
        "test": {
            "predictions_unchanged_after_calibration": predictions_unchanged,
            "before_temperature_scaling": test_metrics_before,
            "after_temperature_scaling": test_metrics_after,
        },
    }
    save_metrics_json(output_paths["metrics_json"], metrics_payload)
    save_reliability_bins_csv(
        output_paths["reliability_bins"],
        test_bins_before,
        test_bins_after,
    )
    save_summary(
        output_paths["summary"],
        temperature,
        validation_metrics_before,
        validation_metrics_after,
        test_metrics_before,
        test_metrics_after,
        predictions_unchanged,
        output_paths,
    )

    print_summary(
        temperature,
        validation_metrics_before,
        validation_metrics_after,
        test_metrics_before,
        test_metrics_after,
        predictions_unchanged,
    )
    print("")
    print(f"Saved temperature JSON: {output_paths['temperature_json']}")
    print(f"Saved metrics JSON: {output_paths['metrics_json']}")
    print(f"Saved reliability bins CSV: {output_paths['reliability_bins']}")
    print(f"Saved calibration summary: {output_paths['summary']}")


if __name__ == "__main__":
    main()
