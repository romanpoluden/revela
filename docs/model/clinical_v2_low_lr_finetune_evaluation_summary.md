# Clinical V2 Evaluation Summary

This evaluation is for the clinical-image EfficientNet-B0 baseline. It is educational model evaluation only and must not be presented as diagnosis.

The lesion class is a routing class for dermoscopic review, not cancer detection.

## Combined Test Metrics

- Test examples: 1515
- Test accuracy: 0.6449
- Macro-F1: 0.6306
- Balanced accuracy: 0.6463

## Lesion Routing Class

- Precision: 0.8397
- Recall: 0.7784
- F1: 0.8079
- Support: 370

## Source-Specific Metrics

| Source | Support | Accuracy | Macro-F1 | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: |
| combined | 1515 | 0.6449 | 0.6306 | 0.6463 |
| google_scin | 561 | 0.5597 | 0.3826 | 0.3972 |
| fitzpatrick17k | 954 | 0.6950 | 0.6300 | 0.6507 |

## Saved Artifacts

- Metrics JSON: `outputs/metrics/clinical_v2_low_lr_finetune_test_metrics.json`
- Classification report CSV: `outputs/metrics/clinical_v2_low_lr_finetune_classification_report.csv`
- Source metrics CSV: `outputs/metrics/clinical_v2_low_lr_finetune_source_metrics.csv`
- Confusion matrix PNG: `outputs/plots/clinical_v2_low_lr_finetune_confusion_matrix.png`
