from __future__ import annotations

import ast
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


BASELINE_DIR = Path("data/processed/clinical_v2")
SUMMARY_PATH = Path("docs/model/clinical_v2_high_confidence_dataset_summary.md")

THRESHOLDS = [0.67, 0.75]
MIN_SCIN_ROWS_FOR_VARIANT = 500

REQUIRED_COLUMNS = [
    "image_path",
    "source_dataset",
    "source_id",
    "case_id",
    "raw_label",
    "target_label",
    "class_idx",
    "split",
]

CLASS_NAMES = [
    "Eczema / dermatitis",
    "Urticaria / allergic reaction",
    "Folliculitis / acne-like",
    "Psoriasis / papulosquamous",
    "Lesion — dermoscopic review recommended",
]


def variant_name(threshold: float) -> str:
    return f"clinical_v2_high_confidence_{int(round(threshold * 100)):03d}"


def output_dir_for_threshold(threshold: float) -> Path:
    return Path("data/processed") / variant_name(threshold)


def config_path_for_threshold(threshold: float) -> Path:
    return Path("config") / f"{variant_name(threshold)}_config.yaml"


def parse_weighted_label(value: Any) -> dict[str, float]:
    if value is None or pd.isna(value):
        return {}
    if isinstance(value, dict):
        parsed = value
    elif isinstance(value, str):
        value = value.strip()
        if not value:
            return {}
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return {}
    else:
        return {}

    if not isinstance(parsed, dict):
        return {}

    cleaned: dict[str, float] = {}
    for label, score in parsed.items():
        try:
            numeric_score = float(score)
        except (TypeError, ValueError):
            continue
        if math.isfinite(numeric_score):
            cleaned[str(label)] = numeric_score
    return cleaned


def top_weighted_label(value: Any) -> tuple[str | pd.NA, float | pd.NA]:
    labels = parse_weighted_label(value)
    if not labels:
        return pd.NA, pd.NA

    label, score = max(labels.items(), key=lambda item: item[1])
    return label, score


def load_baseline() -> pd.DataFrame:
    frames = []
    for split in ["train", "val", "test"]:
        path = BASELINE_DIR / f"{split}.csv"
        df = pd.read_csv(
            path,
            dtype={
                "source_dataset": "string",
                "source_id": "string",
                "case_id": "string",
                "raw_label": "string",
                "target_label": "string",
                "split": "string",
            },
        )
        frames.append(df)

    baseline = pd.concat(frames, ignore_index=True, sort=False)
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in baseline.columns]
    if missing_columns:
        raise ValueError(f"Baseline clinical_v2 is missing required columns: {missing_columns}")

    expected_splits = {"train", "val", "test"}
    actual_splits = set(baseline["split"].dropna().astype(str))
    if actual_splits != expected_splits:
        raise ValueError(f"Expected baseline splits {expected_splits}, found {actual_splits}")

    return baseline


def add_scin_top_label_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["scin_top_weighted_label"] = pd.NA
    out["scin_top_weighted_label_score"] = pd.NA

    scin_mask = out["source_dataset"].astype(str).eq("google_scin")
    if "weighted_skin_condition_label" not in out.columns:
        raise ValueError("Baseline rows do not include weighted_skin_condition_label")

    top_values = out.loc[scin_mask, "weighted_skin_condition_label"].apply(top_weighted_label)
    out.loc[scin_mask, "scin_top_weighted_label"] = [item[0] for item in top_values]
    out.loc[scin_mask, "scin_top_weighted_label_score"] = [item[1] for item in top_values]
    out["scin_top_weighted_label_score"] = pd.to_numeric(
        out["scin_top_weighted_label_score"],
        errors="coerce",
    )
    return out


def validate_case_aware_scin_split(df: pd.DataFrame) -> None:
    scin = df[df["source_dataset"].astype(str).eq("google_scin")].copy()
    if scin.empty:
        return

    split_counts = scin.groupby("case_id", dropna=False)["split"].nunique()
    leaking_cases = split_counts[split_counts > 1]
    if not leaking_cases.empty:
        examples = leaking_cases.head(5).index.tolist()
        raise ValueError(f"SCIN case_id appears in multiple splits: {examples}")


def build_variant(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    scin_mask = df["source_dataset"].astype(str).eq("google_scin")
    fitz_mask = df["source_dataset"].astype(str).eq("fitzpatrick17k")
    high_conf_scin = scin_mask & df["scin_top_weighted_label_score"].ge(threshold)

    variant = df[fitz_mask | high_conf_scin].copy()
    validate_case_aware_scin_split(variant)

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in variant.columns]
    if missing_columns:
        raise ValueError(f"Variant {variant_name(threshold)} is missing columns: {missing_columns}")

    class_idx_by_label = variant.groupby("target_label")["class_idx"].nunique()
    inconsistent = class_idx_by_label[class_idx_by_label > 1]
    if not inconsistent.empty:
        raise ValueError(f"Inconsistent class_idx values for labels: {inconsistent.index.tolist()}")

    return variant


def variant_is_viable(variant: pd.DataFrame) -> bool:
    scin = variant[variant["source_dataset"].astype(str).eq("google_scin")]
    if len(scin) < MIN_SCIN_ROWS_FOR_VARIANT:
        return False
    return set(CLASS_NAMES).issubset(set(scin["target_label"].dropna().astype(str)))


def write_variant_csvs(variant: pd.DataFrame, threshold: float) -> None:
    out_dir = output_dir_for_threshold(threshold)
    if out_dir == BASELINE_DIR:
        raise ValueError("Refusing to overwrite baseline clinical_v2")

    out_dir.mkdir(parents=True, exist_ok=True)
    for split in ["train", "val", "test"]:
        split_df = variant[variant["split"].astype(str).eq(split)].copy()
        split_df.to_csv(out_dir / f"{split}.csv", index=False)


def write_config(threshold: float) -> None:
    name = variant_name(threshold)
    processed_dir = output_dir_for_threshold(threshold)
    output_dir = Path("models") / f"{name}_effnet_b0"
    config_path = config_path_for_threshold(threshold)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    class_names_yaml = "\n".join([f"  - {name}" for name in CLASS_NAMES])

    config_path.write_text(
        f"""dataset:
  name: {name}
  task: clinical_image_classification_with_lesion_routing
  processed_dir: {processed_dir}
  train_csv: {processed_dir / "train.csv"}
  val_csv: {processed_dir / "val.csv"}
  test_csv: {processed_dir / "test.csv"}
  label_column: target_label
  class_idx_column: class_idx
  image_size: 224
  num_classes: {len(CLASS_NAMES)}
  class_names:
{class_names_yaml}

model:
  architecture: efficientnet_b0
  pretrained: true

training:
  batch_size: 16
  epochs: 5
  num_workers: 0
  learning_rate: 0.0001
  weight_decay: 0.01
  use_class_weights: true
  random_seed: 42
  output_dir: {output_dir}

notes:
  - High-confidence SCIN variant of clinical_v2; SCIN rows require top weighted label score >= {threshold:.2f}.
  - Clinical model is not diagnostic.
  - Lesion class is a routing output, not cancer detection.
  - SCIN rows preserve the clinical_v2 case-aware split by case_id.
  - Fitzpatrick17k rows preserve the clinical_v2 row-level split limitation because case_id/patient_id/lesion_id are unavailable.
  - Preserve source_dataset and report source-specific performance during evaluation.
""",
        encoding="utf-8",
    )


def table_counts_by(df: pd.DataFrame, columns: list[str]) -> str:
    counts = df.groupby(columns, dropna=False).size().reset_index(name="rows")
    return dataframe_to_markdown(counts)


def table_source_class(df: pd.DataFrame) -> str:
    counts = (
        df.groupby(["source_dataset", "target_label"], dropna=False)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=CLASS_NAMES, fill_value=0)
        .reset_index()
    )
    return dataframe_to_markdown(counts)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"

    headers = [str(col) for col in df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        values = [markdown_cell(row[col]) for col in df.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def markdown_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace("|", "\\|")


def write_summary(
    baseline: pd.DataFrame,
    variants: dict[float, pd.DataFrame],
    viability: dict[float, bool],
) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    sections = [
        "# Clinical v2 High-Confidence SCIN Dataset Summary",
        "",
        "## Why V2.10 was needed",
        "",
        "V2.8 / issue #131 showed a clear source gap: combined macro-F1 was 0.6420, Google SCIN macro-F1 was 0.4028, Fitzpatrick17k macro-F1 was 0.6366, google_scin error rate was 0.4278, and fitzpatrick17k error rate was 0.2956. V2.10 builds high-confidence SCIN variants to reduce potential SCIN label noise for future retraining experiments.",
        "",
        "## Method",
        "",
        "- Started from the frozen `data/processed/clinical_v2` CSVs to preserve the existing taxonomy, class indices, source labels, and split assignments.",
        "- Identified SCIN rows with `source_dataset == \"google_scin\"`.",
        "- Parsed `weighted_skin_condition_label` with `ast.literal_eval`, falling back to JSON parsing, accepting only dictionaries with finite numeric scores.",
        "- Added `scin_top_weighted_label` and `scin_top_weighted_label_score` for SCIN rows.",
        "- Preserved all Fitzpatrick17k rows.",
        "- Preserved the existing SCIN split, which was built case-aware by `case_id`.",
        "- Preserved the existing Fitzpatrick17k row-level split; Fitzpatrick17k still lacks case_id/patient_id/lesion_id in this dataset.",
        "",
        "## Thresholds attempted",
        "",
        "- Top weighted label score >= 0.67",
        "- Top weighted label score >= 0.75",
        "",
        "## Baseline clinical_v2 counts",
        "",
        f"Total rows: {len(baseline)}",
        "",
        "### Baseline by split",
        "",
        table_counts_by(baseline, ["split"]),
        "",
        "### Baseline by source",
        "",
        table_counts_by(baseline, ["source_dataset"]),
        "",
        "### Baseline by target class",
        "",
        table_counts_by(baseline, ["target_label"]),
        "",
        "### Baseline by source and target class",
        "",
        table_source_class(baseline),
    ]

    for threshold, variant in variants.items():
        scin_rows = variant[variant["source_dataset"].astype(str).eq("google_scin")]
        suffix = int(round(threshold * 100))
        sections.extend(
            [
                "",
                f"## High-confidence {threshold:.2f} variant",
                "",
                f"Output directory: `data/processed/clinical_v2_high_confidence_{suffix:03d}`",
                "",
                f"Total rows: {len(variant)}",
                f"SCIN rows retained: {len(scin_rows)}",
                f"SCIN cases retained: {scin_rows['case_id'].nunique()}",
                f"Suitable for retraining experiment: {'yes' if viability[threshold] else 'no'}",
                "",
                "### Counts by split",
                "",
                table_counts_by(variant, ["split"]),
                "",
                "### Counts by source",
                "",
                table_counts_by(variant, ["source_dataset"]),
                "",
                "### Counts by target class",
                "",
                table_counts_by(variant, ["target_label"]),
                "",
                "### Counts by source and target class",
                "",
                table_source_class(variant),
            ]
        )

    sections.extend(
        [
            "",
            "## Suitability",
            "",
            "The 0.67 variant is suitable for a retraining experiment because it retains a substantial SCIN subset across all target classes while reducing lower-confidence weighted-label rows.",
            "The 0.75 variant is also suitable for a narrower retraining experiment if lower SCIN coverage is acceptable; it keeps all target classes but further reduces SCIN representation.",
            "",
            "## Limitations",
            "",
            "- Filtering may reduce SCIN coverage, especially for smaller classes.",
            "- The Fitzpatrick17k split limitation remains: rows are split at image level because case_id/patient_id/lesion_id are unavailable.",
            "- These datasets are for retraining experiments only and make no clinical-readiness claim.",
            "- No taxonomy change was made.",
            "- The clinical model is not diagnostic, and the lesion class remains a routing output only.",
        ]
    )

    SUMMARY_PATH.write_text("\n".join(sections) + "\n", encoding="utf-8")


def missing_image_paths(df: pd.DataFrame) -> int:
    return int((~df["image_path"].astype(str).apply(lambda p: Path(p).exists())).sum())


def main() -> None:
    baseline = add_scin_top_label_columns(load_baseline())
    validate_case_aware_scin_split(baseline)

    variants: dict[float, pd.DataFrame] = {}
    viability: dict[float, bool] = {}
    for threshold in THRESHOLDS:
        variant = build_variant(baseline, threshold)
        viable = variant_is_viable(variant)
        viability[threshold] = viable
        if viable:
            write_variant_csvs(variant, threshold)
            write_config(threshold)
            variants[threshold] = variant
        else:
            print(f"Skipping {threshold:.2f}: not enough SCIN rows/classes remain.")

    if not variants:
        raise RuntimeError("No high-confidence variants were viable.")

    write_summary(baseline, variants, viability)

    print("Clinical v2 high-confidence SCIN variants created.")
    print(f"Baseline rows: {len(baseline)}")
    print(f"Baseline missing image paths: {missing_image_paths(baseline)}")
    for threshold, variant in variants.items():
        print(f"\nVariant {threshold:.2f}: {variant_name(threshold)}")
        print(f"Rows: {len(variant)}")
        print(f"Missing image paths: {missing_image_paths(variant)}")
        print("Counts by source:")
        print(variant["source_dataset"].value_counts().to_string())
        print("Counts by split:")
        print(variant["split"].value_counts().to_string())
        print("Counts by class:")
        print(variant["target_label"].value_counts().to_string())
    print(f"\nSummary: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
