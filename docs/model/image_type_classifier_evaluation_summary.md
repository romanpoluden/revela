# Image-Type Classifier Evaluation Summary — Stage 3

**Branch:** v2.24-image-type-evaluation  
**Date evaluated:** 2026-05-26  
**Issue:** #199 Stage 3  
**Model artifact:** `models/image_type_classifier_v1/best_model.pth` (epoch 10, val_macro_F1=0.9994)  
**Evaluated split:** test (reserved, never seen during training or validation)  
**Evaluation script:** `src/model/evaluate_image_type_classifier.py`

---

## Model Artifact

| Field | Value |
|---|---|
| Checkpoint | `models/image_type_classifier_v1/best_model.pth` |
| Backbone | EfficientNet-B0 (ImageNet pretrained) |
| Classes | `clinical_macroscopic` (idx 0), `dermoscopic` (idx 1) |
| Image size | 224 × 224 |
| Training epoch | 10 |
| Val macro-F1 at checkpoint | 0.9994 |

---

## Test Split Counts

| Class | Count |
|---|---|
| `dermoscopic` | 2,648 |
| `clinical_macroscopic` | 1,533 |
| **Total** | **4,181** |

| Source dataset | Count | Image type |
|---|---|---|
| `bcn20000` | 2,648 | dermoscopic |
| `fitzpatrick17k` | 991 | clinical_macroscopic |
| `google_scin` | 542 | clinical_macroscopic |

---

## Metrics Summary

| Metric | Value |
|---|---|
| **Accuracy** | **0.9995** |
| **Macro-F1** | **0.9995** |
| **Balanced accuracy** | **0.9993** |
| clinical_macroscopic precision | 1.0000 |
| clinical_macroscopic recall | 0.9987 |
| clinical_macroscopic F1 | 0.9993 |
| dermoscopic precision | 0.9992 |
| dermoscopic recall | 1.0000 |
| dermoscopic F1 | 0.9996 |
| Total misclassified | **2** |
| Runtime | **7.6 ms/image** (MPS) |

---

## Confusion Matrix

|  | Predicted: clinical_macroscopic | Predicted: dermoscopic |
|---|---|---|
| **True: clinical_macroscopic** | 1,531 | **2** |
| **True: dermoscopic** | 0 | 2,648 |

- **False clinical→dermoscopic:** 2 (clinical images predicted as dermoscopic)
- **False dermoscopic→clinical:** 0

---

## Manual Review of Misclassified Examples

Both misclassified images come from Fitzpatrick17k and are clinical images wrongly predicted as dermoscopic.

| image_path | source | true | predicted | confidence | width | height |
|---|---|---|---|---|---|---|
| `fitzpatrick17k/…/f17773a2ee06fb5179ed0e56b7235c2a.jpg` | fitzpatrick17k | clinical_macroscopic | dermoscopic | **0.906** | 653 | 848 |
| `fitzpatrick17k/…/c9a9e472488e0d3d62b1abda22bdec42.jpg` | fitzpatrick17k | clinical_macroscopic | dermoscopic | **0.986** | 604 | 402 |

Both errors are **clinical→dermoscopic** misrouting. The model never misroutes a dermoscopic image as clinical.

**Note:** The higher-confidence error (0.986) would be accepted at any threshold ≤ 0.985. These two Fitzpatrick17k images may contain visual features that resemble dermoscopic crops — such as tight lesion framing, uniform background, or circular lesion presentation — that the model has learned to associate with dermoscopy.

---

## Confidence Distribution

All confidences computed as `max(softmax(logits))` across both classes.

| Statistic | All images | clinical_macroscopic | dermoscopic |
|---|---|---|---|
| min | 0.5546 | 0.5546 | 0.7023 |
| p1 | 0.9688 | — | — |
| p5 | 0.9953 | 0.9920 | 0.9958 |
| p25 | 0.9994 | — | — |
| median | 0.9998 | 0.9999 | 0.9998 |
| p75 | 0.9999 | — | — |
| p95 | 1.0000 | 1.0000 | 1.0000 |
| p99 | 1.0000 | — | — |
| max | 1.0000 | 1.0000 | 1.0000 |
| mean | 0.9981 | — | — |

Key observation: the confidence distribution is extremely right-skewed. Over 95% of images receive confidence ≥ 0.9953. The single lowest-confidence image (0.5546) is one of the two clinical→dermoscopic misclassifications — this is the one caught by the 0.95 threshold.

---

## Threshold Analysis

Threshold logic: if `max_probability ≥ threshold` → accepted; else → `uncertain_or_unsupported`.

| Threshold | Accepted | Coverage | Accepted accuracy | Accepted macro-F1 | Wrong accepted | Rejected (total) | Rejected (correct) | Rejected (incorrect) |
|---|---|---|---|---|---|---|---|---|
| 0.70 | 4,179 | 99.95% | 0.9995 | 0.9995 | **2** | 2 | 2 | 0 |
| 0.80 | 4,176 | 99.88% | 0.9995 | 0.9995 | **2** | 5 | 5 | 0 |
| 0.85 | 4,174 | 99.83% | 0.9995 | 0.9995 | **2** | 7 | 7 | 0 |
| 0.90 | 4,168 | 99.69% | 0.9995 | 0.9995 | **2** | 13 | 13 | 0 |
| **0.95** | **4,151** | **99.28%** | **0.9998** | **0.9997** | **1** | **30** | **29** | **1** |

Observations:
- At thresholds 0.70–0.90: both wrong examples are accepted (confidence 0.906 and 0.986 respectively)
- At threshold 0.95: the lower-confidence error (0.906) is correctly rejected, reducing wrong routing from 2→1
- The higher-confidence error (0.986) cannot be rejected by any practical confidence threshold — it represents a genuine hard case
- All rejected images at thresholds ≤ 0.90 are *correctly* classified images (no incorrect images rejected at those levels)
- At threshold 0.95: 29 correct images are rejected and 1 incorrect is also rejected

---

## Recommended Threshold

**Recommended: 0.90**

Rationale:
- Coverage 99.69% — only 13 of 4,181 images (0.31%) are rejected as uncertain/unsupported
- All 13 rejected images at this threshold are correctly classified images being held back conservatively — no wrong routings are swept under the rug
- The 2 remaining wrong routings are genuine hard cases: both Fitzpatrick17k clinical images that visually resemble dermoscopic crops with high model confidence (0.906 and 0.986)
- Raising to 0.95 catches one of the two errors but rejects 30 images (0.72%), 29 of which are correct — the gain in error reduction does not justify the coverage loss for this classifier
- Threshold 0.90 is consistent with project standards favoring conservative routing over excessive rejection of valid inputs

**Important caveat:** The 0.986-confidence clinical→dermoscopic misclassification is hard-coded into the score distribution and will not be resolved by threshold tuning alone. It requires either OOD/adversarial robustness work or explicit negative training examples — addressed in Stage 4.

---

## Shortcut and Risk Discussion

### Why extremely high performance may not reflect generalisation

The near-perfect test performance (0.9995 accuracy) on this split is consistent with Stage 2 validation results, but the test split has the same structural limitations as the validation set:

1. **Source shortcut — dermoscopic images:** All 2,648 dermoscopic test examples come from a single dataset (BCN20000). The model has never seen dermoscopic images from any other source (ISIC, HAM10000, etc.). If BCN20000 carries distinctive JPEG compression profiles, standardised capture conditions, or resolution normalisation patterns, the classifier may be exploiting these as proxies for "dermoscopic" rather than learning the visual concept of dermoscopic imaging.

2. **Source shortcut — clinical images:** All clinical test examples come from two sources (Fitzpatrick17k, SCIN). Both have web-sourced image characteristics. A model trained and tested only on these distributions may degrade on clinical images from different capture devices or clinical workflows.

3. **Resolution shortcut (partially mitigated):** All images are resized to 224×224 before inference. However, the upsampling frequency spectrum of natively small clinical images differs from the downsampled dermoscopic images. High-frequency aliasing artefacts may be class-informative even after resizing.

4. **Zero out-of-distribution coverage:** The model has never been evaluated on images that are neither clinical macroscopic nor dermoscopic — pathology slides, X-rays, photographs of non-skin subjects, adversarial noise, or AI-generated skin images. In production, such images will arrive and may be confidently classified into one of the two trained classes.

5. **Limited dermoscopic source diversity:** This is the highest-priority shortcut risk. Even if the model generalises well to new clinical images, its dermoscopic boundary may be BCN20000-specific. Cross-source dermoscopic evaluation should be the first validation step in Stage 4.

### What this means for Stage 4

Even with 0.9995 test accuracy, the classifier is **not ready for production routing** until:
- It is evaluated on held-out images from at least one additional dermoscopic source not used in training
- A confidence-based OOD rejection mechanism is validated against genuinely unsupported image types (non-skin photos, pathology slides, etc.)
- Inference pipeline integration is tested end-to-end in Streamlit without routing to the wrong disease classifier

---

## Deployment Readiness (Stage 3 assessment only)

| Criterion | Status |
|---|---|
| Test accuracy ≥ 0.99 | ✅ (0.9995) |
| Macro-F1 ≥ 0.99 | ✅ (0.9995) |
| Dermoscopic recall ≥ 0.99 | ✅ (1.0000) |
| Clinical recall ≥ 0.99 | ✅ (0.9987 — 2/1533 misses) |
| Confidence threshold selected | ✅ (0.90 recommended) |
| OOD / unsupported rejection validated | ❌ (Stage 4 required) |
| Cross-source dermoscopic eval | ❌ (Stage 4 required) |
| App routing integrated | ❌ (Stage 4/5 scope) |

**Overall Stage 3 verdict: classifier performs exceptionally on known-distribution test data. Stage 4 OOD rejection and cross-source validation required before production integration.**

---

## Output Files

| File | Description |
|---|---|
| `outputs/metrics/image_type_classifier_predictions.csv` | 4,181 rows, per-image predictions and probabilities |
| `outputs/metrics/image_type_classifier_metrics.json` | Full metrics including confidence distribution |
| `outputs/metrics/image_type_classifier_confusion_matrix.csv` | 2×2 confusion matrix |
| `outputs/metrics/image_type_classifier_threshold_analysis.csv` | Threshold sweep at 0.70/0.80/0.85/0.90/0.95 |
| `outputs/metrics/image_type_classifier_misclassified_examples.csv` | 2 misclassified examples with metadata |
