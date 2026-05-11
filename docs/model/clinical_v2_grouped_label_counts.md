# Clinical Model v2 Grouped Label Counts

## Purpose

This document supports issue #124: **V2.4 — Count grouped clinical labels across SCIN and Fitzpatrick17k**.

The goal is to check how many examples fall into the approved grouped taxonomy for the future clinical-image model v2.

Clinical model v2 is separate from the dermoscopic cancer-risk model. Cancer-risk classification remains the responsibility of the dermoscopic model.

However, clinical model v2 now includes a routing class:

> Lesion — dermoscopic review recommended

This class is not a diagnosis and not a cancer prediction. It is a routing signal that asks the user to upload a dermoscopic image for additional educational review.

---

## Approved grouped taxonomy

Approved MVP taxonomy:

1. Eczema / dermatitis
2. Urticaria / allergic reaction
3. Folliculitis / acne-like
4. Psoriasis / papulosquamous
5. Lesion — dermoscopic review recommended

Excluded from first baseline:

- Tinea / fungal-like
- Viral / bacterial infection

The app may still show `Unclear / outside current clinical module`, but this should be implemented through confidence/uncertainty thresholds, not trained as a garbage-bucket class in the first baseline.

---

## Counting method

### SCIN

Primary counting method:

- Use `weighted_skin_condition_label`.
- Parse the weighted label dictionary.
- Use the highest-weighted label as the primary single-label target.
- Map the primary label to one of the approved grouped classes.
- Count only cases where the highest-weighted label maps to exactly one approved group.

Additional coverage count:

- `scin_any_weighted_case_count` counts cases where any weighted label maps to the group.
- This is useful for coverage analysis but should not be used as the first clean training target.

Image count:

- SCIN can contain up to 3 images per case.
- `scin_primary_image_count` counts available image paths for cases whose primary weighted label maps to the group.
- All images from the same `case_id` must stay in the same train/validation/test split.

### Fitzpatrick17k

Primary counting method:

- Use the `label` column.
- Map raw labels to the approved grouped classes.
- Count matching rows.

Current status:

- The team has downloaded all Fitzpatrick17k images locally.
- Local path mapping still needs to be validated in the dataset-building task.

Caution:

- Fitzpatrick17k lacks clear `case_id`, `patient_id`, or `lesion_id`.
- Fitzpatrick17k may introduce source-bias if mixed blindly with SCIN.
- Preserve dataset source in processed CSVs and report source-specific performance.

---

## Grouped count summary

| Target group | SCIN primary cases | SCIN primary images | SCIN any weighted cases | Fitzpatrick17k rows | Combined potential |
|---|---:|---:|---:|---:|---:|
| Eczema / dermatitis | 989 | 2,157 | 1,760 | 843 | 1,832 |
| Urticaria / allergic reaction | 235 | 492 | 525 | 351 | 586 |
| Folliculitis / acne-like | 226 | 478 | 374 | 1,023 | 1,249 |
| Psoriasis / papulosquamous | 142 | 304 | 427 | 1,615 | 1,757 |
| Lesion — dermoscopic review recommended | 67 | TBD | 111 | 2,410 | 2,477 |
| Tinea / fungal-like | 116 | 243 | 285 | 0 | 116 |
| Viral / bacterial infection | 217 | 433 | 494 | 0 | 217 |

Machine-readable output:

- `data/processed/clinical_v2_group_counts.csv`

---

## SCIN raw-label contribution by group

### Eczema / dermatitis

| Raw label | Primary case count |
|---|---:|
| Eczema | 523 |
| Allergic Contact Dermatitis | 408 |
| Irritant Contact Dermatitis | 103 |
| Acute dermatitis, NOS | 58 |
| Stasis Dermatitis | 33 |
| Acute and chronic dermatitis | 26 |
| Seborrheic Dermatitis | 18 |

### Urticaria / allergic reaction

| Raw label | Primary case count |
|---|---:|
| Urticaria | 193 |
| Drug Rash | 32 |
| Hypersensitivity | 19 |

### Folliculitis / acne-like

| Raw label | Primary case count |
|---|---:|
| Folliculitis | 132 |
| Acne | 59 |
| Rosacea | 32 |
| Perioral Dermatitis | 17 |

### Psoriasis / papulosquamous

| Raw label | Primary case count |
|---|---:|
| Psoriasis | 77 |
| Pityriasis rosea | 37 |
| Lichen planus/lichenoid eruption | 27 |
| Pityriasis rubra pilaris | 1 |

### Lesion — dermoscopic review recommended

SCIN contributes very few examples to this class.

| Raw label | Primary/top weighted cases | Mentioned / any weighted cases |
|---|---:|---:|
| Melanoma | 2 | 7 |
| Basal Cell Carcinoma | 16 | 21 |
| SCC/SCCIS | 21 | 37 |
| Melanocytic Nevus | 8 | 12 |
| Atypical Nevus | 2 | 5 |
| Epidermal nevus | 2 | 5 |
| Nevus anemicus | 0 | 1 |
| Vascular nevus of skin | 1 | 1 |
| Actinic Keratosis | 15 | 22 |

Summary:

- SCIN primary weighted cases, including actinic keratosis: 67
- SCIN any weighted/mentioned cases, including actinic keratosis: 111

### Tinea / fungal-like

Excluded from first baseline.

| Raw label | Primary case count |
|---|---:|
| Tinea | 66 |
| Tinea Versicolor | 35 |
| Intertrigo | 10 |
| Onychomycosis | 5 |

### Viral / bacterial infection

Excluded from first baseline.

| Raw label | Primary case count |
|---|---:|
| Herpes Simplex | 71 |
| Herpes Zoster | 60 |
| Impetigo | 49 |
| Molluscum Contagiosum | 29 |
| Viral Exanthem | 15 |
| Cellulitis | 14 |
| Skin infection | 4 |
| Verruca vulgaris | 2 |

---

## Fitzpatrick17k raw-label contribution by group

### Eczema / dermatitis

| Raw label | Row count |
|---|---:|
| allergic contact dermatitis | 430 |
| eczema | 204 |
| seborrheic dermatitis | 126 |
| dyshidrotic eczema | 83 |

### Urticaria / allergic reaction

| Raw label | Row count |
|---|---:|
| drug eruption | 200 |
| urticaria | 151 |

### Folliculitis / acne-like

| Raw label | Row count |
|---|---:|
| folliculitis | 342 |
| acne vulgaris | 335 |
| acne | 183 |
| rosacea | 102 |
| perioral dermatitis | 61 |

### Psoriasis / papulosquamous

| Raw label | Row count |
|---|---:|
| psoriasis | 653 |
| lichen planus | 491 |
| pityriasis rubra pilaris | 278 |
| pityriasis rosea | 193 |

### Lesion — dermoscopic review recommended

| Raw label | Row count |
|---|---:|
| melanoma | 261 |
| superficial spreading melanoma ssm | 118 |
| malignant melanoma | 111 |
| lentigo maligna | 83 |
| basal cell carcinoma | 468 |
| basal cell carcinoma morpheiform | 62 |
| solid cystic basal cell carcinoma | 66 |
| squamous cell carcinoma | 581 |
| nevocytic nevus | 86 |
| congenital nevus | 68 |
| halo nevus | 82 |
| becker nevus | 63 |
| epidermal nevus | 91 |
| nevus sebaceous of jadassohn | 95 |
| actinic keratosis | 175 |

Summary:

- Fitzpatrick17k lesion-routing rows, including actinic keratosis: 2,410

### Tinea / fungal-like

Excluded from first baseline.

No direct mapped Fitzpatrick17k labels found in the inspected metadata.

### Viral / bacterial infection

Excluded from first baseline.

No direct mapped Fitzpatrick17k labels found in the inspected metadata.

---

## Interpretation

## Strongest candidates

The approved 5-class taxonomy is feasible by count:

1. Eczema / dermatitis
2. Urticaria / allergic reaction
3. Folliculitis / acne-like
4. Psoriasis / papulosquamous
5. Lesion — dermoscopic review recommended

The lesion-routing class has enough data only because of Fitzpatrick17k.

## Weak candidates

Tinea / fungal-like is too small with the current mapping:

- SCIN primary cases: 116
- SCIN primary images: 243
- Fitzpatrick17k rows: 0

Viral / bacterial infection is also weak and heterogeneous:

- SCIN primary cases: 217
- SCIN primary images: 433
- Fitzpatrick17k rows: 0

These are excluded from the first baseline.

---

## Key risk: source bias

The lesion-routing class is mostly Fitzpatrick17k, while some other clinical classes are SCIN-heavy or mixed.

This creates a source-bias risk:

> The model may learn dataset/image-source style instead of clinical morphology.

Mitigation:

- preserve `source_dataset` in processed CSVs;
- evaluate SCIN and Fitzpatrick17k performance separately;
- use balanced sampling and/or class weighting;
- do not report only combined accuracy;
- label the lesion class as routing, not diagnosis.

---

## Final recommendation

Proceed with the **5-class clinical-image baseline taxonomy**:

1. Eczema / dermatitis
2. Urticaria / allergic reaction
3. Folliculitis / acne-like
4. Psoriasis / papulosquamous
5. Lesion — dermoscopic review recommended

Do not include Tinea / fungal-like or Viral / bacterial infection in the first baseline.

Recommended next step:

- Build clinical-image dataset with these 5 classes using SCIN + Fitzpatrick17k where image paths are available.

---

## Training implications

If combining SCIN + Fitzpatrick17k:

- Evaluate source-specific performance.
- Do not report only combined accuracy.
- Report SCIN test performance and Fitzpatrick17k test performance separately.
- Validate Fitzpatrick17k local image path mapping before training.
- Split SCIN by `case_id`.
- Document Fitzpatrick17k split limitations because no clear case/patient/lesion ID exists.

---

## Decision

Approved direction:

- Use 5-class taxonomy with lesion-routing class.
- Exclude Tinea / fungal-like and Viral / bacterial infection from first baseline.
- Use lesion-routing output to trigger dermoscopic image upload.
- Do not call the lesion-routing class `Cancer`.
- Do not claim cancer detection from clinical-photo model.
