# Clinical V2 EfficientNet-B0 Training Summary

Issue: #129 - V2.6: Train clinical-image CNN baseline

## Scope

The training entry point now supports the Clinical V2 CSV layout:

- `data/processed/clinical_v2/train.csv`
- `data/processed/clinical_v2/val.csv`
- label column: `target_label`
- class index column: `class_idx`

The model is an EfficientNet-B0 image classifier initialized with ImageNet pretrained weights when available through torchvision.

## Approved Classes

1. Eczema / dermatitis
2. Urticaria / allergic reaction
3. Folliculitis / acne-like
4. Psoriasis / papulosquamous
5. Lesion — dermoscopic review recommended

The fifth class is a routing class for dermoscopic review, not cancer detection. This model must not be presented as making diagnoses.

## Outputs

Training writes artifacts to:

`models/clinical_v2_effnet_b0/`

Expected files:

- `best_model.pth`
- `class_to_idx.json`
- `training_history.csv`

Tracked metrics:

- `train_loss`
- `train_accuracy`
- `val_loss`
- `val_accuracy`
- `val_macro_f1`
- `val_balanced_accuracy`

## Smoke Test

Run a short local smoke test before full training:

```bash
python3 -m src.model.train --config config/clinical_v2_config.yaml --epochs 1 --batch-size 4 --num-workers 0 --max-train-batches 2 --max-val-batches 2
```

This checks config parsing, image loading, pretrained EfficientNet-B0 initialization, one small train pass, one small validation pass, metric writing, and checkpoint creation.


## Status

Syntax compilation passed for the modified training, model, and dataset modules.

Runtime smoke test passed locally on MPS with:

`python3 -m src.model.train --config config/clinical_v2_config.yaml --epochs 1 --batch-size 4 --num-workers 0 --max-train-batches 2 --max-val-batches 2`

Smoke-test result:

- Train examples: 6,986
- Validation examples: 1,518
- Device: MPS
- Train loss: 1.5853
- Train accuracy: 0.2500
- Validation loss: 1.5223
- Validation accuracy: 0.3750
- Validation macro-F1: 0.2143
- Validation balanced accuracy: 0.1667

These smoke-test metrics are not model-quality metrics because only two train batches and two validation batches were used. The smoke test only confirms that the training pipeline runs end-to-end and saves artifacts.
