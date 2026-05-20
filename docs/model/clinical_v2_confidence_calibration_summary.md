# Clinical V2 Confidence Calibration Summary

This calibration analysis fits a single scalar temperature on the Clinical V2 validation split and evaluates the frozen test split before and after scaling.

The classifier weights are not retrained, the taxonomy is unchanged, and the app/model registry wiring is unchanged.

Model confidence is not clinical certainty. Calibrated confidence is still not diagnostic certainty. These results do not support any diagnosis, treatment, clinical-readiness, or autonomous decision-making claim.

## Temperature

- Fitted temperature: 1.424174
- Validation NLL before scaling: 0.880698
- Validation NLL after scaling: 0.834971

## Frozen Test Split

- Test examples: 1515
- Predictions unchanged after calibration: True

| Metric | Before | After |
| --- | ---: | ---: |
| Accuracy | 0.655446 | 0.655446 |
| ECE | 0.100348 | 0.020275 |
| NLL | 0.902974 | 0.858709 |
| Brier score | 0.464518 | 0.448535 |

## Confidence Distribution

| Statistic | Before | After |
| --- | ---: | ---: |
| mean | 0.755214 | 0.671267 |
| std | 0.206116 | 0.209633 |
| min | 0.273459 | 0.251033 |
| p25 | 0.572778 | 0.485329 |
| median | 0.793662 | 0.666061 |
| p75 | 0.956302 | 0.869585 |
| max | 0.999917 | 0.998152 |

## Saved Artifacts

- Temperature JSON: `models/clinical_v2_effnet_b0/calibration_temperature.json`
- Metrics JSON: `outputs/metrics/clinical_v2_calibration_metrics.json`
- Reliability bins CSV: `outputs/metrics/clinical_v2_reliability_bins.csv`

Reliability bins compare average model confidence with empirical accuracy within confidence intervals. They describe model calibration on this test split only, not clinical certainty.
