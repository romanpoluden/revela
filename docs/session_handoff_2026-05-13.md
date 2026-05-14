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
- Lesion-level split key: `lesion_id` column (confirmed present in existing splits)
- Split ratio: 70/15/15 — matches existing baseline, use `seed: 42`
- Out of scope: model training, evaluation

---

## What already exists — read before writing any code

**Do not start from scratch.** The split-building pipeline is already implemented.

### Existing pipeline script
`src/data/prepare_bcn20000.py` — config-driven script that:
1. Reads metadata CSV
2. Drops rows with empty `diagnosis_3` (handles the 1,307 exclusions automatically)
3. Drops rows where image file doesn't exist on disk
4. Maps `diagnosis_3` → `class_label` via `map_class_label()`
5. Assigns lesion-level splits (leakage-safe, seeded)
6. Asserts no lesion overlap across splits
7. Writes `master_metadata.csv`, `train.csv`, `val.csv`, `test.csv`
8. Writes a markdown summary

Run as: `python src/data/prepare_bcn20000.py --config config/bcn20000_config.yaml`

### Existing 3-class config
`config/bcn20000_config.yaml` — drives the old 3-class run. **Do not modify this file.**  
It points to `data/processed/bcn20000/` output and the old 3-class `class_mapping`.

### Existing approved label mapping
`data/processed/bcn20000/cancer_risk_label_mapping.csv` — already created in #117.  
All 11 `diagnosis_3` labels mapped to their target class. Use this as the source of truth.

### The problem with reusing the script as-is
`map_class_label()` in `prepare_bcn20000.py` (line 64) only handles 3 classes via config keys `melanoma_contains`, `nevus_exact`, `other_label`. It has no path to produce `Non-melanoma skin cancer` as a separate class — BCC/SCC currently fall through to `other_label`.

### Recommended implementation approach

**Option A (preferred): New script, same pattern**  
Create `src/data/prepare_bcn20000_cancer_risk.py` by copying `prepare_bcn20000.py` and replacing `map_class_label()` with a 4-class version:

```python
def map_class_label(diagnosis_value: str) -> str | None:
    d = diagnosis_value.lower()
    if 'melanoma' in d:
        return 'Melanoma'
    if 'basal cell carcinoma' in d or 'squamous cell carcinoma' in d:
        return 'Non-melanoma skin cancer'
    if 'nevus' in d or 'nevi' in d:
        return 'Benign nevus'
    # actinic keratosis, seborrheic keratosis, scar, solar lentigo, dermatofibroma, etc.
    return 'Other non-cancer / indeterminate lesion'
```

Empty `diagnosis_3` rows are already dropped before `map_class_label()` is called — no change needed there.

**Option B: Extend the existing script**  
Make `map_class_label()` config-driven for 4 classes by adding a `nmsc_contains` key. More flexible but more complex — only worth it if the team wants one generic script long-term.

### New config file to create
`config/bcn20000_cancer_risk_config.yaml` — same structure as the 3-class config but:
- `metadata_csv`: `bcn20000_metadata_2026-05-11.csv` (updated metadata file in repo root)
- `output_dir`: `data/processed/bcn20000_cancer_risk`
- `summary_path`: `docs/model/bcn20000_cancer_risk_split_summary.md`
- `class_names`: all 4 new class names
- `split.seed`: `42` (same as baseline for reproducibility)

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
| `bcn20000_metadata_2026-05-11.csv` | Source metadata for BCN20000 (repo root) |
| `data/processed/bcn20000/cancer_risk_label_mapping.csv` | Approved 4-class label mapping (from #117) |
| `src/data/prepare_bcn20000.py` | Existing split-building pipeline script (3-class) |
| `config/bcn20000_config.yaml` | Existing 3-class config — do not modify |
| `data/processed/bcn20000/train.csv` | Existing 3-class splits — do not overwrite |
| `docs/llm_project_context.md` | Full project context (authoritative) |
| `docs/decision_log.md` | All major decisions with rationale |
| `revela/FitzPatrick/notebooks/03_benchmark_requirements_CNN.ipynb` | Benchmark requirements + label mapping logic |
| `revela/FitzPatrick/notebooks/04_inference_pipeline_requirements.ipynb` | Inference pipeline requirements |
| `src/model/model.py` | EfficientNet-B0 model factory |
