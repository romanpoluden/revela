# Clinical V2 Evaluation Summary

This evaluation is for the clinical-image EfficientNet-B0 baseline. It is educational model evaluation only and must not be presented as diagnosis.

The lesion class is a routing class for dermoscopic review, not cancer detection.

## Combined Test Metrics

- Test examples: 1515
- Test accuracy: 0.7069
- Macro-F1: 0.6901
- Balanced accuracy: 0.7027

## Lesion Routing Class

- Precision: 0.8846
- Recall: 0.8081
- F1: 0.8446
- Support: 370

## Source-Specific Metrics

| Source | Support | Accuracy | Macro-F1 | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: |
| combined | 1515 | 0.7069 | 0.6901 | 0.7027 |
| google_scin | 561 | 0.6221 | 0.4733 | 0.4904 |
| fitzpatrick17k | 954 | 0.7568 | 0.6960 | 0.7146 |

## Saved Artifacts

- Metrics JSON: `outputs/metrics/clinical_v2_convnext_tiny_test_metrics.json`
- Classification report CSV: `outputs/metrics/clinical_v2_convnext_tiny_classification_report.csv`
- Source metrics CSV: `outputs/metrics/clinical_v2_convnext_tiny_source_metrics.csv`
- Confusion matrix PNG: `outputs/plots/clinical_v2_convnext_tiny_confusion_matrix.png`
