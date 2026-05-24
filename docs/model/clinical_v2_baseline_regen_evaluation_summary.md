# Clinical V2 Evaluation Summary

This evaluation is for the clinical-image EfficientNet-B0 baseline. It is educational model evaluation only and must not be presented as diagnosis.

The lesion class is a routing class for dermoscopic review, not cancer detection.

## Combined Test Metrics

- Test examples: 1515
- Test accuracy: 0.6733
- Macro-F1: 0.6527
- Balanced accuracy: 0.6612

## Lesion Routing Class

- Precision: 0.8547
- Recall: 0.8108
- F1: 0.8322
- Support: 370

## Source-Specific Metrics

| Source | Support | Accuracy | Macro-F1 | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: |
| combined | 1515 | 0.6733 | 0.6527 | 0.6612 |
| google_scin | 561 | 0.5829 | 0.4267 | 0.4309 |
| fitzpatrick17k | 954 | 0.7264 | 0.6644 | 0.6817 |

## Saved Artifacts

- Metrics JSON: `outputs/metrics/clinical_v2_baseline_regen_test_metrics.json`
- Classification report CSV: `outputs/metrics/clinical_v2_baseline_regen_classification_report.csv`
- Source metrics CSV: `outputs/metrics/clinical_v2_baseline_regen_source_metrics.csv`
- Confusion matrix PNG: `outputs/plots/clinical_v2_baseline_regen_confusion_matrix.png`
