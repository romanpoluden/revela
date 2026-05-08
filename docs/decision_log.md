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
**Status:** Accepted  
**Owner:** Roman  
**Category:** Model / Scope  
**Linked issues:** #26, #36, #38, #42

### Decision

CNN v1 uses three classes:

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

A 3-class dermoscopic taxonomy is better aligned with available data and reduces domain mismatch. It also keeps the MVP trainable and explainable.

### Consequences

- Top-3 accuracy is not meaningful for CNN v1 because the model has exactly three classes.
- Evaluation should focus on top-1 accuracy, macro-F1, balanced accuracy, class-wise precision/recall/F1, and confusion matrix.
- Future clinical-image model v2 may use a different taxonomy, but that must be treated as a separate module.

### Review date

After clinical-image model v2 planning.

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
**Linked issues:** #109, #110

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
