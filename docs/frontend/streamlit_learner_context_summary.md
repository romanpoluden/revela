# D7.3 — Learner Context Questionnaire Summary

**Ticket:** #183  
**Branch:** d7-v0-ui-inference-integration  
**Date:** 2026-05-22  
**File changed:** `app.py` only

---

## What fields were added

Nine context fields are collected via an expandable form titled **"Learning context (optional)"** that appears in the left column after a valid image is uploaded:

| Field | Widget | Key | Options |
|-------|--------|-----|---------|
| Body location / anatomical site | `st.selectbox` | `ctx_body_location` | not provided, face / scalp / neck, trunk, arm / hand, leg / foot, other |
| Duration | `st.selectbox` | `ctx_duration` | not provided, days, weeks, months, longer / recurring, unsure |
| Itching | `st.selectbox` | `ctx_itching` | not provided, no, mild, moderate, severe |
| Pain / tenderness | `st.selectbox` | `ctx_pain_tenderness` | not provided, no, mild, moderate, severe |
| Change over time / spreading | `st.selectbox` | `ctx_change_over_time` | not provided, no clear change, spreading, changing color / shape / size, improving, unsure |
| Bleeding / crusting / discharge | `st.selectbox` | `ctx_bleeding_crusting_discharge` | not provided, no, bleeding, crusting, discharge, unsure |
| Prior similar episodes | `st.selectbox` | `ctx_prior_episodes` | not provided, no, yes, unsure |
| Image quality concern | `st.selectbox` | `ctx_image_quality_concern` | not provided, blurry, poor lighting, too close / too far, obstruction, unsure |
| Learner note | `st.text_area` | `ctx_learner_note` | free text, optional |

All structured fields default to `"not provided"`. The free-text field defaults to empty string.

**Fields intentionally not collected:**
- Name, address, date of birth, insurance or patient ID
- Exact anatomical location (free text)
- Treatment request or preference
- Any identifying personal data

---

## Why context is collected

The learner context questionnaire serves two purposes:

1. **Educational framing** — it encourages structured observation before seeing model output, mirroring how a learner would approach a case discussion.
2. **Prompt export preparation** — the collected context will be combined with the model output in ticket #186 to generate a ready-to-paste ChatGPT/Claude prompt for further educational discussion.

The form title and caption make the purpose explicit:

> "Optional context for educational discussion. This information is not used by the image model."

---

## Context is not used for model inference

Context does not affect:

- Model selection (`model_id` is determined by the image-type radio, not by context)
- Image preprocessing or transforms
- Model input (only the PIL Image is passed to `run_inference`)
- Model predictions, confidence values, or uncertainty buckets
- The canonical response schema

The context is collected in `st.session_state` and snapshotted into `st.session_state.learner_context` at the moment the user clicks "Analyze case". It is used only for display (the result-screen expander) and will later feed the prompt export function.

---

## How it supports #186 prompt export

When #186 is implemented, it will read `st.session_state.learner_context` and combine it with `st.session_state.analysis_result` to build a structured ChatGPT/Claude prompt. The context fields map directly to the prompt template:

```
Image mode: {mode}
Body location: {body_location}
Duration: {duration}
Itching: {itching}
Pain / tenderness: {pain_tenderness}
Change over time: {change_over_time}
Bleeding / crusting / discharge: {bleeding_crusting_discharge}
Prior similar episodes: {prior_episodes}
Image quality concern: {image_quality_concern}
Learner note: {learner_note}

Model top output: {top_prediction.label} ({top_prediction.confidence_percent}%)
Model uncertainty: {uncertainty.label}
...
```

The prompt template is not yet written — that is in scope for #186.

---

## Session state structure

`st.session_state.learner_context` is a `dict[str, str]` snapshotted at analysis time:

```python
{
    "body_location": "trunk",          # or "not provided"
    "duration": "weeks",
    "itching": "mild",
    "pain_tenderness": "not provided",
    "change_over_time": "spreading",
    "bleeding_crusting_discharge": "not provided",
    "prior_episodes": "no",
    "image_quality_concern": "not provided",
    "learner_note": "learner free text here",  # or ""
}
```

Widget state is stored in Streamlit's own session state under `ctx_*` keys (e.g., `ctx_body_location`, `ctx_duration`, ...). These are managed by the Streamlit widget engine.

---

## Reset behavior

Context is reset in all three scenarios specified:

| Trigger | Mechanism | What resets |
|---------|-----------|-------------|
| Image mode changes | `on_change=reset_analysis_state` on the `st.radio` | `ctx_*` widget keys deleted, `learner_context = {}` |
| Uploaded file changes | `on_change=reset_analysis_state` on the `st.file_uploader` | Same |
| Streamlit session reset | Page refresh | Full session state cleared |

The `reset_analysis_state()` function deletes all keys starting with `ctx_` from `st.session_state`, which causes Streamlit to re-initialize those selectboxes to their first option (`"not provided"`) on the next render.

---

## Step indicator update

The step indicator was updated from 3 steps to 4 steps to reflect the new flow:

1. Choose image type
2. Upload image
3. **Learning context** ← new
4. Review model output

Step tracking logic:

| Condition | Active step shown |
|-----------|------------------|
| No file uploaded | Step 2 (Upload image) |
| File uploaded, analysis idle | Step 3 (Learning context) |
| Analysis running / complete / error | Step 4 (Review model output) |

---

## UI placement

**In the Analyze Image tab — left column:**
- The context form (`st.expander`, `expanded=True`) appears after the image preview and upload metadata, before the "Analyze case" button.
- A context summary card appears below the expander showing filled-in fields as compact tags. If no fields are filled, a soft caption reads: "No learning context added yet. Context is optional."

**On the result screen — right column:**
- An expander titled "Learning context (collected for prompt export)" appears at the bottom of the result panel, listing all non-default context values and a caption explaining that context was not used by the image model.

---

## Safety and privacy notes

- The form does not ask for name, date of birth, patient ID, address, or any identifying information.
- All fields have `"not provided"` as a safe default — no field is required.
- Free-text fields are not validated for content; the UI caption sets the expectation: "add any context you would share in an educational discussion."
- Context is stored only in the browser session (`st.session_state`). It is not persisted to disk, database, or any external service.
- The disclaimer on the context expander makes clear the information is for educational discussion, not clinical use.

---

## Verification performed

| Check | Result |
|-------|--------|
| `.venv/bin/python -m py_compile app.py` | PASS — no syntax errors |
| Clinical adapter smoke test (`clinical_skin_condition_v1`, top-k 3) | PASS — Eczema / dermatitis 44.7% |
| Dermoscopic adapter smoke test (`dermoscopic_cancer_risk_bcn_mnh_v1`, top-k 4) | PASS — Melanoma 75.4% |
| `curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:8502` | HTTP 200 |

Inference outputs are identical to pre-#183 results, confirming context does not affect model behavior.
