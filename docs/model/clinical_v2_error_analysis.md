# Clinical V2 Error Analysis

This summarizes test-set prediction errors for the Clinical V2 EfficientNet-B0 classifier with lesion-routing output. It is a non-diagnostic model analysis for understanding model behavior.

## Artifacts

- Per-image predictions: `outputs/error_analysis/clinical_v2_test_predictions.csv`
- Errors by raw label: `outputs/error_analysis/clinical_v2_errors_by_raw_label.csv`
- Errors by source: `outputs/error_analysis/clinical_v2_errors_by_source.csv`
- Confusion pairs: `outputs/error_analysis/clinical_v2_confusion_pairs.csv`

## Overall Errors

- Test examples: 1515
- Error count: 522
- Error rate: 0.3446

## Errors by Source

| Source | Total examples | Error count | Error rate |
| --- | ---: | ---: | ---: |
| fitzpatrick17k | 954 | 282 | 0.2956 |
| google_scin | 561 | 240 | 0.4278 |

## Errors by True Class

| True class | Total examples | Error count | Error rate |
| --- | ---: | ---: | ---: |
| Eczema / dermatitis | 443 | 195 | 0.4402 |
| Urticaria / allergic reaction | 160 | 57 | 0.3563 |
| Folliculitis / acne-like | 236 | 81 | 0.3432 |
| Psoriasis / papulosquamous | 306 | 113 | 0.3693 |
| Lesion — dermoscopic review recommended | 370 | 76 | 0.2054 |

## Top Confusion Pairs

| True class | Predicted class | Count | Share of all errors |
| --- | --- | ---: | ---: |
| Eczema / dermatitis | Urticaria / allergic reaction | 91 | 0.1743 |
| Eczema / dermatitis | Psoriasis / papulosquamous | 51 | 0.0977 |
| Psoriasis / papulosquamous | Eczema / dermatitis | 39 | 0.0747 |
| Psoriasis / papulosquamous | Urticaria / allergic reaction | 39 | 0.0747 |
| Folliculitis / acne-like | Eczema / dermatitis | 35 | 0.0670 |
| Lesion — dermoscopic review recommended | Psoriasis / papulosquamous | 35 | 0.0670 |
| Eczema / dermatitis | Folliculitis / acne-like | 34 | 0.0651 |
| Urticaria / allergic reaction | Eczema / dermatitis | 25 | 0.0479 |
| Folliculitis / acne-like | Urticaria / allergic reaction | 22 | 0.0421 |
| Psoriasis / papulosquamous | Folliculitis / acne-like | 20 | 0.0383 |

## Notes

- Urticaria false positives: 160. Most common true classes: Eczema / dermatitis (91), Psoriasis / papulosquamous (39), Folliculitis / acne-like (22).
- Eczema false negatives: 195. Most common predicted classes: Urticaria / allergic reaction (91), Psoriasis / papulosquamous (51), Folliculitis / acne-like (34).
- SCIN-specific errors: 240. Most common predicted classes in those errors: Urticaria / allergic reaction (97), Eczema / dermatitis (74), Folliculitis / acne-like (37).
- Lesion-routing false negatives: 76. Most common predicted classes: Psoriasis / papulosquamous (35), Folliculitis / acne-like (18), Eczema / dermatitis (15).

## Limitation

This is educational model analysis only. It is not diagnosis, clinical guidance, or a claim of clinical readiness.
