# Revela — Clinical Model Setup Guide

## Purpose

This guide explains how to set up the local data, model artifacts, and repo context needed to work on clinical model improvement tasks for Revela.

The immediate goal is to let  work on clinical model error analysis and metric improvement using GitHub issues, ChatGPT, and Codex.

Relevant project context:

- Clinical dataset build is complete.
- Clinical model baseline is trained.
- Clinical model evaluation is complete.
- Next work should focus on understanding and improving clinical model metrics, especially source-specific performance and weak classes.

## Relevant issues

Use these as working context:

- `#125 — V2.5: Build clinical-image dataset with approved 5-class taxonomy` — completed.
- `#129 — V2.6: Train clinical-image CNN baseline` — completed.
- `#130 — V2.7: Evaluate clinical-image CNN on held-out test split` — completed.

Recommended next issue to create/work on:

- `V2.8 — Analyze clinical v2 errors by source, class, and raw label`

Possible follow-up issues:

- `V2.9 — Add source-aware/class-aware sampling for clinical v2 training`
- `V2.10 — Build high-confidence clinical v2 dataset variant`

## Current clinical model taxonomy

The clinical-image model uses 5 classes:

1. `Eczema / dermatitis`
2. `Urticaria / allergic reaction`
3. `Folliculitis / acne-like`
4. `Psoriasis / papulosquamous`
5. `Lesion — dermoscopic review recommended`

Important wording rule:

The fifth class is a routing class, not cancer detection. It should trigger dermoscopic review in the product flow. Do not describe it as diagnosis, cancer detection, or melanoma detection.

## Current model performance

Clinical v2 held-out test metrics:

- Combined accuracy: `0.6554`
- Combined macro-F1: `0.6420`
- Combined balanced accuracy: `0.6571`

Class-wise F1:

- `Eczema / dermatitis`: `0.6161`
- `Urticaria / allergic reaction`: `0.4870`
- `Folliculitis / acne-like`: `0.6540`
- `Psoriasis / papulosquamous`: `0.6246`
- `Lesion — dermoscopic review recommended`: `0.8282`

Source-specific macro-F1:

- Combined: `0.6420`
- Google SCIN: `0.4028`
- Fitzpatrick17k: `0.6366`

Interpretation:

- The clinical model is a valid first baseline.
- Lesion-routing is the strongest class.
- Urticaria is the weakest class.
- Google SCIN performance is much weaker than Fitzpatrick17k, so source-bias/generalization must be analyzed before random retraining.

## Local files required

Issa needs the raw images and model artifacts locally. These are not stored in Git.

Required local data:

```text
data/raw/scin/images/
data/raw/scin/metadata/manifest.csv
data/raw/fitzpatrick17k/images/
data/raw/fitzpatrick17k/metadata/fitzpatrick17k.csv
```

Required processed CSVs, already tracked in Git:

```text
data/processed/clinical_v2/train.csv
data/processed/clinical_v2/val.csv
data/processed/clinical_v2/test.csv
```

Required model artifacts, shared separately:

```text
models/clinical_v2_effnet_b0/best_model.pth
models/clinical_v2_effnet_b0/class_to_idx.json
models/clinical_v2_effnet_b0/training_history.csv
```

The `models/` and `data/raw/` folders are ignored by Git. They must be prepared locally.

## Step 1 — Pull latest repo

From the local repo root:

```bash
git checkout main
git pull --ff-only origin main
```

Create a branch for the task:

```bash
git checkout -b v2.8-clinical-error-analysis
```

Use a different branch name if the task is different.

## Step 2 — Create or activate virtual environment

If `.venv` already exists:

```bash
source .venv/bin/activate
```

If it does not exist:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install core dependencies:

```bash
python -m pip install torch torchvision pillow pandas scikit-learn matplotlib pyyaml tqdm datasets huggingface_hub tabulate
```

If using Apple Silicon, make sure PyTorch works with MPS:

```bash
python - <<'PY'
import torch
print('torch:', torch.__version__)
print('mps available:', torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False)
PY
```

## Step 3 — Download and prepare Fitzpatrick17k

Roman used this Google Drive file:

```text
https://drive.google.com/file/d/1B_dHew_vLq3h8QH6ufzA1Eh9N7guB8uj/view
```

Download it manually from the browser.

Then create local folders:

```bash
mkdir -p data/raw/fitzpatrick17k/images
mkdir -p data/raw/fitzpatrick17k/metadata
```

Move files as follows:

```text
fitzpatrick17k.csv → data/raw/fitzpatrick17k/metadata/
all .jpg images → data/raw/fitzpatrick17k/images/
```

Expected final structure:

```text
data/raw/fitzpatrick17k/metadata/fitzpatrick17k.csv
data/raw/fitzpatrick17k/images/<md5hash>.jpg
```

Validate image availability:

```bash
python - <<'PY'
import pandas as pd
from pathlib import Path

csv_path = Path('data/raw/fitzpatrick17k/metadata/fitzpatrick17k.csv')
image_dir = Path('data/raw/fitzpatrick17k/images')

df = pd.read_csv(csv_path)
print('Rows:', len(df))
print('Columns:', list(df.columns))

if 'md5hash' not in df.columns:
    raise SystemExit('ERROR: md5hash column not found')

df['expected_path'] = df['md5hash'].astype(str).apply(lambda x: image_dir / f'{x}.jpg')
df['exists'] = df['expected_path'].apply(lambda p: p.exists())

print('Existing images:', int(df['exists'].sum()))
print('Missing images:', int((~df['exists']).sum()))

if (~df['exists']).any():
    print(df.loc[~df['exists'], ['md5hash', 'label', 'expected_path']].head(10).to_string(index=False))
PY
```

Expected result from Roman's machine:

```text
Rows: 16577
Existing images: 16577
Missing images: 0
```

## Step 4 — Download and prepare official Google SCIN

SCIN is not downloaded through a normal image-download interface. Use Hugging Face.

First log in to Hugging Face if needed:

```bash
hf auth login
```

If a token is needed:

1. Go to Hugging Face.
2. Open `Settings → Access Tokens`.
3. Create a `Read` token.
4. Paste it into the terminal when `hf auth login` asks.
5. When asked `Add token as git credential?`, answer `n`.

Verify login:

```bash
hf auth whoami
```

Then run the existing project script:

```bash
python scripts/data/export_google_scin.py
```

Expected final structure:

```text
data/raw/scin/images/
data/raw/scin/metadata/manifest.csv
```

Expected result from Roman's machine:

```text
Image rows: 10406
Unique cases: 5033
```

The official `google/scin` dataset is required because it preserves metadata such as:

```text
case_id
age_group
sex_at_birth
fitzpatrick_skin_type
body parts
symptoms
condition duration
weighted_skin_condition_label
dermatologist labels
dermatologist confidence
Monk skin tone labels
```

Do not use `pg-dev-ai/scin-processed-clean-dataset` for final work. It drops important metadata and should only be considered a fallback/reference.

## Step 5 — Verify processed clinical dataset

The processed files are already tracked in Git:

```bash
ls -lh data/processed/clinical_v2/
```

Expected files:

```text
train.csv
val.csv
test.csv
```

Expected split sizes:

```text
Train: 6986
Validation: 1518
Test: 1515
```

Quick check:

```bash
python - <<'PY'
import pandas as pd

for split in ['train', 'val', 'test']:
    path = f'data/processed/clinical_v2/{split}.csv'
    df = pd.read_csv(path)
    print('\n', split, len(df))
    print(df['target_label'].value_counts())
    print(df['source_dataset'].value_counts())
PY
```

## Step 6 — Get clinical model artifacts

Roman has the trained clinical model locally:

```text
models/clinical_v2_effnet_b0/best_model.pth
models/clinical_v2_effnet_b0/class_to_idx.json
models/clinical_v2_effnet_b0/training_history.csv
```

These files are ignored by Git and must be shared separately.

Create the local folder:

```bash
mkdir -p models/clinical_v2_effnet_b0
```

Place the shared files there.

Validate:

```bash
ls -lh models/clinical_v2_effnet_b0/
cat models/clinical_v2_effnet_b0/training_history.csv
cat models/clinical_v2_effnet_b0/class_to_idx.json
```

## Step 7 — Re-run clinical evaluation to confirm environment

Run:

```bash
python3 -m src.model.evaluate_clinical_v2 --config config/clinical_v2_config.yaml
```

Expected combined metrics from Roman's run:

```text
Accuracy: 0.6554
Macro-F1: 0.6420
Balanced accuracy: 0.6571
```

Expected lesion-routing metrics:

```text
Precision: 0.8647
Recall: 0.7946
F1: 0.8282
Support: 370
```

Expected source-specific macro-F1:

```text
combined: 0.6420
google_scin: 0.4028
fitzpatrick17k: 0.6366
```

Generated outputs stay local because `outputs/` is ignored by Git:

```text
outputs/metrics/clinical_v2_test_metrics.json
outputs/metrics/clinical_v2_classification_report.csv
outputs/metrics/clinical_v2_source_metrics.csv
outputs/plots/clinical_v2_confusion_matrix.png
```

## Recommended next task — V2.8 error analysis

Before retraining, analyze errors. Do not start random hyperparameter tuning without understanding where the model fails.

Suggested issue title:

```text
V2.8 — Analyze clinical v2 errors by source, class, and raw label
```

Goal:

Identify whether the main metric problems come from source bias, label noise, class overlap, weak raw-label mappings, or training configuration.

Acceptance criteria:

- Save test-set prediction CSV with:
  - image_path
  - source_dataset
  - raw_label
  - target_label
  - predicted_label
  - predicted_confidence
  - class probabilities
  - correctness flag
- Summarize errors by true class.
- Summarize errors by predicted class.
- Summarize errors by source_dataset.
- Summarize errors by raw_label.
- Identify top confusion pairs.
- Inspect especially:
  - Urticaria false positives
  - Eczema false negatives
  - SCIN-specific errors
  - Lesion-routing false negatives
- Save findings in:
  - `outputs/error_analysis/clinical_v2_test_predictions.csv`
  - `outputs/error_analysis/clinical_v2_errors_by_raw_label.csv`
  - `outputs/error_analysis/clinical_v2_errors_by_source.csv`
  - `docs/model/clinical_v2_error_analysis.md`

Suggested Codex prompt:

```text
We are working on Revela clinical model improvement after #130.

Goal:
Create an error-analysis script for the trained clinical_v2 model.

Use:
- config/clinical_v2_config.yaml
- data/processed/clinical_v2/test.csv
- models/clinical_v2_effnet_b0/best_model.pth
- models/clinical_v2_effnet_b0/class_to_idx.json

Inspect existing:
- src/model/evaluate_clinical_v2.py
- src/data/dataset.py
- src/data/transforms.py

Implement:
- src/model/analyze_clinical_v2_errors.py

Requirements:
1. Reuse evaluation logic where possible.
2. Save per-image predictions to outputs/error_analysis/clinical_v2_test_predictions.csv.
3. Include source_dataset, raw_label, target_label, predicted_label, predicted_confidence, correctness flag, and probabilities for all classes.
4. Summarize errors by true class, predicted class, source_dataset, and raw_label.
5. Identify top confusion pairs.
6. Save summary CSVs under outputs/error_analysis/.
7. Write docs/model/clinical_v2_error_analysis.md with key findings and recommended next experiments.
8. Do not claim diagnosis or clinical readiness.
9. Run syntax checks. Do not run full analysis if torch is unavailable.

After implementation, provide exact command to run locally.
```

## Recommended improvement experiments after error analysis

Only after V2.8 is complete, pick one or two experiments.

### Experiment A — Class-aware sampling

Purpose:

Reduce class imbalance impact.

Try:

```text
WeightedRandomSampler by target_label
```

Track:

```text
combined macro-F1
google_scin macro-F1
fitzpatrick17k macro-F1
lesion-routing recall
urticaria F1
```

### Experiment B — Source-aware + class-aware sampling

Purpose:

Reduce source bias between Google SCIN and Fitzpatrick17k.

Try balancing by:

```text
target_label + source_dataset
```

This is likely more relevant than class balancing alone.

### Experiment C — High-confidence SCIN variant

Purpose:

Reduce noisy SCIN labels.

Build a dataset variant where SCIN rows are included only if top weighted label score is high enough.

Try thresholds:

```text
>= 0.67
>= 0.75
```

Compare against the current dataset.

### Experiment D — Conservative augmentation

Try only safe augmentations:

```text
RandomHorizontalFlip
RandomRotation up to 10–15 degrees
mild ColorJitter
safe RandomResizedCrop
```

Avoid aggressive color, blur, erasing, or transformations that destroy clinical morphology.

### Experiment E — Longer training with early stopping

Current clinical model trained for 5 epochs.

Try:

```text
10–15 epochs
early stopping patience 3
save best by validation macro-F1
```

Do not train blindly for many epochs. Validation loss started rising after epoch 3, while macro-F1 still improved until epoch 5.

## What not to do yet

Do not:

- Add random new datasets before error analysis.
- Change taxonomy before analyzing raw-label errors.
- Optimize only combined accuracy.
- Ignore SCIN-specific performance.
- Present the lesion-routing class as cancer detection.
- Build final inference wording before stable output schema.

## Expected working mode with ChatGPT + Codex

Recommended workflow:

1. Read the GitHub issue and latest comments.
2. Pull latest `main`.
3. Create a dedicated branch.
4. Ask ChatGPT to clarify product/ML scope if needed.
5. Ask Codex to implement code changes.
6. Run scripts locally because raw images and model artifacts are local.
7. Share terminal output with ChatGPT for interpretation.
8. Commit only code, configs, docs, and processed CSVs if appropriate.
9. Do not commit raw images or model artifacts unless the team explicitly changes artifact-storage policy.

## Git hygiene

Before starting:

```bash
git checkout main
git pull --ff-only origin main
git status
```

Create branch:

```bash
git checkout -b v2.8-clinical-error-analysis
```

Before committing:

```bash
git status
git diff --stat
```

Commit example:

```bash
git add src/model/analyze_clinical_v2_errors.py docs/model/clinical_v2_error_analysis.md
git commit -m "Analyze clinical v2 model errors"
git push -u origin v2.8-clinical-error-analysis
```

## Artifact policy

Do not commit:

```text
data/raw/
models/
outputs/
.venv/
```

These are ignored by Git.

Commit:

```text
scripts/
src/
config/
docs/
data/processed/ if intentionally generated and small enough
```

## Summary for Issa

Set up both datasets locally, get the trained model artifacts from Roman, rerun the evaluation to confirm your setup, then start with error analysis. The likely improvement path is source-aware/class-aware sampling and higher-quality SCIN filtering, not random architecture changes.
