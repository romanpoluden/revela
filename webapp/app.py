from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError
import streamlit as st

# Allow imports from project root
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

try:
    from src.inference.adapter import run_inference as _run_inference
    _MODELS_AVAILABLE = True
except Exception:
    _MODELS_AVAILABLE = False
    _run_inference = None  # type: ignore[assignment]

# ── HuggingFace model identifiers ────────────────────────────────────────────
HF_CLINICAL_MODEL = "RevelaCap/clinical-skin-condition-v1"
HF_DERMO_MODEL = "RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1"

LOCAL_MODEL_IDS = {
    "Clinical Photo": "clinical_skin_condition_v1",
    "Dermoscopic Image": "dermoscopic_cancer_risk_bcn_mnh_v1",
}

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

RECOMMENDED_ACTIONS = {
    "Melanoma": [
        "Urgent dermatology referral within 2 weeks",
        "Full-body skin examination",
        "Consider sentinel lymph node biopsy",
    ],
    "Non-melanoma skin cancer": [
        "Dermatology referral for biopsy",
        "Document lesion size and borders",
        "Discuss treatment options (excision, Mohs)",
    ],
    "Benign nevus": [
        "Document with dermoscopy photography",
        "Annual skin check recommended",
        "Educate patient on ABCDE self-monitoring",
    ],
    "Other non-cancer / indeterminate lesion": [
        "Clinical correlation advised",
        "Short-interval follow-up in 3–6 months",
        "Consider biopsy if change observed",
    ],
    "Eczema / dermatitis": [
        "Topical corticosteroids (mild–moderate)",
        "Identify and avoid triggers",
        "Emollient therapy twice daily",
    ],
    "Urticaria / allergic reaction": [
        "Oral antihistamine (cetirizine / loratadine)",
        "Identify allergen — allergy panel if recurrent",
        "Epinephrine autoinjector if anaphylaxis risk",
    ],
    "Folliculitis / acne-like": [
        "Topical antibiotic (clindamycin) or benzoyl peroxide",
        "Warm compress for comfort",
        "Review skincare routine and irritants",
    ],
    "Psoriasis / papulosquamous": [
        "Topical corticosteroids + vitamin D analogue",
        "Dermatology referral for moderate-severe disease",
        "Screen for psoriatic arthritis",
    ],
    "Lesion — dermoscopic review recommended": [
        "Proceed to dermoscopic evaluation",
        "Do not delay — book dermoscopy within 2 weeks",
        "Document clinical presentation with photography",
    ],
}

QUESTIONNAIRE: list[dict] = [
    {
        "key": "q_duration",
        "step_label": "Step 3 of 5: Clinical History",
        "question": "How long have you noticed this?",
        "options": [
            "A few days",
            "1–2 weeks",
            "A few weeks",
            "Several months",
            "Longer / recurring",
            "Not sure",
        ],
    },
    {
        "key": "q_itch",
        "step_label": "Step 3 of 5: Symptom Assessment",
        "question": "Does it itch?",
        "options": ["No", "Mild itching", "Moderate itching", "Severe itching"],
    },
    {
        "key": "q_pain",
        "step_label": "Step 3 of 5: Pain & Tenderness",
        "question": "Is it painful or tender?",
        "options": ["No", "Mild discomfort", "Moderate pain", "Severe pain"],
    },
]

NAV_STEPS = [
    ("Overview", "🏠"),
    ("Image Type", "🔬"),
    ("Upload", "⬆"),
    ("History", "📋"),
    ("Results", "📊"),
]

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
<style>
/* ── Base ── */
[data-testid="stAppViewContainer"] {background: #0D1117;}
[data-testid="stSidebar"] {background: #111827; border-right: 1px solid #1F2937;}
[data-testid="stSidebar"] * {color: #E5E7EB !important;}
[data-testid="stHeader"] {background: transparent;}
section[data-testid="stSidebar"] > div {padding-top: 1.5rem;}

/* ── Typography ── */
h1, h2, h3, h4, h5, h6 {color: #F9FAFB !important;}
p, li, span, label {color: #D1D5DB;}
.stMarkdown p {color: #D1D5DB;}

/* ── Sidebar brand ── */
.revela-brand {
    padding: 0 0 1.5rem 0;
    border-bottom: 1px solid #1F2937;
    margin-bottom: 1.5rem;
}
.revela-brand .logo {
    font-size: 1.5rem;
    font-weight: 800;
    color: #F9FAFB !important;
    letter-spacing: -0.5px;
}
.revela-brand .logo span {color: #10B981 !important;}
.revela-brand .subtitle {
    font-size: 0.72rem;
    color: #6B7280 !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 2px;
}

/* ── Nav items ── */
.nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    color: #9CA3AF !important;
    transition: all 0.15s;
}
.nav-item:hover {background: #1F2937;}
.nav-item.active {
    background: #064E3B;
    color: #10B981 !important;
    font-weight: 600;
}
.nav-item .nav-icon {font-size: 1rem;}

/* ── Hero ── */
.hero-section {
    background: linear-gradient(135deg, #111827 0%, #0D1117 100%);
    border: 1px solid #1F2937;
    border-radius: 16px;
    padding: 3rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-section::before {
    content: "";
    position: absolute;
    top: -80px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(16,185,129,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16,185,129,0.12);
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.78rem;
    color: #10B981 !important;
    margin-bottom: 1rem;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    color: #F9FAFB !important;
    line-height: 1.2;
    margin-bottom: 1rem;
}
.hero-title span {
    background: linear-gradient(90deg, #10B981, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-subtitle {
    font-size: 1.05rem;
    color: #9CA3AF !important;
    max-width: 560px;
    line-height: 1.7;
    margin-bottom: 2rem;
}

/* ── Step cards (roadmap) ── */
.steps-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-top: 2rem;
}
.step-card {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 12px;
    padding: 1.5rem 1.25rem;
    position: relative;
}
.step-card:hover {border-color: #10B981; transition: border-color 0.2s;}
.step-number {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #10B981, #06B6D4);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 1rem;
    color: #fff !important;
    margin-bottom: 1rem;
}
.step-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #F9FAFB !important;
    margin-bottom: 0.5rem;
}
.step-desc {
    font-size: 0.8rem;
    color: #6B7280 !important;
    line-height: 1.5;
}

/* ── Section header ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1.25rem;
}
.section-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #10B981 !important;
}
.section-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #F9FAFB !important;
    margin: 0 0 0.25rem 0;
}
.section-desc {color: #6B7280 !important; font-size: 0.88rem; margin-bottom: 1.5rem;}

/* ── Image type cards ── */
.img-type-card {
    background: #111827;
    border: 2px solid #1F2937;
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
    min-height: 160px;
}
.img-type-card:hover {border-color: #10B981;}
.img-type-card.selected {
    border-color: #10B981;
    background: rgba(16,185,129,0.06);
}
.img-type-icon {font-size: 2.5rem; margin-bottom: 0.75rem;}
.img-type-title {
    font-size: 1rem;
    font-weight: 700;
    color: #F9FAFB !important;
    margin-bottom: 0.4rem;
}
.img-type-desc {font-size: 0.8rem; color: #6B7280 !important;}

/* ── Upload area ── */
.upload-area {
    background: #111827;
    border: 2px dashed #374151;
    border-radius: 12px;
    padding: 2.5rem;
    text-align: center;
    margin-bottom: 1.25rem;
}
.upload-area:hover {border-color: #10B981;}
.upload-icon {font-size: 2.5rem; margin-bottom: 0.75rem;}
.upload-label {
    font-size: 1rem;
    font-weight: 600;
    color: #F9FAFB !important;
}
.upload-hint {font-size: 0.8rem; color: #6B7280 !important;}

/* ── Progress bar (questionnaire) ── */
.progress-wrapper {
    background: #1F2937;
    border-radius: 100px;
    height: 6px;
    margin-bottom: 2rem;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    border-radius: 100px;
    background: linear-gradient(90deg, #10B981, #06B6D4);
    transition: width 0.4s ease;
}

/* ── Question card ── */
.question-card {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 14px;
    padding: 2rem;
    margin-bottom: 1.5rem;
}
.question-step {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #10B981 !important;
    margin-bottom: 0.5rem;
}
.question-text {
    font-size: 1.3rem;
    font-weight: 700;
    color: #F9FAFB !important;
    margin-bottom: 0.25rem;
}
.question-hint {font-size: 0.82rem; color: #6B7280 !important; margin-bottom: 1.5rem;}

/* ── Results ── */
.results-header-card {
    background: linear-gradient(135deg, #064E3B, #065F46);
    border: 1px solid #10B981;
    border-radius: 14px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
}
.results-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #6EE7B7 !important;
    margin-bottom: 0.25rem;
}
.results-top-finding {
    font-size: 1.5rem;
    font-weight: 800;
    color: #F9FAFB !important;
    margin-bottom: 0.5rem;
}
.confidence-pct {
    font-size: 2.5rem;
    font-weight: 900;
    background: linear-gradient(90deg, #10B981, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.finding-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.65rem 0;
    border-bottom: 1px solid #1F2937;
}
.finding-name {font-size: 0.88rem; color: #D1D5DB !important;}
.finding-pct {font-size: 0.88rem; font-weight: 700; color: #10B981 !important;}

.conf-bar-bg {
    background: #1F2937;
    border-radius: 100px;
    height: 6px;
    margin-top: 4px;
    overflow: hidden;
}
.conf-bar-fill {
    height: 100%;
    border-radius: 100px;
    background: linear-gradient(90deg, #10B981, #06B6D4);
}

.action-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 0.65rem 0;
    border-bottom: 1px solid #1F2937;
    font-size: 0.88rem;
    color: #D1D5DB !important;
}
.action-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #10B981;
    flex-shrink: 0;
    margin-top: 5px;
}

.safety-note {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.3);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    font-size: 0.82rem;
    color: #FCD34D !important;
    margin-top: 1.25rem;
}

/* ── CTA button ── */
.stButton > button {
    background: linear-gradient(135deg, #10B981, #06B6D4) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.75rem !important;
    font-size: 0.95rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover {opacity: 0.88 !important;}
.stButton > button:disabled {
    background: #374151 !important;
    color: #6B7280 !important;
}

/* ── Radio buttons ── */
[data-testid="stRadio"] label {
    background: #1F2937 !important;
    border: 1.5px solid #374151 !important;
    border-radius: 8px !important;
    padding: 0.65rem 1rem !important;
    margin-bottom: 6px !important;
    color: #D1D5DB !important;
    display: block !important;
    transition: all 0.15s !important;
}
[data-testid="stRadio"] label:hover {border-color: #10B981 !important;}
[data-testid="stRadio"] [aria-checked="true"] + label,
[data-testid="stRadio"] label[data-checked="true"] {
    border-color: #10B981 !important;
    background: rgba(16,185,129,0.1) !important;
    color: #F9FAFB !important;
}

/* ── Misc ── */
.stFileUploader {background: transparent !important;}
[data-testid="stFileUploaderDropzone"] {
    background: #111827 !important;
    border: 2px dashed #374151 !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploaderDropzone"]:hover {border-color: #10B981 !important;}
hr {border-color: #1F2937 !important;}
.hf-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(255,210,0,0.08);
    border: 1px solid rgba(255,210,0,0.25);
    border-radius: 8px;
    padding: 3px 10px;
    font-size: 0.75rem;
    color: #FCD34D !important;
    margin-right: 6px;
}
.model-card {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
}
.model-id {font-size: 0.8rem; color: #10B981 !important; font-family: monospace; margin-bottom: 0.25rem;}
.model-desc {font-size: 0.82rem; color: #6B7280 !important;}
</style>
"""


# ── Session state helpers ─────────────────────────────────────────────────────

def _init_state() -> None:
    defaults = {
        "page": "welcome",
        "step": 1,
        "image_type": None,
        "uploaded_image": None,
        "uploaded_filename": None,
        "quiz_idx": 0,
        "quiz_answers": {},
        "results": None,
        "running": False,
        "error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _go(page: str, step: int = 1) -> None:
    st.session_state.page = page
    st.session_state.step = step
    st.rerun()


def _reset() -> None:
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────

def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("""
        <div class="revela-brand">
            <div class="logo">Reve<span>la</span></div>
            <div class="subtitle">Dermatology AI Suite</div>
        </div>
        """, unsafe_allow_html=True)

        current_step = st.session_state.step if st.session_state.page == "workflow" else 0

        for idx, (label, icon) in enumerate(NAV_STEPS):
            active = (idx + 1 == current_step and st.session_state.page == "workflow")
            css_class = "nav-item active" if active else "nav-item"
            st.markdown(
                f'<div class="{css_class}"><span class="nav-icon">{icon}</span> {label}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<hr/>", unsafe_allow_html=True)

        if st.session_state.page == "workflow":
            if st.button("← Start Over", use_container_width=True):
                _reset()

        st.markdown("""
        <div style="position:absolute; bottom:1.5rem; left:1.5rem; right:1.5rem;">
            <div style="font-size:0.72rem; color:#4B5563; line-height:1.6;">
                ⚠️ Educational use only.<br/>
                Not a substitute for clinical diagnosis.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Welcome page ─────────────────────────────────────────────────────────────

def _render_welcome() -> None:
    st.markdown("""
    <div class="hero-section">
        <div class="hero-badge">✦ AI Learning Lab — Resident Portal</div>
        <div class="hero-title">Revela<br/><span>AI-Powered Skin Analysis</span></div>
        <div class="hero-subtitle">
            A deep-learning educational platform for dermatology residents.
            Upload a clinical or dermoscopic image, provide context, and receive
            AI-assisted diagnostic guidance to sharpen your clinical reasoning.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="steps-grid">
        <div class="step-card">
            <div class="step-number">1</div>
            <div class="step-title">Choose Image</div>
            <div class="step-desc">Select from clinical photo or dermoscopic image to begin your learning session.</div>
        </div>
        <div class="step-card">
            <div class="step-number">2</div>
            <div class="step-title">Add Context</div>
            <div class="step-desc">Upload your patient case and provide clinical history and examination findings.</div>
        </div>
        <div class="step-card">
            <div class="step-number">3</div>
            <div class="step-title">Analyze Case</div>
            <div class="step-desc">Leverage deep learning models to generate potential diagnostic considerations.</div>
        </div>
        <div class="step-card">
            <div class="step-number">4</div>
            <div class="step-title">Review Output</div>
            <div class="step-desc">Compare AI model outputs with gold-standard histopathology and expert consensus.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if st.button("Start Analysis →", use_container_width=True):
            _go("workflow", step=1)

    # HF model info
    st.markdown("<br/><br/>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Connected Models</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="model-card">
            <div class="hf-badge">🤗 HuggingFace</div>
            <div class="model-id">{HF_CLINICAL_MODEL}</div>
            <div class="model-desc">Clinical skin condition classifier · 5 classes · EfficientNet-B0</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="model-card">
            <div class="hf-badge">🤗 HuggingFace</div>
            <div class="model-id">{HF_DERMO_MODEL}</div>
            <div class="model-desc">Dermoscopic cancer risk classifier · 4 classes · EfficientNet-B0</div>
        </div>
        """, unsafe_allow_html=True)


# ── Workflow step 1 — Image Type ──────────────────────────────────────────────

def _render_step_image_type() -> None:
    st.markdown('<div class="section-label">Step 1 of 5</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Choose Image Type</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Select the type of image you are working with. This determines which AI model will be applied.</div>',
        unsafe_allow_html=True,
    )

    selected = st.session_state.image_type
    c1, c2 = st.columns(2)

    with c1:
        card_cls = "img-type-card selected" if selected == "Clinical Photo" else "img-type-card"
        st.markdown(f"""
        <div class="{card_cls}">
            <div class="img-type-icon">📷</div>
            <div class="img-type-title">Clinical Photo</div>
            <div class="img-type-desc">Standard macro photograph of a skin lesion or condition visible to the naked eye.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select Clinical Photo", key="btn_clinical", use_container_width=True):
            st.session_state.image_type = "Clinical Photo"
            st.rerun()

    with c2:
        card_cls = "img-type-card selected" if selected == "Dermoscopic Image" else "img-type-card"
        st.markdown(f"""
        <div class="{card_cls}">
            <div class="img-type-icon">🔬</div>
            <div class="img-type-title">Dermoscopic Image</div>
            <div class="img-type-desc">High-magnification dermoscopy image revealing subsurface structures of pigmented lesions.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select Dermoscopic", key="btn_dermo", use_container_width=True):
            st.session_state.image_type = "Dermoscopic Image"
            st.rerun()

    if selected:
        st.success(f"Selected: **{selected}**")
        _, col, _ = st.columns([1, 1.5, 1])
        with col:
            if st.button("Continue to Upload →", use_container_width=True):
                _go("workflow", step=2)
    else:
        st.markdown(
            '<div style="color:#6B7280;font-size:0.85rem;margin-top:0.75rem;">Select an image type to continue.</div>',
            unsafe_allow_html=True,
        )


# ── Workflow step 2 — Upload ──────────────────────────────────────────────────

def _render_step_upload() -> None:
    st.markdown('<div class="section-label">Step 2 of 5</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Upload Image</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-desc">Upload a <strong>{st.session_state.image_type or "skin"}</strong> image. '
        f'Accepted: JPG, JPEG, PNG (max 10 MB).</div>',
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Drag and drop or click to browse",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
        key="file_uploader",
    )

    if uploaded:
        try:
            img = Image.open(uploaded).convert("RGB")
            st.session_state.uploaded_image = img
            st.session_state.uploaded_filename = uploaded.name
            st.session_state.error = None

            col_img, col_meta = st.columns([1.1, 1])
            with col_img:
                st.image(img, caption="Preview", use_container_width=True)
            with col_meta:
                st.markdown(f"""
                <div class="model-card">
                    <div class="model-id">Image Details</div>
                    <div style="margin-top:0.75rem;">
                        <div style="color:#D1D5DB;font-size:0.85rem;">📁 {uploaded.name}</div>
                        <div style="color:#D1D5DB;font-size:0.85rem;margin-top:4px;">
                            📐 {img.width} × {img.height} px
                        </div>
                        <div style="color:#D1D5DB;font-size:0.85rem;margin-top:4px;">
                            🎨 {img.mode} colour
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            _, col, _ = st.columns([1, 1.5, 1])
            with col:
                if st.button("Continue to Clinical History →", use_container_width=True):
                    _go("workflow", step=3)

        except (UnidentifiedImageError, Exception) as e:
            st.error(f"Could not open image: {e}")
            st.session_state.uploaded_image = None

    else:
        st.markdown("""
        <div class="upload-area">
            <div class="upload-icon">⬆</div>
            <div class="upload-label">Drop your image here</div>
            <div class="upload-hint">JPG, JPEG or PNG · max 10 MB</div>
        </div>
        """, unsafe_allow_html=True)

    col_back, _ = st.columns([1, 3])
    with col_back:
        if st.button("← Back", key="back_upload"):
            _go("workflow", step=1)


# ── Workflow step 3 — Clinical History ───────────────────────────────────────

def _render_step_history() -> None:
    qi = st.session_state.quiz_idx
    total = len(QUESTIONNAIRE)

    pct = int((qi / total) * 100)
    st.markdown(f"""
    <div class="progress-wrapper">
        <div class="progress-fill" style="width:{pct}%;"></div>
    </div>
    """, unsafe_allow_html=True)

    if qi >= total:
        st.success("✅ Clinical history complete.")
        _, col, _ = st.columns([1, 1.5, 1])
        with col:
            if st.button("Run AI Analysis →", use_container_width=True):
                _go("workflow", step=4)
        col_back, _ = st.columns([1, 3])
        with col_back:
            if st.button("← Back", key="back_hist_done"):
                st.session_state.quiz_idx = total - 1
                st.rerun()
        return

    q = QUESTIONNAIRE[qi]

    st.markdown(f"""
    <div class="question-card">
        <div class="question-step">{q["step_label"]}</div>
        <div class="question-text">{q["question"]}</div>
        <div class="question-hint">Take your time — there are no wrong answers.</div>
    </div>
    """, unsafe_allow_html=True)

    existing = st.session_state.quiz_answers.get(q["key"])
    idx_default = q["options"].index(existing) if existing in q["options"] else 0

    choice = st.radio(
        "Select an option:",
        q["options"],
        index=idx_default,
        label_visibility="collapsed",
        key=f"radio_{q['key']}",
    )

    col_back, _, col_next = st.columns([1, 2, 1])
    with col_back:
        if qi > 0:
            if st.button("← Back", key=f"back_q{qi}"):
                st.session_state.quiz_idx -= 1
                st.rerun()
    with col_next:
        if st.button("Next →", key=f"next_q{qi}", use_container_width=True):
            st.session_state.quiz_answers[q["key"]] = choice
            st.session_state.quiz_idx += 1
            st.rerun()


# ── Inference helper ──────────────────────────────────────────────────────────

def _run_inference_safe(image_type: str, image: Image.Image) -> dict:
    model_id = LOCAL_MODEL_IDS.get(image_type)
    if not _MODELS_AVAILABLE or model_id is None:
        # Return a graceful demo result
        classes = CLINICAL_CLASSES if image_type == "Clinical Photo" else DERMOSCOPIC_CLASSES
        import random
        random.seed(42)
        raw = [random.random() for _ in classes]
        total = sum(raw)
        probs = [r / total for r in raw]
        pairs = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)
        return {
            "error": False,
            "demo_mode": True,
            "predictions": [{"label": lb, "confidence": round(p, 4)} for lb, p in pairs],
        }
    return _run_inference(
        model_id=model_id,
        image_input=image,
        top_k=len(CLINICAL_CLASSES if image_type == "Clinical Photo" else DERMOSCOPIC_CLASSES),
        project_root=str(_ROOT),
    )


# ── Workflow step 4 — Results ─────────────────────────────────────────────────

def _render_step_results() -> None:
    if st.session_state.results is None and not st.session_state.running:
        st.session_state.running = True

        with st.spinner("Running AI analysis…"):
            result = _run_inference_safe(
                st.session_state.image_type,
                st.session_state.uploaded_image,
            )
        st.session_state.results = result
        st.session_state.running = False
        st.rerun()

    result = st.session_state.results
    if result is None:
        st.info("Preparing analysis…")
        return

    if result.get("error"):
        st.error(f"Analysis failed: {result.get('message', 'Unknown error')}")
        if st.button("← Back"):
            st.session_state.results = None
            _go("workflow", step=3)
        return

    preds = result.get("predictions", [])
    if not preds:
        st.warning("No predictions returned.")
        return

    top = preds[0]
    top_label = top["label"]
    top_conf = top["confidence"]
    demo = result.get("demo_mode", False)

    st.markdown('<div class="section-label">Step 5 of 5 — AI Analysis Complete</div>', unsafe_allow_html=True)

    if demo:
        st.warning("⚠️ Demo mode — local models not loaded. Run `scripts/pull_hf_models.py` for real inference.")

    # ── Header result card ────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="results-header-card">
        <div class="results-label">Top AI Finding</div>
        <div class="results-top-finding">{top_label}</div>
        <div class="confidence-pct">{top_conf * 100:.1f}%</div>
        <div style="font-size:0.78rem; color:#6EE7B7; margin-top:4px;">model confidence</div>
    </div>
    """, unsafe_allow_html=True)

    col_findings, col_actions = st.columns([1.1, 1])

    # ── Findings ──────────────────────────────────────────────────────────────
    with col_findings:
        st.markdown('<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#6B7280;margin-bottom:0.75rem;">TOP AI OUTPUTS</div>', unsafe_allow_html=True)
        for p in preds:
            pct = p["confidence"] * 100
            st.markdown(f"""
            <div class="finding-row">
                <span class="finding-name">{p["label"]}</span>
                <span class="finding-pct">{pct:.1f}%</span>
            </div>
            <div class="conf-bar-bg">
                <div class="conf-bar-fill" style="width:{pct:.1f}%;"></div>
            </div>
            """, unsafe_allow_html=True)

    # ── Confidence + actions ──────────────────────────────────────────────────
    with col_actions:
        st.markdown('<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#6B7280;margin-bottom:0.75rem;">MODEL CONFIDENCE</div>', unsafe_allow_html=True)
        for p in preds[:3]:
            st.markdown(f"""
            <div class="finding-row">
                <span class="finding-name" style="font-size:0.8rem;">{p["label"][:30]}…</span>
                <span class="finding-pct">{p["confidence"]*100:.1f}%</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#6B7280;margin-bottom:0.75rem;">RECOMMENDED ACTIONS</div>', unsafe_allow_html=True)

        actions = RECOMMENDED_ACTIONS.get(top_label, ["Consult a dermatologist for further evaluation."])
        for action in actions:
            st.markdown(f"""
            <div class="action-item">
                <div class="action-dot"></div>
                <span>{action}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Safety note ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="safety-note">
        ⚠️ <strong>Educational use only.</strong> These outputs are generated by a deep learning model
        trained on research datasets and are intended solely for resident education. They must not be
        used as a basis for clinical diagnosis or treatment decisions. Always consult a licensed
        dermatologist for patient care.
    </div>
    """, unsafe_allow_html=True)

    # ── Context summary ───────────────────────────────────────────────────────
    if st.session_state.quiz_answers:
        st.markdown("<br/>", unsafe_allow_html=True)
        with st.expander("Clinical History Provided"):
            for q in QUESTIONNAIRE:
                ans = st.session_state.quiz_answers.get(q["key"], "—")
                st.markdown(f"**{q['question']}** {ans}")

    # ── Actions ───────────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    col_r, col_n = st.columns([1, 1])
    with col_r:
        if st.button("← Run New Analysis", use_container_width=True):
            _reset()
    with col_n:
        if st.session_state.uploaded_image:
            st.image(
                st.session_state.uploaded_image,
                caption=f"Analysed: {st.session_state.uploaded_filename}",
                width=200,
            )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Revela — Dermatology AI",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CSS, unsafe_allow_html=True)
    _init_state()
    _render_sidebar()

    if st.session_state.page == "welcome":
        _render_welcome()
        return

    # Workflow pages
    step = st.session_state.step
    step_map = {
        1: _render_step_image_type,
        2: _render_step_upload,
        3: _render_step_history,
        4: _render_step_results,
    }
    renderer = step_map.get(step)
    if renderer:
        renderer()
    else:
        st.error(f"Unknown step: {step}")


if __name__ == "__main__":
    main()
