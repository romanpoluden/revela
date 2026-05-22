# D7.4 — Staged Loading and Final Result Screen Summary

**Ticket:** #184  
**Branch:** d7-v0-ui-inference-integration  
**Date:** 2026-05-22  
**File changed:** `app.py` only

---

## What changed

### 1. Staged loading UI (`complete_analysis`)

Replaced the simple `st.spinner` with a `st.progress` bar and `st.status` container showing five named stages:

| Stage | Progress % | Message |
|-------|-----------|---------|
| 1 | 20 | Validating uploaded image |
| 2 | 40 | Preparing model input |
| 3 | 60 | Running local model inference |
| 4 | 80 | Preparing uncertainty and safety output |
| 5 | 95 | Preparing learning prompt area |

Stages 1–2 appear before inference; stage 3 message appears then `run_inference()` runs (blocking); stages 4–5 appear after inference returns. After the `st.status` block closes, progress is set to 100% then `st.rerun()` triggers.

On success: `status_widget.update(label="Analysis complete", state="complete", expanded=False)`  
On error: `status_widget.update(label="Analysis error", state="error", expanded=True)`

### 2. Final result screen (`render_final_result_screen`)

When `analysis_status == "complete"`, `render_analyze_tab` takes an early return that:

1. Renders a small "Start over" button (1/6 width column) — clicking calls `reset_analysis_state()` and `st.rerun()`.
2. Calls `render_final_result_screen(response, mode_config)` — a full-width two-column layout.
3. Calls `render_safety_footer()`.
4. Returns — the file uploader and upload form are NOT rendered in this path.

The two-column layout:

| Left column | Right column |
|-------------|--------------|
| `#### Revela model result` | `#### Continue in ChatGPT / Claude` |
| `render_analysis_result(response, mode_config)` | `render_prompt_export_placeholder()` |
| | `_render_result_context_summary(learner_context)` |

### 3. Prompt export placeholder (`render_prompt_export_placeholder`)

Renders a `.prompt-export-card` card explaining that a structured ChatGPT/Claude prompt will be available in a later iteration (ticket #186). The card uses copy:

> "After review, you will be able to copy a structured prompt combining the model result, uncertainty level, and your learning context — ready to paste into ChatGPT or Claude for further educational discussion."

With italic footer: "Prompt export — available in the next iteration"

### 4. Context summary moved to right column

`_render_result_context_summary(...)` was removed from `render_analysis_result` and is now rendered in the right column of the final screen via `render_final_result_screen`. This keeps context display co-located with the prompt export area.

---

## State machine — complete path

```
idle
  → user clicks "Analyze case" → start_analysis() → analysis_status = "running" → st.rerun()
running
  → render_result_panel calls complete_analysis(image, mode_config)
  → staged loading renders in right column
  → run_inference() executes
  → analysis_status = "complete" → st.rerun()
complete
  → render_analyze_tab early return
  → render_final_result_screen (two-column)
  → user clicks "Start over" → reset_analysis_state() → st.rerun() → status = "idle"
```

---

## What was intentionally not changed

- `run_inference()` — unchanged
- `render_analysis_result()` — unchanged except removal of the trailing `_render_result_context_summary` call
- `get_mode_config()` — unchanged
- All session state keys — unchanged
- Error path — `analysis_status == "error"` is still handled by `render_result_panel` in the two-column upload layout

---

## CSS used

Added in ticket #184 Edit 1 (already in `inject_css`):

- `.loading-stage-msg` — left-border styled stage message (not currently used; `st.status` inner `st.write` is used instead)
- `.prompt-export-card` — teal-bordered card container for prompt export placeholder
- `.prompt-placeholder-text` — body text style inside the card
- `.prompt-placeholder-coming` — italic "coming soon" footer line

---

## Verification

| Check | Result |
|-------|--------|
| `.venv/bin/python -m py_compile app.py` | PASS — no syntax errors |
| Clinical adapter smoke test (`clinical_skin_condition_v1`, top-k 3) | PASS |
| Dermoscopic adapter smoke test (`dermoscopic_cancer_risk_bcn_mnh_v1`, top-k 4) | PASS |
