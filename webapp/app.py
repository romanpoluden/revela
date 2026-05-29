from __future__ import annotations

import base64
import io
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
    },
    "Dermoscopic Image": {
        "repo_id": "RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1",
        "local_dir": _ROOT / "models" / "dermoscopic",
        "model_id": "dermoscopic_cancer_risk_bcn_mnh_v1",
        "files": ["best_model.pth", "class_to_idx.json"],
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
        "Review skincare routine",
    ],
    "Psoriasis / papulosquamous": [
        "Topical corticosteroids + vitamin D analogue",
        "Dermatology referral for moderate-severe disease",
        "Screen for psoriatic arthritis",
    ],
    "Lesion — dermoscopic review recommended": [
        "Proceed to dermoscopic evaluation",
        "Book dermoscopy within 2 weeks",
        "Document clinical presentation with photography",
    ],
}

QUESTIONNAIRE: list[dict] = [
    {
        "key": "q_duration",
        "question": "How long have you noticed this?",
        "options": ["A few days", "1–4 weeks", "1–6 months", "More than 6 months", "I'm not sure"],
    },
    {
        "key": "q_itch",
        "question": "Does it itch?",
        "options": ["Not at all", "Mildly", "Moderately", "Severely"],
    },
    {
        "key": "q_pain",
        "question": "Is it painful or tender?",
        "options": ["No pain", "Mild discomfort", "Moderate pain", "Severe pain"],
    },
    {
        "key": "q_change",
        "question": "Has it changed in size, shape, or colour?",
        "options": ["No change", "Slight change", "Noticeable change", "Significant change", "Not sure"],
    },
    {
        "key": "q_spread",
        "question": "Has it spread to other areas?",
        "options": ["No", "Slightly", "Yes, multiple areas", "Not sure"],
    },
]


# ── Image helpers ─────────────────────────────────────────────────────────────

def _b64(path: Path, max_width: int = 800) -> str:
    """Return a base64 data URI for an image, resized if needed."""
    if not path.exists():
        return ""
    try:
        img = Image.open(path).convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        fmt = "JPEG" if path.suffix.lower() in (".jpg", ".jpeg") else "PNG"
        img.save(buf, format=fmt, quality=88)
        encoded = base64.b64encode(buf.getvalue()).decode()
        mime = "image/jpeg" if fmt == "JPEG" else "image/png"
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return ""


def _pil_b64(img: Image.Image, max_width: int = 600) -> str:
    """Return a base64 data URI for a PIL Image object."""
    if img is None:
        return ""
    try:
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        encoded = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        return ""


# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
<style>
/* ── Reset ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #F5F6FA !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
}
[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
.main > .block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #1C1F2E !important;
    border-right: none !important;
    min-width: 220px !important;
    max-width: 220px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1rem !important;
    height: 100vh;
    display: flex;
    flex-direction: column;
}
[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #94A3B8 !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 400 !important;
    padding: 0.5rem 1rem !important;
    width: 100% !important;
    text-align: left !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #2D3250 !important;
    color: #F1F5F9 !important;
}

/* ── Global button style ── */
.stButton > button {
    background: #111827 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 100px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    padding: 0.65rem 2rem !important;
    cursor: pointer !important;
    transition: opacity 0.15s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
.stButton > button:disabled {
    background: #D1D5DB !important;
    color: #9CA3AF !important;
    cursor: not-allowed !important;
}

/* ── File uploader ── */
[data-testid="stFileUploaderDropzone"] {
    background: #FFFFFF !important;
    border: 2px dashed #D1D5DB !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: #9CA3AF !important; }

/* ── Radio options ── */
[data-testid="stRadio"] > div { gap: 0 !important; }
[data-testid="stRadio"] label {
    border: 1.5px solid #E5E7EB !important;
    border-radius: 8px !important;
    padding: 0.85rem 1rem !important;
    margin-bottom: 8px !important;
    color: #374151 !important;
    font-size: 0.92rem !important;
    cursor: pointer !important;
    background: #FFFFFF !important;
    display: flex !important;
    align-items: center !important;
}
[data-testid="stRadio"] label:hover { border-color: #6B7280 !important; }
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
    if cfg is None:
        return False, "Unknown modality."
    local_dir: Path = cfg["local_dir"]
    missing = [f for f in cfg["files"] if not (local_dir / f).exists()]
    if not missing:
        return True, "Already on disk."
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        return False, "huggingface_hub not installed"
    token = _hf_token()
    local_dir.mkdir(parents=True, exist_ok=True)
    for fname in missing:
        hf_hub_download(
            repo_id=cfg["repo_id"], filename=fname,
            local_dir=str(local_dir), token=token or None,
        )
    return True, f"Downloaded {len(missing)} file(s)"


# ── Inference ─────────────────────────────────────────────────────────────────

def _demo(modality: str) -> dict:
    import random
    classes = CLINICAL_CLASSES if modality == "Clinical Photo" else DERMOSCOPIC_CLASSES
    rng = random.Random(42)
    vals = sorted([rng.random() for _ in classes], reverse=True)
    total = sum(vals)
    return {
        "error": False,
        "demo_mode": True,
        "predictions": [
            {"label": c, "confidence": round(v / total, 4)}
            for c, v in zip(classes, vals)
        ],
    }


def _run(modality: str, image: Image.Image) -> dict:
    cfg = HF_MODEL_MAP.get(modality)
    if cfg is None:
        return {"error": True, "message": "Unknown modality."}
    with st.spinner(f"Downloading model ({cfg['repo_id']})…"):
        ok, msg = _ensure_downloaded(modality)
    if not ok:
        st.warning(f"Model download failed: {msg} — showing demo output.")
        return _demo(modality)
    if not _INFERENCE_IMPORT_OK:
        st.info("Inference backend unavailable — showing demo output.")
        return _demo(modality)
    classes = CLINICAL_CLASSES if modality == "Clinical Photo" else DERMOSCOPIC_CLASSES
    return _run_inference(
        model_id=cfg["model_id"],
        image_input=image,
        top_k=len(classes),
        project_root=str(_ROOT),
    )


# ── Shared layout components ──────────────────────────────────────────────────

def _top_nav(active: str = "AI Workbench"):
    links = ["Curriculum", "Case Library", "AI Workbench", "Community"]
    link_items = "".join(
        f'<a class="nav-link{"nav-link-active" if l == active else ""}" href="#">{l}</a>'
        for l in links
    )
    st.markdown(f"""
    <style>
    .top-nav {{
        background: #fff;
        border-bottom: 1px solid #E5E7EB;
        padding: 0 2.5rem;
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 100;
    }}
    .nav-logo {{ font-size: 1.15rem; font-weight: 800; color: #111827; letter-spacing: -0.5px; text-decoration: none; }}
    .nav-links {{ display: flex; gap: 2rem; align-items: center; }}
    .nav-link {{ font-size: 0.88rem; color: #6B7280; text-decoration: none; }}
    .nav-link:hover {{ color: #111827; }}
    .nav-link-active {{ color: #111827 !important; font-weight: 600; border-bottom: 2px solid #111827; padding-bottom: 3px; }}
    .nav-actions {{ display: flex; align-items: center; gap: 1rem; }}
    .nav-avatar {{ width: 32px; height: 32px; border-radius: 50%; background: #E5E7EB; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; color: #6B7280; }}
    .nav-cta {{ background: #111827; color: #fff; border: none; border-radius: 8px; padding: 0.45rem 1.1rem; font-size: 0.85rem; font-weight: 600; cursor: pointer; }}
    </style>
    <div class="top-nav">
        <div style="display:flex;align-items:center;gap:3rem;">
            <span class="nav-logo">Revela</span>
            <div class="nav-links">{link_items}</div>
        </div>
        <div class="nav-actions">
            <span style="font-size:1.1rem;color:#9CA3AF;cursor:pointer;">🔔</span>
            <div class="nav-avatar">👤</div>
            <button class="nav-cta">Start Analysis</button>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _footer():
    st.markdown("""
    <div style="border-top:1px solid #E5E7EB;padding:1rem 2.5rem;display:flex;
                align-items:center;justify-content:space-between;
                font-size:0.78rem;color:#9CA3AF;background:#fff;margin-top:2.5rem;">
        <span>© 2024 Revela Medical AI · For educational use only · Not for clinical diagnosis</span>
        <div style="display:flex;gap:1.5rem;">
            <a href="#" style="color:#6B7280;text-decoration:none;font-size:0.78rem;">Safety Disclaimer</a>
            <a href="#" style="color:#6B7280;text-decoration:none;font-size:0.78rem;">Privacy Policy</a>
            <a href="#" style="color:#6B7280;text-decoration:none;font-size:0.78rem;">Institutional Terms</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _sidebar():
    tabs = [
        ("⊞", "Overview"),
        ("◎", "Image Selection"),
        ("⬆", "Upload"),
        ("✦", "AI Analysis"),
        ("◈", "Results"),
    ]
    page = st.session_state.get("page", "welcome")
    active = {
        "welcome": "Overview",
        "workflow": "AI Analysis",
        "history": "AI Analysis",
    }.get(page, "Overview")

    with st.sidebar:
        st.markdown(f"""
        <div style="margin-bottom:1.5rem;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
                <div style="width:34px;height:34px;background:#2D3250;border-radius:8px;
                            display:flex;align-items:center;justify-content:center;font-size:1.1rem;">🔬</div>
                <div>
                    <div style="font-size:0.9rem;font-weight:700;color:#F1F5F9;">Resident Portal</div>
                    <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:1px;color:#64748B;">Dermatology AI Suite</div>
                </div>
            </div>
        </div>
        <hr style="border:none;border-top:1px solid #2D3250;margin:0 0 1rem;"/>
        """, unsafe_allow_html=True)

        for icon, label in tabs:
            is_active = label == active
            bg = "#2D3250" if is_active else "transparent"
            color = "#F1F5F9" if is_active else "#94A3B8"
            fw = "600" if is_active else "400"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;
                        border-radius:8px;background:{bg};margin-bottom:3px;">
                <span style="font-size:0.9rem;color:{color};">{icon}</span>
                <span style="font-size:0.88rem;font-weight:{fw};color:{color};">{label}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='flex:1;min-height:2rem;'></div>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none;border-top:1px solid #2D3250;margin:1rem 0;'/>", unsafe_allow_html=True)

        if st.button("＋ New Case", key="new_case_btn", use_container_width=True):
            _reset()

        st.markdown("""
        <div style="margin-top:0.5rem;">
            <div style="padding:8px 12px;color:#64748B;font-size:0.82rem;cursor:pointer;">❓ Help &amp; Docs</div>
            <div style="padding:8px 12px;color:#64748B;font-size:0.82rem;cursor:pointer;">⚙ Settings</div>
        </div>
        """, unsafe_allow_html=True)


# ── Welcome page ─────────────────────────────────────────────────────────────

def _page_welcome():
    _top_nav("Curriculum")
    st.markdown('<div style="padding:2.5rem 3rem;min-height:calc(100vh - 96px);background:#F5F6FA;">', unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 2.5rem;">
        <h1 style="font-size:2.75rem;font-weight:800;color:#111827;line-height:1.15;
                   letter-spacing:-1px;margin:0 0 1rem;">
            Experimental dermatology AI<br/>learning lab
        </h1>
        <p style="font-size:1rem;color:#6B7280;max-width:560px;margin:0 auto 1.5rem;line-height:1.65;">
            Bridging clinical excellence and cutting-edge artificial intelligence
            for the next generation of dermatologists.
        </p>
        <div style="display:inline-flex;align-items:center;gap:8px;background:#FFF7ED;
                    border:1px solid #FED7AA;border-radius:100px;padding:6px 18px;
                    font-size:0.82rem;color:#C2410C;">
            ⚠ Model output, not diagnosis — For educational review only
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Pre-load images as base64
    img1 = _b64(_STATIC / "figma_step1.png", 400)
    img2 = _b64(_STATIC / "figma_step4.png", 400)
    img3 = _b64(_STATIC / "figma_analyze_card.png", 400)
    img4 = _b64(_STATIC / "figma_results_card.png", 400)

    def _card_img(src: str) -> str:
        if src:
            return f'<img src="{src}" style="width:100%;height:140px;object-fit:cover;border-radius:8px;display:block;margin-top:1rem;"/>'
        return '<div style="width:100%;height:140px;background:#F3F4F6;border-radius:8px;margin-top:1rem;"></div>'

    cards = [
        ("1", "Choose Image",
         "Select from macro, dermoscopic, or histopathologic samples to begin your learning session.",
         img1),
        ("2", "Add Context",
         "Upload your patient case and provide essential clinical history and physical examination findings.",
         img2),
        ("3", "Analyze Case",
         "Leverage deep learning models to generate heatmaps and potential diagnostic considerations.",
         img3),
        ("4", "Review Output",
         "Compare educational model outputs with gold-standard histopathology and expert consensus.",
         img4),
    ]

    cols = st.columns(4)
    for col, (num, title, desc, img_src) in zip(cols, cards):
        with col:
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:14px;
                        padding:1.5rem 1.25rem 1.25rem;min-height:280px;">
                <div style="width:32px;height:32px;background:#F3F4F6;border-radius:50%;
                            display:flex;align-items:center;justify-content:center;
                            font-size:0.88rem;font-weight:700;color:#374151;margin-bottom:1rem;">{num}</div>
                <div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:0.4rem;">{title}</div>
                <div style="font-size:0.82rem;color:#6B7280;line-height:1.55;margin-bottom:0.5rem;">{desc}</div>
                {_card_img(img_src)}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    _, mid, _ = st.columns([2, 1.5, 2])
    with mid:
        if st.button("Begin learning case →", use_container_width=True, key="begin_btn"):
            _go("workflow")

    st.markdown("""
    <div style="text-align:center;font-size:0.72rem;text-transform:uppercase;
                letter-spacing:2px;color:#9CA3AF;margin-top:0.75rem;">
        No account required for educational modules
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    _footer()


# ── Analysis Workflow ─────────────────────────────────────────────────────────

def _section_heading(num: str, label: str):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin:1.75rem 0 1rem;">
        <div style="width:28px;height:28px;background:#111827;border-radius:50%;
                    display:flex;align-items:center;justify-content:center;
                    font-size:0.8rem;font-weight:700;color:#fff;flex-shrink:0;">{num}</div>
        <span style="font-size:1.2rem;font-weight:700;color:#111827;">{label}</span>
    </div>
    """, unsafe_allow_html=True)


def _page_workflow():
    _sidebar()
    _top_nav("AI Workbench")

    st.markdown('<div style="padding:2rem 2.5rem;">', unsafe_allow_html=True)

    st.markdown("""
    <h2 style="font-size:1.6rem;font-weight:800;color:#111827;margin:0 0 0.25rem;">Analysis Workflow</h2>
    <p style="color:#6B7280;font-size:0.9rem;margin:0 0 0.5rem;">
        Progressive diagnostic pipeline — follow the steps below to run the neural analysis.
    </p>
    """, unsafe_allow_html=True)

    # ── Step 1: Modality ──────────────────────────────────────────────────────
    _section_heading("1", "Modality Selection")

    img_clin = _b64(_STATIC / "figma_step2.png", 600)
    img_derm = _b64(_STATIC / "figma_step3.png", 600)
    selected = st.session_state.modality

    def _modality_card(key: str, label: str, desc: str, img_src: str, active: bool) -> str:
        border = "#111827" if active else "#E5E7EB"
        check = '<span style="background:#111827;color:#fff;width:20px;height:20px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:0.7rem;margin-left:6px;">✓</span>' if active else ""
        img_html = f'<img src="{img_src}" style="width:100%;height:190px;object-fit:cover;border-radius:10px;display:block;margin-bottom:1rem;"/>' if img_src else '<div style="width:100%;height:190px;background:#F3F4F6;border-radius:10px;margin-bottom:1rem;"></div>'
        return f"""
        <div style="background:#fff;border:2px solid {border};border-radius:14px;
                    overflow:hidden;padding:1.25rem;">
            {img_html}
            <div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:0.35rem;">
                {label}{check}
            </div>
            <div style="font-size:0.82rem;color:#6B7280;line-height:1.5;">{desc}</div>
        </div>
        """

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(_modality_card(
            "clin", "Clinical Photo",
            "Standard macroscopic image captured with a digital camera or mobile lens. Best for general topography.",
            img_clin, selected == "Clinical Photo",
        ), unsafe_allow_html=True)
        if st.button("Select Clinical Photo", key="sel_clin", use_container_width=True):
            st.session_state.modality = "Clinical Photo"
            st.session_state.results = None
            st.rerun()

    with c2:
        st.markdown(_modality_card(
            "derm", "Dermoscopic Image",
            "Polarized, magnified imagery highlighting subsurface pigment patterns. Required for deep AI classification.",
            img_derm, selected == "Dermoscopic Image",
        ), unsafe_allow_html=True)
        if st.button("Select Dermoscopic", key="sel_derm", use_container_width=True):
            st.session_state.modality = "Dermoscopic Image"
            st.session_state.results = None
            st.rerun()

    if selected:
        repo = HF_MODEL_MAP[selected]["repo_id"]
        st.markdown(f"""
        <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:8px 14px;
                    font-size:0.85rem;color:#166534;margin-top:0.75rem;display:inline-flex;
                    gap:6px;align-items:center;">
            ✓ <strong>{selected}</strong> selected &nbsp;·&nbsp;
            Model: <code style="background:transparent;font-size:0.82rem;">{repo}</code>
        </div>
        """, unsafe_allow_html=True)

    # ── Step 2: Upload ────────────────────────────────────────────────────────
    _section_heading("2", "Specimen Upload")

    up_col, prev_col = st.columns([1.6, 1])
    with up_col:
        uploaded = st.file_uploader(
            "Drag and drop high-res specimen",
            type=["jpg", "jpeg", "png", "tiff"],
            key="specimen_upload",
        )
        st.markdown('<div style="font-size:0.78rem;color:#9CA3AF;margin-top:4px;">Supports JPEG, PNG, TIFF · Max 50 MB</div>', unsafe_allow_html=True)

    with prev_col:
        st.markdown('<div style="background:#fff;border:1px solid #E5E7EB;border-radius:12px;padding:1rem;min-height:180px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#6B7280;margin-bottom:0.75rem;">PREVIEW</div>', unsafe_allow_html=True)
        if uploaded:
            try:
                img = Image.open(uploaded).convert("RGB")
                st.session_state.uploaded_image = img
                st.session_state.uploaded_filename = uploaded.name
                preview_src = _pil_b64(img, 400)
                st.markdown(f'<img src="{preview_src}" style="width:100%;border-radius:8px;"/>', unsafe_allow_html=True)
            except Exception:
                st.session_state.uploaded_image = None
                st.markdown('<div style="color:#9CA3AF;font-size:0.88rem;">Invalid image</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#9CA3AF;font-size:0.88rem;padding:2rem 0;text-align:center;">Awaiting file…</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Step 3: Clinical History ──────────────────────────────────────────────
    if st.session_state.uploaded_image and st.session_state.quiz_idx < len(QUESTIONNAIRE):
        _section_heading("3", "Clinical History")
        _inline_quiz()

    # ── Initiate Analysis ─────────────────────────────────────────────────────
    can_run = (
        st.session_state.modality is not None
        and st.session_state.uploaded_image is not None
        and st.session_state.quiz_idx >= len(QUESTIONNAIRE)
    )

    st.markdown("<br/>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1.5, 2, 1.5])
    with mid:
        if st.button("⚡  Initiate AI Analysis", disabled=not can_run,
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
            remaining = len(QUESTIONNAIRE) - st.session_state.quiz_idx
            missing.append(f"answer {remaining} more question(s)")
        st.markdown(
            f'<div style="text-align:center;font-size:0.78rem;color:#9CA3AF;margin-top:6px;">To proceed: {" · ".join(missing)}</div>',
            unsafe_allow_html=True,
        )

    # Run inference
    if st.session_state.running and st.session_state.results is None:
        with st.spinner("Running neural analysis…"):
            result = _run(st.session_state.modality, st.session_state.uploaded_image)
        st.session_state.results = result
        st.session_state.running = False
        st.rerun()

    # Results
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
    <div style="background:#fff;border:1px solid #E5E7EB;border-radius:12px;padding:1.5rem;margin-bottom:1rem;">
        <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
            <span style="font-size:0.88rem;font-weight:600;color:#374151;">Question {qi + 1} of {total}</span>
            <span style="font-size:0.82rem;color:#9CA3AF;">{pct}% complete</span>
        </div>
        <div style="background:#E5E7EB;border-radius:100px;height:4px;overflow:hidden;margin-bottom:1.25rem;">
            <div style="width:{pct}%;height:100%;background:#F97316;border-radius:100px;"></div>
        </div>
        <div style="font-size:1rem;font-weight:600;color:#111827;">{q['question']}</div>
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
    _section_heading("4", "Diagnostic Synthesis")

    if result.get("error"):
        st.error(f"Analysis failed: {result.get('message')}")
        return

    preds = result.get("predictions", [])
    if not preds:
        st.warning("No predictions returned.")
        return

    if result.get("demo_mode"):
        st.info("Demo mode — model weights not on disk. Set HF_TOKEN in .env to auto-download.")

    top = preds[0]
    top_label = top["label"]
    top_conf = top["confidence"]
    is_urgent = top_label in ("Melanoma", "Non-melanoma skin cancer")

    left_col, right_col = st.columns([1.15, 1])

    with left_col:
        st.markdown('<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#9CA3AF;margin-bottom:0.75rem;">TOP AI OUTPUTS</div>', unsafe_allow_html=True)
        for p in preds:
            pct = p["confidence"] * 100
            is_top = p["label"] == top_label
            fw = "700" if is_top else "500"
            pct_color = "#F97316" if is_top else "#9CA3AF"
            if "Melanoma" in p["label"] and "Non" not in p["label"]:
                cls_text = "Class: Malignant"
            elif any(x in p["label"] for x in ["Melanoma", "cancer", "Cancer"]):
                cls_text = "Class: Malignant"
            elif any(x in p["label"] for x in ["Benign", "nevus"]):
                cls_text = "Class: Benign"
            elif any(x in p["label"] for x in ["Eczema", "Urticaria", "Folliculitis", "Psoriasis"]):
                cls_text = "Class: Inflammatory"
            else:
                cls_text = "Class: Review Required"
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;
                        padding:0.85rem 1rem;display:flex;align-items:center;
                        justify-content:space-between;margin-bottom:8px;">
                <div>
                    <div style="font-size:0.95rem;font-weight:{fw};color:#111827;">{p["label"]}</div>
                    <div style="font-size:0.78rem;color:#9CA3AF;">{cls_text}</div>
                </div>
                <div style="font-size:1.1rem;font-weight:800;color:{pct_color};">{pct:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        if is_urgent:
            st.markdown("""
            <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:6px;
                        padding:4px 12px;font-size:0.78rem;color:#C2410C;
                        display:inline-flex;align-items:center;gap:5px;margin-bottom:1rem;">
                ⚠ Urgent Review Recommended
            </div>
            """, unsafe_allow_html=True)

        conf_pct = top_conf * 100
        conf_note = (
            "High certainty based on pattern recognition of structural asymmetry and pigment network irregularity."
            if top_conf > 0.7
            else "Moderate certainty — clinical correlation strongly advised."
        )

        st.markdown(f"""
        <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:1.5px;color:#9CA3AF;margin-bottom:0.4rem;">MODEL CONFIDENCE</div>
        <div style="background:#F3F4F6;border-radius:100px;height:8px;overflow:hidden;margin-bottom:0.5rem;">
            <div style="width:{conf_pct:.0f}%;height:100%;border-radius:100px;background:#F97316;"></div>
        </div>
        <div style="font-size:0.78rem;color:#6B7280;line-height:1.5;font-style:italic;margin-bottom:1.25rem;">{conf_note}</div>
        <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#9CA3AF;margin-bottom:0.5rem;">RECOMMENDED ACTIONS</div>
        """, unsafe_allow_html=True)

        actions = RECOMMENDED_ACTIONS.get(top_label, ["Consult a dermatologist."])
        for a in actions:
            st.markdown(f"""
            <div style="display:flex;gap:8px;align-items:flex-start;padding:6px 0;
                        border-bottom:1px solid #F3F4F6;font-size:0.85rem;color:#374151;">
                <span style="color:#F97316;flex-shrink:0;margin-top:1px;">›</span>{a}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;
                padding:0.9rem 1rem;font-size:0.8rem;color:#6B7280;
                margin-top:1.25rem;display:flex;gap:8px;align-items:flex-start;">
        ℹ️ <span><strong>Safety Note:</strong> AI analysis is provided for educational support only.
        Final diagnosis must be confirmed by a board-certified pathologist.</span>
    </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if st.button("＋ New Case", key="new_case_post_result", use_container_width=True):
            _reset()


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
        _page_welcome()
    elif page == "history":
        _sidebar()
        _top_nav("AI Workbench")
        _page_workflow()
    else:
        _page_workflow()


if __name__ == "__main__":
    main()
