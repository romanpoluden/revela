# Clinical V2 Evaluation Summary

This evaluation is for the clinical-image EfficientNet-B0 baseline. It is educational model evaluation only and must not be presented as diagnosis.

The lesion class is a routing class for dermoscopic review, not cancer detection.

## Combined Test Metrics

- Test examples: 1515
- Test accuracy: 0.6607
- Macro-F1: 0.6447
- Balanced accuracy: 0.6562

## Lesion Routing Class

- Precision: 0.8780
- Recall: 0.7784
- F1: 0.8252
- Support: 370

## Source-Specific Metrics

| Source | Support | Accuracy | Macro-F1 | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: |
| combined | 1515 | 0.6607 | 0.6447 | 0.6562 |
| google_scin | 561 | 0.5865 | 0.3907 | 0.3970 |
| fitzpatrick17k | 954 | 0.7044 | 0.6411 | 0.6689 |

## Saved Artifacts

- Metrics JSON: `outputs/metrics/clinical_v2_effnet_b0_baseline_test_metrics.json`
- Classification report CSV: `outputs/metrics/clinical_v2_effnet_b0_baseline_classification_report.csv`
- Source metrics CSV: `outputs/metrics/clinical_v2_effnet_b0_baseline_source_metrics.csv`
- Confusion matrix PNG: `outputs/plots/clinical_v2_effnet_b0_baseline_confusion_matrix.png`
