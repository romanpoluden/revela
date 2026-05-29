from __future__ import annotations

import html

from PIL import Image, UnidentifiedImageError
import streamlit as st

from src.inference.remote_client import RemoteInferenceError, run_remote_inference
from src.prompting.llm_prompt_builder import build_llm_transfer_prompt


CLINICAL_CLASSES = [
    "Eczema / dermatitis",
    "Urticaria / allergic reaction",
    "Folliculitis / acne-like",
    "Psoriasis / papulosquamous",
    "Lesion — dermoscopic review recommended",
]

DERMOSCOPIC_CLASSES = [
    "Melanoma",
    "Non-melanoma skin cancer",
    "Benign nevus",
    "Other non-cancer / indeterminate lesion",
]

LESION_ROUTING_LABEL = "Lesion — dermoscopic review recommended"

_CASE_TYPES = [
    "Clinical photo",
    "Dermoscopic image",
]

_CONTEXT_OPTIONS: dict[str, list[str]] = {
    "body_location": [
        "not provided",
        "face / scalp / neck",
        "trunk",
        "arm / hand",
        "leg / foot",
        "other",
    ],
    "duration": [
        "not provided",
        "days",
        "weeks",
        "months",
        "longer / recurring",
        "unsure",
    ],
    "itching": [
        "not provided",
        "no",
        "mild",
        "moderate",
        "severe",
    ],
    "pain_tenderness": [
        "not provided",
        "no",
        "mild",
        "moderate",
        "severe",
    ],
    "change_over_time": [
        "not provided",
        "no clear change",
        "spreading",
        "changing color / shape / size",
        "improving",
        "unsure",
    ],
    "bleeding_crusting_discharge": [
        "not provided",
        "no",
        "bleeding",
        "crusting",
        "discharge",
        "unsure",
    ],
    "prior_episodes": [
        "not provided",
        "no",
        "yes",
        "unsure",
    ],
    "image_quality_concern": [
        "not provided",
        "blurry",
        "poor lighting",
        "too close / too far",
        "obstruction",
        "unsure",
    ],
}

_CONTEXT_LABELS: dict[str, str] = {
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


def main() -> None:
    st.set_page_config(
        page_title="Revela",
        page_icon="🔎",
        layout="wide",
    )
    inject_css()
    render_header()

    tabs = st.tabs(
        [
            "Overview",
            "Analyze Image",
            "Model Transparency",
            "Evaluation Metrics",
            "Benchmark",
            "About / Limitations",
        ]
    )

    with tabs[0]:
        render_overview_tab()
    with tabs[1]:
        render_analyze_tab()
    with tabs[2]:
        render_transparency_tab()
    with tabs[3]:
        render_metrics_tab()
    with tabs[4]:
        render_benchmark_tab()
    with tabs[5]:
        render_limitations_tab()


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --revela-bg: #f5f7f8;
            --revela-surface: #ffffff;
            --revela-surface-soft: #f8fafc;
            --revela-ink: #102a43;
            --revela-muted: #52616b;
            --revela-border: #dbe3ea;
            --revela-border-strong: #b8c8d8;
            --revela-primary: #2f6f73;
            --revela-primary-strong: #184e52;
            --revela-primary-soft: #e8f4f3;
            --revela-accent: #b85c38;
            --revela-warning-soft: #fff7ed;
            --revela-radius: 10px;
            --revela-shadow-sm: 0 1px 2px rgba(16, 42, 67, 0.05);
            --revela-shadow-md: 0 10px 24px rgba(16, 42, 67, 0.08);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(47,111,115,0.08), transparent 30rem),
                linear-gradient(180deg, #f8fbfb 0%, var(--revela-bg) 38%, #eef2f4 100%);
            color: var(--revela-ink);
        }

        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }

        /* -- D10 layout foundation hooks ---------------- */
        .revela-workspace {
            border: 1px solid rgba(184, 200, 216, 0.72);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.78);
            box-shadow: var(--revela-shadow-md);
            padding: 1rem;
        }
        .revela-section-card {
            border: 1px solid var(--revela-border);
            border-radius: var(--revela-radius);
            background: var(--revela-surface);
            box-shadow: var(--revela-shadow-sm);
            padding: 1rem 1.1rem;
            margin: 0.75rem 0;
        }
        .revela-section-card[data-state="subtle"] {
            background: var(--revela-surface-soft);
        }
        .revela-section-card[data-state="warning"] {
            background: var(--revela-warning-soft);
            border-color: #fed7aa;
        }
        .revela-workflow-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.85rem;
            margin: 0.75rem 0 1rem 0;
        }
        .revela-workflow-card {
            border: 1px solid var(--revela-border);
            border-radius: var(--revela-radius);
            background: var(--revela-surface);
            box-shadow: var(--revela-shadow-sm);
            padding: 0.95rem 1rem;
            min-height: 118px;
        }
        .revela-workflow-card.is-selected {
            border-color: var(--revela-primary);
            background: linear-gradient(180deg, #f4faf9 0%, #ffffff 100%);
            box-shadow: 0 0 0 3px rgba(47, 111, 115, 0.12);
        }
        .revela-workflow-card.is-unselected {
            color: var(--revela-muted);
        }
        .revela-workflow-card.is-disabled {
            background: #f3f6f8;
            border-style: dashed;
            color: #7b8b9d;
        }
        .revela-step-header {
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            margin: 1rem 0 0.7rem 0;
        }
        .revela-step-index {
            width: 1.8rem;
            height: 1.8rem;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            background: var(--revela-primary-soft);
            color: var(--revela-primary-strong);
            border: 1px solid #b9ded8;
            font-size: 0.82rem;
            font-weight: 750;
        }
        .revela-step-copy h3,
        .revela-section-card h3,
        .revela-workflow-card h3 {
            margin: 0 0 0.3rem 0;
            color: var(--revela-ink);
            font-size: 1.02rem;
            line-height: 1.25;
        }
        .revela-step-copy p,
        .revela-section-card p,
        .revela-workflow-card p {
            color: var(--revela-muted);
            font-size: 0.92rem;
            line-height: 1.5;
            margin: 0;
        }
        .revela-card-kicker {
            margin: 0 0 0.35rem 0;
            color: var(--revela-primary-strong);
            font-size: 0.73rem;
            font-weight: 750;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .revela-primary-cta,
        div.stButton > button[kind="primary"],
        div.stButton > button[data-testid="baseButton-primary"] {
            border-color: var(--revela-primary-strong);
            background: var(--revela-primary-strong);
            color: #ffffff;
            box-shadow: 0 6px 16px rgba(24, 78, 82, 0.18);
        }
        div.stButton > button[kind="primary"]:hover,
        div.stButton > button[data-testid="baseButton-primary"]:hover {
            border-color: #103f43;
            background: #103f43;
            color: #ffffff;
        }

        /* ── Hero header ─────────────────────────────── */
        .hero {
            padding: 2rem 2.2rem;
            border: 1px solid #dbe3ea;
            border-radius: 12px;
            background: linear-gradient(135deg, #f7fbfb 0%, #eef5f2 55%, #f8fafc 100%);
            margin-bottom: 1.2rem;
        }
        .hero h1 {
            font-size: 3rem;
            line-height: 1.05;
            margin: 0 0 0.3rem 0;
            letter-spacing: 0;
            color: #102a43;
        }
        .hero-subtitle {
            color: #184e52;
            font-size: 1.12rem;
            font-weight: 650;
            margin: 0 0 0.2rem 0;
        }
        .hero-tagline {
            color: #52616b;
            font-size: 0.95rem;
            margin: 0;
        }

        /* ── Status pill ─────────────────────────────── */
        .status-pill {
            display: inline-block;
            padding: 0.25rem 0.58rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 650;
            color: #184e52;
            background: #e3f4f1;
            border: 1px solid #b9ded8;
            margin-bottom: 0.45rem;
        }

        /* ── Note / disclaimer strip ─────────────────── */
        .note {
            padding: 0.85rem 1rem;
            border-left: 4px solid #2f6f73;
            background: #f4f9f8;
            border-radius: 8px;
            color: #1f3f46;
            margin: 0.8rem 0 1rem 0;
            font-size: 0.92rem;
        }

        /* ── Generic card ────────────────────────────── */
        .card {
            border: 1px solid #dbe3ea;
            border-radius: 10px;
            padding: 1.05rem 1.1rem;
            background: #ffffff;
            min-height: 132px;
            box-shadow: 0 1px 2px rgba(16, 42, 67, 0.04);
        }
        .card h3 {
            margin-top: 0;
            margin-bottom: 0.45rem;
            color: #102a43;
            font-size: 1.05rem;
        }
        .card p, .card li {
            color: #425466;
            font-size: 0.95rem;
        }

        /* ── Metric card ─────────────────────────────── */
        .metric-card {
            border: 1px solid #dbe3ea;
            border-radius: 10px;
            padding: 1rem;
            background: #ffffff;
            min-height: 112px;
        }
        .metric-value {
            font-size: 1.7rem;
            font-weight: 700;
            color: #184e52;
            margin-bottom: 0.1rem;
        }
        .metric-label {
            color: #52616b;
            font-size: 0.88rem;
        }

        /* ── Disabled panel ──────────────────────────── */
        .disabled-panel {
            border: 1px dashed #aebdca;
            border-radius: 10px;
            padding: 1rem;
            background: #f8fafc;
            color: #425466;
        }

        /* ── Step indicator ──────────────────────────── */
        .step-bar {
            display: flex;
            align-items: center;
            padding: 0.85rem 1.4rem;
            background: #f8fafc;
            border: 1px solid #dbe3ea;
            border-radius: 12px;
            margin-bottom: 1.4rem;
        }
        .step-item {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            flex: 1;
        }
        .step-dot {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.78rem;
            font-weight: 700;
            flex-shrink: 0;
        }
        .step-done   { background: #184e52; color: #ffffff; }
        .step-active { background: #2f6f73; color: #ffffff;
                       box-shadow: 0 0 0 3px rgba(47,111,115,0.18); }
        .step-pending { background: #e8edf2; color: #8a9ab0;
                        border: 1.5px solid #c8d4de; }
        .step-text-done    { font-size: 0.83rem; font-weight: 600; color: #184e52; }
        .step-text-active  { font-size: 0.83rem; font-weight: 700; color: #102a43; }
        .step-text-pending { font-size: 0.83rem; color: #8a9ab0; }
        .step-connector {
            height: 2px; width: 40px;
            background: #dbe3ea;
            flex-shrink: 0;
            margin: 0 0.3rem;
        }
        .conn-done { background: #184e52; }

        /* ── Mode selector (targets Streamlit radio widget) ── */
        div[data-testid="stRadio"] {
            background: #f8fafc;
            border: 1px solid #dbe3ea;
            border-radius: 10px;
            padding: 0.75rem 1rem 0.65rem 1rem;
            margin-bottom: 1rem;
        }

        /* ── Result section label ────────────────────── */
        .section-label {
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #52616b;
            margin: 1rem 0 0.4rem 0;
        }

        /* ── Top prediction card ─────────────────────── */
        .top-pred-card {
            border: 1px solid #b9ded8;
            border-left: 4px solid #2f6f73;
            border-radius: 10px;
            padding: 1rem 1.1rem 0.85rem 1.1rem;
            background: #f4faf9;
        }
        .top-pred-header {
            display: flex;
            align-items: baseline;
            gap: 0.65rem;
            flex-wrap: wrap;
        }
        .top-pred-label {
            font-size: 1.08rem;
            font-weight: 700;
            color: #102a43;
        }
        .top-pred-note {
            font-size: 0.78rem;
            color: #52616b;
            margin: 0.3rem 0 0 0;
        }

        /* ── Confidence badge ────────────────────────── */
        .conf-badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            font-size: 0.83rem;
            font-weight: 700;
        }
        .conf-high    { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
        .conf-medium  { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
        .conf-low     { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
        .conf-unknown { background: #f3f4f6; color: #6b7280; border: 1px solid #d1d5db; }

        /* ── Uncertainty badge ───────────────────────── */
        .unc-badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 600;
        }
        .unc-high   { background: #d1fae5; color: #065f46; }
        .unc-medium { background: #fef3c7; color: #92400e; }
        .unc-low    { background: #fee2e2; color: #991b1b; }
        .unc-explanation {
            font-size: 0.87rem;
            color: #425466;
            margin: 0.4rem 0 0 0;
            line-height: 1.45;
        }

        /* ── Low-certainty warning card ──────────────── */
        .low-certainty-card {
            display: flex;
            gap: 0.7rem;
            align-items: flex-start;
            background: #fffbeb;
            border: 1px solid #fcd34d;
            border-left: 4px solid #f59e0b;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin: 0.75rem 0;
            font-size: 0.87rem;
            color: #78350f;
            line-height: 1.5;
        }
        .low-certainty-marker {
            font-size: 0.78rem;
            font-weight: 700;
            flex-shrink: 0;
            margin-top: 0.1rem;
            background: #f59e0b;
            color: white;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        /* ── Prediction list ─────────────────────────── */
        .pred-list { margin: 0.2rem 0 0.5rem 0; }
        .pred-row {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            padding: 0.45rem 0;
            border-bottom: 1px solid #f0f4f7;
            font-size: 0.87rem;
        }
        .pred-row:last-child { border-bottom: none; }
        .pred-rank {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #e8edf2;
            color: #52616b;
            font-size: 0.73rem;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .pred-label-text {
            flex: 1;
            color: #102a43;
            font-weight: 500;
            min-width: 0;
        }
        .pred-bar-outer {
            width: 72px;
            height: 5px;
            background: #e8edf2;
            border-radius: 4px;
            overflow: hidden;
            flex-shrink: 0;
        }
        .pred-bar-inner {
            height: 100%;
            background: #2f6f73;
            border-radius: 4px;
        }
        .pred-conf-text {
            width: 50px;
            text-align: right;
            color: #52616b;
            font-size: 0.8rem;
            flex-shrink: 0;
        }

        /* ── Next step card ──────────────────────────── */
        .next-step-card {
            background: #f4f9f8;
            border: 1px solid #b9ded8;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin-top: 1rem;
        }
        .next-step-text {
            color: #1f3f46;
            font-size: 0.9rem;
            margin: 0.25rem 0 0 0;
            line-height: 1.5;
        }

        /* ── Context summary card ───────────────────────── */
        .context-summary-card {
            background: #f8fafc;
            border: 1px solid #dbe3ea;
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin: 0.75rem 0 0.5rem 0;
        }
        .ctx-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-top: 0.3rem;
        }
        .ctx-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            background: #e8f4f3;
            border: 1px solid #b9ded8;
            border-radius: 6px;
            padding: 0.18rem 0.5rem;
            font-size: 0.8rem;
        }
        .ctx-tag-label {
            color: #52616b;
            font-weight: 600;
        }
        .ctx-tag-value {
            color: #184e52;
        }

        /* ── Staged loading messages ─────────────────── */
        .loading-stage-msg {
            padding: 0.35rem 0.7rem;
            background: #f4f9f8;
            border-left: 3px solid #2f6f73;
            border-radius: 0 6px 6px 0;
            color: #1f3f46;
            font-size: 0.87rem;
            margin: 0.25rem 0;
        }

        /* ── Prompt export card ──────────────────────── */
        .prompt-export-card {
            border: 1px solid #b9ded8;
            border-left: 4px solid #184e52;
            border-radius: 10px;
            padding: 1rem 1.1rem 1rem 1.1rem;
            background: #f4faf9;
            margin-bottom: 1rem;
            min-height: 160px;
        }

        /* ── Learner rating card ─────────────────────── */
        .rating-card {
            border: 1px solid #b9ded8;
            border-left: 4px solid #2f6f73;
            border-radius: 10px;
            padding: 1rem 1.1rem;
            background: #f4faf9;
            margin-top: 1rem;
        }
        .rating-disclaimer {
            font-size: 0.82rem;
            color: #52616b;
            font-style: italic;
            margin: 0.6rem 0 0 0;
            border-top: 1px solid #d0e8e5;
            padding-top: 0.5rem;
        }

        /* ── Dermoscopic follow-up card ──────────────── */
        .followup-card {
            border: 1px solid #b9ded8;
            border-left: 4px solid #2f6f73;
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            background: #f4faf9;
            margin-top: 1.5rem;
        }
        .followup-card-text {
            color: #1f3f46;
            font-size: 0.9rem;
            line-height: 1.55;
            margin: 0.3rem 0 0.5rem 0;
        }

        /* ── Upload section divider ──────────────────── */
        .upload-divider {
            border: none;
            border-top: 1px dashed #dbe3ea;
            margin: 1.2rem 0;
        }

        /* ── Safety footer ───────────────────────────── */
        .safety-footer {
            margin-top: 2rem;
            padding: 1rem 1.2rem;
            border: 1px solid #dbe3ea;
            border-top: 3px solid #2f6f73;
            border-radius: 0 0 10px 10px;
            background: #f4f9f8;
            color: #1f3f46;
            font-size: 0.87rem;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="status-pill">Prototype</div>
          <h1>Revela</h1>
          <p class="hero-subtitle">Educational dermatology AI training aid</p>
          <p class="hero-tagline">Structured image review for learning. Model output, not diagnosis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="note">
        Revela is not a diagnostic product. It does not provide treatment advice, clinical certainty, or clinical validation.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _escape_html(value: str | int | float | None) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def render_revela_section_card(
    title: str,
    body: str,
    *,
    kicker: str | None = None,
    state: str = "default",
) -> None:
    kicker_html = (
        f'<div class="revela-card-kicker">{_escape_html(kicker)}</div>' if kicker else ""
    )
    st.markdown(
        f"""
        <div class="revela-section-card" data-state="{_escape_html(state)}">
          {kicker_html}
          <h3>{_escape_html(title)}</h3>
          <p>{_escape_html(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_revela_workflow_card(
    title: str,
    body: str,
    *,
    step_label: str | None = None,
    selected: bool = False,
    disabled: bool = False,
) -> None:
    state_class = "is-disabled" if disabled else "is-selected" if selected else "is-unselected"
    step_html = (
        f'<div class="revela-card-kicker">{_escape_html(step_label)}</div>'
        if step_label
        else ""
    )
    st.markdown(
        f"""
        <div class="revela-workflow-card {state_class}">
          {step_html}
          <h3>{_escape_html(title)}</h3>
          <p>{_escape_html(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_revela_step_header(step_number: int, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="revela-step-header">
          <div class="revela-step-index">{_escape_html(step_number)}</div>
          <div class="revela-step-copy">
            <h3>{_escape_html(title)}</h3>
            <p>{_escape_html(description)}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_step_indicator(current_step: int) -> None:
    def _dot(step: int) -> tuple[str, str]:
        if step < current_step:
            return "step-done", "&#10003;"
        if step == current_step:
            return "step-active", str(step)
        return "step-pending", str(step)

    def _label_class(step: int) -> str:
        if step < current_step:
            return "step-text-done"
        if step == current_step:
            return "step-text-active"
        return "step-text-pending"

    def _connector_class(after_step: int) -> str:
        return "step-connector conn-done" if after_step < current_step else "step-connector"

    steps = [
        (1, "Modality"),
        (2, "Upload"),
        (3, "Image type check"),
        (4, "Analyze"),
        (5, "Review output"),
    ]

    parts: list[str] = []
    for i, (num, label) in enumerate(steps):
        dot_class, dot_text = _dot(num)
        lbl_class = _label_class(num)
        parts.append(
            f'<div class="step-item">'
            f'<div class="step-dot {dot_class}">{dot_text}</div>'
            f'<span class="{lbl_class}">{label}</span>'
            f'</div>'
        )
        if i < len(steps) - 1:
            parts.append(f'<div class="{_connector_class(num)}"></div>')

    st.markdown(
        f'<div class="step-bar">{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def render_analyze_tab() -> None:
    initialize_analysis_state()
    status = st.session_state.analysis_status

    if status in ("complete", "error"):
        _step = 5
    elif status == "running":
        _step = 4
    elif st.session_state.get("file_uploaded", False):
        _step = 3
    else:
        _step = 1
    render_step_indicator(_step)

    render_revela_step_header(
        1,
        "Modality Selection",
        "Choose the educational review flow that matches the image you plan to upload.",
    )
    case_type = st.radio(
        "Choose image type",
        _CASE_TYPES,
        horizontal=True,
        key="case_type_radio",
        on_change=reset_analysis_state,
    )

    uploaded_image: Image.Image | None = None
    has_image_error = False
    upload_valid = False

    render_revela_step_header(
        2,
        "Image Upload",
        "Add one supported image for the selected flow. Existing preview and file details remain available here.",
    )
    if case_type == "Clinical photo":
        uploaded_image, img_err, upload_valid = render_upload_card(
            label="Clinical / macroscopic photo",
            upload_key="upload_clinical",
            preview_caption="Clinical photo preview",
            mode_note=(
                "Regular camera photo of visible skin condition. "
                "Not dermoscopic, not microscope, not highly magnified."
            ),
        )
    else:
        uploaded_image, img_err, upload_valid = render_upload_card(
            label="Dermoscopic / close-up lesion image",
            upload_key="upload_dermoscopic",
            preview_caption="Dermoscopic image preview",
            mode_note=(
                "Dermoscopic or magnified lesion image. "
                "Not a regular clinical photo. Model output is not diagnosis."
            ),
        )

    if img_err:
        has_image_error = True

    st.session_state.file_uploaded = upload_valid and not has_image_error

    if upload_valid and not has_image_error:
        render_learner_context_form()
        render_context_summary_card()

    render_revela_step_header(
        3,
        "Image Type Check",
        "Reserved for the image-type status step. This ticket keeps analysis behavior unchanged.",
    )
    render_revela_section_card(
        title="Image type check placeholder",
        body=(
            "No automatic image-type gate is active in this branch. Later D10 work can attach "
            "the status card here without changing the workflow layout."
        ),
        kicker="Workflow status",
        state="subtle" if upload_valid and not has_image_error else "default",
    )

    render_revela_step_header(
        4,
        "Educational Analysis CTA",
        "Run the selected Revela model only after a valid image is available.",
    )
    if st.button(
        "Analyze case",
        disabled=not upload_valid or has_image_error or status == "running",
        type="primary",
    ):
        start_analysis()
        st.rerun()

    render_revela_step_header(
        5,
        "Model Output Review",
        "Review the educational model output, uncertainty notes, and safety guidance.",
    )
    if status == "complete":
        _col, _ = st.columns([1, 5])
        with _col:
            if st.button("Start over"):
                reset_analysis_state()
                st.rerun()
        render_final_result_screen(case_type)
        render_safety_footer()
        return

    render_right_panel(
        case_type=case_type,
        upload_valid=upload_valid,
        has_image_error=has_image_error,
        uploaded_image=uploaded_image,
    )

    render_safety_footer()


def get_mode_config(input_mode: str) -> dict[str, str | int]:
    if input_mode == "Dermoscopic image":
        return {
            "input_mode": input_mode,
            "model_id": "dermoscopic_cancer_risk_bcn_mnh_v1",
            "top_k": 4,
            "result_heading": "Educational Dermoscopic Review Output",
            "top_outputs_heading": "Top-4 Outputs",
            "result_note": (
                "Model output, not diagnosis. Review by a qualified clinician is required for real decisions."
            ),
        }

    return {
        "input_mode": input_mode,
        "model_id": "clinical_skin_condition_v1",
        "top_k": 3,
        "result_heading": "Educational Model Output",
        "top_outputs_heading": "Top-3 Outputs",
        "result_note": "Model output, not diagnosis.",
    }


def initialize_analysis_state() -> None:
    if "analysis_status" not in st.session_state:
        st.session_state.analysis_status = "idle"
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = {}
    if "analysis_error" not in st.session_state:
        st.session_state.analysis_error = None
    if "file_uploaded" not in st.session_state:
        st.session_state.file_uploaded = False
    if "learner_context" not in st.session_state:
        st.session_state.learner_context = {}
    if "learner_rating" not in st.session_state:
        st.session_state.learner_rating = {}
    if "dermoscopic_followup_status" not in st.session_state:
        st.session_state.dermoscopic_followup_status = "idle"


def reset_analysis_state() -> None:
    st.session_state.analysis_status = "idle"
    st.session_state.analysis_results = {}
    st.session_state.analysis_error = None
    st.session_state.file_uploaded = False
    st.session_state.dermoscopic_followup_status = "idle"
    for key in list(st.session_state.keys()):
        if key.startswith("ctx_") or key.startswith("lrt_"):
            del st.session_state[key]
    st.session_state.learner_context = {}
    st.session_state.learner_rating = {}


def reset_followup_state() -> None:
    """Reset only the dermoscopic follow-up without clearing the clinical result."""
    st.session_state.dermoscopic_followup_status = "idle"
    results = dict(st.session_state.get("analysis_results", {}))
    results.pop("dermoscopic", None)
    st.session_state.analysis_results = results


def start_analysis() -> None:
    st.session_state.analysis_status = "running"
    st.session_state.analysis_results = {}
    st.session_state.analysis_error = None
    st.session_state.dermoscopic_followup_status = "idle"
    st.session_state.learner_context = _collect_learner_context()


def complete_analysis(
    case_type: str,
    uploaded_image: Image.Image,
) -> None:
    is_clinical = case_type == "Clinical photo"

    progress = st.progress(0, text="Starting analysis...")
    with st.status("Running educational image analysis...", expanded=True) as status_widget:
        st.write("Validating uploaded image")
        progress.progress(20, text="Validating uploaded image")

        st.write("Preparing model input")
        progress.progress(40, text="Preparing model input")

        if is_clinical:
            st.write("Running clinical model inference")
            progress.progress(60, text="Running clinical model inference")
            try:
                result = run_remote_inference(
                    model_id="clinical_skin_condition_v1",
                    image_input=uploaded_image,
                    top_k=3,
                )
            except RemoteInferenceError as error:
                result = {
                    "error": True,
                    "error_code": "remote_inference_error",
                    "message": "Remote clinical inference is currently unavailable. Please try again shortly.",
                    "details": str(error),
                }
            results = {"clinical": result}
        else:
            st.write("Running dermoscopic model inference")
            progress.progress(60, text="Running dermoscopic model inference")
            try:
                result = run_remote_inference(
                    model_id="dermoscopic_cancer_risk_bcn_mnh_v1",
                    image_input=uploaded_image,
                    top_k=4,
                )
            except RemoteInferenceError as error:
                result = {
                    "error": True,
                    "error_code": "remote_inference_error",
                    "message": "Remote dermoscopic inference is currently unavailable. Please try again shortly.",
                    "details": str(error),
                }
            results = {"dermoscopic": result}

        st.write("Preparing uncertainty and safety output")
        progress.progress(80, text="Preparing uncertainty and safety output")

        st.write("Preparing learning prompt area")
        progress.progress(95, text="Preparing learning prompt area")

        st.session_state.analysis_results = results

        if result.get("error") is True:
            st.session_state.analysis_error = result
            st.session_state.analysis_status = "error"
            status_widget.update(label="Analysis error", state="error", expanded=True)
        else:
            st.session_state.analysis_status = "complete"
            status_widget.update(label="Analysis complete", state="complete", expanded=False)

    progress.progress(100, text="Complete")
    st.rerun()


def run_dermoscopic_followup(derm_image: Image.Image) -> None:
    """Run dermoscopic inference as a sequential follow-up; merges result into analysis_results."""
    progress = st.progress(0, text="Starting dermoscopic follow-up...")
    with st.status("Running dermoscopic follow-up analysis...", expanded=True) as sw:
        st.write("Preparing dermoscopic model input")
        progress.progress(30, text="Preparing dermoscopic model input")

        st.write("Running dermoscopic model inference")
        progress.progress(60, text="Running dermoscopic model inference")

        try:
            response = run_remote_inference(
                model_id="dermoscopic_cancer_risk_bcn_mnh_v1",
                image_input=derm_image,
                top_k=4,
            )
        except RemoteInferenceError as error:
            response = {
                "error": True,
                "error_code": "remote_inference_error",
                "message": "Remote dermoscopic follow-up inference is currently unavailable. Please try again shortly.",
                "details": str(error),
            }

        st.write("Preparing output")
        progress.progress(90, text="Preparing output")

        results = dict(st.session_state.get("analysis_results", {}))
        results["dermoscopic"] = response
        st.session_state.analysis_results = results

        if response.get("error") is True:
            st.session_state.dermoscopic_followup_status = "error"
            sw.update(label="Dermoscopic follow-up error", state="error", expanded=True)
        else:
            st.session_state.dermoscopic_followup_status = "complete"
            sw.update(label="Dermoscopic follow-up complete", state="complete", expanded=False)

    progress.progress(100, text="Complete")
    st.rerun()


def render_upload_card(
    label: str,
    upload_key: str,
    preview_caption: str,
    mode_note: str,
    on_change=None,
) -> tuple[Image.Image | None, str | None, bool]:
    st.markdown(
        f'<div class="section-label" style="margin-top:0.4rem">{label}</div>',
        unsafe_allow_html=True,
    )
    cb = on_change if on_change is not None else reset_analysis_state
    uploaded_file = st.file_uploader(
        label,
        type=["jpg", "jpeg", "png", "webp"],
        help="Accepted formats: JPG, JPEG, PNG, WEBP.",
        key=upload_key,
        on_change=cb,
        label_visibility="collapsed",
    )
    st.caption(mode_note)

    if uploaded_file is None:
        return None, None, False

    try:
        image = load_uploaded_image(uploaded_file)
        st.image(image, caption=preview_caption, use_container_width=True)
        render_upload_metadata(uploaded_file, image)
        return image, None, True
    except (UnidentifiedImageError, OSError):
        st.error(
            "We could not open this image. Please upload a valid JPG, JPEG, PNG, or WEBP file."
        )
        return None, "invalid_image", False


def render_right_panel(
    case_type: str,
    upload_valid: bool,
    has_image_error: bool,
    uploaded_image: Image.Image | None,
) -> None:
    st.markdown("#### Result")

    if has_image_error:
        st.markdown(
            """
            <div class="card">
              <h3>Preview unavailable</h3>
              <p>Please choose a different supported image file. No model inference has been run.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if not upload_valid:
        waiting_text = (
            "Upload a clinical photo to prepare structured educational model output."
            if case_type == "Clinical photo"
            else "Upload a dermoscopic image to prepare educational dermoscopic review output."
        )
        st.markdown(
            f"""
            <div class="card">
              <h3>Waiting for image</h3>
              <p>{waiting_text}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if st.session_state.analysis_status == "running":
        if uploaded_image is None:
            st.session_state.analysis_error = {
                "message": "The uploaded image is unavailable. Please upload a supported image and try again."
            }
            st.session_state.analysis_status = "error"
            st.rerun()
            return
        complete_analysis(case_type, uploaded_image)
        return

    if st.session_state.analysis_status == "error":
        render_analysis_error(st.session_state.analysis_error)
        return

    received_text = (
        "Select Analyze case to prepare structured educational model output for this image."
        if case_type == "Clinical photo"
        else "Select Analyze case to prepare educational dermoscopic review output for this image."
    )
    st.markdown(
        f"""
        <div class="card">
          <h3>Image received</h3>
          <p>{received_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dermoscopic_followup_panel() -> None:
    """Render follow-up upload card and analysis button on the final result screen."""
    followup_status = st.session_state.get("dermoscopic_followup_status", "idle")

    st.markdown(
        """
        <div class="followup-card">
          <div class="section-label" style="margin-top:0">Dermoscopic follow-up image recommended for this learning case</div>
          <p class="followup-card-text">
            The clinical model routed this case to lesion review. You can upload a dermoscopic
            or close-up lesion image to continue the educational review.
            Model output is not diagnosis. Qualified review is required for real decisions.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    derm_image, derm_err, derm_valid = render_upload_card(
        label="Dermoscopic / close-up lesion image",
        upload_key="upload_followup_derm",
        preview_caption="Dermoscopic follow-up preview",
        mode_note=(
            "Dermoscopic or magnified lesion image. "
            "Not a regular clinical photo. Model output is not diagnosis."
        ),
        on_change=reset_followup_state,
    )

    if followup_status == "running":
        if derm_image is not None:
            run_dermoscopic_followup(derm_image)
        else:
            st.session_state.dermoscopic_followup_status = "idle"
            st.rerun()
        return

    if followup_status == "error":
        results = st.session_state.get("analysis_results", {})
        render_analysis_error(results.get("dermoscopic"))

    if st.button(
        "Analyze dermoscopic follow-up",
        disabled=not derm_valid or bool(derm_err) or followup_status == "running",
        type="primary",
    ):
        st.session_state.dermoscopic_followup_status = "running"
        st.rerun()


def load_uploaded_image(uploaded_file) -> Image.Image:
    uploaded_file.seek(0)
    with Image.open(uploaded_file) as image:
        rgb_image = image.convert("RGB")
    uploaded_file.seek(0)
    return rgb_image


def render_upload_metadata(uploaded_file, image: Image.Image) -> None:
    st.markdown("##### Uploaded file")
    name_col, type_col = st.columns(2)
    with name_col:
        st.metric("Filename", uploaded_file.name)
    with type_col:
        st.metric("File type", uploaded_file.type or "Unknown")

    size_col, dimension_col = st.columns(2)
    with size_col:
        st.metric("File size", format_file_size(uploaded_file.size))
    with dimension_col:
        st.metric("Dimensions", f"{image.width} × {image.height}px")


def format_file_size(num_bytes: int) -> str:
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.2f} MB"


def render_analysis_result(response: dict | None, mode_config: dict[str, str | int]) -> None:
    if not response:
        render_analysis_error({"message": "No analysis result is available. Please try again."})
        return

    top_prediction = response.get("top_prediction") or {}
    uncertainty = response.get("uncertainty") or {}
    predictions = response.get("predictions") or []

    label = top_prediction.get("label", "Unavailable")
    conf_pct = top_prediction.get("confidence_percent")
    conf_str = format_percent(conf_pct)
    conf_class = _confidence_color_class(conf_pct)

    st.markdown(
        f"""
        <div class="section-label">{mode_config["result_heading"]}</div>
        <div class="top-pred-card">
          <div class="top-pred-header">
            <span class="top-pred-label">{label}</span>
            <span class="conf-badge {conf_class}">{conf_str}</span>
          </div>
          <p class="top-pred-note">Rank 1 output &mdash; {mode_config["result_note"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    unc_bucket = uncertainty.get("bucket", "")
    unc_label = uncertainty.get("label", "Unavailable")
    unc_explanation = uncertainty.get("explanation", "No uncertainty explanation returned.")
    unc_class = _uncertainty_class(unc_bucket)

    st.markdown(
        f"""
        <div class="section-label">Uncertainty</div>
        <span class="unc-badge {unc_class}">{unc_label}</span>
        <p class="unc-explanation">{unc_explanation}</p>
        """,
        unsafe_allow_html=True,
    )

    if response.get("low_certainty") is True:
        msg = response.get(
            "low_certainty_message",
            "The model output is uncertain. Use this only for educational review. "
            "This is not a diagnosis and does not recommend treatment.",
        )
        reason = response.get("low_certainty_reason") or ""
        reason_html = f"<br><small style='opacity:0.8'>{reason}</small>" if reason else ""
        st.markdown(
            f"""
            <div class="low-certainty-card">
              <div class="low-certainty-marker">!</div>
              <div><strong>Low certainty</strong><br>{msg}{reason_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="section-label">{mode_config["top_outputs_heading"]}</div>',
        unsafe_allow_html=True,
    )
    if predictions:
        rows_html = ""
        for pred in predictions[: int(mode_config["top_k"])]:
            pred_label = pred.get("label", "Unavailable")
            pred_conf_pct = pred.get("confidence_percent")
            pred_conf_str = format_percent(pred_conf_pct)
            bar_width = min(
                max(float(pred_conf_pct) if isinstance(pred_conf_pct, (int, float)) else 0, 0),
                100,
            )
            rank = pred.get("rank", "")
            rows_html += (
                f'<div class="pred-row">'
                f'<span class="pred-rank">{rank}</span>'
                f'<span class="pred-label-text">{pred_label}</span>'
                f'<div class="pred-bar-outer">'
                f'<div class="pred-bar-inner" style="width:{bar_width:.1f}%"></div>'
                f'</div>'
                f'<span class="pred-conf-text">{pred_conf_str}</span>'
                f'</div>'
            )
        st.markdown(f'<div class="pred-list">{rows_html}</div>', unsafe_allow_html=True)
    else:
        st.write("No ranked outputs were returned.")

    st.markdown('<div class="section-label">Safety Note</div>', unsafe_allow_html=True)
    st.info(response.get("safety_note", "No safety note returned."))

    limitations = response.get("model_limitations") or []
    if limitations:
        with st.expander("Model limitations", expanded=False):
            for limitation in limitations:
                st.markdown(f"- {limitation}")

    next_step = response.get("recommended_next_step")
    if next_step:
        st.markdown(
            f"""
            <div class="next-step-card">
              <div class="section-label" style="margin-top:0">Recommended next step</div>
              <p class="next-step-text">{next_step}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _confidence_color_class(conf_pct: object) -> str:
    if not isinstance(conf_pct, (int, float)):
        return "conf-unknown"
    if conf_pct >= 70.0:
        return "conf-high"
    if conf_pct >= 40.0:
        return "conf-medium"
    return "conf-low"


def _uncertainty_class(bucket: str) -> str:
    if bucket == "high_confidence":
        return "unc-high"
    if bucket == "medium_confidence":
        return "unc-medium"
    return "unc-low"


def render_analysis_error(error_response: dict | None) -> None:
    error_response = error_response or {}
    message = error_response.get(
        "message",
        "The educational image review could not be prepared. Please try again.",
    )
    st.error(message)
    if error_response.get("error_code"):
        st.caption(f"Adapter error code: {error_response['error_code']}")


def format_percent(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.2f}%"
    return "Unavailable"


def render_safety_footer() -> None:
    st.markdown(
        """
        <div class="safety-footer">
          <strong>Prototype educational output only.</strong>
          This is not a diagnosis and does not recommend treatment.
          Confidence is model confidence, not clinical certainty.
          Qualified review is required for real decisions.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _collect_learner_context() -> dict[str, str]:
    return {
        "body_location": st.session_state.get("ctx_body_location", "not provided"),
        "duration": st.session_state.get("ctx_duration", "not provided"),
        "itching": st.session_state.get("ctx_itching", "not provided"),
        "pain_tenderness": st.session_state.get("ctx_pain_tenderness", "not provided"),
        "change_over_time": st.session_state.get("ctx_change_over_time", "not provided"),
        "bleeding_crusting_discharge": st.session_state.get(
            "ctx_bleeding_crusting_discharge", "not provided"
        ),
        "prior_episodes": st.session_state.get("ctx_prior_episodes", "not provided"),
        "image_quality_concern": st.session_state.get("ctx_image_quality_concern", "not provided"),
        "learner_note": st.session_state.get("ctx_learner_note", "").strip(),
    }


def render_learner_context_form() -> None:
    with st.expander("Learning context (optional)", expanded=True):
        st.caption(
            "Optional context for educational discussion. "
            "This information is not used by the image model."
        )
        col_a, col_b = st.columns(2)
        with col_a:
            st.selectbox(
                "Body location / anatomical site",
                options=_CONTEXT_OPTIONS["body_location"],
                key="ctx_body_location",
            )
            st.selectbox(
                "Duration",
                options=_CONTEXT_OPTIONS["duration"],
                key="ctx_duration",
            )
            st.selectbox(
                "Itching",
                options=_CONTEXT_OPTIONS["itching"],
                key="ctx_itching",
            )
            st.selectbox(
                "Pain / tenderness",
                options=_CONTEXT_OPTIONS["pain_tenderness"],
                key="ctx_pain_tenderness",
            )
        with col_b:
            st.selectbox(
                "Change over time / spreading",
                options=_CONTEXT_OPTIONS["change_over_time"],
                key="ctx_change_over_time",
            )
            st.selectbox(
                "Bleeding / crusting / discharge",
                options=_CONTEXT_OPTIONS["bleeding_crusting_discharge"],
                key="ctx_bleeding_crusting_discharge",
            )
            st.selectbox(
                "Prior similar episodes",
                options=_CONTEXT_OPTIONS["prior_episodes"],
                key="ctx_prior_episodes",
            )
            st.selectbox(
                "Image quality concern",
                options=_CONTEXT_OPTIONS["image_quality_concern"],
                key="ctx_image_quality_concern",
            )
        st.text_area(
            "Learner note (optional)",
            placeholder=(
                "Optional: add any context you would share in an educational discussion of this case."
            ),
            key="ctx_learner_note",
            height=80,
        )


def render_context_summary_card() -> None:
    ctx = _collect_learner_context()
    filled = {
        _CONTEXT_LABELS[k]: v
        for k, v in ctx.items()
        if k in _CONTEXT_LABELS and k != "learner_note" and v != "not provided"
    }
    note = ctx.get("learner_note", "")

    if not filled and not note:
        st.caption("No learning context added yet. Context is optional.")
        return

    tags_html = ""
    for label, value in filled.items():
        tags_html += (
            f'<span class="ctx-tag">'
            f'<span class="ctx-tag-label">{label}:</span>'
            f'<span class="ctx-tag-value">{value}</span>'
            f'</span>'
        )
    if note:
        truncated = note[:60] + ("..." if len(note) > 60 else "")
        tags_html += (
            f'<span class="ctx-tag">'
            f'<span class="ctx-tag-label">Note:</span>'
            f'<span class="ctx-tag-value">{truncated}</span>'
            f'</span>'
        )

    st.markdown(
        f"""
        <div class="context-summary-card">
          <div class="section-label" style="margin-top:0">Context for prompt export</div>
          <div class="ctx-tags">{tags_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_result_context_summary(ctx: dict[str, str]) -> None:
    has_any = any(v and v != "not provided" for k, v in ctx.items())
    with st.expander("Learning context (collected for prompt export)", expanded=False):
        st.caption(
            "This context will be used to build a ChatGPT/Claude prompt export in a later step. "
            "It was not used as input to the image model."
        )
        if has_any:
            for key, label in _CONTEXT_LABELS.items():
                val = ctx.get(key, "")
                if val and val != "not provided":
                    st.markdown(f"- **{label}:** {val}")
        else:
            st.caption("No context was provided for this analysis.")


def render_final_result_screen(case_type: str) -> None:
    results = st.session_state.get("analysis_results", {})
    clinical_response = results.get("clinical")
    derm_response = results.get("dermoscopic")
    is_lesion_routing = _clinical_top_is_lesion_routing(clinical_response)
    has_derm_result = bool(derm_response)

    result_col, prompt_col = st.columns([1, 1], gap="large")

    with result_col:
        if case_type == "Dermoscopic image":
            st.markdown("#### Revela model result")
            if derm_response and not derm_response.get("error"):
                render_analysis_result(derm_response, get_mode_config("Dermoscopic image"))
            else:
                render_analysis_error(derm_response)

        elif has_derm_result:
            # Clinical result with dermoscopic follow-up completed
            st.markdown("#### Revela model results")
            st.markdown("**Clinical model output**")
            if clinical_response and not clinical_response.get("error"):
                render_analysis_result(clinical_response, get_mode_config("Clinical photo"))
            else:
                render_analysis_error(clinical_response)
            st.markdown("---")
            st.markdown("**Dermoscopic follow-up output**")
            if derm_response and not derm_response.get("error"):
                render_analysis_result(derm_response, get_mode_config("Dermoscopic image"))
            else:
                render_analysis_error(derm_response)

        else:
            # Clinical result only (follow-up may be offered below)
            st.markdown("#### Revela model result")
            if clinical_response and not clinical_response.get("error"):
                render_analysis_result(clinical_response, get_mode_config("Clinical photo"))
            else:
                render_analysis_error(clinical_response)

            if is_lesion_routing:
                render_dermoscopic_followup_panel()

    with prompt_col:
        st.markdown("#### Continue in ChatGPT / Claude")
        render_prompt_export()
        _render_result_context_summary(st.session_state.get("learner_context", {}))

        if is_lesion_routing:
            render_learner_rating_form()


def _clinical_top_is_lesion_routing(clinical_response: dict | None) -> bool:
    if not clinical_response or clinical_response.get("error"):
        return False
    top = clinical_response.get("top_prediction") or {}
    return top.get("label") == LESION_ROUTING_LABEL


def render_learner_rating_form() -> None:
    with st.expander("Learner reflection — lesion routing flagged", expanded=True):
        st.caption(
            "The clinical model output suggests dermoscopic review. "
            "This learning reflection is optional and does not change model output. "
            "Confidence is model confidence, not clinical certainty."
        )

        st.slider(
            "Educational concern level (1 = low concern, 5 = high concern)",
            min_value=1,
            max_value=5,
            value=3,
            step=1,
            key="lrt_concern",
        )

        st.radio(
            "Would you prioritize dermoscopic review for this case?",
            options=["yes", "no", "unsure"],
            index=2,
            key="lrt_prioritize",
            horizontal=True,
        )

        st.text_area(
            "Visible cues that influenced your rating (optional)",
            key="lrt_cues",
            height=80,
            placeholder=(
                "Describe any features you noticed that informed your rating, "
                "for educational discussion only."
            ),
        )

        st.markdown(
            """
            <p class="rating-disclaimer">
            This is a learning reflection, not a diagnosis.
            The rating does not change model output.
            Qualified review is required for real decisions.
            </p>
            """,
            unsafe_allow_html=True,
        )

        st.session_state.learner_rating = {
            "concern": st.session_state.get("lrt_concern", 3),
            "prioritize_dermoscopy": st.session_state.get("lrt_prioritize", "unsure"),
            "visible_cues": st.session_state.get("lrt_cues", "").strip(),
        }


def render_prompt_export() -> None:
    results = st.session_state.get("analysis_results", {})
    clinical_response = results.get("clinical")
    derm_response = results.get("dermoscopic")
    learner_context = st.session_state.get("learner_context") or None
    learner_rating = st.session_state.get("learner_rating") or None

    has_clinical = bool(clinical_response and not (clinical_response or {}).get("error"))
    has_derm = bool(derm_response and not (derm_response or {}).get("error"))

    if has_clinical and has_derm:
        prompt_case_type = "Paired clinical + dermoscopic case"
    elif has_derm:
        prompt_case_type = "Dermoscopic image only"
    else:
        prompt_case_type = "Clinical photo only"

    prompt = build_llm_transfer_prompt(
        case_type=prompt_case_type,
        clinical_response=clinical_response,
        dermoscopic_response=derm_response,
        learner_context=learner_context,
        learner_rating=learner_rating,
    )

    st.caption(
        "Copy this prompt into ChatGPT or Claude to continue the case "
        "as an educational reasoning exercise."
    )
    st.text_area(
        "Generated prompt",
        value=prompt,
        height=400,
        label_visibility="collapsed",
    )
    st.download_button(
        label="Download prompt (.txt)",
        data=prompt,
        file_name="revela_case_prompt.txt",
        mime="text/plain",
    )


def render_overview_tab() -> None:
    st.subheader("Product Overview")
    st.write(
        "Revela is a portfolio-ready prototype for educational dermatology image review. "
        "The app is designed to show model outputs, uncertainty, limitations, and evaluation context in one calm workflow."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        render_card(
            "Clinical Photo Mode",
            "Uses the current clinical-image model for common condition-oriented outputs and lesion-routing review.",
        )
    with col2:
        render_card(
            "Dermoscopic Mode",
            "Uses the dermoscopic BCN+MNH model for educational dermoscopic image review.",
        )
    with col3:
        render_card(
            "Transparent Results",
            "Inference uses the canonical schema with top outputs, uncertainty, safety notes, and limitations.",
        )

    st.markdown("### Current Build Status")
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        render_card(
            "Available now",
            "Clinical-photo mode is available for educational local inference with transparent model outputs.",
        )
    with status_col2:
        render_card(
            "Dermoscopic mode",
            "The improved dermoscopic model is available for educational local inference.",
        )


def render_transparency_tab() -> None:
    st.subheader("Model Transparency")
    st.write("The app uses explicit model roles rather than one hidden universal classifier.")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("#### Clinical model")
        st.markdown("`clinical_skin_condition_v1` backed by `clinical_v2_effnet_b0`")
        st.markdown("Role: clinical-photo condition and lesion-routing prototype.")
        st.markdown("Classes:")
        for label in CLINICAL_CLASSES:
            st.markdown(f"- `{label}`")
        st.info("The lesion-routing class is not cancer detection.")

    with col2:
        st.markdown("#### Dermoscopic model")
        st.markdown("`dermoscopic_cancer_risk_bcn_mnh_v1`")
        st.markdown("Role: dermoscopic educational review prototype.")
        st.markdown("Classes:")
        for label in DERMOSCOPIC_CLASSES:
            st.markdown(f"- `{label}`")
        st.info("Model confidence is not clinical certainty.")

    st.markdown("---")
    st.markdown(
        "`dermoscopic_baseline_v1` is a developer smoke-test model only. "
        "It should not drive public product behavior, UI copy, or demo claims."
    )


def render_metrics_tab() -> None:
    st.subheader("Evaluation Metrics")
    st.caption("Prototype held-out evaluation metrics. These are not clinical validation.")

    metric_rows = [
        ("Accuracy", "0.6554"),
        ("Macro-F1", "0.6420"),
        ("Balanced accuracy", "0.6571"),
        ("Lesion-routing F1", "0.8282"),
        ("Google SCIN macro-F1", "0.4028"),
        ("Fitzpatrick17k macro-F1", "0.6366"),
    ]
    cols = st.columns(3)
    for index, (label, value) in enumerate(metric_rows):
        with cols[index % 3]:
            render_metric_card(label, value)

    st.markdown(
        """
        <div class="note">
        Metrics describe prototype model behavior on held-out data. They should be used for transparency and model-improvement planning, not as clinical-readiness claims.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_benchmark_tab() -> None:
    st.subheader("Benchmark")
    st.write(
        "This area is reserved for a future qualitative portfolio benchmark. "
        "It may compare structured model outputs with selected multimodal AI responses for educational review."
    )
    col1, col2 = st.columns(2)
    with col1:
        render_card(
            "Planned comparison",
            "Case examples, model output, confidence framing, and reviewer notes.",
        )
    with col2:
        render_card(
            "Boundary",
            "The benchmark is not clinical validation and should not be presented as diagnostic performance.",
        )


def render_limitations_tab() -> None:
    st.subheader("About / Limitations")
    limitations = [
        "Revela is not a diagnostic product.",
        "The app does not provide treatment advice.",
        "Model confidence is not clinical certainty.",
        "Performance can vary with image quality, lighting, skin tone, and dataset source.",
        "Dermoscopic model output is educational and requires qualified review for real decisions.",
        "The clinical lesion-routing class is not cancer detection.",
    ]
    for item in limitations:
        st.markdown(f"- {item}")

    st.markdown("### Run Locally")
    st.code("streamlit run app.py", language="bash")


def render_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="card">
          <h3>{title}</h3>
          <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-value">{value}</div>
          <div class="metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
