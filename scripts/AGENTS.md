# Revela Project Instructions for Codex

## Product context

Revela is an educational dermatology training aid for dermatology residents and trainees.

The MVP is not a diagnostic tool. It must never claim that a user "has" a condition. Use language such as:
- differential suggestion
- may be consistent with
- educational output
- not for diagnosis or patient care

## Current technical goal

Build one CNN model using the BCN20000 dataset.

The model is a dermoscopic lesion classifier.

Target classes:
1. Melanoma
2. Benign nevus
3. Other lesion

The model must return:
- top-3 predictions
- confidence scores
- uncertainty bucket
- educational disclaimer

## Dataset

Dataset: BCN20000

Metadata path:
data/raw/bcn20000/bcn20000_metadata_2026-05-07.csv

Image root:
data/raw/bcn20000/images/

Important:
- BCN20000 is dermoscopic-only.
- Use lesion-level splitting.
- Do not split randomly by image.
- All images with the same lesion_id must be in the same split.
- Do not use patient-care or diagnosis wording.

## Required pipeline

Build:

config/bcn20000_config.yaml

src/data/prepare_bcn20000.py
src/data/dataset.py
src/data/transforms.py

src/model/model.py
src/model/train.py
src/model/evaluate.py

src/inference/predict.py

docs/model/bcn20000_model_card.md

## Model

Use PyTorch and torchvision.
Preferred model: EfficientNet-B0 pretrained on ImageNet.
Replace classifier head with a 3-class output.

## Metrics

Evaluation must include:
- top-1 accuracy
- top-3 accuracy
- macro-F1
- balanced accuracy
- classification report
- confusion matrix

## Safety requirements

Every user-facing result must include:
"Educational training aid only. Not for diagnosis or patient care."

Avoid:
- diagnosis result
- you have melanoma
- confirmed condition
- malignant confirmation

Use:
- differential suggestion
- model output
- educational reasoning
- requires expert review

## Coding style

Keep code beginner-readable.
Use clear function names.
Add comments where logic is non-obvious.
Do not over-engineer.
Avoid unnecessary frameworks.
