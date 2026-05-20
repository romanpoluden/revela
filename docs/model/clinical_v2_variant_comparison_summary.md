# Clinical V2 Variant Comparison Summary

Issue: #153

This is educational, non-diagnostic model evaluation. Do not claim clinical readiness or diagnosis.

Training metrics are not used for promotion here. These results are held-out test-set model evaluation metrics, and no model was promoted in code.

## Test Split

- Directly comparable: yes
- Evaluation test CSV: `data/processed/clinical_v2/test.csv`
- All complete variants were evaluated on the original Clinical V2 baseline test split.
- #153 remains the comparison and recommendation task; any code promotion must happen separately.

## Comparison Table

| Variant | Combined macro-F1 | Balanced accuracy | SCIN macro-F1 | SCIN error rate | Fitzpatrick macro-F1 | Fitzpatrick error rate | Lesion FN | Eczema→Urticaria | Urticaria FP | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline_clinical_v2 | 0.6420 | 0.6571 | 0.4028 | 0.4278 | 0.6366 | 0.2956 | 76 | 91 | 160 | keep current baseline |
| clinical_v2_class_sampler | 0.6395 | 0.6607 | 0.3853 | 0.4439 | 0.6417 | 0.2956 | 90 | 92 | 156 | keep experimental |
| clinical_v2_source_class_sampler | 0.6052 | 0.6329 | 0.3801 | 0.5045 | 0.6275 | 0.3197 | 95 | 94 | 178 | keep experimental |
| clinical_v2_high_confidence_067 | 0.6464 | 0.6597 | 0.3675 | 0.4403 | 0.6642 | 0.2809 | 88 | 77 | 121 | keep experimental |
| clinical_v2_high_confidence_075 | 0.6175 | 0.6296 | 0.3488 | 0.4759 | 0.6402 | 0.3092 | 94 | 106 | 196 | keep experimental |

## Final Recommendation

- Keep the current `clinical_v2` baseline.
- Do not promote any #132/#133 variant.
- Document the four variants as unsuccessful for promotion under the #148 criteria.

No additional training was run by this evaluation. No app wiring, taxonomy, inference registry, or model promotion changes were made.

## Generated Files

- `outputs/metrics/clinical_v2_variant_comparison_metrics.json`
- `outputs/metrics/clinical_v2_variant_comparison_table.csv`
- `outputs/metrics/baseline_clinical_v2_classification_report.csv`
- `outputs/metrics/baseline_clinical_v2_source_metrics.csv`
- `outputs/metrics/baseline_clinical_v2_confusion_matrix.csv`
- `outputs/plots/baseline_clinical_v2_confusion_matrix.png`
- `outputs/metrics/clinical_v2_class_sampler_classification_report.csv`
- `outputs/metrics/clinical_v2_class_sampler_source_metrics.csv`
- `outputs/metrics/clinical_v2_class_sampler_confusion_matrix.csv`
- `outputs/plots/clinical_v2_class_sampler_confusion_matrix.png`
- `outputs/metrics/clinical_v2_source_class_sampler_classification_report.csv`
- `outputs/metrics/clinical_v2_source_class_sampler_source_metrics.csv`
- `outputs/metrics/clinical_v2_source_class_sampler_confusion_matrix.csv`
- `outputs/plots/clinical_v2_source_class_sampler_confusion_matrix.png`
- `outputs/metrics/clinical_v2_high_confidence_067_classification_report.csv`
- `outputs/metrics/clinical_v2_high_confidence_067_source_metrics.csv`
- `outputs/metrics/clinical_v2_high_confidence_067_confusion_matrix.csv`
- `outputs/plots/clinical_v2_high_confidence_067_confusion_matrix.png`
- `outputs/metrics/clinical_v2_high_confidence_075_classification_report.csv`
- `outputs/metrics/clinical_v2_high_confidence_075_source_metrics.csv`
- `outputs/metrics/clinical_v2_high_confidence_075_confusion_matrix.csv`
- `outputs/plots/clinical_v2_high_confidence_075_confusion_matrix.png`
