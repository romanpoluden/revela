# Clinical Model v2 Grouped Taxonomy

## Purpose

This document defines the agreed grouped-label taxonomy for the future **clinical-image model v2**.

The clinical-image model is separate from the dermoscopic cancer-risk model.

The clinical-image model should support common clinical skin-condition learning from clinical/photo-style images. It should also include a routing class for lesion-type cases where dermoscopic review is more appropriate.

Cancer-risk / lesion-risk classification is handled by the dermoscopic model.

---

## Product direction

Clinical model v2 should be positioned as:

> A clinical skin-condition learning module for common clinical-photo presentations, with a lesion-routing output that recommends dermoscopic review when the image appears lesion-like.

It should not be positioned as:

- a diagnostic model;
- a clinical cancer classifier;
- a melanoma detector;
- an all-disease dermatology classifier;
- a replacement for clinician judgment.

Recommended product routing:

1. User chooses image type / module, or the app routes based on the model output.
2. Clinical skin photo → clinical skin-condition learning module.
3. If the clinical model predicts `Lesion — dermoscopic review recommended`, the app asks the user to upload a dermoscopic image.
4. Dermoscopic lesion image → dermoscopic cancer-risk learning module.

Recommended user-facing wording for the lesion-routing class:

> This appears to be a lesion-type case where dermoscopic review is more appropriate. Upload a dermoscopic image for additional educational review.

Avoid wording such as:

- Cancer detected
- This is melanoma
- Diagnosis confirmed

---

## Dataset strategy

### Primary dataset

Use **SCIN** as the primary dataset for common clinical inflammatory/rash-style classes.

Reasons:

- has `case_id`;
- has clinical/photo-style images;
- has image paths;
- has dermatologist and weighted condition labels;
- has useful metadata such as body location, symptoms/context, Fitzpatrick/Monk-related fields;
- supports safer split by case.

### Supplemental dataset

Use **Fitzpatrick17k** as supplementation for overlapping common clinical labels and for the lesion-routing class, because all Fitzpatrick17k images have now been downloaded locally.

Reasons for caution:

- no clear `case_id`, `patient_id`, or `lesion_id`;
- label quality and confirmation method are weaker;
- source-bias risk is high if mixed blindly with SCIN.

If SCIN and Fitzpatrick17k are combined, evaluate source-specific performance:

- SCIN test performance;
- Fitzpatrick17k test performance;
- combined test performance.

Do not report only combined accuracy.

---

## Agreed MVP taxonomy

Use a **5-class clinical-image taxonomy**:

1. Eczema / dermatitis
2. Urticaria / allergic reaction
3. Folliculitis / acne-like
4. Psoriasis / papulosquamous
5. Lesion — dermoscopic review recommended

The app can still show:

- `Unclear / outside current clinical module`

but this should be implemented through confidence/uncertainty thresholds, not trained as a separate garbage-bucket class at first.

---

## Excluded first-baseline classes

The following previously considered groups are excluded from the first baseline because the counts are weak or the groups are heterogeneous:

- Tinea / fungal-like
- Viral / bacterial infection

They may be reconsidered later if more compatible data is found.

---

## Group definitions and raw labels

## 1. Eczema / dermatitis

### SCIN labels to map

- Eczema
- Allergic Contact Dermatitis
- Irritant Contact Dermatitis
- Acute dermatitis, NOS
- Atopic Dermatitis
- Dyshidrotic Eczema
- Seborrheic Dermatitis
- Nummular eczema

### Fitzpatrick17k labels to map

- eczema
- allergic contact dermatitis
- seborrheic dermatitis
- dyshidrotic eczema
- atopic dermatitis
- nummular eczema

### Notes

This is expected to be a large and stable class. It may need downsampling or class balancing if it dominates the dataset.

---

## 2. Urticaria / allergic reaction

### SCIN labels to map

- Urticaria
- Drug Rash
- Hypersensitivity
- Morbilliform Drug Eruption
- Allergic reaction

### Fitzpatrick17k labels to map

- urticaria
- urticaria pigmentosa
- drug eruption
- morbilliform drug eruption
- hypersensitivity reaction

### Notes

This class may overlap visually with dermatitis and viral exanthem. Keep wording educational and document the limitation.

---

## 3. Folliculitis / acne-like

### SCIN labels to map

- Folliculitis
- Acne
- Acneiform eruption
- Rosacea
- Perioral dermatitis

### Fitzpatrick17k labels to map

- folliculitis
- acne vulgaris
- acne
- rosacea
- perioral dermatitis

### Notes

Acne and folliculitis are not the same diagnosis, but grouping is acceptable for an MVP because both represent follicular/acneiform clinical presentations.

---

## 4. Psoriasis / papulosquamous

### SCIN labels to map

- Psoriasis
- Pityriasis rosea
- Lichen planus/lichenoid eruption
- Papulosquamous eruption

### Fitzpatrick17k labels to map

- psoriasis
- pityriasis rosea
- lichen planus
- lichen planus/lichenoid eruption

### Notes

If the grouped class becomes too noisy, a later version can narrow it to psoriasis only. For MVP, grouping improves sample size.

---

## 5. Lesion — dermoscopic review recommended

### Purpose

This is a routing class, not a diagnosis class.

Its role is to identify clinical-photo cases that appear lesion-like and should be reviewed through the dermoscopic module rather than classified as a common inflammatory/rash-style condition.

### SCIN labels to map

- Melanoma
- Basal Cell Carcinoma
- SCC/SCCIS
- Melanocytic Nevus
- Atypical Nevus
- Epidermal nevus
- Nevus anemicus
- Vascular nevus of skin
- Actinic Keratosis

### Fitzpatrick17k labels to map

- melanoma
- superficial spreading melanoma ssm
- malignant melanoma
- lentigo maligna
- basal cell carcinoma
- basal cell carcinoma morpheiform
- solid cystic basal cell carcinoma
- squamous cell carcinoma
- nevocytic nevus
- congenital nevus
- halo nevus
- becker nevus
- epidermal nevus
- nevus sebaceous of jadassohn
- actinic keratosis

### Notes

This class intentionally combines malignant, pre-cancer/indeterminate, and benign lesion labels. That is acceptable because the purpose is routing to dermoscopic review, not diagnosis.

Do not call this class `Cancer`.

Do not use this output to claim cancer detection.

---

## Training strategy

Use **single-label classification** for MVP.

Recommended label source:

- SCIN: use `weighted_skin_condition_label` as the primary label.
- Fitzpatrick17k: use `label` after local image path availability is confirmed.

Do not train multi-label for MVP.

Reason:

- SCIN dermatologist labels may represent differential opinions, not multiple confirmed simultaneous conditions.
- Weighted label gives a cleaner single target.
- Single-label CNN training is simpler, faster, and easier to evaluate.

---

## Handling multiple images per case

SCIN can contain multiple images per case.

Important rule:

> Never split images from the same `case_id` across train, validation, and test.

Correct:

- case 123 image 1 → train
- case 123 image 2 → train
- case 123 image 3 → train

Incorrect:

- case 123 image 1 → train
- case 123 image 2 → validation
- case 123 image 3 → test

---

## Handling unclear / outside-module cases

Do not train `Other / unclear` as a class in the first baseline unless the team defines a carefully sampled negative set.

Instead:

- train on approved known groups;
- use confidence/uncertainty thresholding;
- output `Unclear / outside current clinical module` when confidence is low.

---

## Combining SCIN and Fitzpatrick17k

Recommended sequence:

1. Build mapping for both datasets.
2. Validate local image paths for both datasets.
3. Build combined dataset with source labels preserved.
4. Balance classes and source contribution where possible.
5. Split SCIN by `case_id`.
6. Split Fitzpatrick17k carefully and document lack of patient/case IDs.
7. Evaluate separately by source:
   - SCIN test performance;
   - Fitzpatrick17k test performance;
   - combined test performance.

Do not report only combined accuracy if datasets are mixed.

---

## Balance target

Recommended minimum class size targets:

- 500+ images per class: decent for MVP baseline.
- 300–500 images per class: possible but weaker.
- Under 300 images per class: risky unless supplemented.

If one class dominates, use one or more of:

- downsampling;
- class weighting;
- weighted sampler;
- source-aware sampling if datasets are combined.

---

## Next tasks

Related tasks:

- V2.4 — Count grouped clinical labels across SCIN and Fitzpatrick17k
- V2.5 — Build clinical-image dataset with 5 approved classes
- V2.6 — Train clinical-image CNN baseline
- V2.7 — Evaluate clinical-image CNN baseline, including source-specific performance

---

## Decision

Approved for planning:

- Use the 5-class clinical-image taxonomy.
- Add `Lesion — dermoscopic review recommended` as the 5th class.
- Drop `Tinea / fungal-like` and `Viral / bacterial infection` from the first baseline.
- Use SCIN + Fitzpatrick17k where labels and image paths are available.
- Preserve source labels and evaluate source-specific performance.
- Use the dermoscopic model for cancer-risk classification after lesion routing.
