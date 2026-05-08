#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare BCN20000 metadata for the Revela classifier."
    )
    parser.add_argument(
        "--config",
        default="config/bcn20000_config.yaml",
        help="Path to the YAML config file.",
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


def read_metadata(metadata_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata CSV not found: {metadata_path}")

    with metadata_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if not fieldnames:
        raise ValueError(f"Metadata CSV has no header row: {metadata_path}")

    return rows, fieldnames


def clean_value(value: str | None) -> str:
    return (value or "").strip()


def map_class_label(diagnosis_value: str, class_mapping: dict) -> str:
    melanoma_text = class_mapping["melanoma_contains"]
    nevus_text = class_mapping["nevus_exact"]

    if melanoma_text in diagnosis_value:
        return class_mapping["melanoma_label"]
    if diagnosis_value == nevus_text:
        return class_mapping["nevus_label"]
    return class_mapping["other_label"]


def build_image_path(image_root: Path, image_id: str, image_extension: str) -> Path:
    return image_root / f"{image_id}{image_extension}"


def validate_split_config(split_config: dict) -> None:
    require_keys(split_config, ["train", "val", "test", "seed"], "split")

    total_ratio = split_config["train"] + split_config["val"] + split_config["test"]
    if abs(total_ratio - 1.0) > 1e-9:
        raise ValueError(
            "Split ratios must add up to 1.0. "
            f"Got {total_ratio:.6f} instead."
        )


def assign_lesion_splits(lesion_ids: list[str], split_config: dict) -> dict[str, str]:
    unique_lesion_ids = sorted(set(lesion_ids))
    random_generator = random.Random(split_config["seed"])
    random_generator.shuffle(unique_lesion_ids)

    lesion_count = len(unique_lesion_ids)
    train_cutoff = int(lesion_count * split_config["train"])
    val_cutoff = train_cutoff + int(lesion_count * split_config["val"])

    split_lookup: dict[str, str] = {}
    for lesion_id in unique_lesion_ids[:train_cutoff]:
        split_lookup[lesion_id] = "train"
    for lesion_id in unique_lesion_ids[train_cutoff:val_cutoff]:
        split_lookup[lesion_id] = "val"
    for lesion_id in unique_lesion_ids[val_cutoff:]:
        split_lookup[lesion_id] = "test"

    if len(split_lookup) != lesion_count:
        raise ValueError("Every lesion_id must be assigned to exactly one split.")

    return split_lookup


def assert_no_lesion_overlap(rows: list[dict[str, str]], lesion_column: str) -> dict[str, set[str]]:
    lesions_by_split: dict[str, set[str]] = {
        "train": set(),
        "val": set(),
        "test": set(),
    }

    for row in rows:
        split_name = row["split"]
        lesion_id = row[lesion_column]
        lesions_by_split[split_name].add(lesion_id)

    split_names = list(lesions_by_split.keys())
    for index, left_split in enumerate(split_names):
        for right_split in split_names[index + 1 :]:
            overlap = lesions_by_split[left_split] & lesions_by_split[right_split]
            if overlap:
                raise AssertionError(
                    f"Found {len(overlap)} overlapping lesion_id values between "
                    f"`{left_split}` and `{right_split}`."
                )

    return lesions_by_split


def sort_rows(rows: list[dict[str, str]], lesion_column: str, image_column: str) -> list[dict[str, str]]:
    return sorted(
        rows,
        key=lambda row: (row["split"], row[lesion_column], row[image_column]),
    )


def write_csv(output_path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def count_classes(rows: list[dict[str, str]]) -> Counter:
    return Counter(row["class_label"] for row in rows)


def count_classes_by_split(rows: list[dict[str, str]]) -> dict[str, Counter]:
    counts = {
        "train": Counter(),
        "val": Counter(),
        "test": Counter(),
    }
    for row in rows:
        counts[row["split"]][row["class_label"]] += 1
    return counts


def rows_by_split(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    split_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        split_rows[row["split"]].append(row)
    return split_rows


def build_summary_lines(
    summary: dict,
    class_order: list[str],
) -> list[str]:
    lines: list[str] = []
    lines.append("# BCN20000 Processed Summary")
    lines.append("")
    lines.append("## Filtering Summary")
    lines.append("")
    lines.append(f"- Rows before filtering: {summary['rows_before']}")
    lines.append(
        f"- Rows after dropping missing diagnosis_3: {summary['rows_after_diagnosis_filter']}"
    )
    lines.append(f"- Rows after all filtering: {summary['rows_after_all_filters']}")
    lines.append(f"- Rows removed for missing diagnosis_3: {summary['missing_diagnosis_rows']}")
    lines.append(f"- Rows removed for missing image files: {summary['missing_image_rows']}")
    lines.append(
        "- Image existence match count: "
        f"{summary['image_exists_count']} / {summary['rows_after_diagnosis_filter']}"
    )
    lines.append("")
    lines.append("## Overall Class Counts")
    lines.append("")
    for class_name in class_order:
        lines.append(f"- {class_name}: {summary['overall_class_counts'].get(class_name, 0)}")
    lines.append("")
    lines.append("## Split Class Counts")
    lines.append("")
    for split_name in ["train", "val", "test"]:
        lines.append(f"### {split_name}")
        lines.append("")
        for class_name in class_order:
            count = summary["class_counts_by_split"][split_name].get(class_name, 0)
            lines.append(f"- {class_name}: {count}")
        lines.append("")
    lines.append("## Unique lesion_id Counts by Split")
    lines.append("")
    for split_name in ["train", "val", "test"]:
        lines.append(
            f"- {split_name}: {summary['unique_lesion_counts_by_split'].get(split_name, 0)}"
        )
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    for output_name, output_path in summary["output_paths"].items():
        lines.append(f"- {output_name}: `{output_path}`")
    lines.append("")
    return lines


def print_summary(summary: dict, class_order: list[str]) -> None:
    print(f"Rows before filtering: {summary['rows_before']}")
    print(
        "Rows after dropping missing diagnosis_3: "
        f"{summary['rows_after_diagnosis_filter']}"
    )
    print(f"Rows after all filtering: {summary['rows_after_all_filters']}")
    print(f"Rows removed for missing diagnosis_3: {summary['missing_diagnosis_rows']}")
    print(f"Rows removed for missing image files: {summary['missing_image_rows']}")
    print(
        "Image existence match count: "
        f"{summary['image_exists_count']} / {summary['rows_after_diagnosis_filter']}"
    )
    print("")
    print("Class counts overall:")
    for class_name in class_order:
        print(f"  - {class_name}: {summary['overall_class_counts'].get(class_name, 0)}")
    print("")
    print("Class counts by split:")
    for split_name in ["train", "val", "test"]:
        print(f"  {split_name}:")
        for class_name in class_order:
            count = summary["class_counts_by_split"][split_name].get(class_name, 0)
            print(f"    - {class_name}: {count}")
    print("")
    print("Unique lesion_id count by split:")
    for split_name in ["train", "val", "test"]:
        print(
            f"  - {split_name}: "
            f"{summary['unique_lesion_counts_by_split'].get(split_name, 0)}"
        )


def write_summary_markdown(summary_path: Path, summary: dict, class_order: list[str]) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    lines = build_summary_lines(summary, class_order)
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)

    require_keys(config, ["dataset", "columns", "class_mapping", "split", "files"], "root")
    require_keys(
        config["dataset"],
        ["metadata_csv", "image_root", "output_dir", "summary_path", "image_extension"],
        "dataset",
    )
    require_keys(config["columns"], ["image_id", "lesion_id", "diagnosis"], "columns")
    require_keys(
        config["class_mapping"],
        [
            "melanoma_contains",
            "nevus_exact",
            "melanoma_label",
            "nevus_label",
            "other_label",
        ],
        "class_mapping",
    )
    require_keys(config["files"], ["master_metadata", "train", "val", "test"], "files")
    validate_split_config(config["split"])

    metadata_path = Path(config["dataset"]["metadata_csv"])
    image_root = Path(config["dataset"]["image_root"])
    output_dir = Path(config["dataset"]["output_dir"])
    summary_path = Path(config["dataset"]["summary_path"])
    image_extension = config["dataset"]["image_extension"]

    image_column = config["columns"]["image_id"]
    lesion_column = config["columns"]["lesion_id"]
    diagnosis_column = config["columns"]["diagnosis"]

    rows, original_fieldnames = read_metadata(metadata_path)
    required_columns = [image_column, lesion_column, diagnosis_column]
    missing_columns = [column for column in required_columns if column not in original_fieldnames]
    if missing_columns:
        raise KeyError(
            "Metadata CSV is missing required columns: " + ", ".join(missing_columns)
        )

    rows_before = len(rows)
    missing_diagnosis_rows = 0
    missing_image_rows = 0
    image_exists_count = 0
    processed_rows: list[dict[str, str]] = []

    for row in rows:
        diagnosis_value = clean_value(row.get(diagnosis_column))
        if not diagnosis_value:
            missing_diagnosis_rows += 1
            continue

        image_id = clean_value(row.get(image_column))
        lesion_id = clean_value(row.get(lesion_column))
        if not image_id:
            raise ValueError(f"Found a row with an empty `{image_column}` value.")
        if not lesion_id:
            raise ValueError(f"Found a row with an empty `{lesion_column}` value.")

        image_path = build_image_path(image_root, image_id, image_extension)
        if not image_path.exists():
            missing_image_rows += 1
            continue

        image_exists_count += 1

        cleaned_row = {field: clean_value(row.get(field)) for field in original_fieldnames}
        cleaned_row["class_label"] = map_class_label(diagnosis_value, config["class_mapping"])
        cleaned_row["image_path"] = image_path.as_posix()
        processed_rows.append(cleaned_row)

    rows_after_diagnosis_filter = rows_before - missing_diagnosis_rows
    rows_after_all_filters = len(processed_rows)

    lesion_ids = [row[lesion_column] for row in processed_rows]
    split_lookup = assign_lesion_splits(lesion_ids, config["split"])

    for row in processed_rows:
        row["split"] = split_lookup[row[lesion_column]]

    lesions_by_split = assert_no_lesion_overlap(processed_rows, lesion_column)
    processed_rows = sort_rows(processed_rows, lesion_column, image_column)

    output_fieldnames = original_fieldnames + ["class_label", "image_path", "split"]
    split_to_rows = rows_by_split(processed_rows)

    output_paths = {
        "master_metadata": (output_dir / config["files"]["master_metadata"]).as_posix(),
        "train": (output_dir / config["files"]["train"]).as_posix(),
        "val": (output_dir / config["files"]["val"]).as_posix(),
        "test": (output_dir / config["files"]["test"]).as_posix(),
    }

    write_csv(Path(output_paths["master_metadata"]), output_fieldnames, processed_rows)
    write_csv(Path(output_paths["train"]), output_fieldnames, split_to_rows["train"])
    write_csv(Path(output_paths["val"]), output_fieldnames, split_to_rows["val"])
    write_csv(Path(output_paths["test"]), output_fieldnames, split_to_rows["test"])

    class_order = [
        config["class_mapping"]["melanoma_label"],
        config["class_mapping"]["nevus_label"],
        config["class_mapping"]["other_label"],
    ]

    summary = {
        "rows_before": rows_before,
        "rows_after_diagnosis_filter": rows_after_diagnosis_filter,
        "rows_after_all_filters": rows_after_all_filters,
        "missing_diagnosis_rows": missing_diagnosis_rows,
        "missing_image_rows": missing_image_rows,
        "image_exists_count": image_exists_count,
        "overall_class_counts": count_classes(processed_rows),
        "class_counts_by_split": count_classes_by_split(processed_rows),
        "unique_lesion_counts_by_split": {
            split_name: len(lesions_by_split[split_name])
            for split_name in ["train", "val", "test"]
        },
        "output_paths": output_paths,
    }

    print_summary(summary, class_order)
    write_summary_markdown(summary_path, summary, class_order)


if __name__ == "__main__":
    main()
