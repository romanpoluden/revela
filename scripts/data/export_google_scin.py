from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from tqdm import tqdm

REPO_ID = "google/scin"
OUTPUT_DIR = Path("data/raw/scin")
IMAGE_DIR = OUTPUT_DIR / "images"
METADATA_DIR = OUTPUT_DIR / "metadata"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)


def serialize_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def save_image(image, split: str, case_id: str, image_index: int) -> str | None:
    if image is None:
        return None

    filename = f"{split}_{case_id}_image_{image_index}.jpg"
    image_path = IMAGE_DIR / filename

    if not image_path.exists():
        image.convert("RGB").save(image_path, quality=95)

    return str(image_path)


rows = []

for split in ["train"]:
    ds = load_dataset(REPO_ID, split=split)

    for idx, row in enumerate(tqdm(ds, desc=f"Exporting {split}")):
        case_id = str(row["case_id"])

        base_metadata = {}
        for key, value in row.items():
            if key not in ["image_1_path", "image_2_path", "image_3_path"]:
                base_metadata[key] = serialize_value(value)

        for image_index, image_col in enumerate(
            ["image_1_path", "image_2_path", "image_3_path"],
            start=1,
        ):
            image_path = save_image(row[image_col], split, case_id, image_index)

            if image_path is None:
                continue

            image_row = dict(base_metadata)
            image_row["source_dataset"] = "google_scin"
            image_row["source_split"] = split
            image_row["source_index"] = idx
            image_row["image_index"] = image_index
            image_row["image_path"] = image_path
            image_row["image_shot_type"] = row.get(f"image_{image_index}_shot_type")

            rows.append(image_row)

manifest = pd.DataFrame(rows)
manifest_path = METADATA_DIR / "manifest.csv"
manifest.to_csv(manifest_path, index=False)

print(f"Saved images to: {IMAGE_DIR}")
print(f"Saved manifest to: {manifest_path}")
print(f"Image rows: {len(manifest)}")
print(f"Unique cases: {manifest['case_id'].nunique() if 'case_id' in manifest else 'N/A'}")
print("Top weighted labels:")
print(manifest["weighted_skin_condition_label"].value_counts().head(20))
