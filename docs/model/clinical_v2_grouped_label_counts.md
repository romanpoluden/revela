# Clinical Model v2 Grouped Label Counts

## Purpose

This document supports issue #124: **V2.4 — Count grouped clinical labels across SCIN and Fitzpatrick17k**.

The goal is to check how many examples fall into the approved grouped taxonomy for the future clinical-image model v2.

Clinical model v2 is separate from the dermoscopic cancer-risk model. Cancer-risk labels are excluded from this clinical module.

---

## Approved grouped taxonomy

Approved initial taxonomy:

1. Eczema / dermatitis
2. Urticaria / allergic reaction
3. Folliculitis / acne-like
4. Psoriasis / papulosquamous
5. Tinea / fungal-like

Optional 6th class:

6. Viral / bacterial infection

The app may show `Unclear / outside current clinical module`, but this should be implemented through confidence/uncertainty thresholds, not trained as a garbage-bucket class in the first baseline.

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

Caution:

- Fitzpatrick17k image availability still needs validation.
- Fitzpatrick17k lacks clear `case_id`, `patient_id`, or `lesion_id`.
- These counts are potential supplemental counts, not confirmed final training counts.

---

## Grouped count summary

| Target group | SCIN primary cases | SCIN primary images | SCIN any weighted cases | Fitzpatrick17k rows | Combined potential |
|---|---:|---:|---:|---:|---:|
| Eczema / dermatitis | 989 | 2,157 | 1,760 | 843 | 1,832 |
| Urticaria / allergic reaction | 235 | 492 | 525 | 351 | 586 |
| Folliculitis / acne-like | 226 | 478 | 374 | 1,023 | 1,249 |
| Psoriasis / papulosquamous | 142 | 304 | 427 | 1,615 | 1,757 |
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

### Tinea / fungal-like

| Raw label | Primary case count |
|---|---:|
| Tinea | 66 |
| Tinea Versicolor | 35 |
| Intertrigo | 10 |
| Onychomycosis | 5 |

### Viral / bacterial infection

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

### Tinea / fungal-like

No direct mapped Fitzpatrick17k labels found in the inspected metadata.

### Viral / bacterial infection

No direct mapped Fitzpatrick17k labels found in the inspected metadata.

---

## Interpretation

## Strongest candidates

The most feasible groups for a combined SCIN + Fitzpatrick17k model are:

1. Eczema / dermatitis
2. Folliculitis / acne-like
3. Psoriasis / papulosquamous
4. Urticaria / allergic reaction

These groups have potential counts above or near the practical MVP threshold after combining datasets.

## Weak candidates

Tinea / fungal-like is too small with the current mapping:

- SCIN primary cases: 116
- SCIN primary images: 243
- Fitzpatrick17k rows: 0

This is risky for a CNN baseline unless more compatible labels/images are added.

Viral / bacterial infection is optional but also weak:

- SCIN primary cases: 217
- SCIN primary images: 433
- Fitzpatrick17k rows: 0

It is also visually heterogeneous, which may reduce model performance.

---

## Recommendation

For the first clinical-image CNN baseline, use a **4-class taxonomy**:

1. Eczema / dermatitis
2. Urticaria / allergic reaction
3. Folliculitis / acne-like
4. Psoriasis / papulosquamous

Do not include Tinea / fungal-like in the first baseline unless the team accepts a weak class or finds additional data.

Do not include Viral / bacterial infection in the first baseline unless the team explicitly wants a broader but noisier class.

Recommended next step:

- Build a SCIN-only baseline dataset with the 4 strongest groups.
- Keep Fitzpatrick17k as optional supplementation after image availability validation.

---

## Training implications

If using SCIN-only first:

- Eczema / dermatitis is strong.
- Urticaria, Folliculitis/acne-like, and Psoriasis/papulosquamous are smaller but usable by image count.
- Consider class weighting or weighted sampling.
- Split by `case_id`.
- Keep all images from the same case in the same split.

If combining SCIN + Fitzpatrick17k:

- Evaluate source-specific performance.
- Do not report only combined accuracy.
- Report SCIN test performance and Fitzpatrick17k test performance separately.
- Validate Fitzpatrick17k image URL availability before training.

---

## Decision needed

The team should decide between:

### Option A — safer first baseline

4 classes:

- Eczema / dermatitis
- Urticaria / allergic reaction
- Folliculitis / acne-like
- Psoriasis / papulosquamous

### Option B — broader but weaker baseline

5 classes:

- Eczema / dermatitis
- Urticaria / allergic reaction
- Folliculitis / acne-like
- Psoriasis / papulosquamous
- Viral / bacterial infection

### Option C — original 5-class proposal

5 classes including Tinea / fungal-like.

This is not recommended based on current counts.

Current recommendation: **Option A**.
