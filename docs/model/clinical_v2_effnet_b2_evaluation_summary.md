# Clinical V2 Evaluation Summary

This evaluation is for the clinical-image EfficientNet-B0 baseline. It is educational model evaluation only and must not be presented as diagnosis.

The lesion class is a routing class for dermoscopic review, not cancer detection.

## Combined Test Metrics

- Test examples: 1515
- Test accuracy: 0.6554
- Macro-F1: 0.6416
- Balanced accuracy: 0.6563

## Lesion Routing Class

- Precision: 0.8926
- Recall: 0.7865
- F1: 0.8362
- Support: 370

## Source-Specific Metrics

| Source | Support | Accuracy | Macro-F1 | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: |
| combined | 1515 | 0.6554 | 0.6416 | 0.6563 |
| google_scin | 561 | 0.5437 | 0.4244 | 0.4416 |
| fitzpatrick17k | 954 | 0.7212 | 0.6472 | 0.6609 |

## Saved Artifacts

- Metrics JSON: `outputs/metrics/clinical_v2_effnet_b2_test_metrics.json`
- Classification report CSV: `outputs/metrics/clinical_v2_effnet_b2_classification_report.csv`
- Source metrics CSV: `outputs/metrics/clinical_v2_effnet_b2_source_metrics.csv`
- Confusion matrix PNG: `outputs/plots/clinical_v2_effnet_b2_confusion_matrix.png`
