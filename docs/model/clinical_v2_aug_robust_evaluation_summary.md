# Clinical V2 Evaluation Summary

This evaluation is for the clinical-image EfficientNet-B0 baseline. It is educational model evaluation only and must not be presented as diagnosis.

The lesion class is a routing class for dermoscopic review, not cancer detection.

## Combined Test Metrics

- Test examples: 1515
- Test accuracy: 0.6700
- Macro-F1: 0.6556
- Balanced accuracy: 0.6726

## Lesion Routing Class

- Precision: 0.8543
- Recall: 0.8243
- F1: 0.8391
- Support: 370

## Source-Specific Metrics

| Source | Support | Accuracy | Macro-F1 | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: |
| combined | 1515 | 0.6700 | 0.6556 | 0.6726 |
| google_scin | 561 | 0.5651 | 0.3897 | 0.4017 |
| fitzpatrick17k | 954 | 0.7317 | 0.6583 | 0.6751 |

## Saved Artifacts

- Metrics JSON: `outputs/metrics/clinical_v2_aug_robust_test_metrics.json`
- Classification report CSV: `outputs/metrics/clinical_v2_aug_robust_classification_report.csv`
- Source metrics CSV: `outputs/metrics/clinical_v2_aug_robust_source_metrics.csv`
- Confusion matrix PNG: `outputs/plots/clinical_v2_aug_robust_confusion_matrix.png`
