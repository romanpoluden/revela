# Artifact Manifest — clinical_skin_condition_v1

**Model ID:** clinical_skin_condition_v1
**Input type:** Clinical / macroscopic skin photograph
**Architecture:** EfficientNet-B0
**Taxonomy:** 5-class Clinical V2 educational taxonomy
**Classes:**
- 0: Eczema / dermatitis
- 1: Urticaria / allergic reaction
- 2: Folliculitis / acne-like
- 3: Psoriasis / papulosquamous
- 4: Lesion — dermoscopic review recommended

**Artifact owner note:** HF artifact matches Rehma's local checkpoint (eba9a581...). Roman's local checkpoint (5a1bdc05...) is an earlier version. Source of truth: Rehma's machine, confirmed by HF hash comparison.
**Source machine:** Rehma's machine
**Source branch:** v2.22-metrics-to-main
**Source commit SHA:** c0181c4322fd72ce7d55a89705a3f3e46baceed1
**Roman's machine commit SHA:** 8b47a49 (branch: main)
**Created date:** May 24 2026 (file timestamp: models/clinical_v2_effnet_b0/best_model.pth)

## Required Inference Files

| File | Path | Size | SHA256 |
|---|---|---|---|
| Checkpoint | models/clinical_v2_effnet_b0/best_model.pth | 16M | eba9a581505c60cee98152c790c4113a1549c691248d518cc5d1e7097feb20bc |
| class_to_idx | models/clinical_v2_effnet_b0/class_to_idx.json | 189B | 54cfa7c59ff278e52b86b52b8be281300ea14141093e26992ab88d9efb5d55f2 |
| Config | config/clinical_v2_config.yaml | 1.2K | ae7ddcf3f8739403fdd65475ba1e92dbdd920dc024f947a2d76ea8574d7531e4 |

## Inference Verification

**Syntax checks:**
- app.py: PASS
- src/inference/adapter.py: PASS
- src/inference/model_registry.py: PASS
- src/prompting/llm_prompt_builder.py: PASS

**CLI test command:** `python -m src.inference.adapter --model-id clinical_skin_condition_v1 --image <img> --top-k 3`
**Test image:** data/raw/scin/images/train_-3208362477794549016_image_1.jpg
**Output:**
1. Folliculitis / acne-like — 58.99%
2. Eczema / dermatitis — 26.55%
3. Lesion — dermoscopic review recommended — 7.40%

**Exit code:** 0
**Runtime:** ~7.8s (2.6s user CPU)

## Key Metrics
- Combined macro-F1: 0.6420
- Balanced accuracy: 0.6571
- SCIN macro-F1: 0.4028
- Lesion-routing FN: 76
- Evaluation issue: #153

## Safety Note
Educational prototype only. Not for clinical diagnosis, treatment, or patient decisions.
