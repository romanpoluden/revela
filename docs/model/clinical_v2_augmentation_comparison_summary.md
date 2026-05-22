# Clinical V2 Augmentation Comparison Summary

> Non-diagnostic model evaluation. The lesion class is a routing class for dermoscopic review, not cancer detection.

## Purpose

Issue #153 showed sampler and high-confidence SCIN variants were not promotable. Issue #158 evaluates whether clinical-photo augmentation can improve generalization. No taxonomy change, no inference wiring change, no model promotion in code.

## Baseline Augmentation (verbatim from src/data/transforms.py)

```
RandomResizedCrop(224, scale=(0.9, 1.0), ratio=(0.95, 1.05))
RandomHorizontalFlip(p=0.5)
RandomVerticalFlip(p=0.5)
ColorJitter(brightness=0.1, contrast=0.1, saturation=0.05, hue=0.02)
ToTensor()
Normalize(ImageNet mean/std)
```

## Candidate Strategies

### Mild clinical (`mild_clinical`)

```
RandomResizedCrop(224, scale=(0.85, 1.0), ratio=(0.9, 1.1))
RandomHorizontalFlip(p=0.5)
RandomRotation(degrees=10)
ColorJitter(brightness=0.15, contrast=0.15, saturation=0.05, hue=0.0)
ToTensor()
Normalize(ImageNet mean/std)
```

Key changes vs baseline: wider crop, no vertical flip (body-site anatomy is directional), mild rotation, hue=0.0 (preserves skin color).

### Robust clinical (`robust_clinical`)

```
RandomResizedCrop(224, scale=(0.80, 1.0), ratio=(0.9, 1.1))
RandomHorizontalFlip(p=0.5)
RandomRotation(degrees=15)
ColorJitter(brightness=0.2, contrast=0.2, saturation=0.05, hue=0.0)
GaussianBlur(kernel_size=3, sigma=(0.1, 0.5))
RandomGrayscale(p=0.02)
ToTensor()
Normalize(ImageNet mean/std)
```

Key changes vs mild: wider crop range, more rotation, mild blur, very rare grayscale. hue=0.0 preserved.

**Why hue=0.0 in both variants:** Skin color carries diagnostic signal (erythema, pigment). Hue jitter in the baseline (hue=0.02) is very mild but removing it in clinical-photo variants is conservative and appropriate.

## Visual Sanity Check

Augmentation grid saved to `outputs/plots/augmentation_visual_check.png`. Three real clinical images × three strategies × three samples each. Skin tones were preserved across all strategies — no aggressive color shifts or distorted anatomy observed. Training proceeded.

## Results

| Metric | Baseline | Mild aug (Δ) | Robust aug (Δ) |
|---|---:|---:|---:|
| Combined macro-F1 | 0.6447 | 0.6379 (-0.0069) | 0.6556 (+0.0108) |
| Balanced accuracy | 0.6562 | 0.6552 (-0.0009) | 0.6726 (+0.0164) |
| SCIN macro-F1 | 0.3907 | 0.3922 (+0.0014) | 0.3897 (-0.0010) |
| Fitzpatrick macro-F1 | 0.6411 | 0.6247 (-0.0163) | 0.6583 (+0.0173) |
| Lesion routing FN | 82 | 61 (-21) | 65 (-17) |
| Eczema→Urticaria | 87 | 94 (+7) | 91 (+4) |
| Urticaria FP | 157 | 157 (+0) | 176 (+19) |

## Class-wise F1

| Class | Baseline | Mild aug | Robust aug |
|---|---:|---:|---:|
| Eczema / dermatitis | 0.6433 | 0.5923 | 0.6330 |
| Urticaria / allergic reaction | 0.4723 | 0.4574 | 0.4762 |
| Folliculitis / acne-like | 0.6586 | 0.6653 | 0.6876 |
| Psoriasis / papulosquamous | 0.6243 | 0.6369 | 0.6419 |
| Lesion — dermoscopic review recommended | 0.8252 | 0.8374 | 0.8391 |

## Promotion Verdict

Promotion criteria (from issue #158): combined macro-F1 ≥ 0.6420, balanced accuracy ≥ 0.6571, SCIN macro-F1 ≥ 0.4028, Fitzpatrick macro-F1 ≥ 0.6366, lesion routing FN ≤ 76.

**Mild aug:** NOT PROMOTABLE
Failed criteria:
- combined_macro_f1=0.6379 vs threshold=0.642
- balanced_accuracy=0.6552 vs threshold=0.6571
- scin_macro_f1=0.3922 vs threshold=0.4028
- fitzpatrick_macro_f1=0.6247 vs threshold=0.6366

**Robust aug:** NOT PROMOTABLE
Failed criteria:
- scin_macro_f1=0.3897 vs threshold=0.4028

## Recommendation

Neither augmentation strategy meets all promotion criteria against the current baseline. Augmentation alone is insufficient to close the SCIN generalization gap.

Interpretation: The SCIN vs Fitzpatrick17k performance gap is likely driven by dataset distribution differences (image style, label quality, demographic coverage) rather than augmentation choices. Better augmentation cannot compensate for domain shift at this scale.

Recommended next steps:
- Defer augmentation improvement until the expanded 8-class taxonomy (PAD-UFES integration) provides more lesion coverage.
- If SCIN improvement is the priority, revisit source-aware sampling with the enriched dataset.
- Keep the existing baseline (`models/clinical_v2_effnet_b0/`) in production.

## Out of Scope

Confirmed out of scope for this task:
- Expanded 8-class taxonomy
- PAD-UFES integration
- Model registry or app inference changes
- Clinical-readiness or diagnostic claims

## Artifacts

- Comparison table: `outputs/metrics/clinical_v2_augmentation_comparison_table.csv`
- Mild model: `models/clinical_v2_aug_mild_effnet_b0/best_model.pth`
- Robust model: `models/clinical_v2_aug_robust_effnet_b0/best_model.pth`
- Confusion matrices: `outputs/plots/clinical_v2_aug_mild_confusion_matrix.png`, `outputs/plots/clinical_v2_aug_robust_confusion_matrix.png`
- Visual check: `outputs/plots/augmentation_visual_check.png`
- Test set hash: `4b510381927f6265446a62cb990e69fd` (verified unchanged throughout)
