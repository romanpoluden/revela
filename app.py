from __future__ import annotations

from PIL import Image, UnidentifiedImageError
import streamlit as st

from src.inference.adapter import run_inference


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
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
            max-width: 1180px;
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
        (1, "Choose image type"),
        (2, "Upload image"),
        (3, "Review model output"),
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

    if st.session_state.analysis_status in ("complete", "error", "running"):
        _step = 3
    elif st.session_state.get("file_uploaded", False):
        _step = 2
    else:
        _step = 1
    render_step_indicator(_step)

    input_mode = st.radio(
        "Choose image type",
        ["Clinical photo", "Dermoscopic image"],
        horizontal=True,
        on_change=reset_analysis_state,
    )
    mode_config = get_mode_config(input_mode)

    left, right = st.columns([0.95, 1.05], gap="large")
    uploaded_image = None
    image_error = None
    valid_image_uploaded = False

    with left:
        uploaded_file = st.file_uploader(
            mode_config["upload_label"],
            type=["jpg", "jpeg", "png", "webp"],
            help="Accepted formats: JPG, JPEG, PNG, WEBP.",
            key=f"upload_{mode_config['input_mode']}",
            on_change=reset_analysis_state,
        )
        st.info(mode_config["mode_note"])

        if uploaded_file is None:
            render_empty_upload_state(mode_config)
        else:
            try:
                uploaded_image = load_uploaded_image(uploaded_file)
                valid_image_uploaded = True
                st.session_state.file_uploaded = True
                st.image(
                    uploaded_image,
                    caption=mode_config["preview_caption"],
                    use_container_width=True,
                )
                render_upload_metadata(uploaded_file, uploaded_image)
            except (UnidentifiedImageError, OSError):
                image_error = (
                    "We could not open this image. Please upload a valid JPG, JPEG, PNG, or WEBP file."
                )
                st.error(image_error)

        if st.button(
            "Analyze case",
            disabled=not valid_image_uploaded
            or st.session_state.analysis_status == "running",
        ):
            start_analysis()
            st.rerun()

    with right:
        st.markdown("#### Result")
        render_result_panel(
            mode_config=mode_config,
            has_upload=uploaded_file is not None,
            image_error=image_error,
            uploaded_image=uploaded_image,
        )

    render_safety_footer()


def get_mode_config(input_mode: str) -> dict[str, str | int]:
    if input_mode == "Dermoscopic image":
        return {
            "input_mode": input_mode,
            "model_id": "dermoscopic_cancer_risk_bcn_mnh_v1",
            "top_k": 4,
            "upload_label": "Upload a dermoscopic image",
            "preview_caption": "Dermoscopic image preview",
            "mode_note": (
                "Dermoscopic mode shows educational dermoscopic review output from a local "
                "prototype model. Model output is not diagnosis. Review by a qualified "
                "clinician is required for real decisions."
            ),
            "waiting_text": (
                "Upload a supported dermoscopic image to prepare educational dermoscopic review output."
            ),
            "received_text": (
                "Select Analyze case to prepare educational dermoscopic review output for this image."
            ),
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
        "upload_label": "Upload a clinical photo",
        "preview_caption": "Clinical photo preview",
        "mode_note": (
            "Clinical-photo mode runs a local prototype model and displays structured educational output."
        ),
        "waiting_text": (
            "Upload a supported clinical photo to prepare structured educational model output."
        ),
        "received_text": (
            "Select Analyze case to prepare structured educational model output for this image."
        ),
        "result_heading": "Educational Model Output",
        "top_outputs_heading": "Top-3 Outputs",
        "result_note": "Model output, not diagnosis.",
    }


def initialize_analysis_state() -> None:
    if "analysis_status" not in st.session_state:
        st.session_state.analysis_status = "idle"
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "analysis_error" not in st.session_state:
        st.session_state.analysis_error = None
    if "file_uploaded" not in st.session_state:
        st.session_state.file_uploaded = False


def reset_analysis_state() -> None:
    st.session_state.analysis_status = "idle"
    st.session_state.analysis_result = None
    st.session_state.analysis_error = None
    st.session_state.file_uploaded = False


def start_analysis() -> None:
    st.session_state.analysis_status = "running"
    st.session_state.analysis_result = None
    st.session_state.analysis_error = None


def complete_analysis(image: Image.Image, mode_config: dict[str, str | int]) -> None:
    with st.spinner("Preparing educational image review..."):
        try:
            response = run_inference(
                model_id=str(mode_config["model_id"]),
                image_input=image,
                top_k=int(mode_config["top_k"]),
            )
        except Exception as error:
            response = {
                "error": True,
                "error_code": "frontend_inference_error",
                "message": "The educational image review could not be prepared. Please try again.",
                "details": str(error),
            }

        st.session_state.analysis_result = response

        if response.get("error") is True:
            st.session_state.analysis_error = response
            st.session_state.analysis_status = "error"
        else:
            st.session_state.analysis_status = "complete"

    st.rerun()


def render_empty_upload_state(mode_config: dict[str, str | int]) -> None:
    st.markdown(
        f"""
        <div class="card">
          <h3>No image selected</h3>
          <p>{mode_config["waiting_text"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def render_result_panel(
    mode_config: dict[str, str | int],
    has_upload: bool,
    image_error: str | None,
    uploaded_image: Image.Image | None,
) -> None:
    if image_error is not None:
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

    if not has_upload:
        st.markdown(
            f"""
            <div class="card">
              <h3>Waiting for image</h3>
              <p>{mode_config["waiting_text"]}</p>
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
        complete_analysis(uploaded_image, mode_config)
        return

    if st.session_state.analysis_status == "complete":
        render_analysis_result(st.session_state.analysis_result, mode_config)
        return

    if st.session_state.analysis_status == "error":
        render_analysis_error(st.session_state.analysis_error)
        return

    st.markdown(
        f"""
        <div class="card">
          <h3>Image received</h3>
          <p>{mode_config["received_text"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
