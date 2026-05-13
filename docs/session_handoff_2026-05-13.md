# Revela — Session Handoff 2026-05-13

Paste this into Claude web app before asking it to help with Revela tasks. It reflects the current project state as of 2026-05-13.

---

## What Revela is

Revela is an **educational dermatology AI training aid** for dermatology residents, trainees, and practitioners. It is not a diagnostic product and must not be presented as clinically validated.

The product helps users practice structured dermatology image review by showing top differential suggestions, confidence/uncertainty, and educational explanations.

**Current MVP:** Dermoscopic cancer-risk training module. User uploads a dermoscopic lesion image → model predicts cancer-risk class → app shows class, cancer-risk interpretation, confidence, and educational safety warning.

---

## CNN model

- **Architecture:** EfficientNet-B0 (transfer learning)
- **Dataset:** BCN20000 (dermoscopic images, histopathology-confirmed labels)
- **Image type:** Dermoscopic only — never mix with clinical photos

### CNN v1 baseline (old, 3-class — baseline reference only)

| Class | Notes |
|---|---|
| Melanoma | — |
| Benign nevus | — |
| Other lesion | **Problem:** contains BCC, SCC, actinic keratosis — not communicable as low-risk |

**v1 metrics:** Top-1 accuracy 76.16%, Macro-F1 0.7443, Balanced accuracy 75.29%

v1 is now **baseline only** — not the production model. Do not finalize inference schema around v1 output.

---

## Finalized taxonomy (approved #117, 2026-05-12)

The next dermoscopic CNN will use this 4-class cancer-risk taxonomy:

| Class | BCN20000 rows | Risk |
|---|---|---|
| Melanoma | 4,636 | High cancer risk |
| Non-melanoma skin cancer | 4,235 | High cancer risk |
| Benign nevus | 5,647 | Low risk |
| Other non-cancer / indeterminate lesion | 3,121 | Variable — includes pre-cancer |
| **Excluded** (unknown/missing diagnosis_3) | 1,307 | — |
| **Usable total** | **17,639** | — |

**Critical wording rule:** The 4th class MUST be called `Other non-cancer / indeterminate lesion`. Do NOT use `Other benign lesion`, `Safe lesion`, or drop the word `lesion`. This class includes actinic keratosis (pre-malignant), so it cannot be labeled as fully benign.

**BCN20000 label → taxonomy mapping:**
- `Melanoma, NOS` + `Melanoma metastasis` → Melanoma
- `Basal cell carcinoma` + `Squamous cell carcinoma, NOS` → Non-melanoma skin cancer
- `Nevus` / `Nevi` → Benign nevus
- `Seborrheic keratosis`, `Solar or actinic keratosis`, `Solar lentigo`, `Dermatofibroma`, `Scar`, all other → Other non-cancer / indeterminate lesion
- `diagnosis_3` is NaN/unknown → **Excluded from training** (1,307 rows)

---

## Dependency chain

```
D3.1 — Approve 4-class cancer-risk taxonomy            ✅ DONE (#116, #117)
  → D3.3 (#118) — Rebuild BCN20000 splits              ← NEXT (unblocked)
    → D3.4 (#119) — Retrain CNN with new taxonomy
      → D3.5 (#120) — Evaluate CNN on frozen test split
        → D3.7 (#123) — Update inference + app schema for cancer-risk output
```

---

## Current task: #118 — Rebuild BCN20000 processed splits

**Status:** Open, P0, unblocked as of 2026-05-12  
**What it does:** Rebuild train/val/test CSVs using the finalized 4-class label mapping.

### Acceptance criteria
- Apply approved label mapping (see above)
- Lesion-level leakage-safe splitting (no patient/lesion leaking across splits)
- Freeze and reproduce the split with a fixed random seed
- Report class counts per split
- Exclude 1,307 unknown `diagnosis_3` rows (document this clearly)
- Save to new paths — do NOT overwrite old 3-class outputs
- Update config with new class names and paths

### Suggested deliverables
- `data/processed/bcn20000_cancer_risk/train.csv`
- `data/processed/bcn20000_cancer_risk/val.csv`
- `data/processed/bcn20000_cancer_risk/test.csv`
- `config/bcn20000_cancer_risk_config.yaml`
- `docs/model/bcn20000_cancer_risk_split_summary.md`

### Split notes
- Source metadata: `bcn20000_metadata_2026-05-11.csv` (root of repo)
- Lesion-level column for split safety: check for a lesion/case ID column in the metadata
- Suggested split ratio: 70/15/15 or 80/10/10 train/val/test — confirm with Roman
- Random seed: fix and document (e.g. `random_state=42`)
- Out of scope: model training, evaluation

---

## Evaluation metrics (for when #120 runs)

### Safety metrics — report first
| Metric | Why |
|---|---|
| Cancer recall (Melanoma + NMSC combined) | A missed cancer = false-negative with clinical consequence |
| Cancer false-negative rate (1 − cancer recall) | Must be minimized |
| Melanoma recall | Highest-severity class |
| NMSC recall | Second cancer class |

### Standard metrics
Top-1 accuracy, Macro-F1, Balanced accuracy, per-class Precision/Recall/F1, full 4×4 confusion matrix.

---

## Inference pipeline schema (future — blocked on #118/#119)

```python
# Full response object
{
    'status': 'ok',
    'model_version': 'dermoscopic_cancer_risk_v2',
    'top_class': 'Melanoma',
    'top_confidence': 0.731,
    'top3_predictions': [
        {'rank': 1, 'class': 'Melanoma',                                'confidence': 0.731, 'confidence_pct': '73.1%'},
        {'rank': 2, 'class': 'Non-melanoma skin cancer',                'confidence': 0.183, 'confidence_pct': '18.3%'},
        {'rank': 3, 'class': 'Other non-cancer / indeterminate lesion', 'confidence': 0.071, 'confidence_pct': '7.1%'},
    ],
    'safety_note': 'This result is for educational purposes only. It is not a clinical diagnosis. Consult a dermatologist for any skin concern.',
    'reasoning_template_id': 'melanoma',
}
```

Reasoning template IDs: `melanoma` / `nmsc` / `benign_nevus` / `other`

---

## Hard rules — never do these

- Do not claim diagnosis or clinical validation
- Do not claim the model detects all melanoma / all cancer
- Do not claim fairness or skin-tone robustness without slice evaluation
- Do not mix SCIN/Fitzpatrick17k clinical photos into the dermoscopic CNN
- Do not call `Other non-cancer / indeterminate lesion` benign or safe
- Do not let an LLM invent medical certainty from CNN output
- Do not add treatment advice
- Do not overwrite old 3-class split files

---

## Key files

| File | Purpose |
|---|---|
| `bcn20000_metadata_2026-05-11.csv` | Source metadata for BCN20000 |
| `docs/llm_project_context.md` | Full project context (authoritative) |
| `docs/decision_log.md` | All major decisions with rationale |
| `revela/FitzPatrick/notebooks/03_benchmark_requirements_CNN.ipynb` | Benchmark requirements + label mapping logic |
| `revela/FitzPatrick/notebooks/04_inference_pipeline_requirements.ipynb` | Inference pipeline requirements |
| `src/model/model.py` | EfficientNet-B0 model factory |
