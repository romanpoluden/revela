# D7.1 — v0 UI Prototype Audit and Integration Plan

**Ticket:** #181  
**Branch:** d7-v0-ui-inference-integration  
**Date:** 2026-05-22  
**Status:** Planning only — no implementation in this ticket

---

## 1. Executive Recommendation

### Recommendation: Hybrid architecture — keep Streamlit, add Next.js separately

Do not replace Streamlit. It is working, safe, and already demonstrates the two-model inference correctly. The risk of breaking the demo is not justified in a single sprint.

Instead, create a standalone `frontend/` directory copied from the v0 prototype and build a thin Python API wrapper around the existing inference. The two apps coexist on the branch. Streamlit remains the authoritative demo until the Next.js flow is end-to-end verified.

**Safest path for this sprint (D7):**

1. Port the v0 UI shell into `frontend/` — structure and component layout, no new logic.
2. Build a minimal FastAPI wrapper exposing the existing inference pipeline.
3. Wire the frontend to the API so a real image produces a real prediction.
4. Update the UI copy to remove unsafe practitioner/diagnostic wording.
5. Verify dual upload (clinical + dermoscopic) matches the existing Streamlit flow.

Do not remove Streamlit. Do not merge to main until the new flow is fully verified.

---

## 2. Current Revela State

### Streamlit app (`app.py`)

Six-tab application:

| Tab | Content |
|-----|---------|
| Overview | Product description, build status cards |
| Analyze Image | Main inference UI — two image modes, upload, result |
| Model Transparency | Model roles, taxonomies, registry |
| Evaluation Metrics | Prototype held-out metrics |
| Benchmark | Placeholder |
| About / Limitations | Full disclaimer list |

**Image upload flow:**

1. User selects mode: *Clinical photo* or *Dermoscopic image*
2. Single file upload (JPG, JPEG, PNG, WEBP)
3. Metadata display (name, type, size, dimensions)
4. "Analyze case" triggers inference
5. Spinner: *"Preparing educational image review..."*
6. Result rendered: top prediction, confidence, uncertainty bucket, top-k list, safety note, limitations, recommended next step

**Two-model inference:**

| Model ID | Input type | Top-k | Classes |
|----------|-----------|-------|---------|
| `clinical_skin_condition_v1` | Clinical photo | 3 | 5 (eczema, urticaria, folliculitis, psoriasis, lesion-routing) |
| `dermoscopic_cancer_risk_bcn_mnh_v1` | Dermoscopic image | 4 | 4 (melanoma, non-melanoma, benign nevus, indeterminate) |

**Inference pipeline (`src/inference/`):**

- `adapter.py` — public entry point: `run_inference(model_id, image_input, top_k, device, debug)`
- `predict.py` — loads model from registry, transforms image, runs forward pass
- `model_loader.py` — EfficientNet-B0, device selection, `class_to_idx.json`
- `postprocess.py` — ranked top-k list
- `uncertainty.py` — 3-bucket system (high ≥ 0.70 / medium 0.40–0.70 / low < 0.40), low-certainty flag at 0.60
- `response_schema.py` — canonical response dict (success + error shapes)

**Canonical response schema (success):**

```json
{
  "model_id": "clinical_skin_condition_v1",
  "model_name": "...",
  "input_type": "clinical",
  "architecture": "efficientnet_b0",
  "image_size": 224,
  "predictions": [{"rank": 1, "class_index": 0, "label": "...", "confidence": 0.72, "confidence_percent": 72.0}, ...],
  "top_prediction": {...},
  "uncertainty": {"bucket": "high_confidence", "label": "...", "explanation": "..."},
  "low_certainty": false,
  "low_certainty_reason": null,
  "low_certainty_message": null,
  "low_certainty_rule": "confidence < 0.60 or bucket = low_confidence",
  "low_certainty_threshold": 0.60,
  "safety_note": "Prototype educational output only. This response is not a diagnosis...",
  "model_limitations": ["Predictions are model outputs from a finite taxonomy, not clinical conclusions.", ...],
  "recommended_next_step": "Use this output as a prototype aid for review, not as a standalone medical decision."
}
```

**Error response:**

```json
{
  "error": true,
  "error_code": "inference_failed",
  "message": "...",
  "details": null
}
```

**Error codes:** `unknown_model_id`, `missing_model_artifact`, `invalid_image`, `invalid_input`, `inference_failed`, `postprocess_failed`

**Safety framing (enforced):**

- Revela is not a diagnostic product
- No treatment advice
- No clinical certainty claims
- Confidence = model confidence, not clinical certainty
- Clinical lesion-routing is NOT cancer detection
- `Other non-cancer / indeterminate lesion` must not be read as "safe"
- Low-certainty warning when confidence < 60%

---

## 3. v0 Prototype Audit

**Repository:** https://github.com/romanpoluden/v0-revela-dermatology-prototype  
**Framework:** Next.js (v16.2.4) + React 19.2.4 + TypeScript 5.7.3  
**Styling:** Tailwind CSS 4.2.0  
**UI primitives:** Radix UI (tabs, accordion, progress, badges, tooltips, radio groups, collapsible)  
**Forms:** React Hook Form + Zod  
**Charts:** Recharts 2.15.0

### Structure

```
app/
  page.tsx                      — 3-step orchestrator (Upload → Questions → Insights)
components/
  image-uploader.tsx            — drag-drop, quiz mode toggle, privacy note
  symptom-questionnaire.tsx     — 5-question form (duration, itching, pain, location, changes)
  analysis-display.tsx          — simple / detailed result views
  pipeline-visualizer.tsx       — 5-stage technical pipeline breakdown
  step-indicator.tsx            — progress indicator (3 steps)
  fairness-display.tsx          — skin tone selector, fairness card, metrics dashboard
  ui/                           — shadcn/Radix primitives
lib/
  reasoning-engine.ts           — mock analysis generator (returns StructuredAnalysis)
  pipeline/
    index.ts                    — mock 5-stage pipeline orchestration
    preprocessing.ts
    feature-extraction.ts
    classification.ts
    types.ts
  fairness/
    engine.ts                   — Fitzpatrick scale, simulated per-group metrics
    types.ts
    index.ts
```

### Reusable components (safe to port)

| Component | Reusability | Notes |
|-----------|------------|-------|
| `step-indicator.tsx` | High | Generic progress indicator, no domain logic |
| `image-uploader.tsx` | Medium | UI shell reusable; copy requires update; single-upload only |
| `symptom-questionnaire.tsx` | Low | Questionnaire is not part of current Revela flow |
| `analysis-display.tsx` | Medium | Layout and result sections reusable; must bind to real schema |
| `pipeline-visualizer.tsx` | Low | Displays mock stage data; would need real pipeline output |
| `fairness-display.tsx` | Low | Hardcoded mock metrics; useful for layout reference only |
| `ui/` (Radix primitives) | High | Drop-in accessible components |

### Mock / demo-only components

All analysis logic in `lib/` is entirely mock. No real API calls exist anywhere in the codebase.

| File | What is mocked |
|------|---------------|
| `lib/reasoning-engine.ts` | Generates ABCDE observations and differential from symptom answers only; no image model |
| `lib/pipeline/index.ts` | Simulates 5-stage pipeline with hardcoded outputs |
| `lib/fairness/engine.ts` | Returns hardcoded Fitzpatrick metrics (e.g., Type I: 94% AUROC); simulates skin tone detection |
| `components/fairness-display.tsx` | Metrics dashboard shows static numbers (56,300 samples, 91% avg AUROC) |

### Unsafe / outdated wording

The following copy must not be carried into the Revela product:

| Location | Unsafe text |
|----------|------------|
| `app/page.tsx` header | `"For Practitioners"` badge |
| `app/page.tsx` subtitle | `"AI-supported differential for educational review and clinical reasoning support"` |
| `image-uploader.tsx` | `"Upload a clinical image"` |
| `image-uploader.tsx` | `"AI-supported differential analysis"` |
| `image-uploader.tsx` | `"This is a secondary support tool for clinical reasoning"` |
| `image-uploader.tsx` quiz mode | `"Test your diagnostic reasoning before seeing AI predictions"` |
| `analysis-display.tsx` | `"Differential Considerations"` |
| `analysis-display.tsx` | `"Clinical Reasoning"` |
| `analysis-display.tsx` | `"Our confidence level"` (implies ownership/authority) |
| `pipeline-visualizer.tsx` | `"Clinical Interpretation"` |
| `fairness-display.tsx` | `"Average Accuracy: 91% AUROC"` (hardcoded, not from real model) |
| Footer | `"decision support"` |

### Dependencies / build requirements

```json
{
  "next": "16.2.4",
  "react": "19.2.4",
  "typescript": "5.7.3",
  "tailwindcss": "4.2.0",
  "@radix-ui/*": "various",
  "react-hook-form": "^7.x",
  "zod": "^3.x",
  "recharts": "2.15.0",
  "lucide-react": "0.564.0",
  "next-themes": "0.4.6",
  "sonner": "1.7.1",
  "@vercel/analytics": "1.6.1"
}
```

Requires: Node.js 18+, npm/yarn. No Python. Can run standalone with `npm run dev`.

---

## 4. Gap Analysis

| Dimension | v0 Prototype | Current Revela |
|-----------|-------------|----------------|
| **Image upload** | Single image, clinical only | Two modes: clinical photo OR dermoscopic image |
| **Questionnaire** | 5-question symptom form (required before analysis) | No symptom questionnaire — image-only |
| **Inference** | Fully mocked (symptom rules → fake differential) | Real EfficientNet-B0 inference via registry |
| **Model output schema** | Custom `StructuredAnalysis` / `PipelineOutput` TypeScript types | Canonical JSON schema (`response_schema.py`) |
| **Result display** | Differential with ABCDE observations, clinical features, diagnostic modifiers | Top-k ranked predictions, uncertainty bucket, low-certainty warning |
| **Pipeline view** | Mocked 5-stage breakdown (preprocessing → calibration) | No equivalent in Streamlit |
| **Fairness view** | Fitzpatrick scale selector + hardcoded group metrics | No equivalent in Streamlit |
| **API integration** | None — client-side only | Streamlit calls `run_inference()` directly in-process |
| **Copy / framing** | "For Practitioners", "clinical reasoning support", "differential" | "Educational training aid", "prototype educational output", no diagnosis claims |
| **Uncertainty** | "Confidence level: Good/Moderate/Low" | 3-bucket system (high/medium/low) + low_certainty flag with threshold at 0.60 |
| **Dermoscopic flow** | Not present | Full dermoscopic model (`dermoscopic_cancer_risk_bcn_mnh_v1`, top-4 output) |
| **Tech stack** | Next.js / TypeScript / Tailwind | Python / Streamlit / PyTorch |
| **Backend** | None | Python inference runs in-process |

### Critical gaps to close before launch

1. **Dual upload modes** — the frontend must support clinical vs. dermoscopic image selection, matching the Streamlit two-model flow.
2. **Real inference binding** — `analysis-display.tsx` must consume the canonical Python API response, not `StructuredAnalysis`.
3. **Copy cleanup** — practitioner/diagnostic wording must be replaced throughout before any user-facing demo.
4. **Dermoscopic model integration** — the v0 prototype has no dermoscopic flow; must be added.
5. **Symptom questionnaire scope decision** — the questionnaire is not part of current Revela flow; decide whether to include, defer, or remove.

---

## 5. Target Architecture

### This sprint (D7)

```
revela/
├── app.py                          ← UNTOUCHED — Streamlit fallback
├── src/inference/                  ← UNTOUCHED — Python inference
├── frontend/                       ← NEW — Next.js app copied from v0
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── api/                            ← NEW — Python API wrapper
│   └── main.py                     ← FastAPI app exposing /analyze endpoint
└── docs/frontend/                  ← NEW — this document
```

### Data flow

```
[Browser — Next.js frontend]
        |
        | POST /analyze  { model_id, image: base64 }
        v
[Python API — FastAPI api/main.py]
        |
        | run_inference(model_id, image_input, top_k)
        v
[Existing inference — src/inference/adapter.py]
        |
        | canonical response dict
        v
[Python API]
        |
        | JSON response (canonical schema)
        v
[Browser — analysis-display.tsx]
```

### Key constraints

- `app.py` is not modified.
- `src/inference/` is not modified.
- `src/model/`, `src/data/`, model registry, taxonomies, training scripts are not modified.
- The API is a thin wrapper only — no logic beyond calling `run_inference()` and serializing the response.
- The frontend receives the canonical response schema and maps it to UI components.

---

## 6. Implementation Sequence

### #182 — Port v0 UI shell

**Goal:** Copy v0 into `frontend/`, install dependencies, verify dev server starts.

Tasks:
- Copy v0 repo contents into `frontend/`
- Remove or stub `lib/reasoning-engine.ts`, `lib/pipeline/`, `lib/fairness/` (replace with API call stubs)
- Update all unsafe copy (see Section 7)
- Remove Vercel Analytics dependency (not needed for local dev)
- Verify `npm run dev` starts without errors
- Confirm 3-step flow renders (Upload → Questions or skip → Results placeholder)

**Out of scope:** Real inference, API, dual upload.

---

### #183 — Build Python inference API

**Goal:** FastAPI wrapper exposing `POST /analyze` that calls `run_inference()`.

Tasks:
- Create `api/main.py` with FastAPI
- Accept `{ model_id: str, image: str (base64), top_k: int }` 
- Decode base64 → PIL.Image, call `run_inference()`
- Return canonical response JSON as-is
- Add CORS headers (allow localhost:3000 for dev)
- Add `GET /health` endpoint
- Add `api/requirements.txt` (fastapi, uvicorn, pillow)
- Verify with `curl` or Postman against real model

**Out of scope:** Auth, rate limiting, image validation beyond what inference already does.

---

### #184 — Connect frontend to inference outputs

**Goal:** Replace mock analysis calls in Next.js with real API calls; render canonical schema.

Tasks:
- Remove `lib/reasoning-engine.ts` usage from `app/page.tsx`
- Add `lib/api-client.ts` — `analyzeImage(modelId, imageFile)` → fetch `POST /analyze`
- Update `analysis-display.tsx` to consume canonical schema fields:
  - `predictions` (ranked list) instead of `possibleExplanations`
  - `uncertainty.bucket` instead of confidence level string
  - `low_certainty` + `low_certainty_message` for warning panel
  - `safety_note`, `model_limitations`, `recommended_next_step` for disclaimer sections
- Remove all mock data generation from component state
- Verify end-to-end: upload real image → API call → real prediction rendered

**Out of scope:** Fairness display (mock metrics stay mocked or section is hidden).

---

### #185 — Update flow with dual upload and lesion-rating step

**Goal:** Add dermoscopic mode selection to the frontend, matching the two-model Streamlit flow.

Tasks:
- Add mode selector (Clinical photo / Dermoscopic image) before or during image upload step
- Map selected mode to `model_id`:
  - Clinical → `clinical_skin_condition_v1`, top_k=3
  - Dermoscopic → `dermoscopic_cancer_risk_bcn_mnh_v1`, top_k=4
- Add lesion-rating or dermoscopic-specific result framing (matching Streamlit's existing output)
- Ensure the lesion-routing output (`Lesion — dermoscopic review recommended`) in clinical model triggers appropriate UI message
- Decide on symptom questionnaire: include as optional, or remove for this sprint

---

## 7. Safety / Copy Changes Required

### Replace or avoid entirely

| v0 text | Replace with |
|---------|-------------|
| `"For Practitioners"` | Remove badge or replace with `"Educational Tool"` |
| `"AI-supported differential"` | `"Model output for structured review"` |
| `"clinical reasoning support"` | `"educational dermatology review"` |
| `"decision support"` | Remove |
| `"diagnosis"` / `"diagnostic"` | Remove or replace with `"model prediction"` |
| `"treatment guidance"` / `"next steps"` framed as clinical | Replace with `"Use this output as a prototype aid for review"` |
| `"Our confidence level: Good"` | `"Model confidence: [bucket label]"` |
| `"Differential Considerations"` | `"Top predictions"` or `"Model output"` |
| `"Clinical Reasoning"` | `"Why the model ranked this output"` |
| `"Clinical Interpretation"` | Remove or replace with `"Model feature observations"` |
| `"Secondary support tool for clinical reasoning"` | `"Educational training aid — not a diagnostic device"` |
| `"Test your diagnostic reasoning"` (quiz mode) | `"Review before seeing model output"` |
| `"average accuracy: 91% AUROC"` (hardcoded) | Display real metrics from `outputs/` or remove section |

### Use instead

- *Educational dermatology AI training aid*
- *Structured image review for learning*
- *Model output, not diagnosis*
- *Confidence is model confidence, not clinical certainty*
- *Qualified review required for real decisions*
- *Prototype educational output only*
- *This response is not a diagnosis and does not recommend treatment*

### Disclaimer placement

The following disclaimer must appear on every results view:

> "Prototype educational output only. This response is not a diagnosis and does not recommend treatment. Confidence is model confidence, not clinical certainty. Qualified review required for any real clinical decision."

This matches the canonical `safety_note` field in the inference response.

---

## 8. Risk Analysis

### Risk 1 — Breaking the Streamlit demo

**Likelihood:** Low (if constraint is followed)  
**Impact:** High (demo is the primary deliverable)  
**Mitigation:** `app.py` is explicitly out of scope. All D7 work is in `frontend/` and `api/`. No changes to `src/inference/`.

---

### Risk 2 — Over-scoping in 3 hours

**Likelihood:** Medium  
**Impact:** Medium (incomplete feature is worse than no feature)  
**Mitigation:** Tickets are sequenced so that each one is independently deliverable. #182 alone (UI shell, no API) is a valid stopping point. #183 alone (API, no frontend) is testable with curl. Do not start #185 until #184 is verified end-to-end.

---

### Risk 3 — Unsafe v0 wording copied into product

**Likelihood:** High (v0 copy permeates every component)  
**Impact:** High (regulatory and reputational risk)  
**Mitigation:** All copy changes are required before any user-facing demo. Section 7 provides an explicit replacement table. No PR to main until copy audit is complete.

---

### Risk 4 — Frontend / API schema mismatch

**Likelihood:** Medium (TypeScript types in v0 do not match Python canonical schema)  
**Impact:** Medium (silent rendering errors or blank result panels)  
**Mitigation:** #184 explicitly maps canonical schema fields to component props. Add TypeScript types in `lib/types.ts` derived from `src/inference/response_schema.py`. Do not infer field names from v0 mock types.

---

### Risk 5 — Next.js dependency conflicts or build failures

**Likelihood:** Low-Medium (v0 uses React 19 and Next.js 16 which may have peer dependency issues)  
**Impact:** Low (dev environment only; does not affect inference)  
**Mitigation:** Run `npm install` in isolation inside `frontend/`. Keep frontend Node environment separate from Python venv. Document Node version requirement.

---

## 9. Rollback Plan

- `main` branch is untouched throughout D7.
- All work stays on branch `d7-v0-ui-inference-integration`.
- `app.py` and `src/inference/` are not modified; Streamlit remains the authoritative demo at all times.
- The `frontend/` and `api/` directories are additive — deleting them restores the repo to its pre-D7 state with no side effects.
- If the branch is abandoned, `git branch -D d7-v0-ui-inference-integration` leaves `main` fully intact.
- No PR is opened until the Next.js flow is verified end-to-end and the copy audit is confirmed complete.

---

## 10. Acceptance Recommendation

**#181 is complete when:**

- [x] Branch `d7-v0-ui-inference-integration` exists
- [x] `docs/frontend/v0_prototype_integration_plan.md` is committed
- [x] The plan contains all 10 sections with sufficient detail to hand off to a developer
- [x] Unsafe copy from v0 is explicitly identified with replacements specified
- [x] Target architecture is defined with file paths and data flow
- [x] Implementation tickets #182–#185 are scoped and sequenced
- [x] Rollback plan is defined
- [ ] PR is not yet opened (held until D7.x tickets are implemented and verified)

**#181 does not require:**

- Any code changes to `app.py`, `src/inference/`, or any existing file
- Creation of `frontend/` or `api/` directories
- A working Next.js app
- A running API

---

*Document written on branch `d7-v0-ui-inference-integration`. Do not merge to main until D7.x implementation tickets are complete and verified.*
