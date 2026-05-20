from __future__ import annotations

import argparse
import copy
import csv
import json
from pathlib import Path

from src.model.analyze_clinical_v2_errors import compute_focus_error_metrics
from src.model.evaluate_clinical_v2 import (
    LESION_ROUTING_CLASS,
    compute_metric_bundle,
    compute_source_metrics,
    create_test_loader,
    get_class_names,
    get_lesion_metrics,
    load_class_to_idx,
    load_config,
    load_model,
    read_source_datasets,
    run_inference,
    save_classification_report_csv,
    save_confusion_matrix_png,
    save_source_metrics_csv,
    select_device,
    validate_class_names,
)


BASELINE_TEST_CSV = Path("data/processed/clinical_v2/test.csv")
METRICS_DIR = Path("outputs/metrics")
PLOTS_DIR = Path("outputs/plots")
SUMMARY_PATH = Path("docs/model/clinical_v2_variant_comparison_summary.md")

BASELINE_CRITERIA = {
    "combined_macro_f1": 0.6420,
    "combined_balanced_accuracy": 0.6571,
    "google_scin_macro_f1": 0.4028,
    "google_scin_error_rate": 0.4278,
    "fitzpatrick17k_macro_f1": 0.6366,
    "lesion_routing_false_negatives": 76,
    "eczema_to_urticaria": 91,
    "urticaria_false_positives": 160,
}

VARIANTS = [
    {
        "name": "baseline_clinical_v2",
        "config": "config/clinical_v2_config.yaml",
        "model_dir": "models/clinical_v2_effnet_b0",
    },
    {
        "name": "clinical_v2_class_sampler",
        "config": "config/clinical_v2_class_sampler_config.yaml",
        "model_dir": "models/clinical_v2_class_sampler_effnet_b0",
    },
    {
        "name": "clinical_v2_source_class_sampler",
        "config": "config/clinical_v2_source_class_sampler_config.yaml",
        "model_dir": "models/clinical_v2_source_class_sampler_effnet_b0",
    },
    {
        "name": "clinical_v2_high_confidence_067",
        "config": "config/clinical_v2_high_confidence_067_config.yaml",
        "model_dir": "models/clinical_v2_high_confidence_067_effnet_b0",
    },
    {
        "name": "clinical_v2_high_confidence_075",
        "config": "config/clinical_v2_high_confidence_075_config.yaml",
        "model_dir": "models/clinical_v2_high_confidence_075_effnet_b0",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate Clinical V2 baseline and improvement variants."
    )
    parser.add_argument(
        "--test-csv",
        default=str(BASELINE_TEST_CSV),
        help="Common test CSV for direct variant comparison.",
    )
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--num-workers", type=int, default=None)
    return parser.parse_args()


def verify_artifacts(model_dir: Path) -> dict[str, bool]:
    return {
        "best_model.pth": (model_dir / "best_model.pth").exists(),
        "class_to_idx.json": (model_dir / "class_to_idx.json").exists(),
        "training_history.csv": (model_dir / "training_history.csv").exists(),
    }


def is_available(artifact_status: dict[str, bool]) -> bool:
    return all(artifact_status.values())


def source_lookup(source_rows: list[dict]) -> dict[str, dict]:
    return {str(row["source_dataset"]): row for row in source_rows}


def error_rate(row: dict) -> float:
    if not row["support"]:
        return 0.0
    return 1.0 - float(row["accuracy"])


def write_confusion_matrix_csv(
    output_path: Path,
    confusion_matrix: list[list[int]],
    class_names: list[str],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["true_label"] + class_names)
        for class_name, row in zip(class_names, confusion_matrix):
            writer.writerow([class_name] + row)


def evaluate_variant(
    variant: dict,
    baseline_config: dict,
    test_csv: Path,
    args: argparse.Namespace,
    device,
) -> dict:
    config_path = Path(variant["config"])
    model_dir = Path(variant["model_dir"])
    artifact_status = verify_artifacts(model_dir)
    config = load_config(config_path)
    configured_test_csv = Path(config["dataset"]["test_csv"])

    result = {
        "name": variant["name"],
        "config": str(config_path),
        "model_dir": str(model_dir),
        "configured_test_csv": str(configured_test_csv),
        "evaluated_test_csv": str(test_csv),
        "test_split_note": "Evaluated on original Clinical V2 baseline test split for direct comparison.",
        "artifact_status": artifact_status,
        "status": "available" if is_available(artifact_status) else "unavailable",
    }

    if not is_available(artifact_status):
        result["unavailable_reason"] = "Missing one or more required model artifacts."
        return result
    if not configured_test_csv.exists():
        result["status"] = "unavailable"
        result["unavailable_reason"] = f"Configured test CSV not found: {configured_test_csv}"
        return result
    if not test_csv.exists():
        result["status"] = "unavailable"
        result["unavailable_reason"] = f"Common test CSV not found: {test_csv}"
        return result

    class_to_idx = load_class_to_idx(model_dir / "class_to_idx.json")
    class_names = get_class_names(class_to_idx)
    validate_class_names(config, class_names)
    if class_names != baseline_config["dataset"]["class_names"]:
        result["status"] = "unavailable"
        result["unavailable_reason"] = "Class mapping is not compatible with baseline Clinical V2."
        return result

    eval_config = copy.deepcopy(config)
    eval_config["dataset"]["test_csv"] = str(test_csv)
    model_path = model_dir / "best_model.pth"
    test_dataset, test_loader = create_test_loader(
        config=eval_config,
        class_to_idx=class_to_idx,
        args=args,
        device=device,
    )
    sources = read_source_datasets(test_csv)
    if len(sources) != len(test_dataset):
        raise ValueError(f"source_dataset rows do not match test dataset for {variant['name']}.")

    model, checkpoint = load_model(model_path, len(class_names), device)
    true_labels, predicted_labels = run_inference(model, test_loader, device)
    metrics = compute_metric_bundle(true_labels, predicted_labels, class_names)
    source_metrics = compute_source_metrics(
        sources=sources,
        true_labels=true_labels,
        predicted_labels=predicted_labels,
        class_names=class_names,
    )
    focus_metrics = compute_focus_error_metrics(
        true_labels=true_labels,
        predicted_labels=predicted_labels,
        confusion_matrix=metrics["confusion_matrix"],
        class_names=class_names,
    )
    lesion_metrics = get_lesion_metrics(metrics["class_report"])

    output_stem = variant["name"]
    classification_report_path = METRICS_DIR / f"{output_stem}_classification_report.csv"
    source_metrics_path = METRICS_DIR / f"{output_stem}_source_metrics.csv"
    confusion_matrix_csv_path = METRICS_DIR / f"{output_stem}_confusion_matrix.csv"
    confusion_matrix_png_path = PLOTS_DIR / f"{output_stem}_confusion_matrix.png"

    save_classification_report_csv(classification_report_path, metrics["class_report"])
    save_source_metrics_csv(source_metrics_path, source_metrics)
    write_confusion_matrix_csv(
        confusion_matrix_csv_path,
        metrics["confusion_matrix"],
        class_names,
    )
    save_confusion_matrix_png(
        confusion_matrix_png_path,
        metrics["confusion_matrix"],
        class_names,
    )

    sources_by_name = source_lookup(source_metrics)
    google_scin = sources_by_name["google_scin"]
    fitzpatrick = sources_by_name["fitzpatrick17k"]

    result.update(
        {
            "status": "complete",
            "checkpoint": {
                "epoch": int(checkpoint.get("epoch", -1)),
                "val_macro_f1": float(checkpoint.get("val_macro_f1", 0.0)),
            },
            "combined": {
                "support": metrics["support"],
                "accuracy": metrics["accuracy"],
                "macro_f1": metrics["macro_f1"],
                "balanced_accuracy": metrics["balanced_accuracy"],
            },
            "class_report": metrics["class_report"],
            "confusion_matrix": metrics["confusion_matrix"],
            "source_metrics": source_metrics,
            "source_error_rates": {
                "google_scin": error_rate(google_scin),
                "fitzpatrick17k": error_rate(fitzpatrick),
            },
            "lesion_routing": lesion_metrics,
            "focus_errors": focus_metrics,
            "outputs": {
                "classification_report_csv": str(classification_report_path),
                "source_metrics_csv": str(source_metrics_path),
                "confusion_matrix_csv": str(confusion_matrix_csv_path),
                "confusion_matrix_png": str(confusion_matrix_png_path),
            },
        }
    )
    return result


def variant_decision(result: dict) -> str:
    if result["status"] != "complete":
        return "unavailable"
    if Path(result["evaluated_test_csv"]) != BASELINE_TEST_CSV:
        return "not directly comparable"
    if result["name"] == "baseline_clinical_v2":
        return "keep experimental"

    source_rows = source_lookup(result["source_metrics"])
    focus_errors = result["focus_errors"]
    lesion_recall = result["lesion_routing"]["recall"]
    baseline_like = (
        result["combined"]["macro_f1"] >= BASELINE_CRITERIA["combined_macro_f1"]
        and result["combined"]["balanced_accuracy"]
        >= BASELINE_CRITERIA["combined_balanced_accuracy"]
        and (
            source_rows["google_scin"]["macro_f1"]
            > BASELINE_CRITERIA["google_scin_macro_f1"]
            or result["source_error_rates"]["google_scin"]
            < BASELINE_CRITERIA["google_scin_error_rate"]
        )
        and source_rows["fitzpatrick17k"]["macro_f1"]
        >= BASELINE_CRITERIA["fitzpatrick17k_macro_f1"] - 0.02
        and focus_errors["lesion_routing_false_negatives"]
        <= BASELINE_CRITERIA["lesion_routing_false_negatives"]
        and lesion_recall >= 0.0
        and focus_errors["eczema_to_urticaria"]
        <= BASELINE_CRITERIA["eczema_to_urticaria"] + 5
        and focus_errors["urticaria_false_positives"]
        <= BASELINE_CRITERIA["urticaria_false_positives"] + 10
    )
    return "promote candidate" if baseline_like else "keep experimental"


def comparison_row(result: dict) -> dict:
    if result["status"] != "complete":
        return {
            "variant": result["name"],
            "status": result["status"],
            "decision": "unavailable",
        }

    source_rows = source_lookup(result["source_metrics"])
    focus_errors = result["focus_errors"]
    decision = variant_decision(result)
    return {
        "variant": result["name"],
        "status": result["status"],
        "combined_accuracy": result["combined"]["accuracy"],
        "combined_macro_f1": result["combined"]["macro_f1"],
        "combined_balanced_accuracy": result["combined"]["balanced_accuracy"],
        "google_scin_accuracy": source_rows["google_scin"]["accuracy"],
        "google_scin_macro_f1": source_rows["google_scin"]["macro_f1"],
        "google_scin_error_rate": result["source_error_rates"]["google_scin"],
        "fitzpatrick17k_accuracy": source_rows["fitzpatrick17k"]["accuracy"],
        "fitzpatrick17k_macro_f1": source_rows["fitzpatrick17k"]["macro_f1"],
        "fitzpatrick17k_error_rate": result["source_error_rates"]["fitzpatrick17k"],
        "lesion_routing_precision": result["lesion_routing"]["precision"],
        "lesion_routing_recall": result["lesion_routing"]["recall"],
        "lesion_routing_f1": result["lesion_routing"]["f1"],
        "lesion_routing_false_negatives": focus_errors[
            "lesion_routing_false_negatives"
        ],
        "lesion_routing_false_negative_predicted_labels": json.dumps(
            focus_errors["lesion_routing_false_negative_predicted_labels"],
            ensure_ascii=False,
        ),
        "eczema_to_urticaria": focus_errors["eczema_to_urticaria"],
        "eczema_to_psoriasis": focus_errors["eczema_to_psoriasis"],
        "psoriasis_to_eczema": focus_errors["psoriasis_to_eczema"],
        "psoriasis_to_urticaria": focus_errors["psoriasis_to_urticaria"],
        "lesion_to_psoriasis": focus_errors["lesion_to_psoriasis"],
        "urticaria_false_positives": focus_errors["urticaria_false_positives"],
        "decision": decision,
    }


def save_comparison_table(output_path: Path, rows: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "variant",
        "status",
        "combined_accuracy",
        "combined_macro_f1",
        "combined_balanced_accuracy",
        "google_scin_accuracy",
        "google_scin_macro_f1",
        "google_scin_error_rate",
        "fitzpatrick17k_accuracy",
        "fitzpatrick17k_macro_f1",
        "fitzpatrick17k_error_rate",
        "lesion_routing_precision",
        "lesion_routing_recall",
        "lesion_routing_f1",
        "lesion_routing_false_negatives",
        "lesion_routing_false_negative_predicted_labels",
        "eczema_to_urticaria",
        "eczema_to_psoriasis",
        "psoriasis_to_eczema",
        "psoriasis_to_urticaria",
        "lesion_to_psoriasis",
        "urticaria_false_positives",
        "decision",
    ]
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


def format_csv_value(value) -> str | int:
    if isinstance(value, float):
        return f"{value:.6f}"
    return value


def save_metrics_json(output_path: Path, results: list[dict], rows: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "issue": "#153",
        "model_context": {
            "task": "Clinical V2 variant comparison",
            "framing": "Educational, non-diagnostic model evaluation.",
            "test_evaluation_note": "All complete variants were evaluated on the original Clinical V2 baseline test split for direct comparison.",
            "promotion_note": "No model is promoted by this evaluation script.",
        },
        "baseline_criteria": BASELINE_CRITERIA,
        "variants": results,
        "comparison_table": rows,
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def fmt(value) -> str:
    if value == "":
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def summary_table_rows(rows: list[dict]) -> list[str]:
    lines = [
        "| Variant | Combined macro-F1 | Balanced accuracy | SCIN macro-F1 | SCIN error rate | Fitzpatrick macro-F1 | Fitzpatrick error rate | Lesion FN | Eczema→Urticaria | Urticaria FP | Decision |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["variant"]),
                    fmt(row.get("combined_macro_f1", "")),
                    fmt(row.get("combined_balanced_accuracy", "")),
                    fmt(row.get("google_scin_macro_f1", "")),
                    fmt(row.get("google_scin_error_rate", "")),
                    fmt(row.get("fitzpatrick17k_macro_f1", "")),
                    fmt(row.get("fitzpatrick17k_error_rate", "")),
                    fmt(row.get("lesion_routing_false_negatives", "")),
                    fmt(row.get("eczema_to_urticaria", "")),
                    fmt(row.get("urticaria_false_positives", "")),
                    str(row["decision"]),
                ]
            )
            + " |"
        )
    return lines


def final_recommendation(rows: list[dict]) -> str:
    candidates = [
        row
        for row in rows
        if row.get("decision") == "promote candidate"
        and row.get("variant") != "baseline_clinical_v2"
    ]
    if candidates:
        best = max(candidates, key=lambda row: float(row["combined_macro_f1"]))
        return (
            "promote one variant to replace current `clinical_skin_condition_v1`: "
            f"`{best['variant']}`, pending implementation in a separate promotion task."
        )
    return "keep current baseline and document variants as unsuccessful"


def save_summary(output_path: Path, results: list[dict], rows: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    comparable = all(
        result["status"] != "complete"
        or Path(result["evaluated_test_csv"]) == BASELINE_TEST_CSV
        for result in results
    )
    lines = [
        "# Clinical V2 Variant Comparison Summary",
        "",
        "Issue: #153",
        "",
        "This is educational, non-diagnostic model evaluation. Do not claim clinical readiness or diagnosis.",
        "",
        "Training metrics are not used for promotion here. These results are held-out test-set model evaluation metrics, and no model was promoted in code.",
        "",
        "## Test Split",
        "",
        f"- Directly comparable: {'yes' if comparable else 'no'}",
        f"- Evaluation test CSV: `{BASELINE_TEST_CSV}`",
        "- All complete variants were evaluated on the original Clinical V2 baseline test split.",
        "- #153 remains the comparison and recommendation task; any code promotion must happen separately.",
        "",
        "## Comparison Table",
        "",
        *summary_table_rows(rows),
        "",
        "## Final Recommendation",
        "",
        f"- {final_recommendation(rows)}.",
        "",
        "No additional training was run by this evaluation. No app wiring, taxonomy, inference registry, or model promotion changes were made.",
        "",
        "## Generated Files",
        "",
        "- `outputs/metrics/clinical_v2_variant_comparison_metrics.json`",
        "- `outputs/metrics/clinical_v2_variant_comparison_table.csv`",
    ]
    for result in results:
        if result["status"] == "complete":
            lines.extend(
                [
                    f"- `{result['outputs']['classification_report_csv']}`",
                    f"- `{result['outputs']['source_metrics_csv']}`",
                    f"- `{result['outputs']['confusion_matrix_csv']}`",
                    f"- `{result['outputs']['confusion_matrix_png']}`",
                ]
            )
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    device = select_device()
    test_csv = Path(args.test_csv)
    baseline_config = load_config(Path("config/clinical_v2_config.yaml"))

    results = []
    for variant in VARIANTS:
        print(f"Evaluating {variant['name']}...")
        results.append(
            evaluate_variant(
                variant=variant,
                baseline_config=baseline_config,
                test_csv=test_csv,
                args=args,
                device=device,
            )
        )

    rows = [comparison_row(result) for result in results]
    save_metrics_json(
        METRICS_DIR / "clinical_v2_variant_comparison_metrics.json",
        results,
        rows,
    )
    save_comparison_table(
        METRICS_DIR / "clinical_v2_variant_comparison_table.csv",
        rows,
    )
    save_summary(SUMMARY_PATH, results, rows)

    print("")
    print("Clinical V2 variant comparison")
    for line in summary_table_rows(rows):
        print(line)
    print("")
    print(f"Final recommendation: {final_recommendation(rows)}")


if __name__ == "__main__":
    main()
