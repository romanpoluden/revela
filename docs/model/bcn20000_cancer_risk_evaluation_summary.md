# BCN20000 Cancer-Risk CNN — Test Evaluation Summary

Issue: #120 — D3.5: Evaluate dermoscopic cancer-risk CNN  
Model: `models/bcn20000_cancer_risk_effnet_b0/best_model.pth` (epoch 6)  
Test split: `data/processed/bcn20000_cancer_risk/test.csv` — 2,659 rows  
Evaluated: 2026-05-15

---

## Headline Numbers

| Metric | Value |
|--------|-------|
| **Cancer / malignant recall** | **71.91%** |
| **Cancer / malignant FNR** | **28.09%** |
| Melanoma recall | 57.87% |
| Non-melanoma skin cancer recall | 72.41% |
| Macro-F1 | 0.6581 |
| Balanced accuracy | 65.85% |
| Top-1 accuracy | 67.77% |

Cancer recall counts any true malignant case (Melanoma or NMSC) predicted as *any* malignant class (Melanoma or NMSC).

---

## Class-Wise Results

| Class | Precision | Recall | F1 | Support |
|-------|----------:|-------:|---:|--------:|
| Melanoma | 60.51% | 57.87% | 59.16% | 572 |
| Non-melanoma skin cancer | 72.85% | 72.41% | 72.63% | 656 |
| Benign nevus | 76.80% | 76.47% | 76.63% | 935 |
| Other non-cancer / indeterminate lesion | 53.12% | 56.65% | 54.83% | 496 |

---

## Confusion Matrix (counts)

|  | Pred: Melanoma | Pred: NMSC | Pred: Benign nevus | Pred: Other |
|--|---------------:|-----------:|-------------------:|------------:|
| **True: Melanoma** | 331 | 37 | 132 | 72 |
| **True: NMSC** | 40 | 475 | 26 | 115 |
| **True: Benign nevus** | 126 | 33 | 715 | 61 |
| **True: Other** | 50 | 107 | 58 | 281 |

Key misclassification patterns:
- 132 Melanoma cases predicted as Benign nevus (22.9% of melanoma test rows)
- 115 NMSC cases predicted as Other (17.5% of NMSC test rows)
- 107 Other cases predicted as NMSC — inflating NMSC false positives

---

## Confusion Matrix (row-normalized)

|  | Pred: Melanoma | Pred: NMSC | Pred: Benign nevus | Pred: Other |
|--|---------------:|-----------:|-------------------:|------------:|
| **True: Melanoma** | 57.9% | 6.5% | 23.1% | 12.6% |
| **True: NMSC** | 6.1% | 72.4% | 4.0% | 17.5% |
| **True: Benign nevus** | 13.5% | 3.5% | 76.5% | 6.5% |
| **True: Other** | 10.1% | 21.6% | 11.7% | 56.7% |

---

## Comparison vs CNN v1

CNN v1 used a 3-class taxonomy (Melanoma / Benign nevus / Other lesion). CNN v2 uses a 4-class cancer-risk taxonomy. Both evaluated on 2,659-row BCN20000 test subsets, seed=42, 15% hold-out.

**Label mapping caveat:** CNN v1's "Other lesion" silently contained all NMSC cases (BCC + SCC). Class-by-class recall is therefore NOT directly comparable. Only aggregate metrics and melanoma recall can be compared fairly.

| Metric | CNN v1 (3-class) | CNN v2 (4-class) | Change |
|--------|----------------:|----------------:|--------|
| Top-1 accuracy | 76.16% | 67.77% | −8.4 pp |
| Macro-F1 | 0.7443 | 0.6581 | −0.0862 |
| Balanced accuracy | 75.29% | 65.85% | −9.4 pp |
| Melanoma recall | 69.58% | 57.87% | −11.7 pp |
| NMSC recall | — (inside Other) | 72.41% | now measurable |
| Cancer recall | — (not computable) | 71.91% | now measurable |

CNN v2 performs below CNN v1 on all directly comparable metrics. The 4-class split increases task difficulty: what v1 handled as a single "Other" bucket is now a meaningful fourth class, and the model must draw a harder boundary between NMSC and Other non-cancer.

---

## Does the New Taxonomy Better Fit the Product Objective?

Yes, unambiguously — for the product objective, not for raw classification scores. Revela is a clinical reasoning scaffold for dermatology residents: its value is giving residents a structured, educationally grounded review of a lesion image, not returning a binary safe/not-safe flag. Under CNN v1, a resident seeing "Other lesion" for a BCC or SCC image received zero signal about cancer risk — that class conflated melanocytic nevi, actinic keratoses, and thousands of NMSC cases under a single uninformative label. CNN v2 surfaces NMSC explicitly (72.4% recall) and makes cancer recall a first-class metric (71.9%), which directly teaches the melanoma-vs-NMSC distinction residents need to learn. The drop in aggregate accuracy (−8.4 pp) reflects a genuinely harder task, not a failure of the taxonomy: separating four clinically meaningful categories is harder than separating three, and the confusion matrix shows the model is making clinically interpretable errors (Melanoma confused with Benign nevus, NMSC confused with Other) rather than random noise. For an educational prototype in this stage, a model that is wrong in instructive ways and surfaces the right risk categories is more aligned with the product goal than a higher-accuracy model that cannot distinguish NMSC from benign conditions.

---

## Communication Rules

- This is an **educational prototype**, not a clinical diagnostic device.
- Do **not** interpret cancer recall as "the model detects X% of all skin cancers" — these are results on a single dermoscopic dataset under controlled splits.
- Do **not** claim clinical readiness or use these results to support diagnosis decisions.

---

## Known Limitations

1. **Skin-tone (FST) distribution unknown.** BCN20000 is a dermoscopic dataset collected in a clinical setting (Hospital Clínic de Barcelona). The FST distribution of the test set is not documented. Performance on darker skin tones may differ from these aggregate numbers.
2. **Class imbalance.** Benign nevus (935 rows) is the largest test class; Other non-cancer / indeterminate (496 rows) is the smallest. Macro-F1 weights all classes equally and partially compensates, but the confusion matrix should be read with support counts in mind.
3. **Out-of-distribution generalization.** All images are from a single institution's dermoscopy archive. Performance on images from different devices, clinical settings, or patient populations is unknown.
4. **Actinic keratosis (AK).** AK is merged into "Other non-cancer / indeterminate lesion" per DEC-008. The model does not distinguish AK from other indeterminate lesions within that class.
5. **No calibration.** Softmax confidence scores are not calibrated. Probability outputs should not be treated as true posterior probabilities.
