from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError
import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent
_STATIC = Path(__file__).resolve().parent / "static"
sys.path.insert(0, str(_ROOT))

try:
    from src.inference.adapter import run_inference as _run_inference
    _INFERENCE_IMPORT_OK = True
except Exception:
    _INFERENCE_IMPORT_OK = False
    _run_inference = None  # type: ignore[assignment]

# ── HuggingFace model registry ────────────────────────────────────────────────
HF_MODEL_MAP = {
    "Clinical Photo": {
        "repo_id": "RevelaCap/clinical-skin-condition-v1",
        "local_dir": _ROOT / "models" / "clinical",
        "model_id": "clinical_skin_condition_v1",
        "files": ["best_model.pth", "class_to_idx.json"],
        "hf_hosted": True,
    },
    "Dermoscopic Image": {
        "repo_id": "RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1",
        "local_dir": _ROOT / "models" / "dermoscopic",
        "model_id": "dermoscopic_cancer_risk_bcn_mnh_v1",
        "files": ["best_model.pth", "class_to_idx.json"],
        "hf_hosted": True,
    },
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
    "Melanoma": ["Urgent dermatology referral within 2 weeks", "Full-body skin examination", "Consider sentinel lymph node biopsy"],
    "Non-melanoma skin cancer": ["Dermatology referral for biopsy", "Document lesion size and borders", "Discuss treatment options (excision, Mohs)"],
    "Benign nevus": ["Document with dermoscopy photography", "Annual skin check recommended", "Educate patient on ABCDE self-monitoring"],
    "Other non-cancer / indeterminate lesion": ["Clinical correlation advised", "Short-interval follow-up in 3–6 months", "Consider biopsy if change observed"],
    "Eczema / dermatitis": ["Topical corticosteroids (mild–moderate)", "Identify and avoid triggers", "Emollient therapy twice daily"],
    "Urticaria / allergic reaction": ["Oral antihistamine (cetirizine / loratadine)", "Identify allergen — allergy panel if recurrent", "Epinephrine autoinjector if anaphylaxis risk"],
    "Folliculitis / acne-like": ["Topical antibiotic (clindamycin) or benzoyl peroxide", "Warm compress for comfort", "Review skincare routine"],
    "Psoriasis / papulosquamous": ["Topical corticosteroids + vitamin D analogue", "Dermatology referral for moderate-severe disease", "Screen for psoriatic arthritis"],
    "Lesion — dermoscopic review recommended": ["Proceed to dermoscopic evaluation", "Book dermoscopy within 2 weeks", "Document clinical presentation with photography"],
}

QUESTIONNAIRE: list[dict] = [
    {"key": "q_duration", "question": "How long have you noticed this?",
     "options": ["A few days", "1–4 weeks", "1–6 months", "More than 6 months", "I'm not sure"]},
    {"key": "q_itch", "question": "Does it itch?",
     "options": ["Not at all", "Mildly", "Moderately", "Severely"]},
    {"key": "q_pain", "question": "Is it painful or tender?",
     "options": ["No pain", "Mild discomfort", "Moderate pain", "Severe pain"]},
    {"key": "q_change", "question": "Has it changed in size, shape, or colour?",
     "options": ["No change", "Slight change", "Noticeable change", "Significant change", "Not sure"]},
    {"key": "q_spread", "question": "Has it spread to other areas?",
     "options": ["No", "Slightly", "Yes, multiple areas", "Not sure"]},
]

# ── CSS matching Figma exactly ────────────────────────────────────────────────
CSS = """
<style>
/* Reset & base */
html, body, [data-testid="stAppViewContainer"] {
    background: #F5F5F7 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
[data-testid="stHeader"] {display: none !important;}
#MainMenu {display: none !important;}
footer {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}

/* Remove default Streamlit padding */
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
.main > .block-container {padding: 0 !important; max-width: 100% !important;}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #1C1F2E !important;
    border-right: none !important;
    min-width: 220px !important;
    max-width: 220px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1rem 1.5rem 1rem !important;
    height: 100vh;
    display: flex;
    flex-direction: column;
}
[data-testid="stSidebar"] * {color: #E2E8F0 !important;}
[data-testid="stSidebar"] .stButton > button {
    background: #2D3250 !important;
    color: #E2E8F0 !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 1rem !important;
    width: 100% !important;
    text-align: left !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {background: #374168 !important;}

/* ── Top nav ── */
.top-nav {
    background: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
    padding: 0 2rem;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
}
.nav-logo {font-size: 1.1rem; font-weight: 800; color: #111827 !important; letter-spacing: -0.5px;}
.nav-links {display: flex; gap: 2rem; align-items: center;}
.nav-link {font-size: 0.88rem; color: #6B7280 !important; text-decoration: none;}
.nav-link.active {color: #111827 !important; font-weight: 600; border-bottom: 2px solid #111827; padding-bottom: 2px;}
.nav-cta {
    background: #111827;
    color: #FFFFFF !important;
    border: none;
    border-radius: 8px;
    padding: 0.45rem 1.1rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
}

/* ── Main content wrapper ── */
.page-content {padding: 2rem 2.5rem; min-height: calc(100vh - 56px);}

/* ── Welcome hero ── */
.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    color: #111827 !important;
    text-align: center;
    line-height: 1.15;
    margin: 2.5rem 0 1rem;
    letter-spacing: -1px;
}
.hero-subtitle {
    font-size: 1rem;
    color: #6B7280 !important;
    text-align: center;
    max-width: 600px;
    margin: 0 auto 1.5rem;
    line-height: 1.65;
}
.warning-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #FFF7ED;
    border: 1px solid #FED7AA;
    border-radius: 100px;
    padding: 6px 16px;
    font-size: 0.82rem;
    color: #C2410C !important;
    width: fit-content;
    margin: 0 auto 3rem;
}

/* ── Step cards (Welcome) ── */
.step-cards-row {display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; margin-bottom: 2.5rem;}
.step-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.5rem 1.25rem;
    min-height: 260px;
}
.step-num-circle {
    width: 32px; height: 32px;
    background: #F3F4F6;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem; font-weight: 700;
    color: #374151 !important;
    margin-bottom: 1rem;
}
.step-card-title {font-size: 1.05rem; font-weight: 700; color: #111827 !important; margin-bottom: 0.4rem;}
.step-card-desc {font-size: 0.82rem; color: #6B7280 !important; line-height: 1.55; margin-bottom: 1rem;}
.step-card-img {width: 100%; height: 120px; object-fit: cover; border-radius: 8px; background: #F3F4F6;}

/* ── CTA primary button ── */
.stButton > button {
    background: #111827 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 100px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    padding: 0.75rem 2.5rem !important;
    cursor: pointer !important;
    transition: opacity 0.15s !important;
}
.stButton > button:hover {opacity: 0.85 !important;}
.stButton > button[disabled] {background: #D1D5DB !important; color: #9CA3AF !important;}

/* ── Back button override ── */
.back-btn > button {
    background: #FFFFFF !important;
    color: #374151 !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 100px !important;
    padding: 0.55rem 1.25rem !important;
    font-size: 0.9rem !important;
}

/* ── Section heading ── */
.section-step-num {
    width: 28px; height: 28px;
    background: #111827;
    border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.82rem; font-weight: 700;
    color: #FFFFFF !important;
    margin-right: 10px;
    vertical-align: middle;
}
.section-heading {
    font-size: 1.25rem;
    font-weight: 700;
    color: #111827 !important;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* ── Modality cards ── */
.modality-card {
    background: #FFFFFF;
    border: 1.5px solid #E5E7EB;
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    transition: border-color 0.15s;
}
.modality-card:hover {border-color: #9CA3AF;}
.modality-card.selected {border-color: #111827;}
.modality-card img {width: 100%; height: 200px; object-fit: cover; display: block;}
.modality-card-body {padding: 1.25rem;}
.modality-title {
    font-size: 1rem; font-weight: 700;
    color: #111827 !important; margin-bottom: 0.35rem;
    display: flex; align-items: center; justify-content: space-between;
}
.check-badge {
    background: #111827; color: #fff !important;
    width: 22px; height: 22px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.75rem;
}
.modality-desc {font-size: 0.8rem; color: #6B7280 !important; line-height: 1.5;}

/* ── Upload area ── */
.upload-section {display: grid; grid-template-columns: 1.5fr 1fr; gap: 1.25rem; margin-bottom: 1.25rem;}
[data-testid="stFileUploaderDropzone"] {
    background: #FFFFFF !important;
    border: 2px dashed #D1D5DB !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploaderDropzone"]:hover {border-color: #9CA3AF !important;}
.preview-box {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 1rem;
    min-height: 200px;
    display: flex;
    flex-direction: column;
}
.preview-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #6B7280 !important;
    margin-bottom: 0.75rem;
}
.preview-awaiting {
    flex: 1; display: flex; align-items: center; justify-content: center;
    color: #9CA3AF !important; font-size: 0.88rem;
}

/* ── Initiate button ── */
.initiate-btn {
    background: #111827 !important;
    border-radius: 10px !important;
    padding: 0.85rem 2rem !important;
    font-size: 1rem !important;
    width: 100% !important;
}
.initiate-hint {font-size: 0.78rem; color: #9CA3AF !important; text-align: center; margin-top: 6px;}

/* ── Diagnostic Synthesis card ── */
.synthesis-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1.5rem;
}
.synthesis-col-label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #9CA3AF !important;
    margin-bottom: 1rem;
}
.finding-row {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}
.finding-name {font-size: 0.95rem; font-weight: 600; color: #111827 !important;}
.finding-sub {font-size: 0.78rem; color: #9CA3AF !important;}
.finding-pct {font-size: 1.1rem; font-weight: 800; color: #F97316 !important;}
.urgent-badge {
    background: #FFF7ED;
    border: 1px solid #FED7AA;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.75rem;
    color: #C2410C !important;
    display: inline-flex; align-items: center; gap: 5px;
}
.conf-label {font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #9CA3AF !important; margin: 0.75rem 0 0.4rem;}
.conf-bar-bg {background: #F3F4F6; border-radius: 100px; height: 8px; overflow: hidden; margin-bottom: 0.5rem;}
.conf-bar-fill {height: 100%; border-radius: 100px; background: #F97316;}
.conf-note {font-size: 0.78rem; color: #6B7280 !important; line-height: 1.5; font-style: italic;}
.action-btn-row {display: flex; gap: 8px; margin-top: 1rem;}
.action-btn {
    flex: 1;
    background: #FFFFFF;
    border: 1.5px solid #E5E7EB;
    border-radius: 8px;
    padding: 0.65rem 0.5rem;
    text-align: center;
    font-size: 0.85rem;
    font-weight: 600;
    color: #374151 !important;
    cursor: pointer;
}
.safety-note {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 0.9rem 1rem;
    font-size: 0.8rem;
    color: #6B7280 !important;
    margin-top: 1rem;
    display: flex; gap: 8px; align-items: flex-start;
}

/* ── Clinical History ── */
.diag-workflow-label {
    display: inline-block;
    background: #FFF7ED;
    border: 1px solid #FED7AA;
    border-radius: 6px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #C2410C !important;
    margin-bottom: 0.75rem;
}
.step-sub-label {font-size: 1rem; color: #374151 !important; margin-bottom: 1.5rem; font-weight: 500;}
.question-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.75rem;
    margin-bottom: 1.25rem;
}
.q-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
}
.q-counter {font-size: 0.88rem; font-weight: 600; color: #374151 !important;}
.q-progress-pct {font-size: 0.82rem; color: #9CA3AF !important;}
.progress-bar-bg {
    background: #E5E7EB;
    border-radius: 100px;
    height: 5px;
    overflow: hidden;
    margin-bottom: 1.5rem;
}
.progress-bar-fill {
    height: 100%;
    border-radius: 100px;
    background: #F97316;
    transition: width 0.35s ease;
}
.question-text {font-size: 1.05rem; font-weight: 600; color: #111827 !important; margin-bottom: 1.25rem;}

/* Radio option rows */
[data-testid="stRadio"] > div {gap: 0 !important;}
[data-testid="stRadio"] label {
    border: 1.5px solid #E5E7EB !important;
    border-radius: 8px !important;
    padding: 0.85rem 1rem !important;
    margin-bottom: 8px !important;
    color: #374151 !important;
    font-size: 0.92rem !important;
    cursor: pointer !important;
    transition: border-color 0.12s !important;
    background: #FFFFFF !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
}
[data-testid="stRadio"] label:hover {border-color: #6B7280 !important;}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
    border-color: #111827 !important;
    font-weight: 600 !important;
}

/* ── Learning tip cards ── */
.tip-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 1.1rem 1.25rem;
    display: flex; gap: 0.75rem;
    align-items: flex-start;
}
.tip-icon {font-size: 1.5rem; flex-shrink: 0; margin-top: 2px;}
.tip-title {font-size: 0.9rem; font-weight: 700; color: #111827 !important; margin-bottom: 0.25rem;}
.tip-desc {font-size: 0.8rem; color: #6B7280 !important; line-height: 1.55;}

/* ── Footer ── */
.page-footer {
    border-top: 1px solid #E5E7EB;
    padding: 1rem 2.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.78rem;
    color: #9CA3AF !important;
    background: #FFFFFF;
    margin-top: 2rem;
}
.footer-links {display: flex; gap: 1.5rem;}
.footer-link {color: #6B7280 !important; text-decoration: none; font-size: 0.78rem;}

/* Sidebar nav item overrides */
[data-testid="stSidebar"] .stButton > button.active-nav {
    background: #2D3250 !important;
    color: #FFFFFF !important;
}
</style>
"""

# ── State helpers ─────────────────────────────────────────────────────────────

def _init():
    defaults = {
        "page": "welcome",
        "modality": None,
        "uploaded_image": None,
        "uploaded_filename": None,
        "quiz_idx": 0,
        "quiz_answers": {},
        "results": None,
        "running": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _go(page: str):
    st.session_state.page = page
    st.rerun()


def _reset():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


# ── HF auto-download ──────────────────────────────────────────────────────────

def _hf_token() -> str | None:
    tok = os.environ.get("HF_TOKEN", "")
    if tok:
        return tok
    env = _ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line.startswith("HF_TOKEN="):
                val = line.split("=", 1)[1].strip()
                if val and not val.startswith("hf_your"):
                    return val
    return None


def _ensure_downloaded(modality: str) -> tuple[bool, str]:
    cfg = HF_MODEL_MAP.get(modality)
    if cfg is None or not cfg["hf_hosted"]:
        return False, "Not an HF-hosted model."
    local_dir: Path = cfg["local_dir"]
    missing = [f for f in cfg["files"] if not (local_dir / f).exists()]
    if not missing:
        return True, "Already on disk."
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        return False, "Install huggingface_hub: `pip install huggingface_hub`"
    token = _hf_token()
    local_dir.mkdir(parents=True, exist_ok=True)
    for fname in missing:
        hf_hub_download(repo_id=cfg["repo_id"], filename=fname,
                        local_dir=str(local_dir), token=token or None)
    return True, f"Downloaded {len(missing)} file(s) from {cfg['repo_id']}"


# ── Inference ─────────────────────────────────────────────────────────────────

def _demo(modality: str) -> dict:
    import random
    classes = CLINICAL_CLASSES if modality == "Clinical Photo" else DERMOSCOPIC_CLASSES
    rng = random.Random(99)
    vals = sorted([rng.random() for _ in classes], reverse=True)
    total = sum(vals)
    return {
        "error": False,
        "demo_mode": True,
        "predictions": [{"label": c, "confidence": round(v / total, 4)}
                        for c, v in zip(classes, vals)],
    }


def _run(modality: str, image: Image.Image) -> dict:
    cfg = HF_MODEL_MAP.get(modality)
    if cfg is None:
        return {"error": True, "message": "Unknown modality."}

    with st.spinner(f"Downloading model from HuggingFace ({cfg['repo_id']})…"):
        ok, msg = _ensure_downloaded(modality)

    if not ok:
        st.warning(f"Model download failed: {msg} — showing demo output.")
        return _demo(modality)

    if not _INFERENCE_IMPORT_OK:
        st.info("Inference backend not loaded (torch unavailable) — showing demo output.")
        return _demo(modality)

    classes = CLINICAL_CLASSES if modality == "Clinical Photo" else DERMOSCOPIC_CLASSES
    return _run_inference(
        model_id=cfg["model_id"],
        image_input=image,
        top_k=len(classes),
        project_root=str(_ROOT),
    )


# ── Shared nav components ─────────────────────────────────────────────────────

def _top_nav(active: str = "AI Workbench"):
    links = ["Curriculum", "Case Library", "AI Workbench", "Community"]
    link_html = "".join(
        f'<span class="nav-link{" active" if l == active else ""}">{l}</span>'
        for l in links
    )
    st.markdown(f"""
    <div class="top-nav">
        <div style="display:flex;align-items:center;gap:2.5rem;">
            <span class="nav-logo">Revela</span>
            <div class="nav-links">{link_html}</div>
        </div>
        <div style="display:flex;align-items:center;gap:0.75rem;">
            <span style="font-size:1.1rem;color:#6B7280;">🔔</span>
            <span style="font-size:1.1rem;color:#6B7280;">👤</span>
            <button class="nav-cta">Start Analysis</button>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _footer():
    st.markdown("""
    <div class="page-footer">
        <span>© 2024 Revela Medical AI. For educational use only. Not for clinical diagnosis.</span>
        <div class="footer-links">
            <a class="footer-link" href="#">Safety Disclaimer</a>
            <a class="footer-link" href="#">Privacy Policy</a>
            <a class="footer-link" href="#">Institutional Terms</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _sidebar(active_tab: str = "Overview"):
    tabs = ["Overview", "Image Selection", "Upload", "AI Analysis", "Results"]
    icons = {"Overview": "⊞", "Image Selection": "◎", "Upload": "⬆",
              "AI Analysis": "✦", "Results": "◈"}
    with st.sidebar:
        st.markdown("""
        <div style="margin-bottom:1.75rem;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
                <div style="width:32px;height:32px;background:#2D3250;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1rem;">🔬</div>
                <div>
                    <div style="font-size:0.9rem;font-weight:700;color:#F1F5F9;">Resident Portal</div>
                    <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:1px;color:#64748B;">Dermatology AI Suite</div>
                </div>
            </div>
        </div>
        <hr style="border-color:#2D3250;margin:0 0 1rem;"/>
        """, unsafe_allow_html=True)

        for tab in tabs:
            icon = icons.get(tab, "·")
            is_active = tab == active_tab
            bg = "#2D3250" if is_active else "transparent"
            color = "#F1F5F9" if is_active else "#94A3B8"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;
                        background:{bg};margin-bottom:3px;cursor:pointer;">
                <span style="font-size:0.9rem;color:{color};">{icon}</span>
                <span style="font-size:0.88rem;font-weight:{"600" if is_active else "400"};color:{color};">{tab}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='flex:1;'></div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#2D3250;margin:auto 0 1rem;'/>", unsafe_allow_html=True)

        if st.button("+ New Case", key="new_case_btn", use_container_width=True):
            _reset()

        st.markdown("""
        <div style="margin-top:0.75rem;">
            <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;color:#64748B;font-size:0.82rem;">❓ Help & Docs</div>
            <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;color:#64748B;font-size:0.82rem;">⚙ Settings</div>
        </div>
        """, unsafe_allow_html=True)


# ── Welcome page ─────────────────────────────────────────────────────────────

def _page_welcome():
    _top_nav("Curriculum")
    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-title">Experimental dermatology AI<br/>learning lab</div>
    <div class="hero-subtitle">
        Bridging clinical excellence and cutting-edge artificial intelligence
        for the next generation of dermatologists.
    </div>
    <div style="display:flex;justify-content:center;">
        <div class="warning-badge">⚠ Model output, not diagnosis. For educational review only.</div>
    </div>
    """, unsafe_allow_html=True)

    # Figma images — exported directly from the design file
    img_dermoscope   = _STATIC / "figma_step1.png"        # Step 1: dermoscope camera
    img_clinical     = _STATIC / "figma_step2.png"        # Step 2 / Clinical Photo card
    img_analyze      = _STATIC / "figma_analyze_card.png" # Step 3: AI brain card
    img_results      = _STATIC / "figma_results_card.png" # Step 4: results preview

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="step-card">
            <div class="step-num-circle">1</div>
            <div class="step-card-title">Choose Image</div>
            <div class="step-card-desc">Select from macro, dermoscopic, or histopathologic samples to begin your learning session.</div>
        </div>""", unsafe_allow_html=True)
        if img_dermoscope.exists():
            st.image(str(img_dermoscope), use_container_width=True)
    with c2:
        st.markdown("""
        <div class="step-card">
            <div class="step-num-circle">2</div>
            <div class="step-card-title">Add Context</div>
            <div class="step-card-desc">Upload your patient case and provide essential clinical history and physical examination findings.</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("""
        <div style="height:8px;background:#E5E7EB;border-radius:4px;margin-top:0.75rem;overflow:hidden;">
            <div style="width:35%;height:100%;background:#F97316;border-radius:4px;"></div>
        </div>
        <div style="font-size:0.75rem;color:#F97316;margin-top:6px;font-weight:500;">Metadata Integration</div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="step-card">
            <div class="step-num-circle">3</div>
            <div class="step-card-title">Analyze Case</div>
            <div class="step-card-desc">Leverage deep learning models to generate heatmaps and potential diagnostic considerations.</div>
        </div>""", unsafe_allow_html=True)
        if img_analyze.exists():
            st.image(str(img_analyze), use_container_width=True)
    with c4:
        st.markdown("""
        <div class="step-card">
            <div class="step-num-circle">4</div>
            <div class="step-card-title">Review Output</div>
            <div class="step-card-desc">Compare educational model outputs with gold-standard histopathology and expert consensus.</div>
        </div>""", unsafe_allow_html=True)
        if img_results.exists():
            st.image(str(img_results), use_container_width=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1.5, 1.5, 1.5])
    with mid:
        if st.button("Begin learning case →", use_container_width=True):
            _go("workflow")

    st.markdown("""
    <div style="text-align:center;font-size:0.72rem;text-transform:uppercase;letter-spacing:2px;color:#9CA3AF;margin-top:0.75rem;">
        NO ACCOUNT REQUIRED FOR EDUCATIONAL MODULES
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    _footer()


# ── Analysis Workflow ─────────────────────────────────────────────────────────

def _page_workflow():
    _sidebar("AI Analysis")
    _top_nav("AI Workbench")

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    # Page title
    st.markdown("""
    <h2 style="font-size:1.6rem;font-weight:800;color:#111827;margin-bottom:0.25rem;">Analysis Workflow</h2>
    <p style="color:#6B7280;font-size:0.9rem;margin-bottom:2rem;">
        Progressive diagnostic pipeline. Follow the steps below to initialize the neural analysis of the specimen.
    </p>
    """, unsafe_allow_html=True)

    # ── Section 1: Modality Selection ─────────────────────────────────────────
    st.markdown("""
    <div class="section-heading">
        <span class="section-step-num">1</span> Modality Selection
    </div>
    """, unsafe_allow_html=True)

    # Figma images for modality cards
    img_clinical = _STATIC / "figma_step2.png"     # skin lesion close-up
    img_dermo    = _STATIC / "figma_step3.png"     # histopathology microscopy
    selected = st.session_state.modality

    c1, c2 = st.columns(2)
    with c1:
        sel_cls = "modality-card selected" if selected == "Clinical Photo" else "modality-card"
        st.markdown(f'<div class="{sel_cls}">', unsafe_allow_html=True)
        if img_clinical.exists():
            st.image(str(img_clinical), use_container_width=True)
        check = '<span class="check-badge">✓</span>' if selected == "Clinical Photo" else ""
        st.markdown(f"""
        <div class="modality-card-body">
            <div class="modality-title">Clinical Photo {check}</div>
            <div class="modality-desc">Standard macroscopic image captured with a digital camera or mobile lens. Best for general topography.</div>
        </div></div>""", unsafe_allow_html=True)
        if st.button("Select Clinical Photo", key="sel_clin", use_container_width=True):
            st.session_state.modality = "Clinical Photo"
            st.session_state.results = None
            st.rerun()

    with c2:
        sel_cls = "modality-card selected" if selected == "Dermoscopic Image" else "modality-card"
        st.markdown(f'<div class="{sel_cls}">', unsafe_allow_html=True)
        if img_dermo.exists():
            st.image(str(img_dermo), use_container_width=True)
        check = '<span class="check-badge">✓</span>' if selected == "Dermoscopic Image" else ""
        st.markdown(f"""
        <div class="modality-card-body">
            <div class="modality-title">Dermoscopic Image {check}</div>
            <div class="modality-desc">Polarized, magnified imagery highlighting subsurface pigment patterns. Required for deep AI classification.</div>
        </div></div>""", unsafe_allow_html=True)
        if st.button("Select Dermoscopic", key="sel_derm", use_container_width=True):
            st.session_state.modality = "Dermoscopic Image"
            st.session_state.results = None
            st.rerun()

    if selected:
        st.markdown(f"""
        <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:8px 14px;
                    font-size:0.85rem;color:#166534;margin-top:0.5rem;display:inline-flex;gap:6px;align-items:center;">
            ✓ <strong>{selected}</strong> selected
            &nbsp;|&nbsp; Model: <code style="background:transparent;">{HF_MODEL_MAP[selected]['repo_id']}</code>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Section 2: Specimen Upload ────────────────────────────────────────────
    st.markdown("""
    <div class="section-heading">
        <span class="section-step-num">2</span> Specimen Upload
    </div>
    """, unsafe_allow_html=True)

    up_col, prev_col = st.columns([1.6, 1])
    with up_col:
        uploaded = st.file_uploader(
            "Drag and drop high-res specimen",
            type=["jpg", "jpeg", "png", "tiff"],
            key="specimen_upload",
            label_visibility="visible",
        )
        st.markdown('<div style="font-size:0.78rem;color:#9CA3AF;margin-top:4px;">Supports DICOM, JPEG, TIFF (Max 50MB)</div>', unsafe_allow_html=True)

    with prev_col:
        st.markdown('<div class="preview-box"><div class="preview-label">PREVIEW</div>', unsafe_allow_html=True)
        if uploaded:
            try:
                img = Image.open(uploaded).convert("RGB")
                st.session_state.uploaded_image = img
                st.session_state.uploaded_filename = uploaded.name
                st.image(img, use_container_width=True)
            except (UnidentifiedImageError, Exception):
                st.session_state.uploaded_image = None
                st.markdown('<div class="preview-awaiting">Invalid image</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="preview-awaiting">Awaiting file…</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Clinical History inline ───────────────────────────────────────────────
    if st.session_state.uploaded_image and st.session_state.quiz_idx < len(QUESTIONNAIRE):
        st.markdown("""
        <div class="section-heading">
            <span class="section-step-num">3</span> Clinical History
        </div>
        """, unsafe_allow_html=True)
        _inline_quiz()
        st.markdown("<br/>", unsafe_allow_html=True)

    # ── Initiate Analysis button ──────────────────────────────────────────────
    can_run = (
        st.session_state.modality is not None
        and st.session_state.uploaded_image is not None
        and st.session_state.quiz_idx >= len(QUESTIONNAIRE)
    )

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if st.button("⚡ Initiate AI Analysis", disabled=not can_run,
                     key="initiate", use_container_width=True):
            st.session_state.results = None
            st.session_state.running = True
            st.rerun()

    if not can_run:
        missing = []
        if not st.session_state.modality:
            missing.append("select a modality")
        if not st.session_state.uploaded_image:
            missing.append("upload an image")
        if st.session_state.quiz_idx < len(QUESTIONNAIRE):
            missing.append("complete clinical history")
        st.markdown(f'<div class="initiate-hint">To proceed: {" · ".join(missing)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="initiate-hint">Estimated processing time: 4.2 seconds</div>', unsafe_allow_html=True)

    # ── Run inference if triggered ────────────────────────────────────────────
    if st.session_state.running and st.session_state.results is None:
        with st.spinner("Running neural analysis…"):
            result = _run(st.session_state.modality, st.session_state.uploaded_image)
        st.session_state.results = result
        st.session_state.running = False
        st.rerun()

    # ── Section 3: Diagnostic Synthesis ──────────────────────────────────────
    if st.session_state.results:
        _render_synthesis(st.session_state.results, st.session_state.modality)

    st.markdown("</div>", unsafe_allow_html=True)
    _footer()


def _inline_quiz():
    qi = st.session_state.quiz_idx
    total = len(QUESTIONNAIRE)
    pct = int((qi / total) * 100)
    q = QUESTIONNAIRE[qi]

    st.markdown(f"""
    <div class="question-card">
        <div class="q-header-row">
            <span class="q-counter">Question {qi + 1} of {total}</span>
            <span class="q-progress-pct">{pct}% Complete</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width:{pct}%;"></div>
        </div>
        <div class="question-text">{q['question']}</div>
    </div>
    """, unsafe_allow_html=True)

    existing = st.session_state.quiz_answers.get(q["key"])
    idx_default = q["options"].index(existing) if existing in q["options"] else 0
    choice = st.radio("", q["options"], index=idx_default,
                      key=f"q_{q['key']}", label_visibility="collapsed")

    bc, _, nc = st.columns([1, 3, 1])
    with bc:
        if qi > 0:
            if st.button("← Back", key=f"qback_{qi}"):
                st.session_state.quiz_idx -= 1
                st.rerun()
    with nc:
        if st.button("Continue →", key=f"qnext_{qi}", use_container_width=True):
            st.session_state.quiz_answers[q["key"]] = choice
            st.session_state.quiz_idx += 1
            st.rerun()


def _render_synthesis(result: dict, modality: str):
    st.markdown("""
    <div class="section-heading" style="margin-top:2rem;">
        <span class="section-step-num">3</span> Diagnostic Synthesis
    </div>
    """, unsafe_allow_html=True)

    if result.get("error"):
        st.error(f"Analysis failed: {result.get('message')}")
        return

    preds = result.get("predictions", [])
    if not preds:
        st.warning("No predictions returned.")
        return

    if result.get("demo_mode"):
        st.info("Demo mode — models not on disk. Run `scripts/pull_hf_models.py` or ensure HF_TOKEN is set.")

    top = preds[0]
    top_label = top["label"]
    top_conf = top["confidence"]
    is_urgent = top_label in ("Melanoma", "Non-melanoma skin cancer")

    left_col, right_col = st.columns([1.1, 1])

    with left_col:
        st.markdown('<div class="synthesis-col-label">TOP AI OUTPUTS</div>', unsafe_allow_html=True)
        for p in preds:
            pct = p["confidence"] * 100
            is_top = p["label"] == top_label
            weight = "700" if is_top else "500"
            pct_color = "#F97316" if is_top else "#9CA3AF"
            cls_text = "Class: Malignant" if "Melanoma" in p["label"] else \
                       "Class: Benign (Premalignant)" if "Benign" in p["label"] else \
                       "Class: Benign" if any(x in p["label"] for x in ["nevus", "Keratosis", "Eczema", "Urticaria", "Folliculitis", "Psoriasis"]) else \
                       "Class: Review Required"
            st.markdown(f"""
            <div class="finding-row">
                <div>
                    <div class="finding-name" style="font-weight:{weight};">{p["label"]}</div>
                    <div class="finding-sub">{cls_text}</div>
                </div>
                <div class="finding-pct" style="color:{pct_color};">{pct:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        urgent_html = '<div style="margin-bottom:0.75rem;"><span class="urgent-badge">⚠ Urgent Review Recommended</span></div>' if is_urgent else ""
        st.markdown(f"""
        {urgent_html}
        <div class="conf-label">MODEL CONFIDENCE</div>
        <div class="conf-bar-bg">
            <div class="conf-bar-fill" style="width:{top_conf * 100:.0f}%;"></div>
        </div>
        <div class="conf-note">
            {"High certainty based on pattern recognition of structural asymmetry and pigment network irregularity." if top_conf > 0.7 else "Moderate certainty — clinical correlation strongly advised."}
        </div>
        <div class="conf-label" style="margin-top:1.25rem;">RECOMMENDED ACTIONS</div>
        """, unsafe_allow_html=True)

        actions = RECOMMENDED_ACTIONS.get(top_label, ["Consult a dermatologist."])
        for a in actions:
            st.markdown(f"""
            <div style="display:flex;gap:8px;align-items:flex-start;padding:6px 0;border-bottom:1px solid #F3F4F6;font-size:0.85rem;color:#374151;">
                <span style="color:#F97316;margin-top:2px;">›</span> {a}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="safety-note">
        ℹ️ <span><strong>Safety Note:</strong> AI analysis is provided for educational support and clinical decision assistance.
        Final diagnosis must be confirmed by a board-certified pathologist.</span>
    </div>
    """, unsafe_allow_html=True)


# ── Clinical History full page (deep-link from sidebar) ──────────────────────

def _page_history():
    _sidebar("AI Analysis")
    _top_nav("AI Workbench")
    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    st.markdown('<span class="diag-workflow-label">DIAGNOSTIC WORKFLOW</span>', unsafe_allow_html=True)
    qi = st.session_state.quiz_idx
    total = len(QUESTIONNAIRE)
    st.markdown(f'<div class="step-sub-label">Step 3: Clinical History — Question {qi + 1} of {total}</div>',
                unsafe_allow_html=True)

    if qi >= total:
        st.success("Clinical history complete.")
        if st.button("← Back to Workflow"):
            _go("workflow")
        st.markdown("</div>", unsafe_allow_html=True)
        _footer()
        return

    pct = int(((qi + 1) / total) * 100)
    q = QUESTIONNAIRE[qi]

    st.markdown(f"""
    <div class="question-card">
        <div class="q-header-row">
            <span class="q-counter">Question {qi + 1} of {total}</span>
            <span class="q-progress-pct">{pct}% Complete</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width:{pct}%;"></div>
        </div>
        <div class="question-text">{q['question']}</div>
    </div>
    """, unsafe_allow_html=True)

    existing = st.session_state.quiz_answers.get(q["key"])
    idx_default = q["options"].index(existing) if existing in q["options"] else 0
    choice = st.radio("", q["options"], index=idx_default,
                      key=f"hist_{q['key']}", label_visibility="collapsed")

    bc, _, nc = st.columns([1, 2.5, 1])
    with bc:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if qi > 0 and st.button("← Back", key="hist_back"):
            st.session_state.quiz_idx -= 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with nc:
        if st.button("Continue →", key="hist_next", use_container_width=True):
            st.session_state.quiz_answers[q["key"]] = choice
            st.session_state.quiz_idx += 1
            st.rerun()

    # Learning tip + patient card
    st.markdown("<br/>", unsafe_allow_html=True)
    tc1, tc2 = st.columns(2)
    with tc1:
        st.markdown("""
        <div class="tip-card">
            <div class="tip-icon">💡</div>
            <div>
                <div class="tip-title">Learning Tip</div>
                <div class="tip-desc">The duration of a lesion can significantly narrow down differential
                diagnoses between acute inflammatory conditions and chronic pathologies.</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with tc2:
        patient_img = _STATIC / "figma_patient.png"
        c_img, c_txt = st.columns([1, 3])
        with c_img:
            if patient_img.exists():
                st.image(str(patient_img), width=60)
            elif st.session_state.uploaded_image:
                st.image(st.session_state.uploaded_image, width=60)
        with c_txt:
            fname = st.session_state.uploaded_filename or "Uploaded specimen"
            st.markdown(f"""
            <div class="tip-title">Patient #8214</div>
            <div class="tip-desc">Current Case: {fname}</div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    _footer()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Revela — Dermatology AI Learning Lab",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(CSS, unsafe_allow_html=True)
    _init()

    page = st.session_state.page
    if page == "welcome":
        st.set_page_config(initial_sidebar_state="collapsed")
        _page_welcome()
    elif page == "history":
        st.set_page_config(initial_sidebar_state="expanded")
        _page_history()
    else:
        st.set_page_config(initial_sidebar_state="expanded")
        _page_workflow()


if __name__ == "__main__":
    main()
