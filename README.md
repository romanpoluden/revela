# Revela

Revela is an educational dermatology AI training prototype. It is designed for learning, demonstration, and discussion about AI-assisted dermatology workflows.

Revela is not a medical device and is not intended to provide diagnosis, treatment advice, clinical decision support, triage, referral guidance, biopsy guidance, or any patient-care directive.

## Live Demo

The current demo frontend is available at:

- https://revela-sage.vercel.app/

## Current Architecture

The production/demo app is a React/Vite frontend in:

- `frontend/`

The frontend is deployed on Vercel and can optionally call a Hugging Face FastAPI inference backend for live model responses.

The Hugging Face backend is available at:

- https://revelacap-revela-inference-backend.hf.space

Backend health endpoint:

- https://revelacap-revela-inference-backend.hf.space/health

Supported backend model IDs:

- `clinical_skin_condition_v1`
- `dermoscopic_cancer_risk_bcn_mnh_v1`

If live inference is not configured, the frontend uses demo/mock mode.

## Run The Frontend Locally

From the repository root:

```bash
cd frontend
npm install
npm run dev
```

Then open:

- http://127.0.0.1:3000

## Optional Live Inference

To point the local Vite frontend at the hosted Hugging Face backend, configure:

```env
VITE_REVELA_INFERENCE_BACKEND_URL=https://revelacap-revela-inference-backend.hf.space
VITE_REVELA_ENABLE_LIVE_INFERENCE=true
```

Without these environment variables, the frontend remains in demo/mock mode.

## Legacy Streamlit App

The earlier Streamlit interface is kept in the repository as legacy/reference material. It is not the production frontend for the current Vercel demo.

## Contribution Workflow

Use a safe, scoped workflow:

1. Create a new branch from the latest `main`.
2. Keep frontend, backend, and model changes scoped to the area being updated.
3. Run the relevant checks before opening a pull request.
4. Open a pull request with a concise summary of the change and any testing performed.

Keep README and product language presentation-safe and educational-only. Do not overstate validation, fairness, clinical readiness, safety, or real-world deployment suitability.
