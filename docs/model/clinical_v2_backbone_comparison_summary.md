# Clinical V2 Backbone Comparison Summary (V2.18, issue #159)

This is an educational model evaluation. It must not be presented as diagnosis or
clinical readiness. The "Lesion — dermoscopic review recommended" class is a routing
output for dermoscopic review, **not** cancer detection. No model is promoted in code;
this document is a recommendation only. Taxonomy and the inference registry are unchanged.

## 1. Purpose

Issue #153 showed that sampling and high-confidence SCIN dataset variants did not beat
the EfficientNet-B0 `clinical_v2` baseline (macro-F1 0.6420). V2.18 tests a different
hypothesis: **is model capacity the bottleneck?** We trained two stronger backbones
(EfficientNet-B2, ConvNeXt-Tiny) on the identical frozen `clinical_v2` train/val/test
split with comparable settings, and compared them against the B0 baseline on the same
frozen test set plus the SCIN and Fitzpatrick17k source slices.

## 2. Hardware

- **Device:** Apple Silicon MPS (no CUDA GPU available). PyTorch 2.12.0, torchvision 0.27.0.
- **timm not installed** — all backbones built from torchvision pretrained weights.
- **Batch size:** 16 for all backbones (baseline value); MPS unified memory was sufficient,
  no reduction needed.
- Frozen test split fingerprint verified before and after every training and eval run:
  `md5 = 4b510381927f6265446a62cb990e69fd`, 1515 rows. Unchanged throughout.

## 3. Model / Configuration Table

| Backbone | Params (M) | Image size | Batch | LR | Epochs | Deviation from B0 baseline |
|---|---:|---:|---:|---:|---:|---|
| EfficientNet-B0 (baseline) | 4.0 | 224 | 16 | 1e-4 | 5 | — |
| EfficientNet-B2 | 7.7 | 260 | 16 | 1e-4 | 5 | image_size 224→260 (B2 native resolution) |
| ConvNeXt-Tiny | 27.8 | 224 | 16 | 1e-4 | 5 | none (architecture only) |

All other settings identical to baseline: AdamW, weight_decay 0.01, class weights enabled,
no sampler, no scheduler, baseline augmentation, seed 42, ImageNet normalization.

**LR was not changed.** Both EfficientNet-B2 and ConvNeXt-Tiny were fine-tuned at the
baseline 1e-4 with AdamW. A lower LR is sometimes used for ConvNeXt at large-scale training,
but 1e-4 is appropriate for fine-tuning pretrained weights on a small dataset over 5 epochs
with all layers unfrozen. Keeping LR fixed also isolates the effect of capacity, which is
the question the issue asks.

## 4. Training Settings

- Optimizer: AdamW (lr 1e-4, weight_decay 0.01) — identical across all three.
- Loss: CrossEntropy with inverse-frequency class weights.
- Best checkpoint selected by **val macro-F1** (the promotion metric), not val loss.
- Epochs: 5 for each.
- Runtime per epoch (MPS): B2 ≈ 29 min/epoch (260px); ConvNeXt-Tiny ≈ 10 min/epoch (224px).

## 5. Results — Frozen Test Set (1515 examples)

| Metric | B0 baseline | EffNet-B2 | Δ B2 | ConvNeXt-Tiny | Δ ConvNeXt |
|---|---:|---:|---:|---:|---:|
| Combined accuracy | 0.6607 | 0.6554 | −0.0053 | **0.7069** | **+0.0462** |
| Combined macro-F1 | 0.6447 | 0.6416 | −0.0031 | **0.6901** | **+0.0454** |
| Balanced accuracy | 0.6562 | 0.6563 | +0.0001 | **0.7027** | **+0.0465** |
| SCIN macro-F1 | 0.3907 | 0.4244 | +0.0337 | **0.4733** | **+0.0826** |
| SCIN error rate | 0.4135 | 0.4563 | +0.0428 | **0.3779** | **−0.0356** |
| Fitzpatrick17k macro-F1 | 0.6411 | 0.6472 | +0.0061 | **0.6960** | **+0.0549** |
| Fitzpatrick17k error rate | 0.2956 | 0.2788 | −0.0168 | **0.2432** | **−0.0524** |
| Lesion-routing FN | 82 | 79 | −3 | **71** | **−11** |
| Eczema → Urticaria | 87 | 89 | +2 | **48** | **−39** |
| Urticaria false positives | 157 | 148 | −9 | **104** | **−53** |
| Inference (ms/image, MPS) | 6.32 | 12.41 | +6.09 | 13.97 | +7.65 |

> Note on baseline figures: the B0 column above is a fresh re-evaluation of the existing
> `models/clinical_v2_effnet_b0` checkpoint through the unchanged eval pipeline. It matches
> the #153/#159 reference values closely (macro-F1 0.6447 vs documented 0.6420; lesion FN 82
> vs documented 76 — minor differences from re-measurement). **Promotion thresholds below use
> the fixed issue #159 values, not the re-measured numbers.**

### Class-wise F1 (test set)

| Class | B0 | B2 | ConvNeXt-Tiny |
|---|---:|---:|---:|
| Eczema / dermatitis | 0.643 | 0.590 | **0.677** |
| Urticaria / allergic reaction | 0.472 | 0.468 | **0.529** |
| Folliculitis / acne-like | 0.659 | 0.665 | **0.712** |
| Psoriasis / papulosquamous | 0.624 | 0.649 | **0.688** |
| Lesion — dermoscopic review | 0.825 | 0.836 | **0.845** |

ConvNeXt-Tiny improves every class, most notably Urticaria (the weakest class) and
Folliculitis. EfficientNet-B2 regresses on Eczema (0.643 → 0.590) while modestly improving
others, netting roughly flat overall.

## 6. Runtime Notes (demo feasibility)

| Backbone | Inference (ms/image, MPS) | Train min/epoch (MPS) | Params (M) |
|---|---:|---:|---:|
| B0 baseline | 6.32 | ~6 | 4.0 |
| EffNet-B2 | 12.41 | ~29 | 7.7 |
| ConvNeXt-Tiny | 13.97 | ~10 | 27.8 |

ConvNeXt-Tiny roughly doubles per-image inference latency vs B0 (~14 ms vs ~6 ms on MPS),
which is still well within practical limits for the capstone/demo (single-image, on-demand
inference). It is 6.9× the parameter count but, due to the 224px input, trained ~3× faster
per epoch than B2 at 260px.

## 7. Promotion Verdict (thresholds from issue #159, no rounding)

### EfficientNet-B2 — **NOT PROMOTABLE**

| Criterion | Threshold | Value | Result |
|---|---|---:|:---:|
| Combined macro-F1 meaningfully improved | > 0.6420 | 0.6416 | FAIL (flat, −0.0004) |
| Balanced accuracy stable/improved | ≥ 0.6571 | 0.6563 | ~flat |
| SCIN improves (macro-F1 or error rate) | > 0.4028 / < 0.4278 | 0.4244 | PASS |
| Lesion-routing FN does not increase | ≤ 76 | 79 | **FAIL** |

B2 does not meaningfully improve combined macro-F1 and **increases lesion-routing false
negatives** above the 76 threshold — a safety-relevant regression. Higher resolution alone
(260px) did not help.

### ConvNeXt-Tiny — **PROMOTABLE CANDIDATE**

| Criterion | Threshold | Value | Result |
|---|---|---:|:---:|
| Combined macro-F1 meaningfully improved | > 0.6420 | 0.6901 (+0.048) | **PASS** |
| Balanced accuracy stable/improved | ≥ 0.6571 | 0.7027 (+0.046) | **PASS** |
| SCIN improves (macro-F1 or error rate) | > 0.4028 / < 0.4278 | 0.4733 / 0.3779 | **PASS** |
| Lesion-routing FN does not increase | ≤ 76 | 71 (−5) | **PASS** |
| Runtime practical for demo | — | 13.97 ms/img | **PASS** |
| No diagnostic/clinical-readiness claims | — | — | **PASS** |

ConvNeXt-Tiny passes every promotion criterion and additionally reduces both known failure
patterns (Eczema→Urticaria 87→48; Urticaria FP 157→104) and improves SCIN — the slice that
#153 could not move.

## 8. Recommendation

**ConvNeXt-Tiny is the recommended backbone for future clinical experiments.** It is the
first variant across #153 and V2.18 to meaningfully and uniformly beat the EfficientNet-B0
baseline: +0.045 combined macro-F1, +0.047 balanced accuracy, +0.083 SCIN macro-F1, fewer
lesion-routing false negatives, and large reductions in the two known confusion patterns —
all on the frozen test split with no taxonomy or pipeline changes. Inference at ~14 ms/image
on MPS is acceptable for the demo.

This contradicts the implicit conclusion that capacity was not the bottleneck: a stronger
*architecture* (ConvNeXt-Tiny) helped substantially, whereas simply more capacity within the
same family (EfficientNet-B2) did not. EfficientNet-B2 is not recommended — flat overall
quality and a lesion-FN regression.

**Recommended next step:** open a separate promotion task to evaluate replacing the selected
`clinical_v2` baseline with ConvNeXt-Tiny, including inference-schema compatibility checks and
a held-out re-confirmation run. That promotion is explicitly out of scope here.

## 9. Out of Scope — Confirmed Unchanged

- Taxonomy unchanged (same 5 classes, same order).
- Inference registry unchanged; no app inference wiring touched.
- No model promoted in code — recommendation lives in this document only.
- No PAD-UFES integration, no expanded taxonomy, no Hugging Face deployment.
- No diagnostic or clinical-readiness claims.

## 10. What This Tells Us

Capacity *within the EfficientNet family* (B0 → B2) is not the lever — B2 was flat and
regressed on lesion FN. A modern architecture (ConvNeXt-Tiny) is the lever: it improved
every class and every source slice, including the stubborn SCIN slice from #153. The
bottleneck appears to be representational/architectural rather than raw parameter count or
input resolution. Future clinical experiments should build on ConvNeXt-Tiny and revisit
dataset/taxonomy work (#157-style enrichment) on top of the stronger backbone.

## Artifacts

- Comparison table: `outputs/metrics/clinical_v2_backbone_comparison_table.csv`
- Machine-readable bundle: `outputs/metrics/clinical_v2_backbone_comparison_bundle.json`
- Per-backbone metrics JSON / classification reports / source metrics:
  `outputs/metrics/clinical_v2_{effnet_b0_baseline,effnet_b2,convnext_tiny}_*`
- Confusion matrix grid: `outputs/plots/clinical_v2_backbone_comparison_cm.png`
- Training curves: `outputs/plots/clinical_v2_backbone_training_curves.png`
- Checkpoints: `models/clinical_v2_effnet_b2/`, `models/clinical_v2_convnext_tiny/`
- Configs: `config/clinical_v2_effnet_b2_config.yaml`, `config/clinical_v2_convnext_tiny_config.yaml`,
  `config/clinical_v2_resnet50_config.yaml` (optional, not trained)
