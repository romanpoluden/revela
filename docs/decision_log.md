# Revela Decision Log

This file is the permanent source of truth for major project decisions. It should be updated whenever the team changes product scope, dataset strategy, model strategy, evaluation approach, safety posture, or demo direction.

Use this file for decisions that affect more than one task or more than one team member. Do not use it for daily implementation notes.

---

## Decision format

Each decision should include:

- **Decision ID**
- **Date**
- **Status**: Proposed / Accepted / Replaced / Rejected
- **Owner**
- **Linked issues**
- **Decision**
- **Context**
- **Options considered**
- **Rationale**
- **Consequences**
- **Review date**

---

## DEC-001 — Position Revela as an educational training aid

**Date:** 2026-05-08  
**Status:** Accepted  
**Owner:** Roman  
**Category:** Product / Safety  
**Linked issues:** #2, #3, #111

### Decision

Revela is positioned as an educational dermatology AI training aid, not as a diagnostic product and not as a clinical decision-maker.

### Context

The project involves AI-assisted interpretation of skin-condition images. Because this is medically sensitive, the product must avoid diagnosis claims and must frame all outputs as educational support for trainees/practitioners.

### Options considered

1. Diagnostic assistant for skin disease.
2. Broad skin-condition classifier.
3. Educational training aid for structured learning and review.

### Rationale

The educational framing is safer, more credible for a capstone MVP, and better aligned with the current model maturity and dataset limitations.

### Consequences

- All outputs must include safety and educational-use disclaimers.
- The product must not provide treatment advice.
- The product must not claim clinical validation.
- The product must not claim diagnostic certainty.

### Review date

Before final demo deck.

---

## DEC-002 — Use BCN20000 for CNN v1

**Date:** 2026-05-08  
**Status:** Accepted  
**Owner:** Roman  
**Category:** Dataset / Model  
**Linked issues:** #26, #29, #38, #42

### Decision

CNN v1 uses BCN20000 as the primary dataset.

### Context

The team inspected multiple dataset options. BCN20000 is suitable for a dermoscopic lesion classifier and has usable metadata for lesion-level splitting and class mapping.

### Options considered

1. Use BCN20000 for dermoscopic lesion classification.
2. Use SCIN or Fitzpatrick17k for clinical-photo classification.
3. Combine dermoscopic and clinical-photo datasets into one model.

### Rationale

BCN20000 is the best current fit for a focused, trainable, reproducible CNN baseline. It supports the current dermoscopic lesion workflow better than broader clinical-photo datasets.

### Consequences

- CNN v1 is dermoscopic-only.
- SCIN and Fitzpatrick17k are not part of CNN v1 training.
- Clinical-photo model work is future work.

### Review date

After model improvement/error-analysis sprint.

---

## DEC-003 — Scope CNN v1 as a 3-class dermoscopic lesion classifier

**Date:** 2026-05-08  
**Status:** Accepted, now superseded for future retraining by DEC-008  
**Owner:** Roman  
**Category:** Model / Scope  
**Linked issues:** #26, #36, #38, #42, #116

### Decision

CNN v1 used three classes:

- Melanoma
- Benign nevus
- Other lesion

### Context

The original planning included a 4-class classifier with eczema/dermatitis. After dataset inspection, eczema/dermatitis was removed from CNN v1 because BCN20000 is a dermoscopic lesion dataset, not a clinical rash/inflammatory-condition dataset.

### Options considered

1. Keep original 4-class taxonomy.
2. Use a 3-class dermoscopic taxonomy.
3. Build a broad universal dermatology taxonomy.

### Rationale

A 3-class dermoscopic taxonomy was better aligned with the first available data and enabled a working baseline.

### Consequences

- CNN v1 is now treated as a baseline, not the final product model.
- Top-3 accuracy is not meaningful for CNN v1 because the model has exactly three classes.
- The old `Other lesion` class includes non-melanoma cancer cases, so it is insufficient for the updated product goal.
- Future retraining should use the cancer-risk taxonomy described in DEC-008.

### Review date

Superseded by DEC-008 for future dermoscopic model work.

---

## DEC-004 — Do not mix dermoscopic and clinical-photo datasets in CNN v1

**Date:** 2026-05-08  
**Status:** Accepted  
**Owner:** Roman  
**Category:** Dataset / Safety / Model  
**Linked issues:** #109, #110

### Decision

Do not mix dermoscopic datasets such as BCN20000 with clinical/web-style datasets such as SCIN or Fitzpatrick17k in CNN v1.

### Context

Dermoscopic images and clinical photos represent different visual domains. Mixing them without a clear design can cause domain shift and source bias, where the model learns dataset/image-style differences instead of clinically meaningful visual patterns.

### Options considered

1. Merge all available skin datasets into one larger model.
2. Keep dermoscopic and clinical-photo models separate.
3. Use a router or module selector in future versions.

### Rationale

Separate modules are more defensible technically and clearer for users. CNN v1 should remain focused on dermoscopic lesion classification.

### Consequences

- SCIN/Fitzpatrick17k are not used for CNN v1 training.
- Future clinical-photo functionality should be scoped as a separate module/model.
- Product UX should clearly indicate image type/module rather than silently switching class sets.

### Review date

When clinical-image model v2 dataset quality is confirmed.

---

## DEC-005 — Define clinical-image model v2 as future melanoma-risk triage research

**Date:** 2026-05-08  
**Status:** Accepted  
**Owner:** Roman  
**Category:** Product / Model / Safety  
**Linked issues:** #109

### Decision

Clinical-image model v2 should be explored as a future melanoma-risk triage module, not as a broad general skin-disease classifier.

### Context

From a practitioner perspective, missing acne/psoriasis is usually lower immediate risk than missing melanoma. Therefore, a future clinical-photo module should prioritize melanoma sensitivity and route suspicious/uncertain cases to dermoscopic follow-up.

### Options considered

1. Broad clinical skin-disease classifier.
2. Clinical melanoma-risk triage model.
3. Add clinical-photo images directly into CNN v1.

### Rationale

Melanoma-risk triage has a clearer safety-driven product purpose and aligns better with practitioner priorities. It also creates a coherent two-step workflow: clinical image triage followed by dermoscopic image review when needed.

### Consequences

- Future clinical-photo model classes are not final yet.
- The next step is label and metadata validation in SCIN/Fitzpatrick17k.
- The product should say “melanoma-like concern” or “high-priority review recommended,” not “this is melanoma.”

### Review date

After SCIN/Fitzpatrick17k image availability and label-count analysis.

---

## DEC-006 — Prioritize melanoma sensitivity but do not claim all melanoma can be detected

**Date:** 2026-05-08  
**Status:** Accepted  
**Owner:** Roman  
**Category:** Evaluation / Safety  
**Linked issues:** #109, #110, #116, #120

### Decision

For melanoma-related models, prioritize reducing melanoma false negatives. However, never claim that the model detects all melanoma cases.

### Context

Melanoma is high-risk. A practitioner-facing product should avoid missing suspicious melanoma-like cases. This implies a high-sensitivity triage posture, accepting more false positives if needed.

### Options considered

1. Optimize generic accuracy.
2. Optimize melanoma recall/sensitivity.
3. Claim full melanoma detection.

### Rationale

High melanoma sensitivity is clinically more relevant for triage than generic accuracy. Perfect melanoma detection is not realistic and would be unsafe to claim.

### Consequences

- Metrics should include melanoma recall/sensitivity, false negative rate, and class-wise F1.
- More false positives may be acceptable if clearly framed.
- Outputs should be educational and cautious.

### Review date

Before any public demo or stakeholder-facing claim.

---

## DEC-007 — Use responsible evaluation communication

**Date:** 2026-05-08  
**Status:** Accepted  
**Owner:** Roman  
**Category:** Evaluation / Communication  
**Linked issues:** #42, #43, #44, #45, #46, #111

### Decision

Report CNN v1 performance using top-1 accuracy, macro-F1, balanced accuracy, class-wise metrics, and confusion matrix. Do not emphasize top-3 accuracy because it is trivial for the current 3-class model.

### Context

CNN v1 outputs exactly three classes. Therefore, top-3 accuracy is always 100% as long as all three labels are returned.

### Current CNN v1 test results

- Test examples: 2,659
- Top-1 accuracy: 76.16%
- Top-3 accuracy: 100%, not meaningful for 3 classes
- Macro-F1: 0.7443
- Balanced accuracy: 75.29%

Class-wise results:

- Melanoma: precision 57.51%, recall 69.58%, F1 62.97%
- Benign nevus: precision 76.56%, recall 80.00%, F1 78.24%
- Other lesion: precision 88.79%, recall 76.30%, F1 82.07%

### Rationale

Macro-F1 and balanced accuracy are more appropriate than simple accuracy for class-imbalanced data. Class-wise melanoma recall is especially important for the project’s safety framing.

### Consequences

- Present top-3 accuracy only with an explanation that it is not meaningful yet.
- State clearly that melanoma is the weakest class and main improvement target.
- Do not claim clinical readiness.

### Review date

Before final presentation.

---

## DEC-008 — Redefine dermoscopic model as cancer-risk classification

**Date:** 2026-05-11  
**Status:** Accepted  
**Owner:** Roman  
**Category:** Product / Model / Safety  
**Linked issues:** #116, #117, #118, #119, #120, #123

### Decision

The next dermoscopic model iteration should be retrained around **cancer-risk classification**, not the old 3-class `Melanoma / Benign nevus / Other lesion` taxonomy.

The model should primarily help distinguish cancer/malignant dermoscopic cases from non-cancer cases, while still preserving useful educational categories such as melanoma, non-melanoma skin cancer, benign nevus, and other benign/non-cancer lesions.

### Context

BCN20000 contains clearly malignant/cancer cases:

- Melanoma, NOS: 4,003 rows
- Melanoma metastasis: 633 rows
- Basal cell carcinoma: 3,676 rows
- Squamous cell carcinoma, NOS: 559 rows

Total clearly malignant/cancer rows: 8,871.

BCN20000 also contains solar or actinic keratosis: 1,088 rows. This is clinically important as pre-cancer / indeterminate risk and must be handled explicitly.

The old `Other lesion` class contains basal cell carcinoma, squamous cell carcinoma, actinic keratosis, and benign lesions. Therefore, `Other lesion` is too broad and cannot be communicated as low-risk or non-cancer.

### Options considered

1. Keep old 3-class taxonomy.
2. Binary cancer vs non-cancer model.
3. 3-way risk model: cancer / pre-cancer-indeterminate / benign.
4. 4-class educational taxonomy: melanoma / non-melanoma skin cancer / benign nevus / other benign-non-cancer lesion.
5. 5-class taxonomy: melanoma / basal cell carcinoma / squamous cell carcinoma / benign nevus / other lesion.

### Rationale

The product goal is better served by cancer-risk classification. The old 3-class model is useful as a technical baseline, but the taxonomy is not aligned with practitioner value because many cancer cases are hidden inside `Other lesion`.

The preferred next candidate is either:

- 4-class educational taxonomy: melanoma / non-melanoma skin cancer / benign nevus / other benign-non-cancer lesion; or
- 3-way risk taxonomy: cancer / pre-cancer-indeterminate / benign.

Final taxonomy must be selected after #117 mapping analysis.

### Consequences

- The old CNN v1 is baseline-only.
- Inference and app schema must not be finalized around the old 3-class output.
- The model must be retrained after the new taxonomy is approved.
- Evaluation must include cancer/malignant recall and false-negative rate, not only top-1 accuracy and macro-F1.
- Actinic keratosis handling must be decided before retraining.
- Supplemental dermoscopic data may be needed after a new BCN20000 baseline is trained.

### Review date

After #117 taxonomy mapping and #120 evaluation of the retrained model.

### Update — 2026-05-12 — Taxonomy finalized

Final 4-class taxonomy approved in #117 (D3.2):

| Class | BCN20000 rows |
|---|---|
| Melanoma | 4,636 |
| Non-melanoma skin cancer | 4,235 |
| Benign nevus | 5,647 |
| Other non-cancer / indeterminate lesion | 3,121 |
| Excluded (unknown / missing diagnosis_3) | 1,307 |
| **Usable total** | **17,639** |

Wording rule: the 4th class must be called `Other non-cancer / indeterminate lesion`. Do not use `Other benign lesion`, `Safe lesion`, or omit the word `lesion`. This class includes actinic keratosis (pre-malignant) alongside other benign lesions.

Status: Accepted and finalized.

### Update — 2026-05-15 — Issue #116 acceptance criteria met

The following acceptance criteria from #116 are formally resolved by DEC-008 and #117:

- **Why 3-class taxonomy fails:** documented in Context section above — `Other lesion` contained 4,235 NMSC cases (BCC + SCC) alongside benign lesions, making it impossible to communicate cancer risk.
- **Actinic keratosis handling:** merged into `Other non-cancer / indeterminate lesion` (1,088 rows; insufficient for standalone class; "indeterminate" qualifier signals elevated risk without overstating certainty).
- **Two candidate taxonomies considered:** Option B (3-way risk: cancer / pre-cancer indeterminate / benign) and Option C (4-class educational: melanoma / NMSC / nevus / other indeterminate) — see Options considered above.
- **Recommended taxonomy:** Option C (4-class) — finalized in #117, confirmed by BCN20000 class balance, dermatology-resident user need, and Revela's educational scaffold framing.
- **Affected open issues:** #119 (class name wording must match DEC-008 wording rule exactly), #120 (evaluation must use cancer/malignant recall as primary metric, not top-1 accuracy), #121 (supplemental datasets must be mappable to the same 4 classes; datasets that cannot cleanly map AK to "indeterminate" must be flagged as incompatible).

Issue #116 can be closed.

---

## DEC-009 — Map Mel+Nevus Histo (MNH) labels to the 4-class cancer-risk taxonomy

**Date:** 2026-05-17
**Status:** Accepted
**Owner:** Emma
**Category:** Dataset / Taxonomy
**Linked issues:** #137, #138, #139

### Decision

The 12,500 filtered MNH rows (post-BCN20000 dedup) are mapped to the same 4 cancer-risk classes used in BCN20000 (DEC-008): Melanoma | Non-melanoma skin cancer | Benign nevus | Other non-cancer / indeterminate. Full mapping table and per-label rationale live in `docs/mnh_taxonomy_mapping.md`.

### Context

MNH is histopathology-confirmed but melanoma/nevus-focused — it contains no BCC, SCC, or actinic keratosis, so the NMSC class receives zero MNH contribution. MNH also includes lesion subtypes not present in BCN20000 (indeterminate melanocytic proliferations, collision lesions, non-melanocytic benign pigmentations) that require explicit decisions before merge.

### Ambiguous-label resolutions

1. **Indeterminate melanocytic lesions** (Atypical melanocytic neoplasm ×70, Atypical intraepithelial melanocytic proliferation ×6, Atypical proliferative nodules in congenital melanocytic nevus ×4 — 80 rows) → `Other non-cancer / indeterminate`. Rationale: diagnosis_2 literally says "Indeterminate melanocytic proliferations"; honest representation is preferable to inflating the cancer or benign class with non-confirmed labels.
2. **Non-melanocytic / non-nevus benign pigmentations** (Epidermal nevus ×6, Lentigo NOS ×3, Mucosal melanotic macule ×1 — 10 rows) → `Other non-cancer / indeterminate`. Rationale: these are not melanocytic nevi; mapping them as `Benign nevus` would dilute the class with semantically different lesion types.
3. **Collision lesions** (diagnosis_3 NaN, 26 rows) → split by diagnosis_2: benign-only collisions (15) → `Other non-cancer / indeterminate`; collisions with at least one malignant proliferation (11) → `Melanoma`. Rationale: conservative on the malignant side so melanoma-containing collisions surface in cancer recall.

### Final MNH class distribution

| Class | Rows |
|---|---:|
| Benign nevus | 8,050 |
| Melanoma | 4,345 |
| Non-melanoma skin cancer | 0 |
| Other non-cancer / indeterminate | 105 |
| **Total** | **12,500** |

Zero NaN in `cancer_risk_class` (asserted at runtime in `Rehma_Revela/Notebook/10_map_mnh_taxonomy.ipynb`).

### Consequences

- D4.4 merge (#140) can proceed: MNH contributes ~4,345 melanoma and 8,050 nevi to the training pool; NMSC remains entirely BCN20000-sourced.
- Class imbalance shifts: post-merge melanoma share rises; this is the intended effect of the MNH augmentation track.
- Future MNH refreshes must re-validate the mapping if new diagnosis_3 categories appear.

### Review date

After D4.6 evaluation (#142) — verify the mapping choices do not artifactually inflate melanoma recall on the BCN20000 frozen test set.

---

## DEC-010 — D4 — Adopt MNH-augmented CNN as the production dermoscopic cancer-risk model

**Date:** 2026-05-19
**Status:** Closed
**Owner:** Emma
**Category:** Dataset / Model
**Linked issues:** D4.1 (#137), D4.2 (#138), D4.3 (#139), D4.4 (#140), D4.5 (#141), D4.6 (#142), D4.7 (#143)
**Builds on:** [[DEC-008]] (4-class cancer-risk taxonomy), [[DEC-009]] (MNH taxonomy mapping)

### Decision

Promote the BCN20000+MNH-trained dermoscopic CNN (D4.5 / #141) as the production cancer-risk model, replacing the BCN-only baseline (D3.4 / #119). MNH is the Melanoma and Nevus Dermoscopy Images with Confirmed Histopathological Diagnosis dataset (ISIC collection 294), added to training to boost melanoma representation in the training pool while keeping the BCN20000 frozen test set untouched. D4.6 (#142) measured the head-to-head trade-off on the identical frozen test set and confirmed a meaningful melanoma-recall gain with flat aggregate accuracy.

### Dataset composition

| Stage | Rows | Notes |
|---|---:|---|
| BCN20000 training split (input) | 12,352 | from D3.3 (#118) splits |
| MNH raw | 18,133 | from D4.1 (#137) |
| MNH after BCN isic_id dedup | 12,500 | −5,633 dupes asserted (D4.2 / #138) |
| Merged training pool (BCN train + MNH filtered) | 24,852 | input to lesion-grouped split |
| **New train split** | **21,233** | `splits/bcn_mnh_train.csv` (D4.4 / #140) |
| **New val split** | **3,619** | `splits/bcn_mnh_val.csv` |
| **Frozen BCN20000 test set** | **2,659** | unchanged; md5 `a67861586e00812aadf46f2bdb4bc01b` (verified hash-stable across every D4.x notebook) |

### Deduplication and split safety

- Deduplication by exact `isic_id` match against BCN20000 (D4.2): 5,633 MNH images removed before merge.
- Zero overlap asserted at runtime between MNH ∩ BCN train and MNH ∩ BCN test.
- Lesion-grouped train/val split (`random.Random(seed=42).shuffle(unique_lesion_ids)` then slice, val_frac=0.15) — same logic as `src/data/prepare_bcn20000_cancer_risk.py:70-84`. MNH rows with NaN `lesion_id` (4,086) given synthetic `MNH_singleton_<isic_id>` so each is its own singleton lesion. Zero lesion leakage between train and val asserted.
- BCN20000 frozen test file hash unchanged before and after every training and evaluation run.

### Taxonomy mapping

All MNH `diagnosis_3` labels mapped to the same 4-class cancer-risk taxonomy used in BCN20000 (DEC-008). Ambiguous-label decisions (resolved in DEC-009 / D4.3 / #139):
- **Indeterminate melanocytic lesions** (Atypical melanocytic neoplasm, Atypical intraepithelial melanocytic proliferation, Atypical proliferative nodules in congenital nevus — 80 rows) → `Other non-cancer / indeterminate lesion`.
- **Non-melanocytic / non-nevus benign pigmentations** (Epidermal nevus, Lentigo NOS, Mucosal melanotic macule — 10 rows) → `Other non-cancer / indeterminate lesion`.
- **Collision lesions** (26 rows, `diagnosis_3` NaN) → split by `diagnosis_2`: benign-only collisions (15) → `Other non-cancer / indeterminate lesion`; malignant-containing collisions (11) → `Melanoma`.
- **Melanoma subtypes** (`Melanoma, NOS`, `Melanoma in situ`, `Melanoma Invasive`) → `Melanoma`.
- Full mapping table: `docs/mnh_taxonomy_mapping.md`.

Class wording fix at merge time: MNH `cancer_risk_class` was normalized from `"Other non-cancer / indeterminate"` → `"Other non-cancer / indeterminate lesion"` to match the DEC-008 wording rule before being concatenated with BCN training rows.

### Outcome — head-to-head on identical frozen BCN20000 test set (n=2,659)

Source files: `outputs/metrics/bcn_mnh_cancer_risk_test_metrics.json` (BCN+MNH, D4.6) vs `outputs/metrics/bcn20000_cancer_risk_test_metrics.json` (BCN-only, #120). All numbers below pulled from those JSONs.

| Metric | BCN-only (#120) | BCN+MNH (D4.6) | Delta |
|---|---:|---:|---:|
| **Melanoma recall** | 57.87% | **61.36%** | **+3.50 pp** |
| **Melanoma FNR** | 42.13% | **38.64%** | **−3.50 pp** |
| NMSC recall | 72.41% | 75.30% | +2.89 pp |
| Cancer recall (Mel+NMSC → any malignant class) | 71.91% | 73.70% | +1.79 pp |
| Cancer FNR | 28.09% | 26.30% | −1.79 pp |
| Top-1 accuracy | 67.77% | 67.62% | −0.15 pp (flat) |
| Macro-F1 | 0.6581 | 0.6552 | −0.0030 (flat) |
| Balanced accuracy | 65.85% | 65.71% | −0.14 pp (flat) |

Both malignant classes gained recall; both benign classes gave a little back — the correct trade-off direction for a cancer-risk model. Melanoma-misclassified-as-benign-nevus errors dropped from 132 to 93 on the test set, the most safety-relevant failure mode. Net change in missed melanoma: from ~241 to 221 cases out of 572 melanoma in test.

### Model artifact

- **Production checkpoint:** `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth` (PyTorch). Mirror with epoch suffix at `models/bcn_mnh_cancer_risk_cnn_epoch6.pth`.
- **Saved by:** `val_macro_f1` (max), matching DEC-008 / #119 / #120 selection rule for apples-to-apples comparison.
- **Best epoch:** 6 / 10. `val_macro_f1=0.6768` on the BCN+MNH val split (3,619 rows).
- **Architecture and hyperparameters:** EfficientNet-B0 / ImageNet pretrained / 224×224 / batch 16 / AdamW lr=3e-4 wd=0.01 / 10 epochs / inverse-frequency class weights — identical to BCN-only #119. Only the training data differs.
- **Training log:** `outputs/metrics/bcn_mnh_training_log.csv`.
- **Training config:** `config/bcn_mnh_cancer_risk_config.yaml`.
- **Training notebook:** `Rehma_Revela/Notebook/12_train_bcn_mnh_cancer_risk_cnn.ipynb` (guarded against accidental re-execution).
- **Evaluation notebook:** `Rehma_Revela/Notebook/13_evaluate_bcn_mnh_cancer_risk_cnn.ipynb`.

### Effect on downstream work

- Inference and app code (#123 / D3.7, F1.x stubs) should switch from `models/bcn20000_cancer_risk_effnet_b0/best_model.pth` to `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth`. Same `class_to_idx`, same input size, drop-in replacement.
- BCN-only baseline artifacts at `outputs/metrics/bcn20000_cancer_risk_*` are preserved as the comparison baseline — D4.6 wrote to distinct `outputs/metrics/bcn_mnh_*` paths.
- The frozen BCN20000 test set md5 (`a67861586e00812aadf46f2bdb4bc01b`) is now the canonical evaluation benchmark. Any future model iteration must evaluate against this exact file to remain comparable.

### Communication rules (DEC-001, DEC-006, DEC-007)

Revela remains an **educational prototype**, not a clinical diagnostic device. The +3.50 pp melanoma-recall gain and 75.3% NMSC recall must not be presented as clinical readiness. The model misses approximately 1 in 3 melanoma cases in this single-institution test set; communication must not claim that all cancers or all melanoma are detected. The cancer-risk recall metric is for educational scaffold framing only, not patient triage.

### Consequences

- BCN+MNH model becomes the default checkpoint loaded by inference code.
- Future supplemental dermoscopic dataset assessments (e.g. #121) must be evaluated against this new baseline, not the BCN-only one.
- The same dedup-by-isic_id + lesion-grouped split + hash-frozen test pattern is the template for any future dataset-augmentation track.

### Review date

After the next major model iteration (whichever issue follows from #121 supplemental-dataset work) — re-evaluate whether MNH augmentation should remain in the training pool or be replaced by a more skin-tone-diverse dataset (DDI, SCIN clinical) once that becomes feasible.
