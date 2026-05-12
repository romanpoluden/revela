from __future__ import annotations

import ast
import random
from pathlib import Path

import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split


RANDOM_SEED = 42

SCIN_MANIFEST_PATH = Path("data/raw/scin/metadata/manifest.csv")
FITZ_CSV_PATH = Path("data/raw/fitzpatrick17k/metadata/fitzpatrick17k.csv")
FITZ_IMAGE_DIR = Path("data/raw/fitzpatrick17k/images")

OUTPUT_DIR = Path("data/processed/clinical_v2")
CONFIG_PATH = Path("config/clinical_v2_config.yaml")
SUMMARY_PATH = Path("docs/model/clinical_v2_dataset_build_summary.md")


CLASS_NAMES = [
    "Eczema / dermatitis",
    "Urticaria / allergic reaction",
    "Folliculitis / acne-like",
    "Psoriasis / papulosquamous",
    "Lesion — dermoscopic review recommended",
]

CLASS_TO_IDX = {name: idx for idx, name in enumerate(CLASS_NAMES)}


SCIN_LABEL_MAP = {
    # Eczema / dermatitis
    "Eczema": "Eczema / dermatitis",
    "Allergic Contact Dermatitis": "Eczema / dermatitis",
    "Irritant Contact Dermatitis": "Eczema / dermatitis",
    "Acute dermatitis, NOS": "Eczema / dermatitis",
    "Atopic Dermatitis": "Eczema / dermatitis",
    "Dyshidrotic Eczema": "Eczema / dermatitis",
    "Seborrheic Dermatitis": "Eczema / dermatitis",
    "Nummular eczema": "Eczema / dermatitis",
    "Stasis Dermatitis": "Eczema / dermatitis",
    "Acute and chronic dermatitis": "Eczema / dermatitis",
    "CD - Contact dermatitis": "Eczema / dermatitis",

    # Urticaria / allergic reaction
    "Urticaria": "Urticaria / allergic reaction",
    "Drug Rash": "Urticaria / allergic reaction",
    "Hypersensitivity": "Urticaria / allergic reaction",
    "Morbilliform Drug Eruption": "Urticaria / allergic reaction",
    "Allergic reaction": "Urticaria / allergic reaction",

    # Folliculitis / acne-like
    "Folliculitis": "Folliculitis / acne-like",
    "Acne": "Folliculitis / acne-like",
    "Acneiform eruption": "Folliculitis / acne-like",
    "Rosacea": "Folliculitis / acne-like",
    "Perioral Dermatitis": "Folliculitis / acne-like",

    # Psoriasis / papulosquamous
    "Psoriasis": "Psoriasis / papulosquamous",
    "Pityriasis rosea": "Psoriasis / papulosquamous",
    "Lichen planus/lichenoid eruption": "Psoriasis / papulosquamous",
    "Papulosquamous eruption": "Psoriasis / papulosquamous",
    "Pityriasis rubra pilaris": "Psoriasis / papulosquamous",

    # Lesion routing
    "Melanoma": "Lesion — dermoscopic review recommended",
    "Basal Cell Carcinoma": "Lesion — dermoscopic review recommended",
    "SCC/SCCIS": "Lesion — dermoscopic review recommended",
    "Melanocytic Nevus": "Lesion — dermoscopic review recommended",
    "Atypical Nevus": "Lesion — dermoscopic review recommended",
    "Epidermal nevus": "Lesion — dermoscopic review recommended",
    "Nevus anemicus": "Lesion — dermoscopic review recommended",
    "Vascular nevus of skin": "Lesion — dermoscopic review recommended",
    "Actinic Keratosis": "Lesion — dermoscopic review recommended",
}


FITZ_LABEL_MAP = {
    # Eczema / dermatitis
    "eczema": "Eczema / dermatitis",
    "allergic contact dermatitis": "Eczema / dermatitis",
    "seborrheic dermatitis": "Eczema / dermatitis",
    "dyshidrotic eczema": "Eczema / dermatitis",
    "atopic dermatitis": "Eczema / dermatitis",
    "nummular eczema": "Eczema / dermatitis",

    # Urticaria / allergic reaction
    "urticaria": "Urticaria / allergic reaction",
    "urticaria pigmentosa": "Urticaria / allergic reaction",
    "drug eruption": "Urticaria / allergic reaction",
    "morbilliform drug eruption": "Urticaria / allergic reaction",
    "hypersensitivity reaction": "Urticaria / allergic reaction",

    # Folliculitis / acne-like
    "folliculitis": "Folliculitis / acne-like",
    "acne vulgaris": "Folliculitis / acne-like",
    "acne": "Folliculitis / acne-like",
    "rosacea": "Folliculitis / acne-like",
    "perioral dermatitis": "Folliculitis / acne-like",

    # Psoriasis / papulosquamous
    "psoriasis": "Psoriasis / papulosquamous",
    "pityriasis rosea": "Psoriasis / papulosquamous",
    "lichen planus": "Psoriasis / papulosquamous",
    "lichen planus/lichenoid eruption": "Psoriasis / papulosquamous",
    "pityriasis rubra pilaris": "Psoriasis / papulosquamous",

    # Lesion routing
    "melanoma": "Lesion — dermoscopic review recommended",
    "superficial spreading melanoma ssm": "Lesion — dermoscopic review recommended",
    "malignant melanoma": "Lesion — dermoscopic review recommended",
    "lentigo maligna": "Lesion — dermoscopic review recommended",
    "basal cell carcinoma": "Lesion — dermoscopic review recommended",
    "basal cell carcinoma morpheiform": "Lesion — dermoscopic review recommended",
    "solid cystic basal cell carcinoma": "Lesion — dermoscopic review recommended",
    "squamous cell carcinoma": "Lesion — dermoscopic review recommended",
    "nevocytic nevus": "Lesion — dermoscopic review recommended",
    "congenital nevus": "Lesion — dermoscopic review recommended",
    "halo nevus": "Lesion — dermoscopic review recommended",
    "becker nevus": "Lesion — dermoscopic review recommended",
    "epidermal nevus": "Lesion — dermoscopic review recommended",
    "nevus sebaceous of jadassohn": "Lesion — dermoscopic review recommended",
    "actinic keratosis": "Lesion — dermoscopic review recommended",
}


def parse_weighted_label(value: object) -> dict[str, float]:
    if pd.isna(value):
        return {}
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}

    try:
        parsed = ast.literal_eval(value)
    except Exception:
        return {}

    if not isinstance(parsed, dict):
        return {}

    return parsed


def get_top_weighted_label(value: object) -> str | None:
    labels = parse_weighted_label(value)
    if not labels:
        return None

    return max(labels.items(), key=lambda item: item[1])[0]


def image_is_readable(path: str) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def build_scin_rows() -> pd.DataFrame:
    df = pd.read_csv(SCIN_MANIFEST_PATH)

    df["top_weighted_label"] = df["weighted_skin_condition_label"].apply(get_top_weighted_label)
    df["target_label"] = df["top_weighted_label"].map(SCIN_LABEL_MAP)

    df = df[df["target_label"].notna()].copy()
    df["image_exists"] = df["image_path"].apply(lambda p: Path(p).exists())
    df = df[df["image_exists"]].copy()

    df["source_dataset"] = "google_scin"
    df["source_id"] = df["case_id"].astype(str) + "_image_" + df["image_index"].astype(str)
    df["raw_label"] = df["top_weighted_label"]
    df["class_idx"] = df["target_label"].map(CLASS_TO_IDX)

    # Preserve useful metadata columns if present.
    optional_cols = [
        "age_group",
        "sex_at_birth",
        "fitzpatrick_skin_type",
        "condition_duration",
        "related_category",
        "body_parts_head_or_neck",
        "body_parts_arm",
        "body_parts_palm",
        "body_parts_back_of_hand",
        "body_parts_torso_front",
        "body_parts_torso_back",
        "body_parts_genitalia_or_groin",
        "body_parts_buttocks",
        "body_parts_leg",
        "body_parts_foot_top_or_side",
        "body_parts_foot_sole",
        "body_parts_other",
        "textures_raised_or_bumpy",
        "textures_flat",
        "textures_rough_or_flaky",
        "textures_fluid_filled",
        "condition_symptoms_bleeding",
        "condition_symptoms_increasing_size",
        "condition_symptoms_darkening",
        "condition_symptoms_itching",
        "condition_symptoms_burning",
        "condition_symptoms_pain",
        "monk_skin_tone_label_india",
        "monk_skin_tone_label_us",
        "dermatologist_skin_condition_confidence",
        "weighted_skin_condition_label",
        "image_shot_type",
    ]

    base_cols = [
        "image_path",
        "source_dataset",
        "source_id",
        "case_id",
        "raw_label",
        "target_label",
        "class_idx",
    ]

    existing_cols = base_cols + [c for c in optional_cols if c in df.columns]
    return df[existing_cols]


def build_fitz_rows() -> pd.DataFrame:
    df = pd.read_csv(FITZ_CSV_PATH)
    df["target_label"] = df["label"].map(FITZ_LABEL_MAP)
    df = df[df["target_label"].notna()].copy()

    df["image_path"] = df["md5hash"].astype(str).apply(lambda x: str(FITZ_IMAGE_DIR / f"{x}.jpg"))
    df["image_exists"] = df["image_path"].apply(lambda p: Path(p).exists())
    df = df[df["image_exists"]].copy()

    df["source_dataset"] = "fitzpatrick17k"
    df["source_id"] = df["md5hash"].astype(str)
    df["case_id"] = ""
    df["raw_label"] = df["label"].astype(str)
    df["class_idx"] = df["target_label"].map(CLASS_TO_IDX)

    keep_cols = [
        "image_path",
        "source_dataset",
        "source_id",
        "case_id",
        "raw_label",
        "target_label",
        "class_idx",
        "fitzpatrick_scale",
        "fitzpatrick_centaur",
        "nine_partition_label",
        "three_partition_label",
        "qc",
        "url",
    ]

    return df[keep_cols]


def split_scin_by_case(df: pd.DataFrame) -> pd.DataFrame:
    case_labels = (
        df[["case_id", "target_label"]]
        .drop_duplicates()
        .groupby("case_id")["target_label"]
        .first()
        .reset_index()
    )

    train_cases, temp_cases = train_test_split(
        case_labels,
        test_size=0.30,
        random_state=RANDOM_SEED,
        stratify=case_labels["target_label"],
    )

    val_cases, test_cases = train_test_split(
        temp_cases,
        test_size=0.50,
        random_state=RANDOM_SEED,
        stratify=temp_cases["target_label"],
    )

    split_map = {}
    split_map.update({case_id: "train" for case_id in train_cases["case_id"]})
    split_map.update({case_id: "val" for case_id in val_cases["case_id"]})
    split_map.update({case_id: "test" for case_id in test_cases["case_id"]})

    out = df.copy()
    out["split"] = out["case_id"].map(split_map)
    return out


def split_fitz_by_row(df: pd.DataFrame) -> pd.DataFrame:
    train_df, temp_df = train_test_split(
        df,
        test_size=0.30,
        random_state=RANDOM_SEED,
        stratify=df["target_label"],
    )

    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.50,
        random_state=RANDOM_SEED,
        stratify=temp_df["target_label"],
    )

    train_df = train_df.copy()
    val_df = val_df.copy()
    test_df = test_df.copy()

    train_df["split"] = "train"
    val_df["split"] = "val"
    test_df["split"] = "test"

    return pd.concat([train_df, val_df, test_df], ignore_index=True)


def write_config() -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    class_names_yaml = "\n".join([f"  - {name}" for name in CLASS_NAMES])

    CONFIG_PATH.write_text(
        f"""dataset:
  name: clinical_v2
  task: clinical_image_classification_with_lesion_routing
  processed_dir: data/processed/clinical_v2
  train_csv: data/processed/clinical_v2/train.csv
  val_csv: data/processed/clinical_v2/val.csv
  test_csv: data/processed/clinical_v2/test.csv
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
  learning_rate: 0.0001
  use_class_weights: true
  random_seed: {RANDOM_SEED}

notes:
  - Clinical model is not diagnostic.
  - Lesion class is a routing output, not cancer detection.
  - SCIN uses official google/scin export with case_id preserved.
  - Fitzpatrick17k lacks case_id/patient_id/lesion_id; split limitation must be documented.
  - Preserve source_dataset and report source-specific performance during evaluation.
""",
        encoding="utf-8",
    )


def write_summary(all_df: pd.DataFrame) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    split_counts = all_df.groupby(["split", "target_label"]).size().unstack(fill_value=0)
    source_counts = all_df.groupby(["source_dataset", "target_label"]).size().unstack(fill_value=0)
    split_source_counts = all_df.groupby(["split", "source_dataset"]).size().unstack(fill_value=0)

    scin_cases = all_df[all_df["source_dataset"] == "google_scin"]["case_id"].nunique()
    fitz_rows = len(all_df[all_df["source_dataset"] == "fitzpatrick17k"])

    SUMMARY_PATH.write_text(
        f"""# Clinical v2 Dataset Build Summary

## Purpose

This document supports issue #125.

The processed clinical-image dataset was built using the approved 5-class taxonomy:

1. Eczema / dermatitis
2. Urticaria / allergic reaction
3. Folliculitis / acne-like
4. Psoriasis / papulosquamous
5. Lesion — dermoscopic review recommended

The fifth class is a routing class, not cancer detection.

## Dataset sources

- Official Google SCIN export: `google/scin`
- Fitzpatrick17k local downloaded images

## Important split notes

- SCIN is split by `case_id`; all images from the same case stay in the same split.
- Fitzpatrick17k does not provide clear `case_id`, `patient_id`, or `lesion_id`, so it is split at row/image level.
- Source-specific evaluation is required because Fitzpatrick17k is important for the lesion-routing class.

## Total rows

{len(all_df)}

## Source summary

- SCIN image rows: {len(all_df[all_df["source_dataset"] == "google_scin"])}
- SCIN unique cases: {scin_cases}
- Fitzpatrick17k rows: {fitz_rows}

## Counts by split and class

{split_counts.to_markdown()}

## Counts by source dataset and class

{source_counts.to_markdown()}

## Counts by split and source dataset

{split_source_counts.to_markdown()}

## Output files

- `data/processed/clinical_v2/train.csv`
- `data/processed/clinical_v2/val.csv`
- `data/processed/clinical_v2/test.csv`
- `config/clinical_v2_config.yaml`

## Communication rule

Do not claim cancer detection from the clinical-image model. Use the lesion class only to trigger dermoscopic review.
""",
        encoding="utf-8",
    )


def main() -> None:
    random.seed(RANDOM_SEED)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    scin_df = build_scin_rows()
    fitz_df = build_fitz_rows()

    print("Mapped SCIN rows:", len(scin_df))
    print("Mapped Fitzpatrick17k rows:", len(fitz_df))

    scin_split = split_scin_by_case(scin_df)
    fitz_split = split_fitz_by_row(fitz_df)

    all_df = pd.concat([scin_split, fitz_split], ignore_index=True, sort=False)

    readable_mask = all_df["image_path"].apply(image_is_readable)
    unreadable_count = int((~readable_mask).sum())
    all_df = all_df[readable_mask].copy()

    for split in ["train", "val", "test"]:
        all_df[all_df["split"] == split].to_csv(OUTPUT_DIR / f"{split}.csv", index=False)

    write_config()
    write_summary(all_df)

    print("\nClinical v2 dataset created.")
    print(f"Rows: {len(all_df)}")
    print(f"Unreadable images excluded: {unreadable_count}")

    print("\nCounts by class:")
    print(all_df["target_label"].value_counts())

    print("\nCounts by source:")
    print(all_df["source_dataset"].value_counts())

    print("\nCounts by split:")
    print(all_df["split"].value_counts())

    print(f"\nSaved to: {OUTPUT_DIR}")
    print(f"Config: {CONFIG_PATH}")
    print(f"Summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
