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
            margin: 0 0 0.4rem 0;
            letter-spacing: 0;
            color: #102a43;
        }
        .hero p {
            color: #34495e;
            font-size: 1.05rem;
            margin: 0.25rem 0;
        }
        .note {
            padding: 0.85rem 1rem;
            border-left: 4px solid #2f6f73;
            background: #f4f9f8;
            border-radius: 8px;
            color: #1f3f46;
            margin: 0.8rem 0 1rem 0;
        }
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
        .disabled-panel {
            border: 1px dashed #aebdca;
            border-radius: 10px;
            padding: 1rem;
            background: #f8fafc;
            color: #425466;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="status-pill">Prototype app shell</div>
          <h1>Revela</h1>
          <p><strong>Educational AI skin-image training aid</strong></p>
          <p>Explore structured skin-image review with transparent model outputs, confidence framing, and prototype evaluation metrics.</p>
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
            "Reserved for the planned cancer-risk model. This mode stays disabled until retraining and evaluation are complete.",
        )
    with col3:
        render_card(
            "Transparent Results",
            "Future inference will use the canonical schema with top predictions, uncertainty, safety notes, and limitations.",
        )

    st.markdown("### Current Build Status")
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        render_card(
            "Available now",
            "Clinical model artifacts and held-out evaluation are complete. Local inference plumbing exists but is intentionally not connected in this layout task.",
        )
    with status_col2:
        render_card(
            "Coming next",
            "Dermoscopic cancer-risk model retraining, evaluation, and later Streamlit inference wiring.",
        )


def render_analyze_tab() -> None:
    st.subheader("Analyze Image")
    st.caption("Clinical-photo mode uses the local educational inference adapter.")
    initialize_analysis_state()

    input_mode = st.radio(
        "Choose image type",
        ["Clinical photo", "Dermoscopic image"],
        horizontal=True,
    )

    left, right = st.columns([0.95, 1.05], gap="large")
    uploaded_image = None
    image_error = None
    valid_clinical_image_uploaded = False

    with left:
        if input_mode == "Clinical photo":
            uploaded_file = st.file_uploader(
                "Upload a clinical photo",
                type=["jpg", "jpeg", "png", "webp"],
                help="Accepted formats: JPG, JPEG, PNG, WEBP.",
                on_change=reset_analysis_state,
            )
            st.info(
                "Clinical-photo mode runs a local prototype model and displays structured educational output."
            )

            if uploaded_file is None:
                render_empty_upload_state()
            else:
                try:
                    uploaded_image = load_uploaded_image(uploaded_file)
                    valid_clinical_image_uploaded = True
                    st.image(
                        uploaded_image,
                        caption="Clinical photo preview",
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
                disabled=not valid_clinical_image_uploaded
                or st.session_state.analysis_status == "running",
            ):
                start_analysis()
                st.rerun()
        else:
            uploaded_file = None
            st.markdown(
                """
                <div class="disabled-panel">
                <strong>Dermoscopic analysis coming soon.</strong><br>
                The dermoscopic cancer-risk model is pending retraining and evaluation.
                The old dermoscopic baseline is not exposed in the public UI.
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button("Dermoscopic analysis unavailable", disabled=True)

    with right:
        st.markdown("#### Result Preview")
        render_result_panel(
            input_mode=input_mode,
            has_upload=uploaded_file is not None,
            image_error=image_error,
            uploaded_image=uploaded_image,
        )


def initialize_analysis_state() -> None:
    if "analysis_status" not in st.session_state:
        st.session_state.analysis_status = "idle"
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "analysis_error" not in st.session_state:
        st.session_state.analysis_error = None


def reset_analysis_state() -> None:
    st.session_state.analysis_status = "idle"
    st.session_state.analysis_result = None
    st.session_state.analysis_error = None


def start_analysis() -> None:
    st.session_state.analysis_status = "running"
    st.session_state.analysis_result = None
    st.session_state.analysis_error = None


def complete_analysis(image: Image.Image) -> None:
    with st.spinner("Preparing educational image review..."):
        try:
            response = run_inference(
                model_id="clinical_skin_condition_v1",
                image_input=image,
                top_k=3,
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


def render_empty_upload_state() -> None:
    st.markdown(
        """
        <div class="card">
          <h3>No image selected</h3>
          <p>Upload a clinical photo to preview it here. Model inference is intentionally not connected in this UI task.</p>
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
    input_mode: str,
    has_upload: bool,
    image_error: str | None,
    uploaded_image: Image.Image | None,
) -> None:
    if input_mode == "Dermoscopic image":
        st.warning(
            "Dermoscopic mode is intentionally disabled until `dermoscopic_cancer_risk_v2` is ready."
        )
        return

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
            """
            <div class="card">
              <h3>Waiting for image</h3>
              <p>Upload a supported clinical photo to prepare structured educational model output.</p>
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
        complete_analysis(uploaded_image)
        return

    if st.session_state.analysis_status == "complete":
        render_analysis_result(st.session_state.analysis_result)
        return

    if st.session_state.analysis_status == "error":
        render_analysis_error(st.session_state.analysis_error)
        return

    st.markdown(
        """
        <div class="card">
          <h3>Image received</h3>
          <p>Select Analyze case to prepare structured educational model output for this image.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analysis_result(response: dict | None) -> None:
    if not response:
        render_analysis_error({"message": "No analysis result is available. Please try again."})
        return

    top_prediction = response.get("top_prediction") or {}
    uncertainty = response.get("uncertainty") or {}
    predictions = response.get("predictions") or []

    st.markdown("##### Educational Model Output")
    label_col, confidence_col = st.columns(2)
    with label_col:
        st.metric("Top output", top_prediction.get("label", "Unavailable"))
    with confidence_col:
        st.metric(
            "Model confidence",
            format_percent(top_prediction.get("confidence_percent")),
        )

    st.markdown("##### Uncertainty")
    st.write(uncertainty.get("label", "Unavailable"))
    st.caption(uncertainty.get("explanation", "No uncertainty explanation returned."))
    if response.get("low_certainty") is True:
        st.warning(
            response.get(
                "low_certainty_message",
                "The model output is uncertain. Use this only for educational review. "
                "Review the top outputs, image quality, and clinical context, and consider "
                "additional image/context review. "
                "This is not a diagnosis and does not recommend treatment.",
            )
        )
        if response.get("low_certainty_reason"):
            st.caption(response["low_certainty_reason"])

    st.markdown("##### Top-3 Outputs")
    if predictions:
        for index, prediction in enumerate(predictions[:3], start=1):
            label = prediction.get("label", "Unavailable")
            confidence = format_percent(prediction.get("confidence_percent"))
            st.write(f"{index}. {label} - {confidence}")
    else:
        st.write("No ranked outputs were returned.")

    st.markdown("##### Safety Note")
    st.info(response.get("safety_note", "No safety note returned."))

    st.markdown("##### Model Limitations")
    limitations = response.get("model_limitations") or []
    if limitations:
        for limitation in limitations:
            st.markdown(f"- {limitation}")
    else:
        st.write("No model limitations returned.")

    st.markdown("##### Recommended Next Step")
    st.write(response.get("recommended_next_step", "No next-step guidance returned."))


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
        st.markdown("`dermoscopic_cancer_risk_v2`")
        st.markdown("Role: planned dermoscopic educational cancer-risk category model.")
        st.markdown("Expected classes:")
        for label in DERMOSCOPIC_CLASSES:
            st.markdown(f"- `{label}`")
        st.warning("Pending retraining and held-out evaluation.")

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
        "The dermoscopic cancer-risk model is pending retraining and evaluation.",
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
