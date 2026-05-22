# D7.1 — v0 UI Prototype Audit and Integration Plan

**Ticket:** #181  
**Branch:** d7-v0-ui-inference-integration  
**Date:** 2026-05-22  
**Status:** Planning only — no implementation in this ticket

---

## 1. Executive Recommendation

### Recommendation: Stay on Streamlit — use v0 as visual/UX reference only

**Decision (updated 2026-05-22):** Do not port Next.js. Do not build FastAPI. The final capstone demo and deployment will remain Streamlit-only.

The previous plan recommended a hybrid Next.js + FastAPI architecture. That path is intentionally not selected. The integration risk of wiring a new JavaScript frontend to a new Python API in a single sprint outweighs the visual improvement. Streamlit is working, the two-model inference is production-quality, and the demo deadline does not leave room for cross-stack debugging.

**What changes instead:**

The v0 prototype is used exclusively as a visual and UX reference. Its component layout, step flow, card design, loading states, and result screen structure are translated into Streamlit using custom CSS, `st.container`, `st.columns`, and `st.markdown`. No JavaScript is written. No API layer is introduced.

The v0 symptom questionnaire steps are retained — not as mock LLM input, but as structured learner context that feeds a prompt export. The final result screen shows both the real model prediction and a generated ChatGPT/Claude prompt alongside it.

Model artifacts will be hosted on Hugging Face (ticket #180) so the demo loads without local checkpoints.

**Safest path for this sprint (D7):**

1. Redesign the Streamlit UI taking v0 layout and step flow as visual reference.
2. Add a learner context questionnaire (duration, location, changes, etc.) as structured input for prompt export.
3. Add v0-style loading states and a redesigned final result screen.
4. Add dual-upload mode selector and lesion-class learner rating step.
5. Host model artifacts on Hugging Face so the demo is portable.

Do not modify `app.py` inference logic. Do not modify `src/inference/`. Do not merge to main until all D7 tickets are verified.

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

### This sprint (D7) — Streamlit-only

```
revela/
├── app.py                          ← PRIMARY DEMO — redesigned UI, inference untouched
├── src/inference/                  ← UNTOUCHED — Python inference pipeline
├── src/model/                      ← UNTOUCHED — model architecture and training
├── src/data/                       ← UNTOUCHED — data loading
├── models/                         ← LOCAL FALLBACK — checkpoints (also hosted on HF, ticket #180)
└── docs/frontend/                  ← this document
```

No `frontend/` directory. No `api/` directory. No JavaScript. No Node.js.

### Data flow

```
[Streamlit browser session]
        |
        | Step 1: mode selector (clinical / dermoscopic)
        | Step 2: image upload
        | Step 3: learner context questionnaire (duration, location, changes, ...)
        v
[app.py — Streamlit UI layer]
        |
        | run_inference(model_id, image_input, top_k)
        v
[src/inference/adapter.py — unchanged]
        |
        | canonical response dict
        v
[app.py — result screen]
        |
        ├── Model prediction panel (top-k, uncertainty, safety note)
        └── Prompt export panel (ChatGPT/Claude prompt built from questionnaire + model output)
```

### What v0 contributes (reference only)

| v0 element | How it maps to Streamlit |
|------------|--------------------------|
| Step indicator (3 steps) | `st.progress` + custom CSS step bar |
| Image uploader card | `st.file_uploader` inside `st.container` with custom CSS card styling |
| Symptom questionnaire (5 questions) | `st.radio` / `st.selectbox` form fields in a styled container |
| Loading animation | `st.spinner` with custom message and progress feedback |
| Analysis display — simple view | `st.columns` layout: top prediction card + ranked list |
| Analysis display — detailed view | `st.expander` sections for model limitations, uncertainty, safety note |
| Prompt export panel | New Streamlit section: copyable text area with generated ChatGPT/Claude prompt |

### Key constraints

- `app.py` inference logic is not modified. Only UI layout and flow are changed.
- `src/inference/` is not modified.
- `src/model/`, `src/data/`, model registry, taxonomies, training scripts are not modified.
- No new Python packages beyond what is already in `requirements.txt` unless strictly necessary.
- No Next.js. No FastAPI. No cross-stack integration.

---

## 6. Implementation Sequence

### #182 — Redesign Streamlit UI using v0 prototype as visual reference

**Goal:** Replace the current tab-based Streamlit layout with a v0-inspired step flow using custom CSS, cards, and containers. Inference is untouched.

Tasks:
- Study v0 `app/page.tsx` step flow (Upload → Questions → Insights) and `step-indicator.tsx` for layout reference
- Replace tab navigation with a linear step flow in `app.py` using `st.session_state` step tracking
- Add custom CSS (`st.markdown` + `<style>`) to produce card containers, step indicators, and section headers matching v0 visual style
- Redesign the image upload step: mode selector card (clinical / dermoscopic) + upload area
- Redesign result sections: top prediction card, ranked list, uncertainty indicator, safety note
- Apply safe copy (Section 7) throughout

**Out of scope:** Questionnaire, prompt export, dual upload logic, inference changes.

---

### #183 — Add learner context questionnaire for Streamlit prompt export

**Goal:** Add a v0-inspired symptom/context questionnaire step after image upload. Questionnaire answers feed a generated ChatGPT/Claude prompt displayed alongside the model result.

Tasks:
- Add step 2 questionnaire using `st.radio` / `st.selectbox` fields in a styled container:
  - Duration: how long the learner has noticed this
  - Location: body area
  - Changes: whether it has changed recently
  - Symptoms: itching, pain (optional)
- Store answers in `st.session_state`
- Build a prompt export function: takes `questionnaire_answers + model_output` → formats a ChatGPT/Claude prompt string
- Display generated prompt in a copyable `st.text_area` on the result screen alongside model output
- Prompt framing must use safe copy: educational review language, no diagnostic claims

**Out of scope:** Sending the prompt to any API. The prompt is a static export only.

---

### #184 — Add v0-style Streamlit loading states and final result screen

**Goal:** Replace the current spinner and flat result display with a v0-inspired animated loading state and a structured result screen showing model output and prompt export side by side.

Tasks:
- Add multi-step loading feedback: `st.spinner` with stage messages (e.g., *"Preparing image…"*, *"Running model…"*, *"Building learning summary…"*)
- Redesign the final result screen using `st.columns`:
  - Left panel: model prediction (top prediction card, ranked list, uncertainty, low-certainty warning if triggered, safety note)
  - Right panel: prompt export (generated ChatGPT/Claude prompt in `st.text_area` with copy button)
- Add expandable sections for model limitations and recommended next step (`st.expander`)
- Ensure low-certainty warning panel renders visually distinct (coloured container)

**Out of scope:** Sending the prompt to an LLM API. Model inference changes.

---

### #185 — Add dual-upload Streamlit flow and lesion-class learner rating

**Goal:** Add dermoscopic mode to the redesigned flow; add a learner self-rating step where the learner guesses the lesion class before seeing the model result.

Tasks:
- Add mode selector as step 0 or part of step 1: *Clinical photo* / *Dermoscopic image*
- Map selected mode to `model_id` and `top_k`:
  - Clinical → `clinical_skin_condition_v1`, top_k=3
  - Dermoscopic → `dermoscopic_cancer_risk_bcn_mnh_v1`, top_k=4
- Add learner self-rating step: show taxonomy labels for selected mode; learner selects their guess before inference runs
- After inference: show learner guess vs. model top prediction in a comparison card
- Ensure `Lesion — dermoscopic review recommended` output from clinical model triggers a dermoscopic referral message in the UI
- Ensure dermoscopic `Other non-cancer / indeterminate lesion` renders the safe-framing warning (not interpreted as "safe")

**Out of scope:** Inference logic changes. Fairness display (v0 mock metrics are not ported).

---

### #180 — Host Revela model artifacts on Hugging Face

**Goal:** Upload trained model checkpoints and `class_to_idx.json` files to Hugging Face Hub so the demo runs without local model files.

Tasks:
- Create a Hugging Face repository for Revela model artifacts
- Upload `clinical_v2_effnet_b0/best_model.pth` and `class_to_idx.json`
- Upload `bcn_mnh_cancer_risk_effnet_b0/best_model.pth` and `class_to_idx.json`
- Update `model_loader.py` to support downloading from HF Hub when local checkpoint is absent (local file takes priority; HF is fallback)
- Verify that the demo loads and runs inference using HF-hosted artifacts on a machine without local checkpoints
- Document HF repo path in `docs/model/`

**Out of scope:** Inference logic changes. Registry or taxonomy changes.

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

### Risk 1 — Breaking the Streamlit inference while redesigning the UI

**Likelihood:** Low-Medium (UI refactor touches `app.py` layout code which lives alongside inference calls)  
**Impact:** High (inference breakage destroys the demo)  
**Mitigation:** Separate UI layout changes from inference call sites. Do not modify any `run_inference()` call, any session state key that carries image or model_id into inference, or any result-rendering logic that reads the canonical response. Test inference end-to-end after each UI step change before committing.

---

### Risk 2 — Over-scoping across four tickets in limited time

**Likelihood:** Medium (four tickets is ambitious; each adds UI complexity)  
**Impact:** Medium (a half-finished result screen is worse than the current one)  
**Mitigation:** Tickets are sequenced so each is independently shippable. #182 alone (redesigned layout, no questionnaire) is a valid stopping point. #183 alone (questionnaire + prompt export) can be merged without #184 loading states. Do not start #185 until #184 is confirmed stable. Stop and commit at each ticket boundary.

---

### Risk 3 — Unsafe v0 wording copied into Streamlit

**Likelihood:** High (v0 copy is used as visual reference; clinical/practitioner language is pervasive)  
**Impact:** High (regulatory and reputational risk)  
**Mitigation:** Section 7 provides an explicit replacement table. Any v0 copy carried into `app.py` must be checked against that table before commit. No PR to main until copy audit is confirmed complete.

---

### Risk 4 — Prompt export contains unsafe wording

**Likelihood:** Medium (the generated ChatGPT/Claude prompt template is new and has no prior review)  
**Impact:** High (a prompt that frames model output as diagnosis or clinical decision support is unsafe even if the UI copy is clean)  
**Mitigation:** The prompt template must use safe framing (Section 7). The prompt export must include an explicit disclaimer line: *"This is a prototype educational tool. Model output is not a diagnosis."* Review the prompt template as part of the #183 acceptance criteria.

---

### Risk 5 — Hugging Face artifact download fails or is slow in demo environment

**Likelihood:** Low-Medium (network dependency; HF Hub rate limits can apply)  
**Impact:** Medium (demo fails to load model on a new machine)  
**Mitigation:** Local checkpoint takes priority over HF download. Demo machine should have local checkpoints present as fallback. Document that HF download is a convenience path, not the sole path. (#180)

---

## 9. Rollback Plan

- `main` branch is untouched throughout D7.
- All work stays on branch `d7-v0-ui-inference-integration`.
- `src/inference/`, `src/model/`, `src/data/`, model registry, taxonomies, and training scripts are never modified on this branch.
- `app.py` is the only file with meaningful changes. If the branch is abandoned, `git branch -D d7-v0-ui-inference-integration` restores `main` fully intact.
- There are no new directories (`frontend/`, `api/`) to clean up — rollback is a single branch delete.
- If a specific ticket introduces a regression, revert that commit on the branch (`git revert <sha>`) rather than abandoning the whole branch.
- No PR is opened until all D7 tickets are implemented, inference is verified end-to-end, and the copy audit is confirmed complete.

---

## 10. Acceptance Recommendation

**#181 is complete when:**

- [x] Branch `d7-v0-ui-inference-integration` exists
- [x] `docs/frontend/v0_prototype_integration_plan.md` is committed
- [x] The plan contains all 10 sections with sufficient detail to hand off to a developer
- [x] Unsafe copy from v0 is explicitly identified with replacements specified
- [x] Target architecture is defined (Streamlit-only, no Next.js, no FastAPI)
- [x] Implementation tickets #182, #183, #184, #185, and #180 are scoped and sequenced
- [x] Previous Next.js/FastAPI path is explicitly documented as intentionally not selected
- [x] Rollback plan is defined
- [ ] PR is not yet opened (held until D7.x tickets are implemented and verified)

**#181 does not require:**

- Any code changes to `app.py`, `src/inference/`, or any existing file
- Creation of `frontend/` or `api/` directories
- A working Next.js app or FastAPI server

**Why the Next.js/FastAPI path was not selected:**

The hybrid architecture would have required wiring a new JavaScript frontend to a new Python API, introducing two new build systems, a cross-origin request layer, a TypeScript → Python schema mapping, and a new deployment surface — all within the capstone sprint window. The integration risk exceeds the visual improvement. Streamlit with custom CSS achieves the same UX improvement at a fraction of the risk. The Next.js/FastAPI path remains documented here for reference if the product evolves beyond the capstone phase.

---

*Document updated 2026-05-22 on branch `d7-v0-ui-inference-integration`. Do not merge to main until D7.x implementation tickets are complete and verified.*
