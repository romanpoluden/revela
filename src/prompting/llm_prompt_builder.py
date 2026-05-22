"""Build copy-ready LLM transfer prompts from Revela model output and learner context.

No external API calls are made. The output is a plain-text string intended for
the learner to paste into ChatGPT or Claude for educational discussion.
"""
from __future__ import annotations

_SAFETY_HEADER = (
    "This is an educational dermatology training case for structured model output review.\n"
    "This is NOT a diagnosis. Do not recommend treatment. "
    "Model confidence is not clinical certainty.\n"
    "Qualified review is required for real decisions."
)

_LLM_INSTRUCTIONS_SINGLE = """\
=== Instructions for the AI assistant ===

Please treat this as an educational dermatology training case. Your task is to:

1. Explain the Revela model output in learning-friendly terms for a medical education context.
2. Compare the top model alternatives and explain what visual or contextual features might
   support or weaken each category from the supplied taxonomy.
3. Discuss the uncertainty level and what it means for educational interpretation.
4. Briefly explain the model's stated limitations.
5. Suggest 2–3 non-identifying follow-up questions a learner could explore to deepen understanding.
6. Stay within the supplied taxonomy classes — do not introduce diagnoses outside this list.

Important constraints:
- Do NOT diagnose the patient.
- Do NOT recommend treatment.
- Do NOT claim clinical certainty.
- Do NOT describe any output as "safe", "confirmed", or "detected".
- "Other non-cancer / indeterminate lesion" does NOT mean safe — explain this if it appears.
- Frame all discussion as educational model output review, not clinical conclusions.
- Qualified review by a licensed clinician is required for any real decision."""

_LLM_INSTRUCTIONS_PAIRED = """\
=== Instructions for the AI assistant ===

Please treat this as a paired educational dermatology training case with both a clinical-photo
model output and a dermoscopic-image model output. Your task is to:

1. Explain each Revela model output in learning-friendly terms.
2. Discuss what visual or contextual features might support or weaken the top alternatives
   from each model's taxonomy.
3. Compare the two model outputs educationally — where they agree, where they differ,
   and why that matters for a learner.
4. Discuss uncertainty for each output and what it means for educational interpretation.
5. Briefly explain the models' limitations.
6. Suggest 2–3 non-identifying follow-up questions a learner could explore.
7. Stay within the supplied taxonomy classes for each model.

Important constraints:
- Do NOT diagnose the patient.
- Do NOT recommend treatment.
- Do NOT claim clinical certainty.
- Do NOT describe any output as "safe", "confirmed", or "detected".
- "Other non-cancer / indeterminate lesion" does NOT mean safe — explain this if it appears.
- Frame all discussion as educational model output review, not clinical conclusions.
- Qualified review by a licensed clinician is required for any real decision."""

_LOW_CERTAINTY_BLOCK = """\
=== Low-Certainty Notice ===
One or more Revela outputs were marked low-certainty. Please prioritise:
- Discussion of uncertainty and what it means for educational review.
- Alternative possibilities from the model taxonomy.
- What additional context, image quality, or further review might help.
Do not make a firm conclusion from this output alone."""


def build_llm_transfer_prompt(
    case_type: str,
    clinical_response: dict | None,
    dermoscopic_response: dict | None,
    learner_context: dict[str, str] | None,
    learner_rating: dict | None = None,
) -> str:
    """Return a copy-ready LLM transfer prompt for educational discussion.

    Returns an unavailability message if no valid model output exists.
    No external calls are made.
    """
    is_paired = case_type == "Paired clinical + dermoscopic case"

    has_clinical = bool(clinical_response and not clinical_response.get("error"))
    has_dermoscopic = bool(dermoscopic_response and not dermoscopic_response.get("error"))

    if not has_clinical and not has_dermoscopic:
        return (
            "Prompt export is unavailable because model output is unavailable.\n"
            "Please re-run the analysis or upload a supported image."
        )

    has_low_certainty = (
        (has_clinical and _is_low_certainty(clinical_response))
        or (has_dermoscopic and _is_low_certainty(dermoscopic_response))
    )

    parts: list[str] = []

    parts.append("=== Revela Educational Case Prompt ===")
    parts.append("")
    parts.append(_SAFETY_HEADER)
    parts.append("")
    parts.append("--- Case Type ---")
    parts.append(case_type)
    parts.append("")

    if has_clinical:
        parts.append("--- Clinical Model Output (clinical_skin_condition_v1) ---")
        parts.append("Input type: Clinical macroscopic photo")
        parts.append("")
        parts.extend(_format_response_block(clinical_response))  # type: ignore[arg-type]
        parts.append("")

    if has_dermoscopic:
        parts.append("--- Dermoscopic Model Output (dermoscopic_cancer_risk_bcn_mnh_v1) ---")
        parts.append("Input type: Dermoscopic / close-up lesion image")
        parts.append("")
        parts.extend(_format_response_block(dermoscopic_response))  # type: ignore[arg-type]
        parts.append("")

    ctx_lines = _format_learner_context(learner_context)
    if ctx_lines:
        parts.append(
            "--- Learner Context (provided before analysis; not used as model input) ---"
        )
        parts.extend(ctx_lines)
        parts.append("")

    rating_lines = _format_learner_rating(learner_rating)
    if rating_lines:
        parts.append(
            "--- Learner Reflection (not a diagnosis; does not change model output) ---"
        )
        parts.extend(rating_lines)
        parts.append("")

    if has_low_certainty:
        parts.append(_LOW_CERTAINTY_BLOCK)
        parts.append("")

    parts.append(_LLM_INSTRUCTIONS_PAIRED if is_paired else _LLM_INSTRUCTIONS_SINGLE)

    return "\n".join(parts)


def _is_low_certainty(response: dict) -> bool:
    if response.get("low_certainty") is True:
        return True
    unc = response.get("uncertainty") or {}
    return unc.get("bucket") == "low_confidence"


def _format_response_block(response: dict) -> list[str]:
    lines: list[str] = []

    top = response.get("top_prediction") or {}
    label = top.get("label", "Unavailable")
    conf = top.get("confidence_percent")
    conf_str = f"{conf:.2f}%" if isinstance(conf, (int, float)) else "Unavailable"
    lines.append(f"Top output: {label} ({conf_str})")

    unc = response.get("uncertainty") or {}
    unc_label = unc.get("label", "Unavailable")
    unc_expl = unc.get("explanation", "")
    lines.append(f"Uncertainty: {unc_label}")
    if unc_expl:
        lines.append(f"  {unc_expl}")

    if response.get("low_certainty") is True:
        lc_msg = response.get(
            "low_certainty_message",
            "The model output is uncertain. Use for educational review only.",
        )
        reason = response.get("low_certainty_reason", "")
        lines.append(f"Low-certainty flag: {lc_msg}")
        if reason:
            lines.append(f"  Reason: {reason}")

    predictions = response.get("predictions") or []
    if predictions:
        lines.append("")
        lines.append("All model outputs:")
        for pred in predictions:
            rank = pred.get("rank", "?")
            plabel = pred.get("label", "Unavailable")
            pconf = pred.get("confidence_percent")
            pconf_str = f"{pconf:.2f}%" if isinstance(pconf, (int, float)) else "Unavailable"
            lines.append(f"  {rank}. {plabel} — {pconf_str}")

    safety = response.get("safety_note")
    if safety:
        lines.append("")
        lines.append(f"Safety note: {safety}")

    limitations = response.get("model_limitations") or []
    if limitations:
        lines.append("Model limitations:")
        for lim in limitations:
            lines.append(f"  - {lim}")

    next_step = response.get("recommended_next_step")
    if next_step:
        lines.append(f"Recommended next step: {next_step}")

    return lines


def _format_learner_context(ctx: dict[str, str] | None) -> list[str]:
    if not ctx:
        return []

    _LABELS = {
        "body_location": "Body location",
        "duration": "Duration",
        "itching": "Itching",
        "pain_tenderness": "Pain / tenderness",
        "change_over_time": "Change over time",
        "bleeding_crusting_discharge": "Bleeding / crusting / discharge",
        "prior_episodes": "Prior similar episodes",
        "image_quality_concern": "Image quality concern",
        "learner_note": "Learner note",
    }

    lines: list[str] = []
    for key, label in _LABELS.items():
        val = ctx.get(key, "")
        if val and val != "not provided":
            lines.append(f"{label}: {val}")
    return lines


def _format_learner_rating(rating: dict | None) -> list[str]:
    if not rating:
        return []

    concern = rating.get("concern")
    prioritize = rating.get("prioritize_dermoscopy")
    cues = (rating.get("visible_cues") or "").strip()

    lines: list[str] = []
    if isinstance(concern, int):
        lines.append(f"Concern level: {concern} / 5")
    if prioritize:
        lines.append(f"Would prioritize dermoscopic review: {prioritize}")
    if cues:
        lines.append(f"Visible cues noted: {cues}")
    return lines
