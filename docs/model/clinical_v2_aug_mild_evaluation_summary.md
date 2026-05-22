# Clinical V2 Evaluation Summary

This evaluation is for the clinical-image EfficientNet-B0 baseline. It is educational model evaluation only and must not be presented as diagnosis.

The lesion class is a routing class for dermoscopic review, not cancer detection.

## Combined Test Metrics

- Test examples: 1515
- Test accuracy: 0.6548
- Macro-F1: 0.6379
- Balanced accuracy: 0.6552

## Lesion Routing Class

- Precision: 0.8397
- Recall: 0.8351
- F1: 0.8374
- Support: 370

## Source-Specific Metrics

| Source | Support | Accuracy | Macro-F1 | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: |
| combined | 1515 | 0.6548 | 0.6379 | 0.6552 |
| google_scin | 561 | 0.5508 | 0.3922 | 0.4151 |
| fitzpatrick17k | 954 | 0.7159 | 0.6247 | 0.6295 |

## Saved Artifacts

- Metrics JSON: `outputs/metrics/clinical_v2_aug_mild_test_metrics.json`
- Classification report CSV: `outputs/metrics/clinical_v2_aug_mild_classification_report.csv`
- Source metrics CSV: `outputs/metrics/clinical_v2_aug_mild_source_metrics.csv`
- Confusion matrix PNG: `outputs/plots/clinical_v2_aug_mild_confusion_matrix.png`
