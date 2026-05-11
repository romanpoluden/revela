# Clinical Model v2 Label Inventory

## Purpose

This document supports issue #112: **V2.1 — Inspect SCIN and Fitzpatrick17k labels for melanoma-risk triage**.

The goal is to check whether the available clinical-photo metadata can support a future **clinical melanoma-risk triage model v2** for Revela.

The current product direction is not a broad all-skin-disease classifier. The preferred v2 direction is:

> Clinical photo → melanoma-risk triage → request dermoscopic image if melanoma-like concern or uncertainty is high.

This document only analyzes metadata/labels. It does not decide that a clinical model can be trained yet.

---

## Current CNN v1 context

CNN v1 remains unchanged:

- Dataset: BCN20000
- Image domain: dermoscopic images
- Classes: Melanoma, Benign nevus, Other lesion
- Model: EfficientNet-B0
- Test top-1 accuracy: 76.16%
- Test macro-F1: 0.7443
- Test balanced accuracy: 75.29%

SCIN and Fitzpatrick17k must not be mixed into CNN v1 training. They are candidates only for future clinical-photo model planning.

---

## Metadata files inspected

### SCIN

Files inspected:

- `scin_cases.csv`
- `scin_labels.csv`
- `scin_app_questions.csv`
- `scin_label_questions.csv`

Observed structure:

- `scin_cases.csv`: 5,033 cases, 57 columns
- `scin_labels.csv`: 5,033 cases, 17 columns
- Up to 3 images per case
- `case_id` is available and links cases to labels
- Image paths are available in `image_1_path`, `image_2_path`, `image_3_path`
- Dermatologist labels and weighted condition labels are available
- Fitzpatrick and Monk-related skin tone metadata are available

### Fitzpatrick17k

File inspected:

- `fitzpatrick17k.csv`

Observed structure:

- 16,577 rows, 9 columns
- Main label column: `label`
- Broad labels: `nine_partition_label`, `three_partition_label`
- Skin-tone fields: `fitzpatrick_scale`, `fitzpatrick_centaur`
- URL field: `url`
- No clear `case_id`, `patient_id`, or `lesion_id`

---

## SCIN label inventory

SCIN has 5,033 cases. It is strong for clinical/photo-style images and metadata, but weak for melanoma/nevus counts.

### SCIN label columns

Relevant columns:

- `dermatologist_skin_condition_on_label_name`
- `dermatologist_skin_condition_confidence`
- `weighted_skin_condition_label`
- `dermatologist_gradable_for_skin_condition_1/2/3`
- `dermatologist_fitzpatrick_skin_type_label_1/2/3`
- `monk_skin_tone_label_india`
- `monk_skin_tone_label_us`

The `weighted_skin_condition_label` field can be used to identify the highest-weighted label per case, but it should be treated carefully because it may combine multiple dermatologist opinions.

### SCIN top weighted labels

Top weighted labels show that SCIN is mostly useful for inflammatory/rash-style conditions:

| Label | Top weighted count |
|---|---:|
| Eczema | 488 |
| Allergic Contact Dermatitis | 270 |
| Urticaria | 214 |
| Insect Bite | 185 |
| Folliculitis | 142 |
| Psoriasis | 109 |
| Tinea | 93 |
| Impetigo | 69 |
| Herpes Zoster | 68 |
| Acne | 61 |
| Drug Rash | 58 |

### SCIN melanoma/nevus-related labels

Counts across all dermatologist label mentions:

| Label group | Mention count | Top weighted count |
|---|---:|---:|
| Melanoma-related | 7 | 1 |
| Nevus / melanocytic-related | 26 | 7 |
| Basal cell carcinoma-related | 23 | 6 |
| SCC / squamous-related | 38 | 8 |
| Actinic keratosis | 22 | 12 |

Exact SCIN melanoma/nevus labels observed:

| Label | Mention count | Top weighted count |
|---|---:|---:|
| Melanoma | 7 | 1 |
| Melanocytic Nevus | 14 | 5 |
| Atypical Nevus | 5 | 0 |
| Epidermal nevus | 5 | 2 |
| Nevus anemicus | 1 | 0 |
| Vascular nevus of skin | 1 | 0 |

### SCIN interpretation

SCIN is **not suitable as the main source for clinical melanoma/nevus triage training** because melanoma and nevus counts are too low.

SCIN is useful for:

- clinical-photo metadata design;
- skin-tone metadata analysis;
- image quality / gradability concepts;
- possible non-melanoma negative examples;
- future inflammatory/rash module exploration.

However, SCIN alone cannot support a reliable melanoma-risk triage classifier.

---

## Fitzpatrick17k label inventory

Fitzpatrick17k has 16,577 rows and 114 unique fine-grained labels. It has much stronger melanoma and nevus label coverage than SCIN, but weaker metadata quality.

### Fitzpatrick17k label columns

Relevant columns:

- `label`
- `nine_partition_label`
- `three_partition_label`
- `fitzpatrick_scale`
- `fitzpatrick_centaur`
- `url`
- `qc`

### Fitzpatrick17k partition counts

`three_partition_label`:

| Partition | Count |
|---|---:|
| non-neoplastic | 12,080 |
| malignant | 2,263 |
| benign | 2,234 |

`nine_partition_label`:

| Partition | Count |
|---|---:|
| inflammatory | 10,886 |
| malignant epidermal | 1,352 |
| genodermatoses | 1,194 |
| benign dermal | 1,067 |
| benign epidermal | 931 |
| malignant melanoma | 573 |
| benign melanocyte | 236 |
| malignant cutaneous lymphoma | 182 |
| malignant dermal | 156 |

### Fitzpatrick17k melanoma-related labels

Fine-grained melanoma-related labels:

| Label | Count |
|---|---:|
| melanoma | 261 |
| superficial spreading melanoma ssm | 118 |
| malignant melanoma | 111 |

Combined fine-grained melanoma-related rows: **490**.

The broader `nine_partition_label` value `malignant melanoma` has **573** rows. This is larger than the direct fine-grained label match and may include additional melanoma-related classes.

### Fitzpatrick17k nevus / benign melanocytic labels

Fine-grained nevus-related labels:

| Label | Count |
|---|---:|
| nevus sebaceous of jadassohn | 95 |
| epidermal nevus | 91 |
| nevocytic nevus | 86 |
| halo nevus | 82 |
| congenital nevus | 68 |
| becker nevus | 63 |

Combined fine-grained nevus-related rows: **485**.

The broader `nine_partition_label` value `benign melanocyte` has **236** rows. This is likely a cleaner but narrower grouping for benign melanocytic lesions.

### Fitzpatrick17k other malignant / lesion-relevant labels

| Label | Count |
|---|---:|
| squamous cell carcinoma | 581 |
| basal cell carcinoma | 468 |
| actinic keratosis | 175 |
| seborrheic keratosis | 69 |
| solid cystic basal cell carcinoma | 66 |
| basal cell carcinoma morpheiform | 62 |

These labels may be relevant as non-melanoma malignant or melanoma-like confounder classes.

### Fitzpatrick17k inflammatory / non-melanoma labels

Examples of inflammatory or non-melanoma labels:

| Label | Count |
|---|---:|
| psoriasis | 653 |
| allergic contact dermatitis | 430 |
| folliculitis | 342 |
| acne vulgaris | 335 |
| eczema | 204 |
| acne | 183 |
| urticaria | 151 |
| seborrheic dermatitis | 126 |
| urticaria pigmentosa | 112 |
| dyshidrotic eczema | 83 |

These labels are useful for negative/non-melanoma examples, but they may be too visually different from melanoma-like lesions. For a melanoma-risk triage model, hard negatives such as nevi, seborrheic keratosis, basal cell carcinoma, and actinic keratosis may be more important than inflammatory classes.

---

## Skin-tone metadata inventory

### SCIN

SCIN has stronger skin-tone metadata:

- User/self-reported `fitzpatrick_skin_type` is present but partially missing.
- Dermatologist Fitzpatrick labels are available.
- Monk Skin Tone labels are available for most cases.

Observed counts:

- `monk_skin_tone_label_india`: 5,019 non-null
- `monk_skin_tone_label_us`: 5,005 non-null
- `dermatologist_fitzpatrick_skin_type_label_1`: 4,302 non-null
- `dermatologist_fitzpatrick_skin_type_label_2`: 634 non-null
- `dermatologist_fitzpatrick_skin_type_label_3`: 631 non-null

SCIN is therefore stronger for fairness/slice-evaluation planning, although melanoma/nevus sample sizes are too small.

### Fitzpatrick17k

Fitzpatrick17k includes:

- `fitzpatrick_scale`
- `fitzpatrick_centaur`

Observed `fitzpatrick_scale` counts:

| Fitzpatrick scale | Count |
|---|---:|
| -1 / unknown | 565 |
| 1 | 2,947 |
| 2 | 4,808 |
| 3 | 3,308 |
| 4 | 2,781 |
| 5 | 1,533 |
| 6 | 635 |

Fitzpatrick17k therefore has usable skin-tone grouping metadata, but the reliability and source of those labels should be documented carefully.

---

## Suitability for clinical melanoma-risk triage

### SCIN

Verdict: **Not sufficient for melanoma-risk triage training by itself.**

Reason:

- Too few melanoma and nevus cases.
- Strong clinical metadata, but not enough positive melanoma examples.

Best use:

- Clinical-photo metadata reference.
- Skin-tone/fairness planning reference.
- Possible non-melanoma negative examples if model design allows it.
- Separate inflammatory/rash model exploration if the product direction changes.

### Fitzpatrick17k

Verdict: **Potentially useful for exploratory clinical melanoma-risk triage, but not ready without image availability and leakage checks.**

Reason:

- Has melanoma-related labels.
- Has nevus/benign melanocytic labels.
- Has non-melanoma malignant and benign/inflammatory labels.
- But lacks case/patient/lesion IDs.
- URL image availability must be validated.
- Label quality and clinical confirmation method are weaker.

Best use:

- Candidate dataset for clinical-photo melanoma-risk triage feasibility.
- Candidate source for initial label taxonomy analysis.
- Not enough yet for a trustworthy model-training decision.

---

## Taxonomy implications

Based on current label inventory, three possible v2 taxonomies should be considered.

### Option A — Binary triage

Labels:

- Melanoma-like concern
- No melanoma-like concern

Pros:

- Closest to safety-driven practitioner use case.
- Directly optimizes melanoma recall/sensitivity.
- Easier to explain.

Cons:

- Requires careful threshold tuning.
- May create many false positives.
- Needs strong negative class construction.

### Option B — Three-way triage

Labels:

- High melanoma concern
- Low melanoma concern
- Unclear / needs dermoscopy

Pros:

- Best product fit.
- Allows uncertain cases to route to dermoscopic follow-up.
- Avoids forced classification when image quality or confidence is poor.

Cons:

- Requires a defined rule for `Unclear`.
- May require calibration or confidence thresholds.

### Option C — Multi-class clinical lesion model

Possible labels:

- Melanoma
- Benign nevus / benign melanocytic lesion
- Other malignant lesion
- Benign non-melanocytic lesion
- Inflammatory / rash-like
- Other / unclear

Pros:

- More informative.
- Better educational detail.

Cons:

- More complex.
- More label noise.
- Requires larger, cleaner datasets.
- Higher risk of unstable performance.

### Recommended planning direction

For v2 planning, prefer **Option B: three-way melanoma-risk triage**.

Recommended outputs:

- High melanoma concern
- Low melanoma concern
- Unclear / needs dermoscopy

This matches the product idea: clinical photo first, dermoscopic follow-up if risk or uncertainty is high.

---

## Evaluation implications

For clinical v2, generic accuracy should not be the main metric.

Priority metrics:

- Melanoma recall / sensitivity
- Melanoma false-negative rate
- Specificity
- Balanced accuracy
- Class-wise F1
- Confusion matrix

Key principle:

> Higher melanoma sensitivity may be worth lower specificity if the product is clearly positioned as triage and does not claim diagnosis.

Do not claim that the model detects all melanoma cases.

---

## Missing information before training decision

Before training clinical model v2, the team still needs:

1. Image availability validation, especially for Fitzpatrick17k URLs.
2. Split feasibility check, especially because Fitzpatrick17k has no clear case/patient/lesion ID.
3. Duplicate-image risk analysis.
4. Label quality review.
5. Decision on binary vs three-way vs multi-class taxonomy.
6. Definition of `Unclear / needs dermoscopy`.
7. Minimum melanoma sample count for credible evaluation.
8. Safety and wording rules for clinical triage output.

---

## Final recommendation

SCIN and Fitzpatrick17k are useful for planning, but they do not yet prove that clinical model v2 can be trained responsibly.

Recommended next steps:

1. Use Fitzpatrick17k as the main candidate for melanoma/nevus clinical-photo label analysis.
2. Use SCIN as metadata/fairness reference and possible non-melanoma negative dataset, but not as the primary melanoma dataset.
3. Complete image availability and leakage-safe split feasibility before any training decision.
4. Define v2 as three-way melanoma-risk triage unless label analysis proves a stronger option.
5. Keep CNN v1 and clinical v2 separate.
