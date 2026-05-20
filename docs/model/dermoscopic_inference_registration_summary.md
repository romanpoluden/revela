# Dermoscopic Inference Registration Summary

Issue: #163

This is educational, non-diagnostic inference plumbing work. It does not enable dermoscopic mode in Streamlit and does not make clinical-readiness or diagnostic claims.

## Registered Model

- Selected model ID: `dermoscopic_cancer_risk_bcn_mnh_v1`
- Selected model directory: `models/bcn_mnh_cancer_risk_effnet_b0/`
- Selected config path: `config/bcn_mnh_cancer_risk_config.yaml`
- Input type: `dermoscopic`
- Architecture: `efficientnet_b0`
- Number of classes: `4`
- Image size: `224`
- Checkpoint path: `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth`
- Class mapping path: `models/bcn_mnh_cancer_risk_effnet_b0/class_to_idx.json`

## Artifact Availability

The selected BCN+MNH model is documented by the D4.5 config and notebooks as the improved dermoscopic model, not the older 3-class smoke-test baseline. Artifacts are provided through GitHub release tag `bcn-mnh-v1-artifacts`.

Expected local artifact paths:

- `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth`
- `models/bcn_mnh_cancer_risk_effnet_b0/class_to_idx.json`
- `models/bcn_mnh_cancer_risk_effnet_b0/training_history.csv`

Local artifact verification passed.

Class names from the registered BCN+MNH taxonomy:

1. `Melanoma`
2. `Non-melanoma skin cancer`
3. `Benign nevus`
4. `Other non-cancer / indeterminate lesion`

## Smoke Test

- Smoke-test image path: `data/raw/bcn20000/images/ISIC_0058528.jpg`
- Smoke-test command:

```bash
.venv/bin/python -m src.inference.adapter --model-id dermoscopic_cancer_risk_bcn_mnh_v1 --image data/raw/bcn20000/images/ISIC_0058528.jpg --top-k 4
```

- Smoke-test result summary: passed.
- `model_id`: `dermoscopic_cancer_risk_bcn_mnh_v1`
- `input_type`: `dermoscopic`
- `architecture`: `efficientnet_b0`
- `image_size`: `224`
- Top-k returned `4` classes.
- Sample top prediction: `Melanoma`, `38.57%` model confidence.
- Uncertainty bucket: `low_confidence`
- `low_certainty`: `true`
- Low-certainty fields are present.
- Safety note and limitations are present.
- No diagnosis or treatment claims are made.

Invalid-image check returned a structured safe error:

- `error_code`: `invalid_image`
- `message`: `The provided image input could not be read as a valid image.`

Syntax check passed:

```bash
python -m py_compile src/inference/model_registry.py src/inference/adapter.py src/inference/predict.py src/inference/response_schema.py src/inference/uncertainty.py
```

## Scope Confirmation

- `app.py` was not changed.
- Clinical registry entries were not changed.
- Clinical inference behavior was not changed.
- No training was run.
- Dermoscopic mode was not enabled in Streamlit.
- The existing older dermoscopic registry entries were kept.
