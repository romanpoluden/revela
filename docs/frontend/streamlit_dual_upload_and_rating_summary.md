# D7.5 — Dual Upload Flow and Lesion Rating Summary

**Ticket:** #185  
**Branch:** d7-v0-ui-inference-integration  
**Date:** 2026-05-22  
**File changed:** `app.py` only

---

## New case types

The image-type radio (2 options) is replaced by a 3-option case type selector:

| Case type | Upload required | Model(s) run | top_k |
|-----------|----------------|--------------|-------|
| Clinical photo only | Clinical image | `clinical_skin_condition_v1` | 3 |
| Dermoscopic image only | Dermoscopic image | `dermoscopic_cancer_risk_bcn_mnh_v1` | 4 |
| Paired clinical + dermoscopic case | Both images | Both models (clinical first, then dermoscopic) | 3 + 4 |

Widget key: `case_type_radio`. `on_change=reset_analysis_state` fires when case type changes.

---

## Upload routing

A new `render_upload_card(label, upload_key, preview_caption, mode_note)` function renders each upload slot. It returns `(pil_image | None, error_str | None, is_valid: bool)`.

| Case type | Upload slots shown |
|-----------|-------------------|
| Clinical photo only | Clinical / macroscopic photo |
| Dermoscopic image only | Dermoscopic / close-up lesion image |
| Paired | Both, separated by a dashed divider |

Upload copy:
- Clinical card: "Regular camera photo of visible skin condition. Not dermoscopic, not microscope, not highly magnified."
- Dermoscopic card: "Dermoscopic or magnified lesion image. Not a regular clinical photo. Model output is not diagnosis."

**Analyze case button gating:**

| Case type | Button enabled when |
|-----------|---------------------|
| Clinical photo only | Clinical image valid |
| Dermoscopic image only | Dermoscopic image valid |
| Paired | Both images valid |

---

## Paired inference behavior

`complete_analysis(case_type, clinical_image, dermoscopic_image)` handles all three modes:

1. Renders `st.progress` + `st.status` staged loading (5 stages).
2. Runs clinical inference if `clinical_image is not None` (stage 3).
3. Runs dermoscopic inference if `dermoscopic_image is not None` (stage 4 for paired, same slot as 3 for dermoscopic-only).
4. Stores results: `st.session_state.analysis_results = {"clinical": ..., "dermoscopic": ...}`

**Error handling for paired:**
- If one model errors, it is stored with `"error": True` in its results key.
- `analysis_status` is set to `"complete"` as long as at least one result succeeded.
- Only if **all** results errored does `analysis_status` become `"error"`.
- On the final screen, a failed result shows `render_analysis_error()` inline for that model section.

**Session state key:** `analysis_results: dict[str, dict]`  
- `{"clinical": response}` for clinical-only  
- `{"dermoscopic": response}` for dermoscopic-only  
- `{"clinical": r1, "dermoscopic": r2}` for paired  

The old `analysis_result` key has been removed and replaced by `analysis_results` throughout.

---

## Final result screen

`render_final_result_screen(case_type: str)` dispatches by case type:

| Case type | Left column | Right column |
|-----------|-------------|--------------|
| Clinical photo only | Revela model result (clinical) | Prompt export placeholder + context summary + rating (if triggered) |
| Dermoscopic image only | Revela model result (dermoscopic) | Prompt export placeholder + context summary |
| Paired | Clinical model output + divider + Dermoscopic model output | Prompt export placeholder + context summary + rating (if triggered) |

For paired mode, both results use their respective `get_mode_config()` — clinical with `"Clinical photo"`, dermoscopic with `"Dermoscopic image"`. All canonical response fields are rendered: top output, confidence, uncertainty, low-certainty warning, top-k outputs, safety note, limitations, recommended next step.

---

## Lesion-class learner rating

**Trigger:** `_clinical_top_is_lesion_routing(clinical_response)` returns `True` when the clinical model's `top_prediction.label` is exactly `"Lesion — dermoscopic review recommended"`.

This shows `render_learner_rating_form()` in the right column of the final screen, below the prompt export card and context summary.

**Rating fields:**

| Field | Widget | Session key | Default |
|-------|--------|-------------|---------|
| Educational concern level | `st.slider` (1–5) | `lrt_concern` | 3 |
| Would you prioritize dermoscopic review? | `st.radio` (yes / no / unsure) | `lrt_prioritize` | unsure |
| Visible cues (optional) | `st.text_area` | `lrt_cues` | empty |

**Stored in:** `st.session_state.learner_rating` as:
```python
{
    "concern": int,                   # 1–5
    "prioritize_dermoscopy": str,     # "yes" | "no" | "unsure"
    "visible_cues": str,              # stripped free text or ""
}
```

Updated on every render while the form is visible.

**Safety copy shown in the rating expander:**
> "This is a learning reflection, not a diagnosis. The rating does not change model output. Qualified review is required for real decisions."

---

## Reset behavior

`reset_analysis_state()` clears:

| Key cleared | When |
|-------------|------|
| `analysis_status` → `"idle"` | Case type change, upload change, Start over |
| `analysis_results` → `{}` | Same |
| `analysis_error` → `None` | Same |
| `file_uploaded` → `False` | Same |
| All `ctx_*` widget keys | Same |
| All `lrt_*` widget keys | Same |
| `learner_context` → `{}` | Same |
| `learner_rating` → `{}` | Same |

Triggers: `on_change=reset_analysis_state` on the case type radio and all file uploaders; "Start over" button calls `reset_analysis_state()` + `st.rerun()`.

---

## What is not changed

- `run_inference()` — no changes to adapter, model, or inference schema
- `render_analysis_result()` — no changes; takes `(response, mode_config)` as before
- `get_mode_config()` — no changes; now called internally from `render_final_result_screen`
- `render_learner_context_form()`, `render_context_summary_card()` — no changes
- `_render_result_context_summary()` — no changes
- `render_prompt_export_placeholder()` — no changes
- All tabs except Analyze Image — no changes
- Canonical response schema — no changes

---

## Safety copy notes

- Dermoscopic upload note: "Not a regular clinical photo. Model output is not diagnosis." — avoids framing dermoscopic output as safer.
- `"Other non-cancer / indeterminate lesion"` appears only as a model output label. It is not described as "safe" or "benign" anywhere in the app copy.
- Learner rating disclaimer explicitly states it does not change model output.
- All result headings use "Educational … Output" framing.

---

## Verification

| Check | Result |
|-------|--------|
| `.venv/bin/python -m py_compile app.py` | PASS |
| Clinical adapter CLI smoke test (`clinical_skin_condition_v1`, top-k 3, real image) | PASS — Medium confidence, low_certainty=True |
| Dermoscopic adapter CLI smoke test (`dermoscopic_cancer_risk_bcn_mnh_v1`, top-k 4, real image) | PASS — Melanoma 75.41% |
| Paired inference simulation (both adapters, random input) | PASS — both results stored in `analysis_results` |
| `_clinical_top_is_lesion_routing` unit logic | PASS — lesion / non-lesion / error / None cases |
| `curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:8503` | HTTP 200 |

---

## Limitations

- The lesion-routing learner rating is not triggered if the clinical model outputs a different top class — i.e., if the model has low confidence and the top class happens to be a non-lesion label. This is by design: the trigger is the model's own top output label, not a confidence threshold.
- The rating is stored only in session state. It is not persisted to disk or any external service.
- For paired mode, if the clinical inference errors but dermoscopic succeeds, the rating form will not appear (clinical response has `"error": True`, so `_clinical_top_is_lesion_routing` returns `False`).
- `"Other non-cancer / indeterminate lesion"` is a dermoscopic class only. It does not trigger the rating form.
