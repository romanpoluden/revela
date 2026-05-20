# Dermoscopic Inference Registration — BCN+MNH v1

**Issue:** D5.1 (#163)
**Date:** 2026-05-20
**Model ID:** `dermoscopic_cancer_risk_bcn_mnh_v1`

## Artifact Location

| File | Path |
|---|---|
| Checkpoint | `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth` |
| class_to_idx | `models/bcn_mnh_cancer_risk_effnet_b0/class_to_idx.json` |
| training_history | `models/bcn_mnh_cancer_risk_effnet_b0/training_history.csv` |

## Registry Entry

| Field | Value |
|---|---|
| input_type | dermoscopic |
| architecture | efficientnet_b0 |
| num_classes | 4 |
| image_size | 224 |
| config_path | `config/bcn_mnh_cancer_risk_config.yaml` |
| checkpoint_path | `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth` |
| class_to_idx_path | `models/bcn_mnh_cancer_risk_effnet_b0/class_to_idx.json` |

## Class Names (index order)

0. Melanoma
1. Non-melanoma skin cancer
2. Benign nevus
3. Other non-cancer / indeterminate lesion

## Smoke Test Result

| Check | Result |
|---|---|
| Image tested | `data/mel_nevus_histo/images/ISIC_0000002.jpg` |
| Top prediction | Benign nevus (51.89%) |
| All 10 schema fields present | yes |
| 4 classes in predictions | yes |
| Confidences in [0, 1] | yes |
| Forbidden phrases absent | yes |
| Invalid input returns safe error | yes (`error_code: missing_model_artifact`) |

## Safety

This model is an educational cancer-risk review tool. Model confidence is not clinical
certainty. Not diagnosis and not treatment guidance.

## Out of Scope

Streamlit UI enablement, clinical model changes, Hugging Face deployment,
clinical-readiness claims.
