# Hugging Face Model Artifact Hosting

Revela model artifacts are hosted on the [RevelaCap](https://huggingface.co/RevelaCap) Hugging Face organization.

---

## Hosted Repositories

### 1. Clinical Skin Condition Model

| Field | Value |
|---|---|
| **Hugging Face URL** | https://huggingface.co/RevelaCap/clinical-skin-condition-v1 |
| **Local model ID** | `clinical_skin_condition_v1` |
| **Local path** | `models/clinical_v2_effnet_b0/` |
| **Architecture** | EfficientNet-B0 (PyTorch / torchvision) |
| **Input type** | Clinical / macroscopic skin photographs |
| **Classes** | 5-class Clinical V2 taxonomy |
| **Version tag** | v1 |

**Uploaded files:**

| File | Description |
|---|---|
| `README.md` | Model card with disclaimers, taxonomy, loading instructions |
| `best_model.pth` | PyTorch state dict (EfficientNet-B0, 5-class head, ~16 MB) |
| `class_to_idx.json` | Label → class index mapping |
| `training_history.csv` | Per-epoch train/val loss and macro-F1 |

**Taxonomy:**

| Index | Label |
|---|---|
| 0 | Eczema / dermatitis |
| 1 | Urticaria / allergic reaction |
| 2 | Folliculitis / acne-like |
| 3 | Psoriasis / papulosquamous |
| 4 | Lesion — dermoscopic review recommended |

---

### 2. Dermoscopic Cancer Risk Model

| Field | Value |
|---|---|
| **Hugging Face URL** | https://huggingface.co/RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1 |
| **Local model ID** | `dermoscopic_cancer_risk_bcn_mnh_v1` |
| **Local path** | `models/bcn_mnh_cancer_risk_effnet_b0/` |
| **Architecture** | EfficientNet-B0 (PyTorch / torchvision) |
| **Input type** | Dermoscopic images (dermatoscope-captured) |
| **Classes** | 4-class dermoscopic lesion-risk taxonomy |
| **Version tag** | v1 |

**Uploaded files:**

| File | Description |
|---|---|
| `README.md` | Model card with disclaimers, taxonomy, loading instructions |
| `best_model.pth` | PyTorch state dict (EfficientNet-B0, 4-class head, ~16 MB) |
| `class_to_idx.json` | Label → class index mapping |
| `training_history.csv` | Per-epoch train/val loss and macro-F1 |

**Taxonomy:**

| Index | Label |
|---|---|
| 0 | Melanoma |
| 1 | Non-melanoma skin cancer |
| 2 | Benign nevus |
| 3 | Other non-cancer / indeterminate lesion |

---

## Download / Loading Instructions

### Using `huggingface_hub`

```python
from huggingface_hub import hf_hub_download

# Clinical model
ckpt = hf_hub_download("RevelaCap/clinical-skin-condition-v1", "best_model.pth")
idx  = hf_hub_download("RevelaCap/clinical-skin-condition-v1", "class_to_idx.json")

# Dermoscopic model
ckpt = hf_hub_download("RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1", "best_model.pth")
idx  = hf_hub_download("RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1", "class_to_idx.json")
```

### Restoring to local `models/` structure

```bash
# Clinical
mkdir -p models/clinical_v2_effnet_b0
huggingface-cli download RevelaCap/clinical-skin-condition-v1 \
  best_model.pth class_to_idx.json training_history.csv \
  --local-dir models/clinical_v2_effnet_b0

# Dermoscopic
mkdir -p models/bcn_mnh_cancer_risk_effnet_b0
huggingface-cli download RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1 \
  best_model.pth class_to_idx.json training_history.csv \
  --local-dir models/bcn_mnh_cancer_risk_effnet_b0
```

---

## Known Limitations

- Both models are educational prototypes not validated for clinical use.
- Clinical and dermoscopic models use different input modalities — do not mix.
- Performance varies across skin tone, image quality, and dataset source.
- See each model card for full disclaimer and limitations.

---

## Out of Scope

- Hugging Face Space deployment
- Public API serving
- Automatic model download at runtime
- Clinical validation or regulatory deployment
