# Revela — Final Demo Deployment Guide

> **Issue:** #225  
> **Branch:** `d9-3-final-deployment-docs`  
> **Status:** ✅ Production-ready for demo  
> **Last updated:** 2026-05-27

---

## 1. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│             Streamlit Frontend  (app.py)                     │
│  • User uploads clinical or dermoscopic image                │
│  • Collects learner-context metadata                         │
│  • Calls remote backend via src/inference/remote_client.py   │
└────────────────────────┬─────────────────────────────────────┘
                         │  HTTP POST multipart/form-data
                         │  REVELA_INFERENCE_BACKEND_URL
                         │  (default: https://revelacap-revela-inference-backend.hf.space)
                         ▼
┌──────────────────────────────────────────────────────────────┐
│   FastAPI Inference Backend                                  │
│   Hugging Face Space: RevelaCap/revela-inference-backend     │
│   Runtime: Docker / CPU Basic (free tier)                    │
│                                                              │
│   GET  /health   → status, version, loaded model IDs        │
│   POST /predict  → {model_id, top_k, image}                  │
│         ├─ downloads model artifacts from HF Hub on demand  │
│         ├─ caches to /tmp/revela_models                     │
│         ├─ runs EfficientNet-B0 inference (CPU)              │
│         └─ returns canonical Revela JSON                    │
└────────────────────────┬─────────────────────────────────────┘
                         │  Canonical JSON response
                         ▼
┌──────────────────────────────────────────────────────────────┐
│             Streamlit Renders Results                        │
│  • Top-k predictions with confidence percentages            │
│  • Uncertainty bucket + explanation                         │
│  • Low-certainty flag when top confidence < 60 %            │
│  • Educational safety note and next-step recommendation     │
│  • LLM learning-prompt export                               │
└──────────────────────────────────────────────────────────────┘

Model Artifact Repos (Hugging Face Hub)
  RevelaCap/clinical-skin-condition-v1
  RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1
```

---

## 2. Backend Space

| Property | Value |
|---|---|
| HF Space | <https://huggingface.co/spaces/RevelaCap/revela-inference-backend> |
| Live base URL | `https://revelacap-revela-inference-backend.hf.space` |
| Runtime | HF Docker / CPU Basic (free tier) |
| Backend version | `d9.1-hf-fastapi-backend-v1` |
| Container port | `7860` |

---

## 3. Streamlit Frontend Config

The Streamlit app reads a single environment variable to locate the backend:

```
REVELA_INFERENCE_BACKEND_URL=https://revelacap-revela-inference-backend.hf.space
```

**Default** (no env var needed in normal operation):

```python
# src/inference/remote_client.py
DEFAULT_BACKEND_URL = "https://revelacap-revela-inference-backend.hf.space"

def get_backend_url() -> str:
    return os.getenv("REVELA_INFERENCE_BACKEND_URL", DEFAULT_BACKEND_URL).rstrip("/")
```

**To override** (e.g. point at a staging backend or local dev server):

```bash
export REVELA_INFERENCE_BACKEND_URL=http://localhost:8000
streamlit run app.py
```

No other configuration changes are needed in `app.py`.

---

## 4. API Endpoints

### 4.1 Health check

```bash
curl https://revelacap-revela-inference-backend.hf.space/health
```

Example response:

```json
{
  "status": "ok",
  "version": "d9.1-hf-fastapi-backend-v1",
  "device": "cpu",
  "supported_model_ids": [
    "clinical_skin_condition_v1",
    "dermoscopic_cancer_risk_bcn_mnh_v1"
  ],
  "loaded_model_ids": ["dermoscopic_cancer_risk_bcn_mnh_v1"]
}
```

### 4.2 Predict

```bash
curl -X POST https://revelacap-revela-inference-backend.hf.space/predict \
  -F "model_id=dermoscopic_cancer_risk_bcn_mnh_v1" \
  -F "top_k=4" \
  -F "image=@/path/to/dermoscopy.jpg"
```

```bash
# Clinical model
curl -X POST https://revelacap-revela-inference-backend.hf.space/predict \
  -F "model_id=clinical_skin_condition_v1" \
  -F "top_k=3" \
  -F "image=@/path/to/clinical_photo.jpg"
```

Fields:

| Field | Type | Required | Notes |
|---|---|---|---|
| `model_id` | string | ✅ | See §5 |
| `top_k` | int | ✅ | See §5 for defaults/limits |
| `image` | file | ✅ | JPEG / PNG, any resolution |

---

## 5. Supported Model IDs

| `model_id` | Image type | Default `top_k` | Max `top_k` | Architecture |
|---|---|---|---|---|
| `clinical_skin_condition_v1` | Clinical photo | 3 | 5 | EfficientNet-B0 (224 × 224) |
| `dermoscopic_cancer_risk_bcn_mnh_v1` | Dermoscopic image | 4 | 4 | EfficientNet-B0 (224 × 224) |

**Output classes**

`clinical_skin_condition_v1`:
- Eczema / dermatitis
- Urticaria / allergic reaction
- Folliculitis / acne-like
- Psoriasis / papulosquamous
- Lesion — dermoscopic review recommended

`dermoscopic_cancer_risk_bcn_mnh_v1`:
- Melanoma
- Non-melanoma skin cancer
- Benign nevus
- Other non-cancer / indeterminate lesion

---

## 6. Canonical Response Contract

Every `/predict` response follows this shape:

```jsonc
{
  "model_id": "dermoscopic_cancer_risk_bcn_mnh_v1",
  "model_name": "...",
  "input_type": "dermoscopic",
  "architecture": "efficientnet_b0",
  "image_size": 224,

  // Ranked predictions
  "predictions": [
    {
      "rank": 1,
      "class_index": 0,
      "label": "Melanoma",
      "confidence": 0.72,
      "confidence_percent": "72.0%"
    }
    // … up to top_k entries
  ],

  // Convenience alias for predictions[0]
  "top_prediction": { /* same shape as one predictions entry */ },

  // Uncertainty summary
  "uncertainty": {
    "bucket": "moderate_confidence",   // low_confidence | moderate_confidence | high_confidence
    "confidence": 0.72,
    "confidence_percent": "72.0%",
    "label": "Melanoma",
    "explanation": "..."
  },

  // Low-certainty flag (true when top confidence < 0.60 or bucket == low_confidence)
  "low_certainty": false,
  "low_certainty_reason": null,
  "low_certainty_message": null,
  "low_certainty_rule": null,
  "low_certainty_threshold": 0.60,

  // Safety metadata
  "safety_note": "Educational prototype only …",
  "model_limitations": "...",
  "recommended_next_step": "..."
}
```

Consumers should treat `low_certainty: true` as a signal to surface additional disclaimers in the UI.

---

## 7. Model Artifact Source Repos

| Model ID | HF Hub repo | Key files |
|---|---|---|
| `clinical_skin_condition_v1` | `RevelaCap/clinical-skin-condition-v1` | `best_model.pth`, `class_to_idx.json`, `training_history.csv` |
| `dermoscopic_cancer_risk_bcn_mnh_v1` | `RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1` | `best_model.pth`, `class_to_idx.json`, `training_history.csv` |

The backend downloads artifacts on first use and caches them to `/tmp/revela_models` inside the Space container. The cache is ephemeral: it resets on each cold start.

---

## 8. Local / Dev Fallback

The primary path for development and local testing is documented separately in:

```
docs/deployment/huggingface_runtime_artifact_loading.md
```

That document covers:
- Loading model artifacts from `models/{name}/` on disk
- Automatic HF Hub download when local files are absent
- Required files (`best_model.pth`, `class_to_idx.json`) and optional files (`training_history.csv`)

For a lightweight local backend that mirrors the production Space, run:

```bash
cd spaces/revela-inference-backend
uvicorn app:app --host 0.0.0.0 --port 8000
```

Then set:

```bash
export REVELA_INFERENCE_BACKEND_URL=http://localhost:8000
```

---

## 9. Free-Tier Caveats

The backend runs on **Hugging Face CPU Basic (free tier)**.

| Caveat | Impact |
|---|---|
| **Cold starts** | Space sleeps after ~15 min of inactivity. First request after sleep takes 60–120 s while the container restarts and model artifacts re-download. |
| **CPU-only inference** | No GPU acceleration. Single image inference typically takes 1–4 s after warm-up. |
| **Ephemeral `/tmp`** | Model weights cached in `/tmp/revela_models` are lost on every cold start; re-download is automatic but adds latency. |
| **No SLA** | Free-tier Spaces have no uptime guarantee. |
| **Single worker** | Concurrent requests queue behind one another. |

---

## 10. Demo Warm-Up Checklist

Run these steps **at least 5 minutes before** the live demo:

- [ ] Open the HF Space: <https://huggingface.co/spaces/RevelaCap/revela-inference-backend>
  - Confirm the Space shows **Running** (green dot), not *Building* or *Sleeping*.
- [ ] Hit the health endpoint:
  ```bash
  curl https://revelacap-revela-inference-backend.hf.space/health
  ```
  Expected: `"status": "ok"`
- [ ] Send one warm-up inference for each model (wakes the model into memory):
  ```bash
  curl -X POST https://revelacap-revela-inference-backend.hf.space/predict \
    -F "model_id=clinical_skin_condition_v1" -F "top_k=3" -F "image=@<any_jpg>"

  curl -X POST https://revelacap-revela-inference-backend.hf.space/predict \
    -F "model_id=dermoscopic_cancer_risk_bcn_mnh_v1" -F "top_k=4" -F "image=@<any_jpg>"
  ```
- [ ] Open the Streamlit app and run one end-to-end inference per model tab.
- [ ] Verify results render correctly (predictions list, uncertainty bucket, safety note).
- [ ] Confirm no `low_certainty` false-positive on the sample images you plan to demo.

---

## 11. Safety Boundaries

> **This is an educational prototype. It is not a medical device.**

- Predictions are **not diagnoses**. They are illustrative outputs for learning purposes only.
- The app must **not** be used to guide treatment decisions, triage, or clinical workflows.
- Every response from the backend includes a `safety_note` field and `recommended_next_step`. The Streamlit UI surfaces both.
- The dermoscopic model was trained on BCN20000 + MNH data. Test-set melanoma recall is ~61 %. It will miss lesions.
- The clinical model covers 5 coarse categories; many real conditions fall outside these classes.
- Always present the app under explicit supervision of a qualified clinician when used with real patient images.

---

## 12. Completed Task Chain

| Issue | Title | Status |
|---|---|---|
| #222 | Approve final architecture: Streamlit → HF FastAPI backend | ✅ Approved |
| #223 | Create and deploy HF inference backend Space | ✅ Deployed |
| #224 | Update Streamlit to call remote backend | ✅ Merged |
| #225 | Final deployment documentation (this document) | ✅ Done |

---

## 13. Future / Optional Work

### #207 — Image-Modality Soft Gate

A classifier that detects whether an uploaded image matches the expected modality (clinical vs. dermoscopic) before routing it to a model.

- **Status:** Future / optional — not in scope for the current demo.
- **Trigger:** Promote to active only if the team decides to handle accidental wrong-modality uploads more gracefully than the current user-instruction approach.
- **Integration point:** `src/inference/remote_client.py` or a pre-call check in `app.py` before `run_remote_inference`.
- **No backend changes required** for a client-side soft gate; a separate HF endpoint would be needed for a server-side gate.

---

*For questions about the deployment, see the related docs:*
- [`docs/deployment/hf_fastapi_backend_space.md`](hf_fastapi_backend_space.md) — backend Space spec
- [`docs/deployment/huggingface_runtime_artifact_loading.md`](huggingface_runtime_artifact_loading.md) — local/dev artifact loading
