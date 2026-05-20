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

The selected BCN+MNH model is documented by the D4.5 config and notebooks as the improved dermoscopic model, not the older 3-class smoke-test baseline. In this local checkout, the selected artifact directory is currently unavailable, so the required files could not be confirmed on disk:

- `best_model.pth`: missing
- `class_to_idx.json`: missing
- `training_history.csv`: missing

Because `class_to_idx.json` is missing locally, class names could not be read from the artifact. The expected taxonomy from `config/bcn_mnh_cancer_risk_config.yaml` is:

1. `Melanoma`
2. `Non-melanoma skin cancer`
3. `Benign nevus`
4. `Other non-cancer / indeterminate lesion`

No taxonomy mismatch can be confirmed until the artifact `class_to_idx.json` is present.

## Smoke Test

- Smoke-test image path: `data/raw/bcn20000/images/ISIC_0061284.jpg`
- Smoke-test command:

```bash
.venv/bin/python - <<'PY'
from src.inference.adapter import run_inference

response = run_inference(
    model_id="dermoscopic_cancer_risk_bcn_mnh_v1",
    image_input="data/raw/bcn20000/images/ISIC_0061284.jpg",
    top_k=4,
)
print(response)
PY
```

- Smoke-test result summary: the adapter returned a safe error response because the selected model artifacts are missing locally.
- Error code: `missing_model_artifact`
- Error message: `A required model artifact or input file could not be found.`

A successful inference response should be re-run after restoring the selected artifact directory. At that point, confirm the response contains `model_id`, `input_type`, `architecture`, `image_size`, `predictions`, `top_prediction`, `uncertainty`, `safety_note`, `model_limitations`, and `recommended_next_step`, and confirm `input_type` is `dermoscopic`.

## Scope Confirmation

- `app.py` was not changed.
- Clinical registry entries were not changed.
- Clinical inference behavior was not changed.
- No training was run.
- Dermoscopic mode was not enabled in Streamlit.
- The existing older dermoscopic registry entries were kept.
