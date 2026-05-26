# Image-Type Classifier Dataset Summary

**Index file:** `outputs/model/image_type_classifier_dataset_index.csv`  
**Builder script:** `scripts/build_image_type_classifier_dataset.py`  
**Date built:** 2026-05-26  
**Branch:** v2.24-image-type-dataset

---

## Purpose

Two-class image-type classifier to distinguish:
- `clinical_macroscopic` — smartphone / clinical photos of skin conditions
- `dermoscopic` — dermoscopy images taken with a dermatoscope

This index is Stage 1 only. No model is trained here.

---

## Source Files Used to Build the Index

| Source CSV | Description |
|---|---|
| `data/processed/clinical_v2/train.csv` | Clinical V2 training split (SCIN + Fitzpatrick17k) |
| `data/processed/clinical_v2/val.csv` | Clinical V2 validation split |
| `data/processed/clinical_v2/test.csv` | Clinical V2 test split |
| `data/processed/bcn20000_cancer_risk/master_metadata.csv` | BCN20000 de-duplicated master (used for the dermoscopic cancer-risk model) |

> **Note on BCN20000 paths:** The `master_metadata.csv` was updated in a recent commit to contain teammate-local paths (`revela/Rehma_Revela/data/ISIC-images/…`) that do not exist in this repository. The builder script reconstructs the canonical path `data/raw/bcn20000/images/{isic_id}.jpg` from the `isic_id` column. All 17,639 images resolved successfully at that path.

---

## Class Counts

| image_type | Count |
|---|---|
| `dermoscopic` | 17,639 |
| `clinical_macroscopic` | 10,019 |
| **Total** | **27,658** |

Class ratio (dermoscopic : clinical_macroscopic) = **1.76 : 1**

---

## Source Dataset Counts

| source_dataset | Count | image_type |
|---|---|---|
| `bcn20000` | 17,639 | dermoscopic |
| `fitzpatrick17k` | 6,354 | clinical_macroscopic |
| `google_scin` | 3,665 | clinical_macroscopic |

---

## Split Counts

Split assigned deterministically by SHA-256 hash of `image_path` mod 10000, with cutoffs at 70/15/15.

| split | image_type | Count |
|---|---|---|
| train | clinical_macroscopic | 6,980 |
| train | dermoscopic | 12,344 |
| val | clinical_macroscopic | 1,506 |
| val | dermoscopic | 2,647 |
| test | clinical_macroscopic | 1,533 |
| test | dermoscopic | 2,648 |
| **Total** | | **27,658** |

Split proportions approximate 70/15/15 for both classes individually (verified above).

---

## Unreadable / Missing File Counts

| Issue | Count |
|---|---|
| `file_not_found` | 0 |
| `pil_error` | 0 |
| Unreadable total | **0** |

All 27,658 images were opened successfully by PIL.

---

## Duplicate Image Path Check

Duplicate `image_path` rows: **0**

No image appears more than once in the index. Cross-split leakage via path identity is ruled out.

---

## Resolution Distribution

All BCN20000 (dermoscopic) images are uniformly **1024 × 1024 px**.

Clinical macroscopic images have variable resolutions (smartphone photos):

| Statistic | Width (px) | Height (px) |
|---|---|---|
| count | 10,019 | 10,019 |
| mean | 621 | ~680 |
| min | 89 | 85 |
| 25th pct | ~512 | ~512 |
| 50th pct | ~600 | ~600 |
| max | 3,872 | 3,288 |

> **Implication for training:** The resolution difference between dermoscopic (uniform 1024²) and clinical (variable, smaller on average) could be a spurious shortcut. The classifier should be trained on resized/cropped versions to the same input size (e.g., 224×224) before evaluating, and resolution-based features should be explicitly tested as a potential bias source.

---

## Split Logic

- Split key: SHA-256 hash of `image_path` string → integer mod 10000
- Cutoffs: `< 7000` → train, `7000–8499` → val, `8500+` → test
- Seed: implicit in the hash function (deterministic, no random seed needed)
- Splits are non-overlapping by construction (one path → one bucket)
- The `split` column in the original disease-classification CSVs is **not** reused here; this classifier gets independent splits

---

## Leakage / Shortcut Risks

| Risk | Assessment |
|---|---|
| **Path-identity leakage** | None — 0 duplicate paths, hash-based split ensures each image is in exactly one split |
| **Resolution shortcut** | Moderate risk — dermoscopic images are uniformly 1024×1024; clinical images are smaller and variable. Model could learn resolution rather than visual type. Mitigate by resizing all images to a fixed input size before training. |
| **Source-dataset shortcut** | Moderate risk — all dermoscopic examples come from one dataset (BCN20000) and all clinical examples come from two (SCIN, Fitzpatrick17k). The model could learn dataset-level artifacts rather than image type. `source_dataset` is included in the index for audit only and must not be used as a model input. |
| **Label shortcut** | Low risk — disease labels are orthogonal to image type and are not used in the classifier |
| **JPEG artifact shortcut** | Low — all images are JPG; BCN20000 was collected clinically with a dermatoscope and SCIN/Fitzpatrick17k via smartphone/web, so JPEG compression profiles may differ slightly |

---

## Why `unsupported` Is Not Used as a Training Class

The `unsupported` category exists in the Revela app routing to handle images that are neither clinical macroscopic nor dermoscopic (e.g., pathology slides, synthetic images, noise). Including `unsupported` as a training class would require a carefully curated negative set with clear boundaries. Without that, the model would learn an ill-defined catch-all rather than a meaningful boundary.

The image-type classifier's role is binary: confidently separate clinical from dermoscopic. Out-of-distribution detection (flagging truly unsupported images) should be handled at inference time via confidence thresholding or a separate OOD detector, not by training a "junk" class on unlabeled negatives.

---

## Recommendation for Stage 2 Training

Stage 2 training is ready to start subject to the following:

1. **Address class imbalance:** Ratio is 1.76:1 (dermoscopic : clinical). Use class-weighted loss (`pos_weight` or `weight` in CrossEntropyLoss) or oversample the minority class during training.

2. **Resize all inputs to a fixed size** (e.g., 224×224) before training to prevent the model from learning resolution as a proxy for image type.

3. **Hold `source_dataset` out of the model** — it is in the index for audit only. The model must not receive it as a feature.

4. **Evaluate on a held-out cross-source subset** after training: e.g., evaluate dermoscopic performance on any non-BCN20000 dermoscopic images if they become available, to check for dataset-level shortcut learning.

5. **Recommended architecture:** EfficientNet-B0 or MobileNetV3-Small pretrained on ImageNet — consistent with the existing BCN20000 cancer-risk model and Clinical V2 model, enabling weight reuse and keeping inference lightweight.

6. **Minimum baseline to beat:** a trivial classifier predicting the majority class (dermoscopic) would achieve ~63.8% accuracy. Any trained model should significantly exceed this, and recall on the minority class (clinical_macroscopic) should be ≥ 0.90.
