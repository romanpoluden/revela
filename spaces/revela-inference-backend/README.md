---
title: Revela Inference Backend
emoji: 🔬
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
license: mit
---

# Revela Inference Backend

FastAPI backend for the Revela capstone demo.

## Purpose

This Space is intended to run Revela model inference remotely on Hugging Face CPU Basic free tier while Streamlit acts as the public frontend.

Primary flow:

```text
Streamlit frontend -> FastAPI /predict -> PyTorch inference -> canonical JSON response -> Streamlit rendering
```

## Scope

- Educational prototype only.
- Not a diagnostic system.
- Not for clinical decision-making or treatment recommendations.
- CPU Basic free-tier target only.

## Endpoints

- `GET /health` — backend status and loaded model IDs.
- `POST /predict` — multipart image upload plus `model_id` and `top_k`.

Supported `model_id` values:

- `clinical_skin_condition_v1`
- `dermoscopic_cancer_risk_bcn_mnh_v1`

## Notes

The backend downloads hosted model artifacts from Hugging Face model repositories when local files are missing and runs local PyTorch inference inside the Space container.
