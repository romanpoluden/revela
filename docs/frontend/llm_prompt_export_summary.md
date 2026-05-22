# D7.6 — ChatGPT / Claude Prompt Export Summary

**Ticket:** #186  
**Branch:** d7-v0-ui-inference-integration  
**Date:** 2026-05-22  
**Files changed:** `app.py`, `src/prompting/__init__.py` (new), `src/prompting/llm_prompt_builder.py` (new)

---

## What was implemented

The prompt export placeholder (`render_prompt_export_placeholder`) has been replaced with a
functional prompt export panel. The final result screen's right column now shows:

- A one-line explanation caption.
- An editable `st.text_area` (height 400px) containing the generated prompt.
- A `st.download_button` to save the prompt as `revela_case_prompt.txt`.
- The learner context summary expander (unchanged from #185).
- The learner rating form, if triggered (unchanged from #185).

**No external API call is made.** The prompt is assembled entirely from session state on the
Revela server and displayed locally.

---

## Prompt builder module

**Location:** `src/prompting/llm_prompt_builder.py`

**Main function:**

```python
build_llm_transfer_prompt(
    case_type: str,
    clinical_response: dict | None,
    dermoscopic_response: dict | None,
    learner_context: dict[str, str] | None,
    learner_rating: dict | None = None,
) -> str
```

Returns a plain-text string. All internal helpers are module-private.

---

## Prompt inputs

| Input | Source | Notes |
|-------|--------|-------|
| `case_type` | `st.session_state["case_type_radio"]` | Determines which result sections to include and which instruction block to use |
| `clinical_response` | `st.session_state.analysis_results["clinical"]` | Full canonical response dict |
| `dermoscopic_response` | `st.session_state.analysis_results["dermoscopic"]` | Full canonical response dict |
| `learner_context` | `st.session_state.learner_context` | Snapshotted at analysis time |
| `learner_rating` | `st.session_state.learner_rating` | Present only if lesion-routing class fired |

---

## Prompt structure

```
=== Revela Educational Case Prompt ===

[Safety header — NOT diagnosis, no treatment, qualified review required]

--- Case Type ---
[case type string]

--- Clinical Model Output (clinical_skin_condition_v1) ---    [if clinical result present]
Input type: Clinical macroscopic photo
Top output: [label] ([confidence]%)
Uncertainty: [bucket label]
  [explanation]
[Low-certainty flag if present]

All model outputs:
  1. [label] — [confidence]%
  ...

Safety note: [text]
Model limitations:
  - [text]
Recommended next step: [text]

--- Dermoscopic Model Output (dermoscopic_cancer_risk_bcn_mnh_v1) ---   [if dermoscopic present]
[same structure]

--- Learner Context (not used as model input) ---   [only if any fields are non-default]
[field]: [value]
...

--- Learner Reflection (not a diagnosis; does not change model output) ---   [only if present]
Concern level: [1-5] / 5
Would prioritize dermoscopic review: [yes/no/unsure]
Visible cues noted: [text]

=== Low-Certainty Notice ===   [only if any result has low_certainty == True or bucket == low_confidence]
[prioritise uncertainty, alternatives, do not make firm conclusion]

=== Instructions for the AI assistant ===
[Single-mode or paired-mode instructions block]
```

---

## Clinical / dermoscopic / paired behavior

| Mode | Clinical section | Dermoscopic section | Instructions block |
|------|-----------------|---------------------|--------------------|
| Clinical photo only | Included | Absent | Single-mode |
| Dermoscopic image only | Absent | Included | Single-mode |
| Paired | Included | Included | Paired (compare both outputs educationally) |

---

## Safety constraints in generated prompt

The prompt text explicitly instructs the LLM to:
- Treat the case as educational, not clinical.
- NOT diagnose the patient.
- NOT recommend treatment.
- NOT claim clinical certainty.
- NOT describe any output as "safe", "confirmed", or "detected".
- Explain that "Other non-cancer / indeterminate lesion" does NOT mean safe.
- Stay within the supplied taxonomy classes.
- Note that qualified review is required for real decisions.

The following phrases are absent from the generated prompt: "diagnose this patient",
"confirm this condition", "treatment plan", "safe lesion", "cancer detected", "clinical decision".

---

## No external API call

`build_llm_transfer_prompt` is pure Python string assembly. It:
- Reads only from function arguments (dicts).
- Makes no network requests.
- Does not import `requests`, `httpx`, `openai`, or `anthropic`.
- Does not touch uploaded images (images are not stored anywhere by Revela).

---

## How learner context is used

`_format_learner_context(ctx)` iterates `_LABELS` (the same 9 fields from `#183`) and includes
only fields whose value is non-empty and not `"not provided"`. If all fields are at default,
the entire context section is omitted from the prompt.

---

## How learner rating is used

`_format_learner_rating(rating)` includes:
- `Concern level: [n] / 5` — included if concern is an int.
- `Would prioritize dermoscopic review: [value]` — included if value is truthy.
- `Visible cues noted: [text]` — included only if text is non-empty.

The section header frames the rating as "not a diagnosis; does not change model output".
The rating section only appears in the prompt if `learner_rating` is non-empty
(i.e., the lesion-routing class fired during clinical inference).

---

## Error handling

If all available model responses have `"error": True`, the prompt is:

```
Prompt export is unavailable because model output is unavailable.
Please re-run the analysis or upload a supported image.
```

For paired mode where one model errors: only the successful result section is included.
The error result is simply absent from the prompt (no crash, no placeholder).

---

## Low-certainty block

Triggered when any included response has `low_certainty == True` OR
`uncertainty.bucket == "low_confidence"`. Adds a notice before the LLM instructions
asking the AI to prioritize uncertainty discussion and avoid firm conclusions.

---

## Verification

| Check | Result |
|-------|--------|
| `py_compile app.py` | PASS |
| `py_compile src/prompting/llm_prompt_builder.py` | PASS |
| Clinical adapter CLI (real image) | PASS — Eczema / dermatitis 44.73% |
| Dermoscopic adapter CLI (real image) | PASS — Melanoma 75.41% |
| Unit tests — 6 cases (clinical, dermoscopic, paired, low-cert, error, empty-ctx) | ALL PASS |
| End-to-end: real inference → prompt build → paired prompt 86 lines / 4274 chars | PASS |
| Safety phrase check — no unsafe language in output | PASS |
| Streamlit HTTP 200 | PASS |

---

## Limitations

- The prompt is generated from session state at render time. If the user edits the text area,
  the download button still downloads the originally generated prompt (the Python variable,
  not the widget state).
- The text area content resets to the generated prompt on every Streamlit rerun (e.g., when
  the learner adjusts the rating slider). This is by design — the prompt stays current.
- The prompt does not include the uploaded image. No image is stored or sent anywhere.
- Prompt length scales with the number of model outputs and context fields; typical range is
  60–100 lines.
- `Other non-cancer / indeterminate lesion` appears verbatim in the prompt as a model class
  label. The LLM instructions explicitly state this does not mean safe.
