# Artifact Manifest — dermoscopic_cancer_risk_bcn_mnh_v1

**Model ID:** dermoscopic_cancer_risk_bcn_mnh_v1
**Input type:** Dermoscopic image
**Architecture:** EfficientNet-B0
**Taxonomy:** 4-class dermoscopic cancer-risk educational taxonomy
**Classes:** Melanoma | Non-melanoma skin cancer | Benign nevus | Other non-cancer / indeterminate lesion

**Trainer:** Rehma Aziz (final retrained version — D4.5 #141)
**Source machine:** Rehma's machine
**Source branch:** v2.22-metrics-to-main
**Source commit SHA:** c0181c4322fd72ce7d55a89705a3f3e46baceed1
**Artifact owner note:** Rehma retrained the final version from her machine. All three sources match (Rehma local = HF = Roman local, SHA256: 71a20d7cf8137c0ac5a1d43c24892a97b308e51f0c29407a19696c75d323c385). Rehma's machine is canonical source of truth per issue #195.
**Training data:** BCN20000 + Mel+Nevus Histo filtered (D4.1–D4.7)
**Created date:** May 18 2026 (file timestamp: models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth)

## Required Inference Files

| File | Path | Size | SHA256 |
|---|---|---|---|
| Checkpoint | models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth | 16M | 71a20d7cf8137c0ac5a1d43c24892a97b308e51f0c29407a19696c75d323c385 |
| class_to_idx | models/bcn_mnh_cancer_risk_effnet_b0/class_to_idx.json | 121B | 303efc9ca936a78b573c4cdc30e4767af77efc90edd8e1d901e92cab101a0d96 |
| Config | config/bcn_mnh_cancer_risk_config.yaml | 1.2K | c6c729fe065077ba2ea0d984b747c63d4f44c2a10680283cf5397e19b1c31007 |

## Inference Verification

**Syntax checks:**
- app.py: PASS
- src/inference/adapter.py: PASS
- src/inference/model_registry.py: PASS
- src/prompting/llm_prompt_builder.py: PASS

**CLI test command:** `python -m src.inference.adapter --model-id dermoscopic_cancer_risk_bcn_mnh_v1 --image <img> --top-k 4`
**Test image:** data/mel_nevus_histo/images/ISIC_0000002.jpg
**Output:**
1. Benign nevus — 51.89%
2. Melanoma — 47.88%
3. Other non-cancer / indeterminate lesion — 0.18%
4. Non-melanoma skin cancer — 0.05%

**Exit code:** 0
**Runtime:** ~3.8s (2.7s user CPU)

## Key Metrics (from D4.6 #142)
- Melanoma recall: 0.6136 (61.36%)
- Melanoma FNR: 0.3864 (38.64%)
- Macro-F1: 0.6552
- Test set: frozen BCN20000 test set (hash: a67861586e00812aadf46f2bdb4bc01b), 2659 examples

## Safety Note
Educational prototype only. Not for clinical diagnosis, treatment, or patient decisions.
