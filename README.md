# Revela

Revela is an educational dermatology training aid. The current MVP focuses on a CNN-based image classifier that supports learning about lesion differentials from dermoscopic images. It is not a diagnostic tool and should not be used for patient care.

## What The Model Does

The model is an EfficientNet-B0 image classifier trained to group dermoscopic lesion images into 3 classes:

- `Melanoma`
- `Benign nevus`
- `Other lesion`

Its purpose is to provide an educational model output for trainees, not a clinical diagnosis.

## What Dataset It Uses

The model uses the `BCN20000` dataset, with metadata prepared from:

- `data/raw/bcn20000/bcn20000_metadata_2026-05-07.csv`

Processed train, validation, and test splits are saved under:

- `data/processed/bcn20000/`

## Why It Is Dermoscopic-Only

This pipeline is intentionally dermoscopic-only because the BCN20000 images used here are dermoscopic lesion images. Keeping the scope limited to one image modality makes the prototype more consistent and reduces confusion that could come from mixing dermoscopic and non-dermoscopic photos.

## What The Metrics Mean

- `Top-1 accuracy`: how often the model's highest-scoring class matches the true class.
- `Top-3 accuracy`: how often the true class appears in the model's top 3 scores.
- `Macro-F1`: the average F1 score across classes, giving each class equal weight.
- `Balanced accuracy`: the average recall across classes, which helps when class sizes differ.
- `Precision`: when the model predicts a class, how often that prediction is correct.
- `Recall`: how often the model finds examples that truly belong to a class.
- `F1`: a balance between precision and recall for one class.
- `Confusion matrix`: a table showing which classes the model confuses with each other.

Evaluation outputs are saved under:

- `outputs/metrics/`
- `outputs/plots/`

## Limitations

- The model only supports dermoscopic images, not smartphone photos or general clinical images.
- It predicts only 3 broad classes, so it is a simplified educational prototype.
- Performance depends on the BCN20000 data distribution and may not generalize well to new settings.
- Top-3 accuracy is less informative in a 3-class problem because all classes can appear in the top 3.
- The model output should be treated as an educational differential suggestion only, not as diagnosis or treatment advice.
