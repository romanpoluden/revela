from pathlib import Path
from datasets import load_dataset
import pandas as pd
from tqdm import tqdm

REPO_ID = "pg-dev-ai/scin-processed-clean-dataset"
OUTPUT_DIR = Path("data/raw/scin_processed_clean")
IMAGE_DIR = OUTPUT_DIR / "images"
METADATA_DIR = OUTPUT_DIR / "metadata"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)

rows = []

for split in ["train", "test"]:
    ds = load_dataset(REPO_ID, split=split)

    for idx, row in enumerate(tqdm(ds, desc=f"Exporting {split}")):
        label = row["label"]
        text = row.get("text", "")
        image = row["image"].convert("RGB")

        safe_label = label.replace("/", "_").replace(" ", "_")
        filename = f"{split}_{idx:06d}_{safe_label}.jpg"
        image_path = IMAGE_DIR / filename

        if not image_path.exists():
            image.save(image_path, quality=95)

        rows.append({
            "source_dataset": "scin_processed_clean",
            "source_split": split,
            "source_index": idx,
            "case_id": "",
            "raw_label": label,
            "text": text,
            "image_path": str(image_path),
        })

manifest = pd.DataFrame(rows)
manifest_path = METADATA_DIR / "manifest.csv"
manifest.to_csv(manifest_path, index=False)

print(f"Saved images to: {IMAGE_DIR}")
print(f"Saved manifest to: {manifest_path}")
print(f"Rows: {len(manifest)}")
print("Label counts:")
print(manifest["raw_label"].value_counts().head(30))
