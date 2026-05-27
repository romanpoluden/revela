# Hugging Face FastAPI Backend Space

**Related issue:** #223  
**Architecture parent:** #222  
**Target Space:** `RevelaCap/revela-inference-backend`  
**SDK:** Docker  
**Backend:** FastAPI  
**Hardware target:** CPU Basic / free tier

---

## Purpose

This backend serves Revela model inference remotely on Hugging Face while Streamlit remains the public frontend.

Primary demo flow:

```text
User uploads image in Streamlit
  -> Streamlit sends image + model_id + top_k to HF backend
  -> FastAPI backend loads/runs the correct PyTorch model
  -> backend returns canonical Revela JSON
  -> Streamlit renders educational result and prompt export
```

---

## Repo-side Space Scaffold

The Space files are staged inside the main repository at:

```text
spaces/revela-inference-backend/
```

Files:

```text
README.md
Dockerfile
requirements.txt
app.py
```

These files should be copied/pushed to the Hugging Face Space repo:

```text
RevelaCap/revela-inference-backend
```

---

## Endpoints

### Health

```text
GET /health
```

Returns:

- backend status;
- version;
- device;
- supported model IDs;
- currently loaded model IDs.

### Predict

```text
POST /predict
```

Multipart form fields:

- `model_id`: `clinical_skin_condition_v1` or `dermoscopic_cancer_risk_bcn_mnh_v1`
- `top_k`: optional integer
- `image`: uploaded image file

Returns the Revela canonical response shape used by the current frontend.

---

## Supported Model IDs

```text
clinical_skin_condition_v1
dermoscopic_cancer_risk_bcn_mnh_v1
```

Model artifacts are loaded from:

```text
RevelaCap/clinical-skin-condition-v1
RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1
```

---

## Free-Tier Constraint

Use only CPU Basic / free-tier hardware for the capstone demo unless the team explicitly re-approves scope.

Expected limitations:

- cold starts after inactivity;
- CPU-only inference;
- latency may be slower on first request because model artifacts must be downloaded/loaded.

Mitigation:

- warm `/health` and one `/predict` request before the final demo.

---

## Local Backend Test

From the Space scaffold folder:

```bash
cd spaces/revela-inference-backend
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

Health check:

```bash
curl http://localhost:7860/health
```

Prediction smoke test:

```bash
curl -X POST http://localhost:7860/predict \
  -F "model_id=clinical_skin_condition_v1" \
  -F "top_k=3" \
  -F "image=@/path/to/clinical_or_fixture_image.jpg"
```

Dermoscopic smoke test:

```bash
curl -X POST http://localhost:7860/predict \
  -F "model_id=dermoscopic_cancer_risk_bcn_mnh_v1" \
  -F "top_k=4" \
  -F "image=@/path/to/dermoscopic_or_fixture_image.jpg"
```

---

## Hugging Face Space Setup

If the Space does not exist yet, create it in the Hugging Face UI or with CLI.

Suggested target:

```text
Owner: RevelaCap
Name: revela-inference-backend
SDK: Docker
Hardware: CPU Basic / free
Visibility: public or private depending on demo needs
```

Then push the contents of:

```text
spaces/revela-inference-backend/
```

to the Space repository.

---

## Safety Boundaries

This backend:

- does not make diagnosis;
- does not recommend treatment;
- does not claim clinical readiness;
- does not call an LLM;
- does not change model weights;
- does not change disease taxonomies.

It returns educational prototype model output only.
