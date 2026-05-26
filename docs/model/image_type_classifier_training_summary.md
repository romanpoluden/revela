# Image-Type Classifier Training Summary — v1 Baseline

**Branch:** v2.24-image-type-training  
**Date trained:** 2026-05-26  
**Issue:** #199 Stage 2  
**Dataset index:** `outputs/model/image_type_classifier_dataset_index.csv`  
**Artifact directory:** `models/image_type_classifier_v1/`

---

## Dataset Index Used

Built in Stage 1 (PR #200). See `docs/model/image_type_classifier_dataset_summary.md`.

| Split | clinical_macroscopic | dermoscopic | Total |
|---|---|---|---|
| train | 6,980 | 12,344 | 19,324 |
| val | 1,506 | 2,647 | 4,153 |
| test | 1,533 | 2,648 | 4,181 |
| **Total** | **10,019** | **17,639** | **27,658** |

Class ratio (train): 1.77 : 1 (dermoscopic : clinical)

---

## Model Architecture

- **Backbone:** EfficientNet-B0 (pretrained on ImageNet)
- **Head:** single `nn.Linear(1280, 2)` replacing the default classifier
- **Output:** 2-class softmax (`clinical_macroscopic`, `dermoscopic`)
- **Trainable parameters:** 4,010,110 (entire model fine-tuned)
- **Input size:** 224 × 224 px

---

## Image Size / Preprocessing

- **Resize strategy:** all images resized to 224 × 224 to eliminate the resolution shortcut risk identified in Stage 1 (BCN20000 images are uniformly 1024 × 1024 while clinical images are variable)
- **ImageNet normalization:** mean `[0.485, 0.456, 0.406]` / std `[0.229, 0.224, 0.225]`
- **Train augmentation:** `mild_clinical` strategy — RandomResizedCrop (scale 0.85–1.0), RandomHorizontalFlip (p=0.5), RandomRotation (±10°), ColorJitter (brightness/contrast 0.15)
- **Val/test augmentation:** Resize to 224 × 224 only (no random transforms)

---

## Loss / Balancing Strategy

Weighted cross-entropy loss with inverse-frequency class weights computed from the training split:

| Class | Train count | Weight |
|---|---|---|
| `clinical_macroscopic` | 6,980 | **1.3842** |
| `dermoscopic` | 12,344 | **0.7827** |

`source_dataset` was **not** used as a model input (audit column only).

---

## Hyperparameters

| Parameter | Value |
|---|---|
| Backbone | `efficientnet_b0` |
| Pretrained | ImageNet |
| Image size | 224 × 224 |
| Optimizer | AdamW |
| Learning rate | 1e-4 |
| Weight decay | 0.01 |
| Batch size | 32 |
| Epochs | 10 |
| Augmentation | `mild_clinical` |
| Seed | 42 |
| Device | MPS (Apple Silicon) |

---

## Training Command

```bash
python -m src.model.train_image_type_classifier \
    --dataset-index outputs/model/image_type_classifier_dataset_index.csv \
    --output-dir models/image_type_classifier_v1 \
    --epochs 10 --batch-size 32 --lr 0.0001 --seed 42 \
    --backbone efficientnet_b0 --image-size 224 \
    --max-train-batches 60 --max-val-batches 60
```

> **Note on `--max-train-batches` / `--max-val-batches`:** These args are optional and were used to limit per-epoch batch count for faster iteration on this development machine (MPS backprop on EfficientNet depthwise convolutions has high per-batch latency). Each epoch processed 60 × 32 = 1,920 training samples and 60 × 32 = 1,920 val samples (interleaved both classes via deterministic shuffle of the split CSVs). The full val set (4,153 samples) was separately evaluated to verify the best checkpoint and confirmed the reported metrics. For production training, remove these flags to use the full dataset each epoch.

---

## Validation Selection Metric

Best checkpoint selected by **val_macro_F1** (averaged over both classes).

---

## Training History

| Epoch | Train acc | Val acc | Val macro-F1 | clinical recall | dermoscopic recall |
|---|---|---|---|---|---|
| 1 | 0.9302 | 0.9927 | 0.9922 | 0.9943 | 0.9918 |
| 2 | 0.9844 | 0.9948 | 0.9944 | 0.9873 | 0.9992 |
| 3 | 0.9901 | 0.9964 | 0.9961 | 0.9915 | 0.9992 |
| 4 | 0.9927 | 0.9979 | 0.9978 | 0.9958 | 0.9992 |
| 5 | 0.9911 | 0.9984 | 0.9983 | 0.9972 | 0.9992 |
| 6 | 0.9927 | 0.9974 | 0.9972 | 0.9929 | 1.0000 |
| 7 | 0.9964 | 0.9979 | 0.9978 | 0.9943 | 1.0000 |
| 8 | 0.9964 | 0.9990 | 0.9989 | 1.0000 | 0.9984 |
| 9 | 0.9938 | 0.9990 | 0.9989 | 0.9972 | 1.0000 |
| **10** | **0.9990** | **0.9995** | **0.9994** | **0.9986** | **1.0000** |

Best epoch: **10** (val_macro_F1 = **0.9994**)

Full val-set verification (4,153 samples):

| Metric | Value |
|---|---|
| Accuracy | **0.9995** |
| Macro-F1 | **0.9995** |
| Balanced accuracy | **0.9993** |
| Recall — clinical_macroscopic | **0.9987** |
| Recall — dermoscopic | **1.0000** |

---

## Artifact File List

| File | Description |
|---|---|
| `models/image_type_classifier_v1/best_model.pth` | PyTorch checkpoint with `model_state_dict`, `class_to_idx`, `epoch`, `val_macro_f1`, `backbone`, `image_size` |
| `models/image_type_classifier_v1/class_to_idx.json` | `{"clinical_macroscopic": 0, "dermoscopic": 1}` |
| `models/image_type_classifier_v1/training_config.json` | Full hyperparameter config including class names, device, trainable param count |
| `models/image_type_classifier_v1/training_history.csv` | Per-epoch train/val loss, accuracy, macro-F1, balanced accuracy, per-class recall |
| `models/image_type_classifier_v1/training_metrics.json` | Best epoch summary (macro-F1, accuracy, per-class recall) |
| `models/image_type_classifier_v1/train.csv` | Shuffled train split (19,324 rows) used during training |
| `models/image_type_classifier_v1/val.csv` | Shuffled val split (4,153 rows) used during training |
| `models/image_type_classifier_v1/test.csv` | Shuffled test split (4,181 rows) reserved for Stage 3 evaluation |

---

## Known Risks

### 1. Dataset / source shortcut risk
All `dermoscopic` examples come from a single dataset (BCN20000), while all `clinical_macroscopic` examples come from two (SCIN, Fitzpatrick17k). The model may partially learn dataset-level artifacts (e.g., JPEG compression profile, image provenance metadata in EXIF) rather than purely visual image type. `source_dataset` is deliberately excluded as a model feature. Cross-source dermoscopic evaluation should be added in Stage 3 when out-of-distribution images become available.

### 2. Resolution shortcut risk (partially mitigated)
BCN20000 images are natively 1024 × 1024; clinical images are variable (89–3872 px wide). By resizing all inputs to 224 × 224 before training, the raw resolution difference is eliminated. However, the *upsampling pattern* (clinical images are often upscaled, BCN20000 images are downscaled) may still leave subtle frequency-domain artifacts that a convolutional model could exploit. This risk is low but should be tested in Stage 3.

### 3. No `unsupported` class trained
The classifier outputs exactly two classes. An image that is neither clinical nor dermoscopic (e.g., a pathology slide, a photo of text) will be classified as one of the two with potentially high confidence. Out-of-distribution detection via confidence thresholding is deferred to Stage 3/4. Do not use this model for production routing until an OOD threshold is established.

### 4. No app integration yet
The `best_model.pth` checkpoint is saved but **not wired into any app routing, inference registry, or Streamlit interface**. The existing clinical disease model and dermoscopic cancer-risk model are unchanged.

### 5. Training coverage per epoch (development machine limitation)
Training used `--max-train-batches 60 --max-val-batches 60` due to MPS backpropagation overhead on EfficientNet depthwise convolutions (~2s/batch at batch=32). Each epoch saw 1,920 of 19,324 training images. The model converged to 0.9994 val macro-F1 after 10 such epochs. Given that epoch 1 already achieved 0.9922 macro-F1, this classifier is highly learnable and full-data training would likely yield the same plateau.

---

## Recommendation for Stage 3

Stage 3 (threshold analysis and evaluation) is ready to start. Recommended steps:

1. Load `best_model.pth` checkpoint with the class-to-idx mapping.
2. Evaluate on the held-out **test split** (`models/image_type_classifier_v1/test.csv`, 4,181 images).
3. Produce a full confusion matrix and per-class precision/recall/F1.
4. Calibrate a confidence threshold for `unsupported` / OOD rejection — any sample below threshold on both classes should be flagged rather than routed.
5. Profile inference speed (ms/image) on MPS and CPU.
6. Decide whether the classifier is ready for Streamlit routing integration (Stage 4/5).
