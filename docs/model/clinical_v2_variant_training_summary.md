# Clinical V2 Variant Training Summary

Issue: #152

Training metrics are validation-only. Test-set evaluation and promotion decision are out of scope and handled in #153.

## Preflight Checks

- YAML parse check: passed for all four configs using the project virtual environment.
- Train/validation CSV existence check: passed for all four configs.
- Output directory check: all four configs write to distinct variant directories.
- Baseline protection check: no config writes to `models/clinical_v2_effnet_b0/`.
- Taxonomy changes: none.
- App inference wiring changes: none.
- Inference registry changes: none.
- No held-out test-set evaluation was run.
- No model was promoted.
- Do not claim clinical readiness or diagnosis from these validation-only results.

## Variants

### Class-aware sampler

- Status: complete
- Config path: `config/clinical_v2_class_sampler_config.yaml`
- Dataset path: `data/processed/clinical_v2`
- Train CSV: `data/processed/clinical_v2/train.csv`
- Validation CSV: `data/processed/clinical_v2/val.csv`
- Output directory: `models/clinical_v2_class_sampler_effnet_b0/`
- Sampler mode: `class`
- Class weights used: yes
- Training mode note: sampler + class-weighted loss, not sampler-only.
- Exact training command: `.venv/bin/python -m src.model.train --config config/clinical_v2_class_sampler_config.yaml`
- Best validation macro-F1: 0.658372
- Best validation balanced accuracy: 0.678165
- Best validation accuracy: 0.664690
- Best epoch: 5
- Artifacts exist:
  - `best_model.pth`: yes
  - `class_to_idx.json`: yes
  - `training_history.csv`: yes
- Runtime notes: Full training completed. Metrics are validation-only.

### Source+class-aware sampler

- Status: complete
- Config path: `config/clinical_v2_source_class_sampler_config.yaml`
- Dataset path: `data/processed/clinical_v2`
- Train CSV: `data/processed/clinical_v2/train.csv`
- Validation CSV: `data/processed/clinical_v2/val.csv`
- Output directory: `models/clinical_v2_source_class_sampler_effnet_b0/`
- Sampler mode: `source_class`
- Class weights used: yes
- Training mode note: source+class sampler + class-weighted loss, not sampler-only.
- Exact training command: `.venv/bin/python -m src.model.train --config config/clinical_v2_source_class_sampler_config.yaml`
- Best validation macro-F1: 0.636100
- Best validation balanced accuracy: 0.662300
- Best validation accuracy: 0.641600
- Best epoch: 5
- Artifacts exist:
  - `best_model.pth`: yes
  - `class_to_idx.json`: yes
  - `training_history.csv`: yes
- Runtime notes: Full training completed. Metrics are validation-only.

### High-confidence SCIN 0.67

- Status: complete
- Config path: `config/clinical_v2_high_confidence_067_config.yaml`
- Dataset path: `data/processed/clinical_v2_high_confidence_067`
- Train CSV: `data/processed/clinical_v2_high_confidence_067/train.csv`
- Validation CSV: `data/processed/clinical_v2_high_confidence_067/val.csv`
- Output directory: `models/clinical_v2_high_confidence_067_effnet_b0/`
- Sampler mode: `none`
- Class weights used: yes
- Exact training command: `.venv/bin/python -m src.model.train --config config/clinical_v2_high_confidence_067_config.yaml`
- Best validation macro-F1: 0.681468
- Best validation balanced accuracy: 0.696755
- Best validation accuracy: 0.707957
- Best epoch: 5
- Artifacts exist:
  - `best_model.pth`: yes
  - `class_to_idx.json`: yes
  - `training_history.csv`: yes
- Runtime notes: Full training completed. Metrics are validation-only.

### High-confidence SCIN 0.75

- Status: complete
- Config path: `config/clinical_v2_high_confidence_075_config.yaml`
- Dataset path: `data/processed/clinical_v2_high_confidence_075`
- Train CSV: `data/processed/clinical_v2_high_confidence_075/train.csv`
- Validation CSV: `data/processed/clinical_v2_high_confidence_075/val.csv`
- Output directory: `models/clinical_v2_high_confidence_075_effnet_b0/`
- Sampler mode: `none`
- Class weights used: yes
- Exact training command: `.venv/bin/python -m src.model.train --config config/clinical_v2_high_confidence_075_config.yaml`
- Best validation macro-F1: 0.685332
- Best validation balanced accuracy: 0.708923
- Best validation accuracy: 0.709502
- Best epoch: 4
- Artifacts exist:
  - `best_model.pth`: yes
  - `class_to_idx.json`: yes
  - `training_history.csv`: yes
- Runtime notes: Full training completed. Metrics are validation-only.

## Validation Ranking

1. High-confidence SCIN 0.75
2. High-confidence SCIN 0.67
3. Class-aware sampler
4. Source+class-aware sampler

These are validation-only results. No held-out test-set evaluation was run. No model was promoted. #153 remains required for test-set comparison and promotion decision. Do not claim clinical readiness or diagnosis.

## Commands To Run

```bash
.venv/bin/python -m src.model.train --config config/clinical_v2_class_sampler_config.yaml
.venv/bin/python -m src.model.train --config config/clinical_v2_source_class_sampler_config.yaml
.venv/bin/python -m src.model.train --config config/clinical_v2_high_confidence_067_config.yaml
.venv/bin/python -m src.model.train --config config/clinical_v2_high_confidence_075_config.yaml
```

After each completed run, verify:

```bash
test -f models/<variant_output_dir>/best_model.pth
test -f models/<variant_output_dir>/class_to_idx.json
test -f models/<variant_output_dir>/training_history.csv
```
