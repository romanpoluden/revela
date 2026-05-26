# Image-Type Classifier v1 — Final Recommendation

**Decision: soft-gating candidate only / needs more data**

The classifier is not ready for silent automatic routing. It may be integrated later as a user-facing warning and confirmation gate only.

---

## 1. Objective

Detect supported input modality (`clinical_macroscopic` or `dermoscopic`) for a given uploaded image, and produce a product-level `uncertain_or_unsupported` state via validation + confidence thresholding. The goal is to prevent wrong-modality uploads from being sent to the wrong disease model — not to diagnose disease.

---

## 2. Stage 1 — Dataset Audit

**Total rows:** 27,658

| Class | Count |
|---|---|
| clinical_macroscopic | 10,019 |
| dermoscopic | 17,639 |

| Source dataset | Count |
|---|---|
| bcn20000 | 17,639 |
| fitzpatrick17k | 6,354 |
| google_scin | 3,665 |

| Split | clinical_macroscopic | dermoscopic |
|---|---|---|
| train | 6,980 | 12,344 |
| val | 1,506 | 2,647 |
| test | 1,533 | 2,648 |

**Key risks:**

- **Class imbalance:** dermoscopic:clinical = 1.76:1. Weighted CrossEntropy loss applied.
- **Source shortcut risk:** all dermoscopic examples come from BCN20000 only; any BCN20000-specific texture or metadata artifact could inflate dermoscopic recall without generalising.
- **Resolution/source shortcut:** clinical examples come from two different sources (Fitzpatrick17k, SCIN) at different resolutions; the model may learn source-level cues rather than pure modality cues.
- **No unsupported training class:** `uncertain_or_unsupported` is entirely a product-level post-processing state, not a trained class. OOD rejection relies on validation checks and confidence thresholding.

---

## 3. Stage 2 — Training Summary

| Setting | Value |
|---|---|
| Architecture | EfficientNet-B0, ImageNet pretrained |
| Input size | 224 × 224 |
| Head | `nn.Linear(1280, 2)` |
| Classes | `clinical_macroscopic` (idx 0), `dermoscopic` (idx 1) |
| Loss | Weighted CrossEntropy |
| Fine-tuning | Full (all layers) |
| Best epoch | 10 |
| Val macro-F1 at best epoch | 0.9994 |

Artifacts are stored locally at `models/image_type_classifier_v1/` and gitignored. No app routing, disease model weights, inference registry, or disease taxonomy was changed.

---

## 4. Stage 3 — Supported-Modality Evaluation

Evaluated on the held-out test split (4,181 images).

| Metric | Value |
|---|---|
| Accuracy | 0.9995 |
| Macro-F1 | 0.9995 |
| Balanced accuracy | 0.9993 |

**Confusion matrix:**

| True \ Predicted | clinical_macroscopic | dermoscopic |
|---|---|---|
| clinical_macroscopic | 1,531 | 2 |
| dermoscopic | 0 | 2,648 |

- False clinical → dermoscopic: **2**
- False dermoscopic → clinical: **0**

**Confidence distribution (test set):**

| Percentile | Confidence |
|---|---|
| min | 0.5546 |
| p5 | 0.9953 |
| median | 0.9998 |
| p95 | 1.0000 |
| max | 1.0000 |

**Threshold analysis:**

| Threshold | Coverage | Accuracy | Wrong accepts |
|---|---|---|---|
| 0.70 | 99.95% | 99.95% | 2 |
| 0.80 | 99.88% | 99.95% | 2 |
| 0.85 | 99.83% | 99.95% | 2 |
| **0.90** | **99.69%** | **99.95%** | **2** |
| 0.95 | 99.28% | 99.98% | 1 |

**Recommended threshold: 0.90** (best coverage/accuracy trade-off).

**Key caveat:** One of the two wrong-accepted clinical→dermoscopic misclassifications had confidence ~0.986, which exceeds even the 0.95 threshold. Confidence thresholding alone cannot catch all wrong-routes. User confirmation is required before any route switch.

---

## 5. Stage 4 — OOD / Unsupported Rejection

Evaluated against 15 programmatic OOD/problematic fixtures in `tests/fixtures/ood_image_type/`.

**At threshold 0.90:**

| Layer | Rejected | % of 15 |
|---|---|---|
| PIL validation | 9 | 60% |
| Confidence threshold | 2 | 13% |
| **Total rejected** | **11** | **73%** |
| False accepts | 4 | 27% |

**Validation rejections (9):** blank white, blank black, near-blank low-contrast noise, 16×16 image, 8×8 image, extreme wide aspect ratio, extreme tall aspect ratio, overexposed frame (zero variance), corrupted JPEG.

**False accepts (4):**

| Fixture | Predicted | Confidence |
|---|---|---|
| solid_green.jpg | clinical_macroscopic | 0.937 |
| random_noise.jpg | dermoscopic | 1.000 |
| underexposed_transformed.jpg | clinical_macroscopic | 0.970 |
| document_text_like.jpg | clinical_macroscopic | 0.968 |

**Key caveats:**

- The 15 fixtures are programmatic and controlled; they do not represent the full distribution of real-world unsupported images.
- "Unsupported" in production can mean anything (screenshots, X-rays, food photos, text images, non-skin photos). More real OOD data is needed before claiming robust rejection.
- Three of the four false accepts exceed 0.95 confidence and cannot be stopped by threshold alone.
- The random_noise false accept (confidence 1.000) is structurally indistinguishable from a valid dermoscopic image by the current classifier.

---

## 6. Decision

**Decision: soft-gating candidate only / needs more data**

| Criterion | Status |
|---|---|
| Distinguishes clinical vs dermoscopic (in-distribution) | Strong (macro-F1 0.9995) |
| Rejects clearly malformed images | Adequate (9/9 tested) |
| Rejects real-world unsupported images | Insufficient evidence |
| Safe for silent automatic routing | **No** |
| Safe as user-facing confirmation gate | Candidate, with caveats |

The model is strong at distinguishing the two supported modalities within the current dataset distribution. It is not robust enough to silently route all uploads without user confirmation. One in-distribution misclassification exceeds the highest tested threshold, and 27% of OOD test fixtures are incorrectly accepted. It should not be used as a hard gate without user confirmation.

It can be used later as a soft warning and confirmation layer if scoped carefully, after additional real-world OOD validation data is collected.

---

## 7. Recommended Future Integration Behavior

If D7.12 is created, it should implement this flow only:

1. Run PIL validation first. If rejected → show unsupported/invalid upload warning; stop.
2. Run the classifier.
3. If `confidence < 0.90` → ask the user to confirm the image type before proceeding.
4. If `confidence >= 0.90` and detected type matches selected mode → allow normal flow.
5. If `confidence >= 0.90` and detected type conflicts with selected mode → **warn the user and ask for confirmation before switching route**. Do not auto-switch.
6. Preserve manual user control at all times. Do not silently auto-route.

---

## 8. Required User-Facing Wording

**Allowed:**

- "This image appears to be a clinical/macroscopic photo."
- "This image appears to be a dermoscopic or magnified lesion image."
- "Revela could not confidently determine the image type."
- "Please confirm the image type or upload a supported image."

**Avoid:** diagnosis, cancer detected, safe, confirmed, clinical decision, treatment, clinically validated.

---

## 9. Follow-Up Tasks

**Create separately (after this recommendation):**

> **D7.12 — Integrate image-type classifier as soft modality warning and confirmation gate**

Scope for D7.12:

- Integrate artifact loading for the image-type classifier only after artifacts are included in the model hosting plan.
- Run PIL validation checks before classifier inference.
- Show warning and request user confirmation when detected modality conflicts with the selected mode.
- Ask confirmation before any route switch; never switch silently.
- Preserve manual user control.
- No silent auto-routing.

**Future improvements before or alongside D7.12:**

- Collect real OOD/unsupported validation data (non-skin photos, screenshots, X-rays, etc.).
- Add cross-source dermoscopic evaluation to de-risk BCN20000 shortcut.
- Improve validation heuristics to catch synthetic/document/noise false accepts (e.g., edge detection, frequency analysis).
- Consider a separate lightweight OOD detector if false-accept rate remains high.

---

## 10. Safety Statement

This classifier predicts image modality only, not disease or risk. It does not provide diagnosis or treatment guidance. `uncertain_or_unsupported` is a product-level routing state, not a clinical output.
