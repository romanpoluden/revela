# Revela — Final Model Artifact Collection

**Issue:** D8.5 (#195)
**Date:** 2026-05-27
**Completed by:** rehmaaziz
**Your machine — Branch:** v2.22-metrics-to-main | **Commit SHA:** c0181c4322fd72ce7d55a89705a3f3e46baceed1
**Roman's machine — Branch:** main | **Commit SHA:** 8b47a49

## Source of Truth Per Model

| Model | Source of Truth Machine | Confirmed by |
|---|---|---|
| clinical_skin_condition_v1 | Rehma's machine — HF artifact matches local checkpoint | SHA256 hash match (mine = HF; Roman's local is an earlier version) |
| dermoscopic_cancer_risk_bcn_mnh_v1 | Rehma's machine (retrained final version D4.5) | SHA256 hash match (mine = HF = Roman's local — all three identical) |

## Artifact Locations (canonical inference paths)

### clinical_skin_condition_v1
- Checkpoint: `models/clinical_v2_effnet_b0/best_model.pth`
- class_to_idx: `models/clinical_v2_effnet_b0/class_to_idx.json`
- Config: `config/clinical_v2_config.yaml`

### dermoscopic_cancer_risk_bcn_mnh_v1
- Checkpoint: `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth`
- class_to_idx: `models/bcn_mnh_cancer_risk_effnet_b0/class_to_idx.json`
- Config: `config/bcn_mnh_cancer_risk_config.yaml`

## Hash Comparison Table

| Artifact | Rehma SHA256 | Roman SHA256 | HF SHA256 | Match |
|---|---|---|---|---|
| clinical best_model.pth | eba9a581505c60cee98152c790c4113a1549c691248d518cc5d1e7097feb20bc | 5a1bdc05e3d13b618ebc34bd004eb4c508d93702cb9539ddee6a169a60595b3f | eba9a581505c60cee98152c790c4113a1549c691248d518cc5d1e7097feb20bc | Rehma=HF; Roman≠ |
| clinical class_to_idx.json | 54cfa7c59ff278e52b86b52b8be281300ea14141093e26992ab88d9efb5d55f2 | 54cfa7c59ff278e52b86b52b8be281300ea14141093e26992ab88d9efb5d55f2 | — | Match |
| clinical_v2_config.yaml | ae7ddcf3f8739403fdd65475ba1e92dbdd920dc024f947a2d76ea8574d7531e4 | ae7ddcf3f8739403fdd65475ba1e92dbdd920dc024f947a2d76ea8574d7531e4 | — | Match |
| dermoscopic best_model.pth | 71a20d7cf8137c0ac5a1d43c24892a97b308e51f0c29407a19696c75d323c385 | 71a20d7cf8137c0ac5a1d43c24892a97b308e51f0c29407a19696c75d323c385 | 71a20d7cf8137c0ac5a1d43c24892a97b308e51f0c29407a19696c75d323c385 | All match |
| dermoscopic class_to_idx.json | 303efc9ca936a78b573c4cdc30e4767af77efc90edd8e1d901e92cab101a0d96 | 303efc9ca936a78b573c4cdc30e4767af77efc90edd8e1d901e92cab101a0d96 | — | Match |
| bcn_mnh_cancer_risk_config.yaml | c6c729fe065077ba2ea0d984b747c63d4f44c2a10680283cf5397e19b1c31007 | c6c729fe065077ba2ea0d984b747c63d4f44c2a10680283cf5397e19b1c31007 | — | Match |

## Verification Results

| Check | Clinical | Dermoscopic |
|---|---|---|
| Checkpoint exists | OK | OK |
| class_to_idx exists | OK | OK |
| app.py syntax | PASS | PASS |
| adapter.py syntax | PASS | PASS |
| model_registry.py syntax | PASS | PASS |
| llm_prompt_builder.py syntax | PASS | PASS |
| Inference CLI | PASS | PASS |
| Inference output | Folliculitis / acne-like (58.99%), Eczema / dermatitis (26.55%), Lesion — dermoscopic review recommended (7.40%) | Benign nevus (51.89%), Melanoma (47.88%), Other non-cancer / indeterminate lesion (0.18%), Non-melanoma skin cancer (0.05%) |
| Exit code | 0 | 0 |
| Runtime | ~7.8s | ~3.8s |
| Test image | data/raw/scin/images/train_-3208362477794549016_image_1.jpg | data/mel_nevus_histo/images/ISIC_0000002.jpg |

## Excluded
Intermediate checkpoints, optimizer states, failed experiment artifacts,
and training-only files excluded per issue #195 scope.

## Next Step
Upload to Hugging Face via D5.4 (#180).

## Safety Note
Educational prototype. Not for clinical diagnosis, treatment, or patient decisions.
