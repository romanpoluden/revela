# Clinical Model v2 Grouped Taxonomy

## Purpose

This document defines the agreed grouped-label taxonomy for the future **clinical-image model v2**.

The clinical-image model is separate from the dermoscopic cancer-risk model.

The clinical-image model should support common clinical skin-condition learning from clinical/photo-style images. It should not be responsible for cancer-risk detection.

Cancer-risk / lesion-risk learning is handled by the dermoscopic model.

---

## Product direction

Clinical model v2 should be positioned as:

> A clinical skin-condition learning module for common clinical-photo presentations.

It should not be positioned as:

- a diagnostic model;
- a cancer-risk model;
- a melanoma detector;
- an all-disease dermatology classifier;
- a replacement for clinician judgment.

Recommended product routing:

1. User chooses image type / module.
2. Clinical skin photo → clinical skin-condition learning module.
3. Dermoscopic lesion image → dermoscopic cancer-risk learning module.

---

## Dataset strategy

### Primary dataset

Use **SCIN** as the primary dataset for the first clinical-image baseline.

Reasons:

- has `case_id`;
- has clinical/photo-style images;
- has image paths;
- has dermatologist and weighted condition labels;
- has useful metadata such as body location, symptoms/context, Fitzpatrick/Monk-related fields;
- supports safer split by case.

### Supplemental dataset

Use **Fitzpatrick17k** only as optional supplementation after SCIN-only baseline and feasibility checks.

Reasons for caution:

- no clear `case_id`, `patient_id`, or `lesion_id`;
- URL/image availability must be validated;
- label quality and confirmation method are weaker;
- source-bias risk is high if mixed blindly with SCIN.

### Do not include cancer labels in clinical model v2

Cancer/lesion-risk labels should be excluded from clinical model v2 and handled by the dermoscopic model.

Examples to exclude from clinical model v2:

- Melanoma
- Nevus / melanocytic nevus
- Basal cell carcinoma
- Squamous cell carcinoma
- Actinic keratosis
- Seborrheic keratosis
- Solar lentigo

These labels may be useful for other research, but they are not part of the clinical-photo MVP module.

---

## Agreed MVP taxonomy

Start with a **5-class clinical-image taxonomy**:

1. Eczema / dermatitis
2. Urticaria / allergic reaction
3. Folliculitis / acne-like
4. Psoriasis / papulosquamous
5. Tinea / fungal-like

The app can still show:

- `Unclear / outside current clinical module`

but this should be implemented through confidence/uncertainty thresholds, not trained as a separate garbage-bucket class at first.

---

## Optional 6th class

Optional after count and image-quality review:

6. Viral / bacterial infection

This class may be useful, but it is broader and more visually heterogeneous. Add it only if grouped counts and image quality are acceptable.

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

This is expected to be the largest and most stable class. It may need downsampling or class balancing if it dominates the dataset.

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

## 5. Tinea / fungal-like

### SCIN labels to map

- Tinea
- Tinea corporis
- Tinea pedis
- Tinea cruris
- Onychomycosis
- Candidiasis
- Intertrigo

### Fitzpatrick17k labels to map

- tinea
- tinea corporis
- tinea pedis
- tinea cruris
- onychomycosis
- candidiasis
- intertrigo

### Notes

If many images are nail-only, consider excluding nail-only images or documenting that the model includes some nail/fungal presentations.

---

## Optional 6. Viral / bacterial infection

### SCIN labels to map

- Herpes Zoster
- Herpes Simplex
- Viral Exanthem
- Impetigo
- Cellulitis
- Bacterial infection
- Molluscum contagiosum
- Warts
- Verruca

### Fitzpatrick17k labels to map

- herpes zoster
- herpes simplex
- viral exanthem
- impetigo
- molluscum contagiosum
- warts
- verruca vulgaris
- cellulitis

### Notes

This class is clinically useful but broad. Add only after grouped label counts and image-quality checks.

---

## Training strategy

Use **single-label classification** for MVP.

Recommended label source:

- SCIN: use `weighted_skin_condition_label` as the primary label.
- Fitzpatrick17k: use `label` only after image availability and label mapping are validated.

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

1. Build SCIN-only baseline first.
2. Evaluate SCIN-only performance.
3. Validate Fitzpatrick17k image availability.
4. Map Fitzpatrick17k labels to the same taxonomy.
5. Compare class balance before and after adding Fitzpatrick17k.
6. If combined, evaluate separately by source:
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

- V2.4 — Define grouped clinical-image taxonomy
- V2.5 — Count grouped labels across SCIN and Fitzpatrick17k
- V2.6 — Build SCIN-only clinical baseline dataset
- V2.7 — Evaluate whether Fitzpatrick17k supplementation is worth adding

---

## Decision

Approved for planning:

- Start with the 5-class clinical-image taxonomy.
- Treat viral / bacterial infection as optional 6th class after count check.
- Use SCIN as primary dataset.
- Use Fitzpatrick17k only as optional supplementation.
- Keep cancer-risk labels out of the clinical model.
- Use the dermoscopic model for cancer-risk learning.
