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

<!-- Fill in after running -->

## Full Training Run

Command:

```bash
python3 -m src.model.train --config config/bcn20000_cancer_risk_config.yaml
```

Training history:

<!-- Fill in after training completes -->

| Epoch | Train loss | Train acc | Val loss | Val acc | Val macro-F1 | Val bal. acc |
|------:|-----------:|----------:|---------:|--------:|-------------:|-------------:|

## Priority Metrics (Best Epoch)

<!-- Fill in after training completes -->

| Metric | Value |
|--------|-------|
| Val macro-F1 | — |
| Melanoma recall | — |
| Non-melanoma skin cancer recall | — |
| Cancer / malignant recall | — |
| Balanced accuracy | — |

## Notes

- Old CNN v1 artifacts in `models/effnet_b0/` are not overwritten.
- Per-class recall columns added to `training_history.csv`: `val_recall_melanoma`, `val_recall_non_melanoma_skin_cancer`, `val_recall_benign_nevus`, `val_recall_other_non_cancer_indeterminate_lesion`, `val_cancer_recall`.
- Cancer recall counts any true malignant case (Melanoma or NMSC) predicted as *any* malignant class.
