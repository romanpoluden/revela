# Image-Type Classifier Hugging Face Hosting

**Related issue:** #219  
**Source task:** #199  
**Status:** Planned / pending upload  
**Recommended Hugging Face repo:** `RevelaCap/image-type-classifier-v1`

---

## Purpose

This document describes how to host the Revela image-type classifier artifacts on Hugging Face and how to restore them into the local project structure.

The image-type classifier predicts upload modality only:

- `clinical_macroscopic`
- `dermoscopic`

It does **not** predict disease, cancer risk, treatment, clinical severity, or diagnosis.

The final recommendation from #199 remains:

```text
soft-gating candidate only / needs more data
```

The classifier is not approved for silent automatic routing. If integrated later, it should only support user-facing warning and confirmation behavior.

---

## Local Artifact Source

Expected local artifact folder:

```text
models/image_type_classifier_v1/
```

Expected required files:

```text
best_model.pth
class_to_idx.json
training_config.json
training_history.csv
training_metrics.json
```

Optional files, only if safe to share and free of private/local absolute paths:

```text
train.csv
val.csv
test.csv
```

Do not upload raw datasets or raw images.

---

## Hugging Face Repository

Recommended repository:

```text
https://huggingface.co/RevelaCap/image-type-classifier-v1
```

This should be separate from the clinical and dermoscopic disease-model artifact repositories because this model is a modality/routing-support classifier, not a disease classifier.

---

## Recommended Upload Commands

Run from the repository root on the machine that contains `models/image_type_classifier_v1/`:

```bash
huggingface-cli login

huggingface-cli repo create image-type-classifier-v1 \
  --organization RevelaCap \
  --type model

huggingface-cli upload RevelaCap/image-type-classifier-v1 \
  models/image_type_classifier_v1 \
  . \
  --include "best_model.pth" \
  --include "class_to_idx.json" \
  --include "training_config.json" \
  --include "training_history.csv" \
  --include "training_metrics.json"
```

If `train.csv`, `val.csv`, and `test.csv` are verified to contain no private/local absolute paths, they may be uploaded separately:

```bash
huggingface-cli upload RevelaCap/image-type-classifier-v1 \
  models/image_type_classifier_v1 \
  . \
  --include "train.csv" \
  --include "val.csv" \
  --include "test.csv"
```

---

## Model Card Content

The Hugging Face `README.md` must state:

- This is an educational prototype artifact.
- The model predicts image modality only.
- It does not predict disease, cancer risk, diagnosis, treatment, or clinical severity.
- It must not be used for patient care, clinical decision-making, diagnosis, or treatment recommendations.
- Final recommendation: `soft-gating candidate only / needs more data`.
- It is not safe for silent automatic routing.
- If integrated, it should only support user-facing warning and confirmation behavior.
- Recommended confidence threshold: `0.90`.
- Known OOD / unsupported-image limitations are material and must be disclosed.

Suggested model-card text:

```markdown
# Revela Image-Type Classifier v1

## Purpose

This model predicts whether an uploaded image appears to be one of Revela's supported input modalities:

- `clinical_macroscopic`
- `dermoscopic`

It is intended for educational app routing support only.

## Not a Disease Model

This model does not predict disease, cancer risk, diagnosis, treatment, or clinical severity.

It must not be used for diagnosis, patient care, clinical decision-making, or treatment recommendations.

## Intended Use

The model may be used as a soft warning / confirmation layer before running Revela's educational disease-model flows.

Recommended behavior:

- If the image type matches the selected flow, allow normal analysis.
- If the image type conflicts with the selected flow, warn the user and ask for confirmation.
- If the model is uncertain, ask the user to confirm or upload a supported image.
- Never silently auto-route or switch models.

## Classes

| Index | Label |
|---:|---|
| 0 | clinical_macroscopic |
| 1 | dermoscopic |

## Recommended Threshold

Default confidence threshold: `0.90`.

This threshold is not sufficient for silent routing. User confirmation is still required for mismatch cases.

## Evaluation Summary

Held-out supported-modality test split:

- Accuracy: 0.9995
- Macro-F1: 0.9995
- Balanced accuracy: 0.9993
- False clinical → dermoscopic: 2
- False dermoscopic → clinical: 0

OOD/problematic fixture test at threshold 0.90:

- Total rejected: 11 / 15
- False accepts: 4 / 15

## Final Recommendation

Soft-gating candidate only / needs more data.

The model is not ready for silent automatic routing. It may be integrated only as a user-facing warning and confirmation gate.

## Known Risks

- Source shortcut risk: all dermoscopic examples came from BCN20000.
- Unsupported/OOD validation set is small and synthetic/programmatic.
- Confidence thresholding alone cannot catch all wrong-modality or unsupported uploads.
- Some unsupported fixtures were accepted with high confidence.

## Safety Statement

This classifier predicts image modality only. It does not provide diagnosis, treatment guidance, cancer detection, or clinical validation.
```

---

## Restore / Download Verification

After upload, verify restore into a clean temporary folder:

```bash
mkdir -p /tmp/revela_image_type_test

huggingface-cli download RevelaCap/image-type-classifier-v1 \
  best_model.pth class_to_idx.json training_config.json training_history.csv training_metrics.json \
  --local-dir /tmp/revela_image_type_test

ls -lh /tmp/revela_image_type_test
```

Compare hashes:

```bash
shasum -a 256 models/image_type_classifier_v1/best_model.pth
shasum -a 256 /tmp/revela_image_type_test/best_model.pth

shasum -a 256 models/image_type_classifier_v1/class_to_idx.json
shasum -a 256 /tmp/revela_image_type_test/class_to_idx.json
```

The local and restored hashes should match.

---

## Deployment / Integration Notes

Hosting this artifact does not change current Streamlit behavior.

If the team later integrates the classifier into Streamlit, the follow-up task is #207. That integration must preserve these constraints:

- no silent automatic routing;
- no disease-model behavior change;
- no disease taxonomy change;
- no diagnosis, treatment, clinical-readiness, or patient-use claims;
- user confirmation required for mismatch or uncertainty cases.

If runtime loading is required, #204 or a follow-up extension should add this model to the artifact resolver only after the Hugging Face repo exists and restore has been verified.

---

## Current Completion Checklist

- [ ] Hugging Face repo created: `RevelaCap/image-type-classifier-v1`
- [ ] Required artifacts uploaded
- [ ] Hugging Face model card added
- [ ] Download/restore command verified
- [ ] Local/restored hashes compared
- [ ] #219 updated with uploaded file list and verification result

---

## Safety Statement

This artifact supports modality checking only. It is not a diagnostic model and does not provide clinical or treatment guidance. Any future product use must frame the output as image-type confidence for educational workflow support, not as medical evidence.
