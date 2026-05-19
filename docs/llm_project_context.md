# Revela LLM Project Context

This file is the current compressed project context for all team members and their LLM tools. Paste this file into any LLM before asking it to work on Revela tasks.

Update this file after any major change in product scope, dataset strategy, model strategy, evaluation results, or safety posture.

---

## Product summary

Revela is an educational dermatology AI training aid for dermatology residents, trainees, and practitioners. It is not a diagnostic product and must not be presented as clinically validated.

The product helps users practice structured dermatology image review by showing top differential suggestions, confidence/uncertainty, and educational explanations.

---

## Current MVP scope

Current MVP focuses on a dermoscopic cancer-risk training module.

Revised product logic:

1. User uploads a dermoscopic lesion image.
2. Model predicts cancer-risk oriented class output.
3. App shows class prediction, cancer-risk interpretation, confidence, uncertainty, and educational safety warning.
4. Explanation / quiz / LLM layer may be added later.

Current MVP is not a general skin-disease classifier and not a patient-facing diagnostic system.

---

## Current production dermoscopic CNN (BCN+MNH — D4.5/#141, evaluated D4.6/#142)

The production dermoscopic cancer-risk model is now trained on **BCN20000 + MNH (filtered)** — see DEC-010 in `docs/decision_log.md`.

- Training data: BCN20000 training split (12,352 rows) + MNH filtered (12,500 rows, post-BCN dedup) = merged pool 24,852 → lesion-grouped split into **21,233 train / 3,619 val**.
- Evaluation benchmark: frozen BCN20000 test set, 2,659 rows, md5 `a67861586e00812aadf46f2bdb4bc01b` (unchanged from #120).
- Model: EfficientNet-B0, ImageNet pretrained, 224×224, AdamW lr=3e-4 wd=0.01, 10 epochs, inverse-frequency class weights.
- Checkpoint: `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth` (PyTorch; mirror `models/bcn_mnh_cancer_risk_cnn_epoch6.pth`). Saved by `val_macro_f1` (max) — same selection rule as the BCN-only baseline.
- Best epoch: 6 / 10. Test melanoma recall: 61.36% (BCN-only baseline 57.87%, delta +3.50 pp).

Full augmentation decisions: `docs/decision_log.md` D4 (DEC-010).
Taxonomy mapping for MNH: `docs/mnh_taxonomy_mapping.md`.

---

## Previous baselines (kept for comparison)

### BCN-only cancer-risk CNN (D3.4/#119, evaluated D3.5/#120)

4-class cancer-risk CNN trained on BCN20000 only. Kept on disk as the comparison baseline at `models/bcn20000_cancer_risk_effnet_b0/best_model.pth`. Test melanoma recall 57.87% on the same frozen test set; superseded on melanoma recall (+3.50 pp), NMSC recall (+2.89 pp), and cancer recall (+1.79 pp) by the BCN+MNH model above.

### CNN v1 (3-class, archived)

CNN v1 is the original 3-class baseline (Melanoma / Benign nevus / Other lesion), now archived.

Dataset: BCN20000  
Image type: Dermoscopic lesion images  
Model: EfficientNet-B0  
Training approach: Transfer learning  
Old classes:

- Melanoma
- Benign nevus
- Other lesion

The model was trained for 3 epochs and evaluated on a held-out lesion-level test split. Replaced by the 4-class cancer-risk taxonomy (DEC-008) and superseded by the BCN+MNH model above.

---

## Current CNN v1 metrics

Test set size: 2,659 images

Main metrics:

- Top-1 accuracy: 76.16%
- Macro-F1: 0.7443
- Balanced accuracy: 75.29%
- Top-3 accuracy: 100%, but this is not meaningful because the model has exactly 3 classes

Class-wise metrics:

- Melanoma: precision 57.51%, recall 69.58%, F1 62.97%
- Benign nevus: precision 76.56%, recall 80.00%, F1 78.24%
- Other lesion: precision 88.79%, recall 76.30%, F1 82.07%

Important limitation:

The old `Other lesion` class contains non-melanoma cancer and pre-cancer / indeterminate-risk cases. Therefore, this old taxonomy is insufficient for the revised product goal.

---

## Revised dermoscopic model direction

The next dermoscopic model should be retrained around cancer-risk classification.

BCN20000 contains clearly malignant/cancer cases:

- Melanoma, NOS: 4,003 rows
- Melanoma metastasis: 633 rows
- Basal cell carcinoma: 3,676 rows
- Squamous cell carcinoma, NOS: 559 rows

Total clearly malignant/cancer rows: 8,871.

BCN20000 also contains:

- Solar or actinic keratosis: 1,088 rows

This must be handled explicitly as pre-cancer / indeterminate risk / separate class / excluded, depending on the final taxonomy decision.

Confirmed taxonomy — approved in #117, finalized 2026-05-12:

4-class dermoscopic cancer-risk taxonomy:

1. Melanoma — 4,636 rows
2. Non-melanoma skin cancer — 4,235 rows
3. Benign nevus — 5,647 rows
4. Other non-cancer / indeterminate lesion — 3,121 rows

Unknown / missing diagnosis_3: 1,307 rows (excluded from training)
Usable training rows: 17,639

Wording rule: the 4th class must be called `Other non-cancer / indeterminate lesion`. Do not use `Other benign lesion` or `Safe lesion`. This class includes actinic keratosis (pre-malignant) alongside other benign lesions.

---

## Important current decisions

1. Revela is an educational training aid, not a diagnostic product.
2. BCN20000 + MNH (filtered) is the production dermoscopic training set (DEC-010, D4 / #137–#143). Earlier BCN-only model is kept as the comparison baseline.
3. The old 3-class CNN v1 is archived.
4. Dermoscopic model objective is cancer-risk classification (4-class — DEC-008).
5. Do not mix dermoscopic and clinical-photo datasets in the dermoscopic model.
6. SCIN and Fitzpatrick17k are candidates for future clinical-photo model planning, not dermoscopic retraining.
7. Future clinical-image model v2 should be explored as melanoma-risk triage, not broad skin-disease classification.
8. For melanoma/cancer-related models, prioritize sensitivity / false-negative reduction, but never claim all melanoma or all cancer cases can be detected.
9. Evaluation should include cancer/malignant recall, false-negative rate, melanoma recall, macro-F1, balanced accuracy, class-wise metrics, and confusion matrix.
10. Top-3 accuracy should not be used as a success claim for old CNN v1 because it is trivial with 3 classes.

---

## Clinical-image model v2 direction

Clinical model v2 is future work.

Current direction:

- Clinical-photo melanoma-risk triage module.
- It should flag melanoma-like concern or uncertainty from clinical images.
- If concern or uncertainty is high, the product should ask the practitioner to upload a dermoscopic image for second-step review.

Potential workflow:

1. Practitioner uploads clinical image.
2. Clinical-image model estimates melanoma-risk signal.
3. If high-risk or uncertain, system asks for dermoscopic image.
4. Dermoscopic model provides a more specialized lesion/cancer-risk review.
5. App shows educational explanation and safety warning.

Do not call this diagnosis. Use language like:

- Suspicious / melanoma-like features detected
- High-priority review recommended
- Upload dermoscopic image for additional educational review

---

## Dataset notes

### BCN20000

Used for dermoscopic model development.

Strengths:

- Dermoscopic images.
- Contains melanoma, non-melanoma skin cancer, nevus, and other lesion categories.
- Supports lesion-level split.

Limitations:

- Dermoscopic-only.
- No reliable skin-tone metadata.
- Old 3-class mapping hid BCC/SCC inside `Other lesion`.
- Not suitable for clinical-photo inflammatory/rash classification.

### SCIN

Candidate for future clinical-photo work.

Strengths:

- Clinical/photo-style images.
- Strong metadata compared with Fitzpatrick17k.
- Includes body site, symptoms/context, demographic fields, Fitzpatrick/Monk-related metadata.
- Better for inflammatory/rash-like condition exploration.

Limitations:

- Very few melanoma/nevus cases.
- Not suitable as main melanoma/nevus clinical-image training dataset by itself.

### Fitzpatrick17k

Candidate for future clinical-photo work.

Strengths:

- Clinical/web-style images.
- Contains melanoma and nevus / melanocytic labels.
- Contains Fitzpatrick-related metadata.

Limitations:

- No clear case_id, patient_id, or lesion_id.
- Label quality and diagnosis confirmation may vary.
- Image availability/URL access must be validated.
- Weaker metadata than SCIN.

### DDI

Potentially useful but current access is uncertain. Do not rely on DDI unless access is confirmed.

---

## Do-not-do rules

Do not:

- Claim diagnosis.
- Claim clinical validation.
- Claim the model detects all melanoma or all cancer cases.
- Claim fairness or skin-tone robustness without slice evaluation.
- Mix SCIN/Fitzpatrick17k clinical photos into the dermoscopic CNN.
- Present the dermoscopic model as working on normal phone/clinical skin photos.
- Present top-3 accuracy as meaningful for the old 3-class CNN v1.
- Treat `Other lesion` as benign/safe.
- Add treatment advice.
- Let an LLM invent medical certainty from CNN output.

---

## Current open work

## Completed

- Redefined dermoscopic CNN target as cancer-risk classification — DEC-008, #116.
- Created cancer-risk label mapping for BCN20000 — #117.
- Rebuilt BCN20000 processed splits for 4-class taxonomy — #118.
- Trained BCN-only cancer-risk CNN — #119.
- Evaluated BCN-only cancer-risk CNN — #120.
- **MNH augmentation track (D4) — DEC-010, #137–#143:** downloaded MNH (#137), filtered BCN overlaps (#138), mapped to cancer-risk taxonomy (#139, DEC-009), merged + lesion-grouped split (#140), retrained CNN (#141), evaluated on frozen BCN test (#142, +3.50 pp melanoma recall), closed docs (#143).

## High-priority / near-term

- Update inference and app schema for the BCN+MNH model — checkpoint path swap, otherwise drop-in (#123 / D3.7).
- Write revised model evaluation report.
- Write revised model card.
- Update presentation/demo narrative.

Model improvement / research:

- Assess whether supplemental dermoscopic datasets should be added.
- Evaluate whether HAM10000 / ISIC can supplement BCN20000.
- Plan clinical-image model v2.
- Prepare benchmark plan vs ChatGPT / Claude.

Future:

- Clinical-photo melanoma-risk triage model.
- LLM explanation layer.
- Skin-tone slice evaluation if metadata and sample size allow.
- Improved cancer/melanoma recall through longer training, augmentation, focal loss, or data expansion.

---

## How team members should use this file

Before starting work:

1. Pull latest repository state.
2. Read this file.
3. Read assigned GitHub issue.
4. Paste this file plus the issue into the LLM being used.
5. Ask the LLM to work only within the current project decisions.

After finishing work:

1. Commit code/docs if relevant.
2. Update the GitHub issue.
3. Update this file if project direction changed.
4. Add a decision to `docs/decision_log.md` if a new major decision was made.

---

## Current concise status for stakeholders

Revela has a working first CNN baseline for dermoscopic lesion training, but the team discovered that the old `Other lesion` class contains non-melanoma skin cancers such as basal cell carcinoma and squamous cell carcinoma. Therefore, the baseline model is not aligned with the revised product goal. The next dermoscopic model iteration should be retrained around cancer-risk classification, while keeping the product educational and non-diagnostic.
