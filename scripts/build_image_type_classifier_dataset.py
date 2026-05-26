"""
Build the image-type classifier dataset index.

Classes:
  clinical_macroscopic - from clinical_v2 (google_scin + fitzpatrick17k)
  dermoscopic          - from BCN20000 cancer-risk model data

Outputs:
  outputs/model/image_type_classifier_dataset_index.csv
"""

import hashlib
import os
import sys
from pathlib import Path

import pandas as pd
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED = 42


def split_by_hash(path: str, train_frac: float = 0.70, val_frac: float = 0.15) -> str:
    """Deterministically assign a split based on the image path hash."""
    h = int(hashlib.sha256(path.encode()).hexdigest(), 16) % 10000
    train_cut = int(train_frac * 10000)
    val_cut = train_cut + int(val_frac * 10000)
    if h < train_cut:
        return "train"
    elif h < val_cut:
        return "val"
    return "test"


def get_image_info(abs_path: Path):
    """Return (width, height, file_ext, readable, notes)."""
    file_ext = abs_path.suffix.lower().lstrip(".")
    if not abs_path.exists():
        return None, None, file_ext, False, "file_not_found"
    try:
        with Image.open(abs_path) as img:
            w, h = img.size
        return w, h, file_ext, True, ""
    except Exception as e:
        return None, None, file_ext, False, f"pil_error:{type(e).__name__}"


def load_clinical_macroscopic() -> pd.DataFrame:
    """
    Load clinical_v2 images (google_scin + fitzpatrick17k) as clinical_macroscopic.
    We use the full clinical_v2 master (train+val+test combined) and re-split here.
    """
    rows = []
    for split_file in ["train.csv", "val.csv", "test.csv"]:
        df = pd.read_csv(REPO_ROOT / "data/processed/clinical_v2" / split_file)
        rows.append(df)
    clin = pd.concat(rows, ignore_index=True)

    records = []
    for _, row in clin.iterrows():
        img_path = row["image_path"]
        abs_path = REPO_ROOT / img_path
        w, h, ext, readable, notes = get_image_info(abs_path)
        label = str(row.get("raw_label", "")) or str(row.get("target_label", ""))
        records.append(
            {
                "image_path": img_path,
                "image_type": "clinical_macroscopic",
                "source_dataset": row["source_dataset"],
                "split": split_by_hash(img_path),
                "original_label_or_class_if_available": label,
                "width": w,
                "height": h,
                "file_ext": ext,
                "readable": readable,
                "notes": notes,
            }
        )
    return pd.DataFrame(records)


def load_dermoscopic() -> pd.DataFrame:
    """
    Load BCN20000 cancer-risk images as dermoscopic.
    Uses master_metadata which de-duplicates across the original cancer-risk splits.
    Reconstructs canonical image_path from isic_id since the metadata CSV may contain
    teammate-local paths (revela/Rehma_Revela/…) that don't exist in this repo.
    """
    master = pd.read_csv(
        REPO_ROOT / "data/processed/bcn20000_cancer_risk/master_metadata.csv"
    )

    records = []
    for _, row in master.iterrows():
        # Canonical path relative to repo root
        isic_id = str(row["isic_id"])
        img_path = f"data/raw/bcn20000/images/{isic_id}.jpg"
        abs_path = REPO_ROOT / img_path
        w, h, ext, readable, notes = get_image_info(abs_path)
        label = str(row.get("class_label", "")) or str(row.get("diagnosis_3", ""))
        records.append(
            {
                "image_path": img_path,
                "image_type": "dermoscopic",
                "source_dataset": "bcn20000",
                "split": split_by_hash(img_path),
                "original_label_or_class_if_available": label,
                "width": w,
                "height": h,
                "file_ext": ext,
                "readable": readable,
                "notes": notes,
            }
        )
    return pd.DataFrame(records)


def main():
    print("Loading clinical_macroscopic images (clinical_v2)…")
    clin_df = load_clinical_macroscopic()
    print(f"  Loaded {len(clin_df)} clinical records")

    print("Loading dermoscopic images (BCN20000)…")
    derm_df = load_dermoscopic()
    print(f"  Loaded {len(derm_df)} dermoscopic records")

    index = pd.concat([clin_df, derm_df], ignore_index=True)

    # ── Validation ────────────────────────────────────────────────────────────
    dup_count = index["image_path"].duplicated().sum()
    if dup_count > 0:
        print(f"WARNING: {dup_count} duplicate image_path rows detected — keeping first")
        index = index.drop_duplicates(subset="image_path", keep="first")

    unreadable = (~index["readable"]).sum()
    missing = (index["notes"] == "file_not_found").sum()
    pil_errors = (index["notes"].str.startswith("pil_error", na=False)).sum()

    # Exclude unreadable from training index (mark, not drop)
    readable_index = index[index["readable"]].copy()

    # Verify splits contain both classes
    for split in ["train", "val", "test"]:
        split_classes = readable_index[readable_index["split"] == split]["image_type"].unique()
        missing_classes = {"clinical_macroscopic", "dermoscopic"} - set(split_classes)
        if missing_classes:
            print(f"ERROR: split '{split}' is missing classes: {missing_classes}")
            sys.exit(1)

    # Verify no 'unsupported' class
    if "unsupported" in index["image_type"].values:
        print("ERROR: 'unsupported' class found in index")
        sys.exit(1)

    # ── Write CSV ─────────────────────────────────────────────────────────────
    out_dir = REPO_ROOT / "outputs/model"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "image_type_classifier_dataset_index.csv"
    index.to_csv(out_path, index=False)
    print(f"\nWrote {len(index)} rows → {out_path.relative_to(REPO_ROOT)}")

    # ── Print summary stats ───────────────────────────────────────────────────
    print("\n── Class counts (all rows) ──")
    print(index["image_type"].value_counts().to_string())

    print("\n── Source counts ──")
    print(index["source_dataset"].value_counts().to_string())

    print("\n── Split counts (all rows) ──")
    print(index.groupby(["split", "image_type"]).size().to_string())

    print("\n── Readable (all rows) ──")
    print(index["readable"].value_counts().to_string())
    print(f"  file_not_found : {missing}")
    print(f"  pil_error      : {pil_errors}")
    print(f"  duplicates removed: {dup_count}")

    print("\n── Split counts (readable only) ──")
    print(readable_index.groupby(["split", "image_type"]).size().to_string())

    print("\n── Resolution distribution (readable, width) ──")
    print(readable_index["width"].describe().to_string())

    print("\nDone.")


if __name__ == "__main__":
    main()
