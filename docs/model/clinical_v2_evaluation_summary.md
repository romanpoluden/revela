# Clinical V2 Evaluation Summary

This evaluation is for the clinical-image EfficientNet-B0 baseline. It is educational model evaluation only and must not be presented as diagnosis.

The lesion class is a routing class for dermoscopic review, not cancer detection.

## Combined Test Metrics

- Test examples: 1515
- Test accuracy: 0.6554
- Macro-F1: 0.6420
- Balanced accuracy: 0.6571

## Lesion Routing Class

- Precision: 0.8647
- Recall: 0.7946
- F1: 0.8282
- Support: 370

## Source-Specific Metrics

| Source | Support | Accuracy | Macro-F1 | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: |
| combined | 1515 | 0.6554 | 0.6420 | 0.6571 |
| google_scin | 561 | 0.5722 | 0.4028 | 0.4172 |
| fitzpatrick17k | 954 | 0.7044 | 0.6366 | 0.6526 |

## Saved Artifacts

- Metrics JSON: `outputs/metrics/clinical_v2_test_metrics.json`
- Classification report CSV: `outputs/metrics/clinical_v2_classification_report.csv`
- Source metrics CSV: `outputs/metrics/clinical_v2_source_metrics.csv`
- Confusion matrix PNG: `outputs/plots/clinical_v2_confusion_matrix.png`
