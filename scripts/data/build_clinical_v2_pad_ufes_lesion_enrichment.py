"""
V2.16 — Build PAD-UFES lesion-routing enrichment variant for Clinical V2.
Issue #157. Dataset preparation only — no training, evaluation, or inference changes.
"""

import hashlib
import os

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import GroupShuffleSplit

PAD_META = "Data Samples/pad-ufes-20_metadata_2026-05-15.csv"
IMAGE_DIR = "revela/Rehma_Revela/data/PAD-UFES"

CLINv2_TRAIN = "data/processed/clinical_v2/train.csv"
CLINv2_VAL   = "data/processed/clinical_v2/val.csv"
CLINv2_TEST  = "data/processed/clinical_v2/test.csv"

OUT_DIR = "data/processed/clinical_v2_pad_ufes_lesion_enrichment"

SEED      = 42
VAL_RATIO = 0.15

# diagnosis_3 full-name → short code
DIAG3_TO_SHORT = {
    "Basal cell carcinoma":          "BCC",
    "Squamous cell carcinoma, NOS":  "SCC",
    "Melanoma, NOS":                 "MEL",
    "Solar or actinic keratosis":    "ACK",
    "Nevus":                         "NEV",
    "Seborrheic keratosis":          "SEK",
}

INCLUDE_MAP = {
    "BCC": "Lesion — dermoscopic review recommended",
    "SCC": "Lesion — dermoscopic review recommended",
    "MEL": "Lesion — dermoscopic review recommended",
    "ACK": "Lesion — dermoscopic review recommended",
}
EXCLUDE_LABELS = ["NEV", "SEK"]
EXCLUDE_REASON = {
    "NEV": "Benign melanocytic nevus — may dilute lesion-routing safety signal in 5-class taxonomy",
    "SEK": "Seborrheic keratosis — benign keratosis, more appropriate for 8-class taxonomy",
}


def file_hash(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


# ── SECTION 1 — Load and inspect PAD-UFES ────────────────────────────────────

pad = pd.read_csv(PAD_META)
print(f"PAD-UFES total rows: {len(pad):,}")

# Confirm required source columns
REQUIRED_COLS = ["patient_id", "lesion_id", "diagnosis_3", "isic_id"]
for col in REQUIRED_COLS:
    assert col in pad.columns, f"Missing column: {col} — STOP"
print("All required columns confirmed (patient_id, lesion_id, diagnosis_3, isic_id).")

# Derive short-code diagnostic column
pad["diagnostic"] = pad["diagnosis_3"].map(DIAG3_TO_SHORT)

print(f"\nAll diagnostic counts:")
print(pad["diagnostic"].value_counts().to_string())


# ── SECTION 2 — Apply taxonomy mapping and exclusions ────────────────────────

print("\nInclusion/exclusion breakdown:")
for diag, count in pad["diagnostic"].value_counts().items():
    if pd.isna(diag):
        status = "EXCLUDE — not in scope (unmapped diagnosis_3)"
    elif diag in INCLUDE_MAP:
        status = "INCLUDE"
    else:
        status = f"EXCLUDE — {EXCLUDE_REASON.get(diag, 'not in scope')}"
    print(f"  {str(diag):5s}: {count:>4,}  {status}")

pad_included = pad[pad["diagnostic"].isin(INCLUDE_MAP)].copy()
pad_excluded = pad[pad["diagnostic"].isin(EXCLUDE_LABELS)].copy()

pad_included["target_label"]   = pad_included["diagnostic"].map(INCLUDE_MAP)
pad_included["source_dataset"] = "pad_ufes_20"

print(f"\nIncluded rows: {len(pad_included):,}")
print(f"Excluded rows: {len(pad_excluded):,}"
      f" (NEV: {(pad['diagnostic']=='NEV').sum()},"
      f" SEK: {(pad['diagnostic']=='SEK').sum()})")


# ── SECTION 3 — Validate image paths for ALL included rows ───────────────────

def resolve_image_path(isic_id):
    for ext in [".jpg", ".jpeg", ".png"]:
        p = os.path.join(IMAGE_DIR, isic_id + ext)
        if os.path.exists(p):
            return p
        p2 = os.path.join(IMAGE_DIR, isic_id)
        if os.path.exists(p2):
            return p2
    return None

pad_included["image_path"] = pad_included["isic_id"].apply(resolve_image_path)

missing = pad_included["image_path"].isna()
print(f"\nImage paths resolved: {(~missing).sum():,}/{len(pad_included):,}")
if missing.sum() > 0:
    print(f"WARNING: {missing.sum()} images not found:")
    print(pad_included[missing]["isic_id"].head(10).to_string())
    print("Dropping rows with missing images.")
    pad_included = pad_included[~missing].copy()

print(f"Final included rows after image check: {len(pad_included):,}")


# ── SECTION 4 — Patient-level leakage-safe split ─────────────────────────────

unique_patients = pad_included["patient_id"].unique()
print(f"\nUnique patients in included set: {len(unique_patients):,}")

gss = GroupShuffleSplit(n_splits=1, test_size=VAL_RATIO, random_state=SEED)
train_idx, val_idx = next(gss.split(pad_included, groups=pad_included["patient_id"]))

pad_train = pad_included.iloc[train_idx].copy()
pad_val   = pad_included.iloc[val_idx].copy()

train_patients = set(pad_train["patient_id"])
val_patients   = set(pad_val["patient_id"])
assert len(train_patients & val_patients) == 0, "Patient leakage between train and val — STOP"

train_lesions = set(pad_train["lesion_id"])
val_lesions   = set(pad_val["lesion_id"])
assert len(train_lesions & val_lesions) == 0, "Lesion leakage between train and val — STOP"

print(f"PAD-UFES train rows: {len(pad_train):,} | val rows: {len(pad_val):,}")
print("Patient leakage: NONE confirmed")
print("Lesion leakage:  NONE confirmed")

val_counts = pad_val["target_label"].value_counts()
print(f"\nVal class distribution:\n{val_counts.to_string()}")
if (val_counts < 3).any():
    print("WARNING: some classes have < 3 val examples — patient-level split causes imbalance")
    print("Documenting this in summary. Proceeding with patient-level split as per issue scope.")


# ── SECTION 5 — Load Clinical V2 splits and capture test set hash ─────────────

test_hash_before = file_hash(CLINv2_TEST)
cv2_train = pd.read_csv(CLINv2_TRAIN)
cv2_val   = pd.read_csv(CLINv2_VAL)
cv2_test  = pd.read_csv(CLINv2_TEST)

print(f"\nClinical V2 train: {len(cv2_train):,} | val: {len(cv2_val):,} | test: {len(cv2_test):,}")
print(f"Test hash (before): {test_hash_before}")

CV2_REQUIRED = list(cv2_train.columns)
print(f"Clinical V2 columns ({len(CV2_REQUIRED)}): {CV2_REQUIRED}")


# ── SECTION 6 — Align PAD-UFES to Clinical V2 schema and merge ───────────────

LESION_CLASS_IDX = int(
    cv2_train[cv2_train["target_label"] == "Lesion — dermoscopic review recommended"]["class_idx"].iloc[0]
)
print(f"\nLesion-routing class_idx in Clinical V2: {LESION_CLASS_IDX}")

for df in [pad_train, pad_val]:
    df["class_idx"]  = LESION_CLASS_IDX
    df["source_id"]  = df["isic_id"]
    df["case_id"]    = df["patient_id"]
    df["raw_label"]  = df["diagnosis_3"]
    for col in CV2_REQUIRED:
        if col not in df.columns:
            df[col] = None

pad_train_aligned = pad_train[CV2_REQUIRED].copy()
pad_val_aligned   = pad_val[CV2_REQUIRED].copy()

merged_train = pd.concat([cv2_train, pad_train_aligned], ignore_index=True)
merged_val   = pd.concat([cv2_val,   pad_val_aligned],   ignore_index=True)

print(f"\nMerged train: {len(merged_train):,} (+{len(pad_train_aligned):,} PAD-UFES rows)")
print(f"Merged val:   {len(merged_val):,} (+{len(pad_val_aligned):,} PAD-UFES rows)")

def lesion_pct(df, label="Lesion — dermoscopic review recommended"):
    n = (df["target_label"] == label).sum()
    return n, n / len(df) * 100

cv2_lesion_n, cv2_lesion_pct = lesion_pct(cv2_train)
mrg_lesion_n, mrg_lesion_pct = lesion_pct(merged_train)
print(f"\nLesion-routing rows:")
print(f"  Clinical V2 train:  {cv2_lesion_n:,} ({cv2_lesion_pct:.1f}%)")
print(f"  Merged train:       {mrg_lesion_n:,} ({mrg_lesion_pct:.1f}%)")
overweight = ("HIGH"     if mrg_lesion_pct > cv2_lesion_pct * 1.5
              else "MODERATE" if mrg_lesion_pct > cv2_lesion_pct * 1.2
              else "LOW")
print(f"  Over-weighting risk: {overweight}")


# ── SECTION 7 — Class distribution before and after ──────────────────────────

print("\n=== CLASS DISTRIBUTION BEFORE ENRICHMENT ===")
for cls, n in cv2_train["target_label"].value_counts().items():
    print(f"  {cls:45s} {n:>5,}  ({n/len(cv2_train)*100:.1f}%)")

print("\n=== CLASS DISTRIBUTION AFTER ENRICHMENT ===")
for cls, n in merged_train["target_label"].value_counts().items():
    before = cv2_train["target_label"].value_counts().get(cls, 0)
    delta  = n - before
    print(f"  {cls:45s} {n:>5,}  ({n/len(merged_train)*100:.1f}%)  delta: +{delta}")


# ── SECTION 8 — Final asserts and save ───────────────────────────────────────

os.makedirs(OUT_DIR, exist_ok=True)

assert list(merged_train.columns) == CV2_REQUIRED, "Column mismatch in train — STOP"
assert list(merged_val.columns)   == CV2_REQUIRED, "Column mismatch in val — STOP"
assert merged_train["source_dataset"].isna().sum() == 0, "Missing source_dataset in train — STOP"
assert merged_val["source_dataset"].isna().sum() == 0,   "Missing source_dataset in val — STOP"

# Validate only PAD-UFES rows — Clinical V2 rows are cloud-stored and pre-validated
for df_name, pad_df in [("train", pad_train_aligned), ("val", pad_val_aligned)]:
    missing_paths = pad_df[~pad_df["image_path"].apply(os.path.exists)]
    assert len(missing_paths) == 0, f"{df_name} PAD-UFES: {len(missing_paths)} missing image paths — STOP"
    print(f"{df_name} PAD-UFES: all {len(pad_df):,} image paths verified")

merged_train.to_csv(f"{OUT_DIR}/train.csv", index=False)
merged_val.to_csv(  f"{OUT_DIR}/val.csv",   index=False)
cv2_test.to_csv(    f"{OUT_DIR}/test.csv",  index=False)

test_hash_after = file_hash(CLINv2_TEST)
assert test_hash_before == test_hash_after, "Clinical V2 test file was modified — STOP"
print(f"Test set hash unchanged: {test_hash_after}")
print(f"\nSaved to: {OUT_DIR}/")


# ── SECTION 9 — Write config YAML ────────────────────────────────────────────

config = {
    "variant_name":        "clinical_v2_pad_ufes_lesion_enrichment",
    "base_variant":        "clinical_v2",
    "enrichment_source":   "PAD-UFES-20",
    "enrichment_purpose":  "Reduce lesion-routing false negatives (baseline FN: 76)",
    "taxonomy":            "5-class Clinical V2 — unchanged",
    "pad_ufes_mapping": {
        "BCC": "Lesion — dermoscopic review recommended",
        "SCC": "Lesion — dermoscopic review recommended",
        "MEL": "Lesion — dermoscopic review recommended",
        "ACK": "Lesion — dermoscopic review recommended",
    },
    "excluded_labels": {
        "NEV": "Benign nevus — may dilute lesion-routing signal",
        "SEK": "Seborrheic keratosis — more appropriate for 8-class taxonomy",
    },
    "split_strategy": "patient_level",
    "split_seed":     SEED,
    "val_ratio":      VAL_RATIO,
    "data": {
        "train": f"{OUT_DIR}/train.csv",
        "val":   f"{OUT_DIR}/val.csv",
        "test":  f"{OUT_DIR}/test.csv",
    },
    "promotion_criteria": {
        "lesion_routing_fn_max":       76,
        "macro_f1_min":                0.6420,
        "scin_macro_f1_min":           0.4028,
        "fitzpatrick_macro_f1_min":    0.6366,
        "inflammatory_f1_note":        "must not collapse",
    },
    "out_of_scope": [
        "Model training",
        "Model evaluation",
        "Model promotion",
        "8-class taxonomy",
        "Clinical-readiness claims",
    ],
}

os.makedirs("config", exist_ok=True)
with open("config/clinical_v2_pad_ufes_lesion_enrichment_config.yaml", "w") as f:
    yaml.dump(config, f, allow_unicode=True, sort_keys=False)
print("Saved: config/clinical_v2_pad_ufes_lesion_enrichment_config.yaml")
