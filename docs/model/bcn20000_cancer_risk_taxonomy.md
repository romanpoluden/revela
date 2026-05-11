# BCN20000 Cancer-Risk Taxonomy

## Purpose

This document supports issue #117: **D3.2 — Create cancer-risk label mapping for BCN20000**.

The current dermoscopic baseline model used three classes:

- Melanoma
- Benign nevus
- Other lesion

That taxonomy is no longer sufficient for the product goal because the `Other lesion` class contains malignant non-melanoma skin cancer cases, especially basal cell carcinoma and squamous cell carcinoma.

The revised product goal is:

> Use the dermoscopic model to support cancer-risk classification while still providing educational lesion categories such as melanoma, non-melanoma skin cancer, benign nevus, and other non-cancer / indeterminate lesions.

This remains an educational prototype, not a diagnostic product.

---

## Metadata inspected

Input metadata:

- `bcn20000_metadata_2026-05-07.csv`

Metadata shape:

- Rows: 18,946
- Columns: 17

Relevant columns:

- `isic_id`
- `diagnosis_1`
- `diagnosis_2`
- `diagnosis_3`
- `diagnosis_confirm_type`
- `image_type`
- `lesion_id`
- `melanocytic`

All images in this metadata file are dermoscopic:

- `image_type = dermoscopic`: 18,946 rows

---

## Diagnosis distribution

### diagnosis_1

| diagnosis_1 | Rows |
|---|---:|
| Malignant | 8,871 |
| Benign | 7,831 |
| Indeterminate | 1,088 |
| Missing / NaN | 1,156 |

### diagnosis_2

| diagnosis_2 | Rows |
|---|---:|
| Benign melanocytic proliferations | 5,647 |
| Malignant melanocytic proliferations (Melanoma) | 4,636 |
| Malignant adnexal epithelial proliferations - Follicular | 3,676 |
| Benign epidermal proliferations | 1,551 |
| Missing / NaN | 1,156 |
| Indeterminate epidermal proliferations | 1,088 |
| Malignant epidermal proliferations | 559 |
| Benign soft tissue proliferations - Fibro-histiocytic | 482 |
| Benign soft tissue proliferations - Vascular | 151 |

### diagnosis_3

| diagnosis_3 | Rows |
|---|---:|
| Nevus | 5,647 |
| Melanoma, NOS | 4,003 |
| Basal cell carcinoma | 3,676 |
| Missing / NaN | 1,307 |
| Seborrheic keratosis | 1,268 |
| Solar or actinic keratosis | 1,088 |
| Melanoma metastasis | 633 |
| Squamous cell carcinoma, NOS | 559 |
| Scar | 314 |
| Solar lentigo | 283 |
| Dermatofibroma | 168 |

---

## Why the old taxonomy is insufficient

The old class `Other lesion` likely included:

- Basal cell carcinoma: 3,676 rows
- Squamous cell carcinoma, NOS: 559 rows
- Solar or actinic keratosis: 1,088 rows
- Seborrheic keratosis: 1,268 rows
- Solar lentigo: 283 rows
- Scar: 314 rows
- Dermatofibroma: 168 rows

This means `Other lesion` contained both:

- malignant non-melanoma cancer cases;
- pre-cancer / indeterminate-risk cases;
- benign/non-cancer cases.

Therefore, `Other lesion` must not be interpreted as low-risk, benign, or non-cancer.

---

## Recommended target taxonomy

Recommended next taxonomy for retraining:

1. **Melanoma**
2. **Non-melanoma skin cancer**
3. **Benign nevus**
4. **Other non-cancer / indeterminate lesion**

This is a 4-class taxonomy. It preserves the most important educational and safety distinctions while avoiding very small classes.

The previous 5-class proposal separated:

- Pre-cancer / indeterminate risk
- Other benign / non-cancer lesion

The team decided to combine these because both classes were relatively small:

- Pre-cancer / indeterminate risk: 1,088 rows
- Other benign / non-cancer lesion: 2,033 rows

Combined class:

- Other non-cancer / indeterminate lesion: 3,121 rows

This is more stable for the next training experiment.

---

## Raw diagnosis to target mapping

| diagnosis_3 | Rows | Target class | Risk group |
|---|---:|---|---|
| Melanoma, NOS | 4,003 | Melanoma | Cancer / malignant |
| Melanoma metastasis | 633 | Melanoma | Cancer / malignant |
| Basal cell carcinoma | 3,676 | Non-melanoma skin cancer | Cancer / malignant |
| Squamous cell carcinoma, NOS | 559 | Non-melanoma skin cancer | Cancer / malignant |
| Nevus | 5,647 | Benign nevus | Non-cancer / benign |
| Solar or actinic keratosis | 1,088 | Other non-cancer / indeterminate lesion | Non-cancer / indeterminate |
| Seborrheic keratosis | 1,268 | Other non-cancer / indeterminate lesion | Non-cancer / indeterminate |
| Solar lentigo | 283 | Other non-cancer / indeterminate lesion | Non-cancer / indeterminate |
| Scar | 314 | Other non-cancer / indeterminate lesion | Non-cancer / indeterminate |
| Dermatofibroma | 168 | Other non-cancer / indeterminate lesion | Non-cancer / indeterminate |
| Missing / NaN | 1,307 | Exclude / unknown | Unknown / excluded |

Mapping CSV:

- `data/processed/bcn20000/cancer_risk_label_mapping.csv`

---

## Target class counts

| Target class | Rows |
|---|---:|
| Benign nevus | 5,647 |
| Melanoma | 4,636 |
| Non-melanoma skin cancer | 4,235 |
| Other non-cancer / indeterminate lesion | 3,121 |
| Exclude / unknown | 1,307 |

If unknown rows are excluded, usable mapped rows:

- 17,639 rows

---

## Risk group counts

| Risk group | Rows |
|---|---:|
| Cancer / malignant | 8,871 |
| Non-cancer / benign | 5,647 |
| Non-cancer / indeterminate | 3,121 |
| Unknown / excluded | 1,307 |

If unknown rows are excluded, usable mapped rows:

- 17,639 rows

---

## Handling actinic keratosis

Decision for next experiment:

> Treat `Solar or actinic keratosis` as part of **Other non-cancer / indeterminate lesion**.

Rationale:

- It is not usually classified as invasive cancer.
- It is clinically relevant and risk-associated.
- The separate pre-cancer class had only 1,088 rows.
- Combining it with other non-cancer / indeterminate lesions creates a more stable class for the next training experiment.

Important communication rule:

> The combined class must not be described as simply “benign” or “safe,” because it includes actinic keratosis.

Use the label `Other non-cancer / indeterminate lesion`, not `Other benign lesion`.

---

## Handling missing / unknown diagnosis rows

Rows with missing `diagnosis_3` should be excluded from the next supervised training experiment unless a reliable lower-level mapping can be agreed.

Reason:

- `diagnosis_3` is the most specific label available.
- Missing `diagnosis_3` rows create ambiguous target labels.
- Including them would add label noise.

Count excluded:

- 1,307 rows

---

## Training implications

The next training dataset should use the mapped 4-class taxonomy:

- Melanoma
- Non-melanoma skin cancer
- Benign nevus
- Other non-cancer / indeterminate lesion

Important implications:

- Class balance is better than the 5-class version.
- The smallest retained class has 3,121 rows.
- Class weighting may still be useful.
- Evaluation must include cancer/malignant recall and false-negative rate.
- Evaluation should also report melanoma recall and non-melanoma skin cancer recall separately.
- The new model should be compared against the old 3-class baseline only as a baseline, not as equivalent product models.

---

## Recommended evaluation metrics

For the retrained cancer-risk model, report:

- overall accuracy;
- macro-F1;
- balanced accuracy;
- class-wise precision, recall, F1;
- melanoma recall;
- non-melanoma skin cancer recall;
- cancer / malignant recall after grouping melanoma + non-melanoma skin cancer;
- cancer / malignant false-negative rate;
- confusion matrix.

Do not claim clinical validation.
Do not claim all cancers can be detected.

---

## Recommendation

Proceed with the 4-class cancer-risk educational taxonomy for the next dermoscopic model experiment.

Recommended next issue:

- #118 — Rebuild BCN20000 processed splits for cancer-risk taxonomy

Before training, the team should review and approve this mapping.
