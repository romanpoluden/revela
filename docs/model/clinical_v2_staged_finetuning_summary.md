# V2.19 — Clinical V2 Fine-Tuning Schedule Comparison

**Issue:** [#160](https://github.com/romanpoluden/revela/issues/160)  
**Branch:** `clinical_v2_16_17_18`  
**Date:** 2026-05-24  
**Author:** Rehma Aziz  
**Scope:** Test two alternative LR schedules (staged fine-tuning, lower-LR cosine decay) against the standard full-model EfficientNet-B0 training on the frozen `clinical_v2` test split. Same backbone, same split, same augmentation, same seed — only the training schedule differs.

---

## Outcome Summary

**Neither schedule variant improves over the standard baseline. Standard full-model training at lr=1e-4 remains the best schedule for B0 on clinical_v2.**

Both staged fine-tuning (0.6192 test macro-F1) and low-LR cosine (0.6306) underperform the same-run baseline-regen (0.6527). Lesion-routing recall drops in both variants (staged: 0.74, low-LR: 0.78) vs the baseline (0.81). Low-LR achieved the highest val macro-F1 of all three (0.6698) but failed to generalise — the val/test gap reveals overfitting to the validation distribution. The schedule axis is not the lever that explains V2.18's ConvNeXt-Tiny improvement; that was architecture, not schedule.

This is an educational model evaluation. The lesion class is a routing output for dermoscopic review, **not** cancer detection. No diagnostic or clinical-readiness claims are made.

---

## Variants

All variants use: EfficientNet-B0, ImageNet pretrained, 224×224, AdamW (weight_decay=0.01), inverse-frequency class weights, no sampler, seed 42, `clinical_v2` frozen split.

| Variant | Phase 1 | Phase 2 | Config |
|---|---|---|---|
| Baseline-regen | Full model, lr=1e-4, 5 ep, constant | — | `clinical_v2_config.yaml` |
| Staged fine-tuning | Head only, lr=1e-3, 2 ep (frozen backbone) | Full model, lr=5e-5, 5 ep, cosine | `clinical_v2_staged_finetune_config.yaml` |
| Low-LR cosine | Full model, lr=5e-5, 8 ep, cosine | — | `clinical_v2_low_lr_finetune_config.yaml` |

---

## Training Results

| Variant | Best epoch | Best val macro-F1 | Best val balanced-acc |
|---|---:|---:|---:|
| Baseline-regen | 5 | 0.6682 | 0.6813 |
| Staged fine-tuning | 7 (phase: finetune) | 0.6497 | 0.6676 |
| Low-LR cosine | 7 | 0.6698 | 0.6904 |

Low-LR achieves the highest validation macro-F1 (0.6698) but this does not generalise to the test set — it has the worst val/test gap of the three variants.

---

## Test Set Results (n=1,515, hash=`4b510381927f6265446a62cb990e69fd`)

| Variant | Accuracy | Macro-F1 | Balanced acc | Lesion recall | Lesion FN |
|---|---:|---:|---:|---:|---:|
| Baseline ref (issue #153) | — | 0.6420 | 0.6571 | — | 76 |
| **Baseline-regen** | **0.6733** | **0.6527** | **0.6612** | **0.8108** | **70** |
| Staged fine-tuning | 0.6330 | 0.6192 | 0.6352 | 0.7432 | 95 |
| Low-LR cosine | 0.6449 | 0.6306 | 0.6463 | 0.7784 | 82 |

The baseline-regen also exceeds the original #153 reference (0.6527 vs 0.6420), confirming run validity. Both schedule variants are below the original baseline reference, not just below the regen.

---

## Source-Specific Results

| Variant | SCIN (n=561) macro-F1 | SCIN balanced-acc | Fitzpatrick (n=954) macro-F1 | Fitzpatrick balanced-acc |
|---|---:|---:|---:|---:|
| Baseline-regen | 0.4267 | 0.4309 | 0.6644 | 0.6817 |
| Staged fine-tuning | 0.3919 | 0.4065 | 0.5811 | 0.6054 |
| Low-LR cosine | 0.3826 | 0.3972 | 0.6300 | 0.6507 |

Both schedule variants regress on both source slices relative to the baseline-regen.

---

## Class-Wise F1

| Class | Baseline-regen | Staged | Low-LR |
|---|---:|---:|---:|
| Eczema / dermatitis | 0.6518 | 0.6135 | 0.6064 |
| Urticaria / allergic reaction | 0.4644 | 0.4686 | 0.4652 |
| Folliculitis / acne-like | 0.6587 | 0.6409 | 0.6550 |
| Psoriasis / papulosquamous | 0.6563 | 0.5806 | 0.6186 |
| Lesion — dermoscopic review recommended | 0.8322 | 0.7925 | 0.8079 |

The only class where either variant is competitive is Urticaria — but the difference is within noise (0.46–0.47 across all three).

---

## Verdict

**Neither schedule variant is adopted.** Standard full-model training (lr=1e-4, 5 epochs, constant LR) outperforms both alternatives on every metric on the frozen test set.

Key observations:
- **Staged fine-tuning** — the head-only warm-up gives a weaker starting point for the backbone unfreezing phase. Lesion-routing recall collapses to 0.74 (95 FN vs 70 for baseline), which would fail the issue #153 promotion threshold of ≤76 FN.
- **Low-LR cosine** — achieves the best val score but overfits to the val distribution. Generalises poorly to the test set across all source slices.
- **Schedule is not the lever.** The ConvNeXt-Tiny improvement in V2.18 was architectural capacity, not schedule tuning. Future B0 experiments should focus on augmentation or data strategy, not LR schedule variants.

---

## Artifacts

| File | Description |
|---|---|
| `docs/model/clinical_v2_baseline_regen_evaluation_summary.md` | Baseline-regen eval (auto-generated) |
| `docs/model/clinical_v2_staged_finetune_evaluation_summary.md` | Staged fine-tune eval (auto-generated) |
| `docs/model/clinical_v2_low_lr_finetune_evaluation_summary.md` | Low-LR fine-tune eval (auto-generated) |
| `outputs/metrics/clinical_v2_baseline_regen_test_metrics.json` | Baseline-regen metrics JSON |
| `outputs/metrics/clinical_v2_staged_finetune_test_metrics.json` | Staged fine-tune metrics JSON |
| `outputs/metrics/clinical_v2_low_lr_finetune_test_metrics.json` | Low-LR fine-tune metrics JSON |
| `outputs/metrics/clinical_v2_finetuning_comparison_table.csv` | Side-by-side comparison CSV |
| `revela/Rehma_Revela/Notebook/17_compare_clinical_v2_finetuning.ipynb` | Results notebook |
| `models/clinical_v2_effnet_b0/best_model.pth` | Baseline-regen checkpoint (epoch 5) |
| `models/clinical_v2_staged_finetune_effnet_b0/best_model.pth` | Staged fine-tune checkpoint (epoch 7) |
| `models/clinical_v2_low_lr_finetune_effnet_b0/best_model.pth` | Low-LR fine-tune checkpoint (epoch 7) |
| `logs/v2_19_run.sh` | Orchestration script (train + eval, all three runs) |
| `logs/v2_19_run.log` | Full training + eval log |
