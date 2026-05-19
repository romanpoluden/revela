# Clinical V2 Sampling Experiment Summary

## Purpose

V2.9 adds configurable training samplers for the clinical v2 image classifier so baseline training can be compared with class-aware and source+class-aware sampling. This was motivated by the V2.8 source gap:

- Combined accuracy: 0.6554
- Combined macro-F1: 0.6420
- Combined balanced accuracy: 0.6571
- google_scin accuracy: 0.5722
- google_scin macro-F1: 0.4028
- fitzpatrick17k accuracy: 0.7044
- fitzpatrick17k macro-F1: 0.6366
- google_scin error rate: 0.4278
- fitzpatrick17k error rate: 0.2956

The goal is to compare training strategies using validation macro-F1, validation balanced accuracy, lesion-routing recall, urticaria F1 when available, and source-specific metrics when available. Combined accuracy alone should not drive selection.

## Sampler Modes

The clinical training pipeline now supports:

- `none`: default DataLoader shuffle behavior, preserving the previous training behavior.
- `class`: weighted sampling by `target_label`.
- `source_class`: weighted sampling by `source_dataset` and `target_label`.

The sampler uses inverse-frequency group weights with `torch.utils.data.WeightedRandomSampler`.

## Config Files

- `config/clinical_v2_config.yaml` documents the default backward-compatible sampler config with `mode: none`.
- `config/clinical_v2_class_sampler_config.yaml` runs class-aware sampling and writes to `models/clinical_v2_class_sampler_effnet_b0`.
- `config/clinical_v2_source_class_sampler_config.yaml` runs source+class-aware sampling and writes to `models/clinical_v2_source_class_sampler_effnet_b0`.

## Smoke Test

Command:

```bash
.venv/bin/python -m src.model.train \
  --config config/clinical_v2_source_class_sampler_config.yaml \
  --epochs 1 \
  --max-train-batches 2 \
  --max-val-batches 2
```

Result:

- Completed successfully with the source+class sampler active.

Smoke-test metrics to record:

- Validation macro-F1: 0.1115
- Validation balanced accuracy: 0.1077
- Lesion-routing recall: not emitted by the short training script
- Urticaria F1: not emitted by the short training script
- Source-specific validation metrics: not emitted by the short training script

Additional smoke-test output:

- Train loss: 1.5716
- Train accuracy: 0.2812
- Validation loss: 1.6499
- Validation accuracy: 0.1250
- Best model path: `models/clinical_v2_source_class_sampler_effnet_b0/best_model.pth`
- History path: `models/clinical_v2_source_class_sampler_effnet_b0/training_history.csv`

## Safety Note

This is an educational, non-diagnostic model experiment. The lesion-routing class is for routing an image toward dermoscopic review, not cancer detection. These changes do not establish clinical readiness.
