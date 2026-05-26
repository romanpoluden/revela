# Image-Type Classifier: Rejection Logic

## Overview

Before routing an uploaded image through the dermoscopic or clinical model, the system runs a two-layer rejection pipeline to detect images that are unsupported, malformed, or ambiguous. Images that fail either layer are assigned product state `uncertain_or_unsupported` and no skin-condition inference is run.

## Layer 1 — PIL Validation

Implemented in `src/model/evaluate_image_type_ood_rejection.py::validate_image()`.

| Check | Reject condition | Reason field |
|---|---|---|
| Decode | PIL cannot open the file | `cannot_decode:<ExcType>` |
| Min side | `min(width, height) < 32` | `too_small:<W>x<H>` |
| Aspect ratio | `max(W,H) / min(W,H) > 10` | `extreme_aspect:<W>x<H>_ratio<R>` |
| Variance | mean pixel variance across RGB channels `< 5.0` | `near_blank:variance=<V>` |

Constants (all defined at module top):

```python
MIN_SIDE = 32
MAX_ASPECT_RATIO = 10
MIN_VARIANCE = 5.0
```

## Layer 2 — Confidence Threshold

After validation passes, the image is run through the EfficientNet-B0 2-class classifier (`models/image_type_classifier_v1/best_model.pth`). The classifier outputs probabilities over `[clinical_macroscopic, dermoscopic]`.

`accepted = max(p_clinical, p_dermoscopic) >= threshold`

**Recommended threshold: 0.90**

Rationale from in-distribution evaluation (Stage 3, `outputs/metrics/image_type_classifier_threshold_analysis.csv`):

| Threshold | Coverage | Accuracy | Wrong accepts |
|---|---|---|---|
| 0.70 | 99.95% | 99.95% | 2 |
| 0.80 | 99.88% | 99.95% | 2 |
| 0.85 | 99.83% | 99.95% | 2 |
| **0.90** | **99.69%** | **99.95%** | **2** |
| 0.95 | 99.28% | 99.98% | 1 |

At 0.90 the classifier rejects 0.31% of real skin images as uncertain while keeping wrong-accepts to 2/4181 — both are Fitzpatrick17k clinical images mistaken for dermoscopic.

## OOD / Rejection Fixture Evaluation (Stage 4)

Evaluated with `src/model/evaluate_image_type_ood_rejection.py` against 15 programmatic fixtures in `tests/fixtures/ood_image_type/`. Results at threshold 0.90:

| Rejection layer | Count | % of 15 |
|---|---|---|
| PIL validation | 9 | 60% |
| Confidence threshold | 2 | 13% |
| **Total rejected** | **11** | **73%** |
| False accepts (incorrectly classified) | 4 | 27% |

### Validation rejections (9/15)

| Fixture | Reason |
|---|---|
| `blank_white.jpg` | `near_blank:variance=0.00` |
| `blank_black.jpg` | `near_blank:variance=0.00` |
| `low_contrast_noise.jpg` | `near_blank:variance=4.21` |
| `tiny_image_16x16.jpg` | `too_small:16x16` |
| `tiny_image_8x8.jpg` | `too_small:8x8` |
| `extreme_aspect_wide.jpg` | `extreme_aspect:1024x32_ratio32.0` |
| `extreme_aspect_tall.jpg` | `extreme_aspect:32x1024_ratio32.0` |
| `overexposed_transformed.jpg` | `near_blank:variance=0.00` |
| `corrupted_jpeg.jpg` | `cannot_decode:UnidentifiedImageError` |

### Threshold rejections at 0.90 (2/6 that reached the model)

| Fixture | Predicted | Confidence |
|---|---|---|
| `solid_red.jpg` | clinical_macroscopic | 0.883 |
| `heavily_blurred_transformed.jpg` | clinical_macroscopic | 0.635 |

### False accepts at 0.90 (4/6 that reached the model)

These are structurally valid images the model misclassifies with high confidence:

| Fixture | Predicted | Confidence | Notes |
|---|---|---|---|
| `solid_green.jpg` | clinical_macroscopic | 0.937 | Solid color passes variance check |
| `random_noise.jpg` | dermoscopic | 1.000 | Noise texture resembles dermoscopy pattern |
| `underexposed_transformed.jpg` | clinical_macroscopic | 0.970 | Dark clinical-like region survives validation |
| `document_text_like.jpg` | clinical_macroscopic | 0.968 | White background + content resembles clinical photo |

These cases illustrate the fundamental limitation: the classifier distinguishes clinical from dermoscopic texture, so any image with similar texture statistics will be routed. A higher threshold (0.95) eliminates 1 of the 4 false accepts but the other 3 exceed even 0.95.

## Product State Mapping

```
validate_image(path) == "rejected"  →  uncertain_or_unsupported  (skip model)
max_prob < threshold                →  uncertain_or_unsupported
max_prob >= threshold               →  predicted class (clinical_macroscopic | dermoscopic)
```

## Output Files

| File | Description |
|---|---|
| `outputs/metrics/image_type_classifier_ood_predictions.csv` | Per-fixture predictions, validation status, threshold flags |
| `outputs/metrics/image_type_classifier_ood_rejection_results.csv` | Aggregate rejection stats per threshold |
| `outputs/metrics/image_type_classifier_ood_false_accepts.csv` | Rows that passed validation + threshold 0.90 (OOD only) |

## Related

- [image_type_classifier_dataset_summary.md](image_type_classifier_dataset_summary.md)
- [image_type_classifier_training_summary.md](image_type_classifier_training_summary.md)
- [image_type_classifier_evaluation_summary.md](image_type_classifier_evaluation_summary.md)
