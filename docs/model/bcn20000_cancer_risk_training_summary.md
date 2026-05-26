# BCN20000 Cancer-Risk EfficientNet-B0 Training Summary

Issue: #119 — D3.4: Retrain dermoscopic CNN with cancer-risk taxonomy

## Scope

Training entry point: `src/model/train.py`  
Config: `config/bcn20000_cancer_risk_config.yaml`

Splits:

- `data/processed/bcn20000_cancer_risk/train.csv` — 12,352 rows
- `data/processed/bcn20000_cancer_risk/val.csv` — 2,628 rows

The model is an EfficientNet-B0 initialized with ImageNet pretrained weights.  
Best model is selected by validation macro-F1.

## Classes

| Index | Class | Train count | Weight |
|------:|-------|------------:|-------:|
| 0 | Melanoma | 3,363 | 0.9182 |
| 1 | Non-melanoma skin cancer | 2,968 | 1.0404 |
| 2 | Benign nevus | 3,934 | 0.7850 |
| 3 | Other non-cancer / indeterminate lesion | 2,087 | 1.4796 |

Class weights use inverse frequency: `total / (num_classes × count)`.

## Outputs

Artifacts saved to `models/bcn20000_cancer_risk_effnet_b0/`:

- `best_model.pth`
- `class_to_idx.json`
- `training_history.csv`

## Training Configuration

| Parameter | Value |
|-----------|-------|
| Architecture | EfficientNet-B0 |
| Pretrained | ImageNet |
| Image size | 224 × 224 |
| Batch size | 16 |
| Epochs | 10 |
| Learning rate | 0.0003 |
| Weight decay | 0.01 |
| Optimizer | AdamW |
| Class weights | Yes (inverse frequency) |
| Device | MPS / CPU |

## Smoke Test

```bash
python3 -m src.model.train \
  --config config/bcn20000_cancer_risk_config.yaml \
  --epochs 1 --batch-size 4 --num-workers 0 \
  --max-train-batches 2 --max-val-batches 2
```

Smoke-test result:

Passed. Pipeline ran end-to-end: model loaded (EfficientNet-B0, MPS, 4 classes), 2 train batches + 2 val batches completed, best model saved. Image path fix applied — CSVs updated from `revela/BCN20000/` to `revela/Rehma_Revela/data/ISIC-images/`.

## Full Training Run

Command:

```bash
python3 -m src.model.train --config config/bcn20000_cancer_risk_config.yaml
```

Training history:

| Epoch | Train loss | Train acc | Val loss | Val acc | Val macro-F1 | Val bal. acc |
|------:|-----------:|----------:|---------:|--------:|-------------:|-------------:|
| 1 | 0.9434 | 62.71% | 0.8884 | 65.75% | 0.6445 | 65.64% |
| 2 | 0.7695 | 69.37% | 0.8588 | 66.97% | 0.6606 | 66.49% |
| 3 | 0.6678 | 74.55% | 0.8859 | 69.22% | 0.6768 | 67.75% |
| 4 | 0.5911 | 77.36% | 0.8673 | 68.95% | 0.6813 | 68.52% |
| 5 | 0.5198 | 80.68% | 0.9401 | 69.25% | 0.6787 | 68.28% |
| **6** | **0.4454** | **83.61%** | **0.9895** | **70.09%** | **0.6924** | **69.42%** |
| 7 | 0.3995 | 84.97% | 1.0091 | 67.39% | 0.6675 | 66.60% |
| 8 | 0.3456 | 87.07% | 1.1550 | 69.86% | 0.6910 | 69.44% |
| 9 | 0.3189 | 88.17% | 1.1390 | 66.48% | 0.6599 | 66.08% |
| 10 | 0.2875 | 89.18% | 1.2279 | 67.54% | 0.6642 | 66.68% |

Best epoch: **6** (Val macro-F1 0.6924, Val bal. acc 69.42%)

## Priority Metrics (Best Epoch)

Per-class recall not captured in training loop — to be measured in #120 evaluation on test split.

| Metric | Value |
|--------|-------|
| Val macro-F1 (epoch 6) | 0.6924 |
| Val balanced accuracy (epoch 6) | 69.42% |
| Val accuracy (epoch 6) | 70.09% |
| Melanoma recall | — (see #120) |
| Non-melanoma skin cancer recall | — (see #120) |
| Cancer / malignant recall | — (see #120) |

## Notes

- Old CNN v1 artifacts in `models/effnet_b0/` are not overwritten.
- Per-class recall columns added to `training_history.csv`: `val_recall_melanoma`, `val_recall_non_melanoma_skin_cancer`, `val_recall_benign_nevus`, `val_recall_other_non_cancer_indeterminate_lesion`, `val_cancer_recall`.
- Cancer recall counts any true malignant case (Melanoma or NMSC) predicted as *any* malignant class.
