# Clinical V2 Evaluation Summary

This evaluation is for the clinical-image EfficientNet-B0 baseline. It is educational model evaluation only and must not be presented as diagnosis.

The lesion class is a routing class for dermoscopic review, not cancer detection.

## Combined Test Metrics

- Test examples: 1515
- Test accuracy: 0.6330
- Macro-F1: 0.6192
- Balanced accuracy: 0.6352

## Lesion Routing Class

- Precision: 0.8488
- Recall: 0.7432
- F1: 0.7925
- Support: 370

## Source-Specific Metrics

| Source | Support | Accuracy | Macro-F1 | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: |
| combined | 1515 | 0.6330 | 0.6192 | 0.6352 |
| google_scin | 561 | 0.5900 | 0.3919 | 0.4065 |
| fitzpatrick17k | 954 | 0.6583 | 0.5811 | 0.6054 |

## Saved Artifacts

- Metrics JSON: `outputs/metrics/clinical_v2_staged_finetune_test_metrics.json`
- Classification report CSV: `outputs/metrics/clinical_v2_staged_finetune_classification_report.csv`
- Source metrics CSV: `outputs/metrics/clinical_v2_staged_finetune_source_metrics.csv`
- Confusion matrix PNG: `outputs/plots/clinical_v2_staged_finetune_confusion_matrix.png`
