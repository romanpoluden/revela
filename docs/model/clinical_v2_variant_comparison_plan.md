# Clinical V2 Variant Comparison Plan

This document defines how Clinical V2 model variants should be compared before any variant replaces the current baseline in the Revela prototype.

The goal is not to find the highest combined accuracy. The goal is to decide whether an alternative training or dataset strategy improves the model in a way that is useful, stable, and safe for an educational prototype.

## Scope

This plan covers comparison of the current Clinical V2 baseline against candidate variants from:

- #132 — source-aware and class-aware sampling
- #133 — high-confidence SCIN dataset variants
- later combined variants, if created

This plan does not train models, change taxonomy, change app inference wiring, or claim clinical readiness.

## Current Baseline

Current baseline model:

- Model: Clinical V2 EfficientNet-B0
- Model registry ID: `clinical_skin_condition_v1`
- Dataset: `clinical_v2`
- Input domain: clinical / phone-style skin photos
- Output taxonomy:
  1. `Eczema / dermatitis`
  2. `Urticaria / allergic reaction`
  3. `Folliculitis / acne-like`
  4. `Psoriasis / papulosquamous`
  5. `Lesion — dermoscopic review recommended`

The fifth class is a routing class. It is not cancer detection.

Baseline test metrics from the current Clinical V2 evaluation:

| Metric | Value |
|---|---:|
| Combined accuracy | 0.6554 |
| Combined macro-F1 | 0.6420 |
| Combined balanced accuracy | 0.6571 |
| Google SCIN macro-F1 | 0.4028 |
| Fitzpatrick17k macro-F1 | 0.6366 |
| Lesion-routing F1 | 0.8282 |

Baseline error-analysis findings from #131:

| Finding | Baseline value |
|---|---:|
| Test examples | 1515 |
| Total errors | 522 |
| Error rate | 0.3446 |
| Google SCIN errors | 240 / 561 = 0.4278 |
| Fitzpatrick17k errors | 282 / 954 = 0.2956 |
| Eczema / dermatitis errors | 195 / 443 = 0.4402 |
| Top confusion pair | Eczema / dermatitis → Urticaria / allergic reaction: 91 |
| Lesion-routing false negatives | 76 |

## Candidate Variants to Compare

Each candidate should be compared against the same current baseline.

| Variant | Source issue | Description |
|---|---|---|
| Baseline `clinical_v2` | #129 / #130 / #131 | Current Clinical V2 model and dataset |
| Class-aware sampler | #132 | Weighted sampling by `target_label` |
| Source+class-aware sampler | #132 | Weighted sampling by `source_dataset` + `target_label` |
| High-confidence SCIN 0.67 | #133 | Keeps SCIN rows with top weighted label score >= 0.67 |
| High-confidence SCIN 0.75 | #133 | Keeps SCIN rows with top weighted label score >= 0.75 |
| Combined variant | Future | Possible high-confidence dataset plus source/class-aware sampling |

Do not promote a candidate only because one metric improves. Use the full comparison matrix below.

## Required Evaluation Metrics

Every candidate model should report these metrics on its validation set during training and on the held-out test set before any promotion decision.

### Overall metrics

| Metric | Required | Reason |
|---|---|---|
| Accuracy | Yes | General sanity check, but not sufficient |
| Macro-F1 | Yes | Main combined metric because classes are imbalanced |
| Balanced accuracy | Yes | Helps detect poor minority-class behavior |
| Weighted F1 | Optional | Useful secondary summary, not promotion driver |
| Loss | Optional | Useful for training diagnostics |

### Class-wise metrics

For each class, report:

- precision
- recall
- F1
- support

Required classes:

- `Eczema / dermatitis`
- `Urticaria / allergic reaction`
- `Folliculitis / acne-like`
- `Psoriasis / papulosquamous`
- `Lesion — dermoscopic review recommended`

### Source-specific metrics

Source-specific metrics are required even though both SCIN and Fitzpatrick17k are clinical-photo-style datasets. They are a guardrail against a model improving on one source while degrading on another.

Report at minimum:

| Source | Required metrics |
|---|---|
| `google_scin` | accuracy, macro-F1, error rate, class-wise metrics where support allows |
| `fitzpatrick17k` | accuracy, macro-F1, error rate, class-wise metrics where support allows |
| combined | accuracy, macro-F1, balanced accuracy |

Source-specific comparison is not an argument against merging SCIN and Fitzpatrick17k. The datasets can be merged because both are clinical image sources. The source split is used to verify whether the merged model behaves consistently across the two label/image distributions.

### Safety-relevant routing metrics

The lesion-routing class must be tracked separately because it controls whether a case is routed toward dermoscopic review in the product concept.

Report:

- lesion-routing precision
- lesion-routing recall
- lesion-routing F1
- lesion-routing false negatives
- most common predicted labels among lesion-routing false negatives

A candidate should not be promoted if lesion-routing false negatives increase materially, even if combined accuracy improves.

### Confusion-pattern metrics

Track the specific failure patterns identified in #131:

| Confusion pattern | Baseline count | Direction wanted |
|---|---:|---|
| Eczema / dermatitis → Urticaria / allergic reaction | 91 | decrease |
| Eczema / dermatitis → Psoriasis / papulosquamous | 51 | decrease or stable |
| Psoriasis / papulosquamous → Eczema / dermatitis | 39 | decrease or stable |
| Psoriasis / papulosquamous → Urticaria / allergic reaction | 39 | decrease or stable |
| Lesion-routing → Psoriasis / papulosquamous | 35 | decrease |
| Total lesion-routing false negatives | 76 | decrease or stable |

Also track total Urticaria false positives. The baseline error analysis reported 160 Urticaria false positives, mostly from Eczema / dermatitis, Psoriasis / papulosquamous, and Folliculitis / acne-like.

## Comparison Table Template

Use this table for the final variant comparison summary.

| Variant | Combined macro-F1 | Balanced accuracy | SCIN macro-F1 | SCIN error rate | Fitzpatrick macro-F1 | Fitzpatrick error rate | Lesion FN | Eczema→Urticaria | Urticaria FP | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Baseline `clinical_v2` | 0.6420 | 0.6571 | 0.4028 | 0.4278 | 0.6366 | 0.2956 | 76 | 91 | 160 | Current baseline |
| Class-aware sampler | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Source+class-aware sampler | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| High-confidence SCIN 0.67 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| High-confidence SCIN 0.75 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Combined variant | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Promotion Criteria

A candidate can be considered for promotion if it satisfies most of the following criteria:

1. Combined macro-F1 is stable or improved versus 0.6420.
2. Balanced accuracy is stable or improved versus 0.6571.
3. SCIN macro-F1 improves materially versus 0.4028, or SCIN error rate decreases versus 0.4278.
4. Fitzpatrick17k macro-F1 does not materially degrade versus 0.6366.
5. Lesion-routing false negatives do not increase versus 76.
6. Lesion-routing recall is stable or improved.
7. Eczema → Urticaria confusion decreases versus 91, or at minimum does not increase materially.
8. Urticaria false positives decrease versus 160, or at minimum do not increase materially.
9. The model remains compatible with the current inference response schema.
10. Documentation keeps the educational-only, non-diagnostic framing.

For this capstone, a practical material-change threshold is around 2–3 percentage points for aggregate metrics or a clearly meaningful reduction in key error counts. Do not overfit the decision to tiny metric changes.

## Rejection Criteria

Reject or keep a candidate as experimental if any of the following occur:

- Combined accuracy improves but macro-F1 or balanced accuracy degrades materially.
- SCIN performance remains weak and does not improve meaningfully.
- Fitzpatrick17k performance collapses after source-aware changes.
- Lesion-routing false negatives increase materially.
- High-confidence SCIN filtering removes too much SCIN coverage to be credible for the demo.
- A class becomes too small for reliable training or evaluation.
- The candidate requires taxonomy changes outside the approved Clinical V2 scope.
- The candidate creates incompatible model artifacts or breaks the inference adapter.
- The summary uses diagnostic or clinical-readiness language.

## High-Confidence SCIN Variant Checks

For each high-confidence SCIN dataset variant, report:

| Check | Required output |
|---|---|
| SCIN rows retained | count and percentage |
| SCIN rows removed | count and percentage |
| Rows retained by `target_label` | table |
| Rows retained by split | train / val / test counts |
| Fitzpatrick17k rows | confirm unchanged |
| Required columns | confirm preserved |
| Missing image paths | should be 0 |
| SCIN case split leakage | should be 0 |
| Minimum class support | identify any weak class |
| Suitability for retraining | yes / no / conditional |

A high-confidence variant is useful only if it plausibly reduces noisy or ambiguous SCIN rows without making the dataset too narrow or class-imbalanced.

## Sampling Variant Checks

For each sampling variant, report:

| Check | Required output |
|---|---|
| Sampler mode | `none`, `class`, or `source_class` |
| Backward compatibility | default config should preserve previous behavior |
| Sample weighting basis | `target_label` or `source_dataset` + `target_label` |
| Smoke training | confirms sampler works |
| Full training metrics | required before promotion decision |
| Source-specific validation metrics | required if implemented |

Sampler changes should improve training behavior without changing the dataset taxonomy or leaking test data.

## Reporting Requirements

Each candidate experiment should produce a concise summary containing:

1. Config used.
2. Dataset variant used.
3. Model artifact path.
4. Training command.
5. Test/evaluation command.
6. Overall metrics.
7. Class-wise metrics.
8. Source-specific metrics.
9. Lesion-routing false negatives.
10. Key confusion pairs.
11. Decision: promote / keep experimental / reject.
12. Non-diagnostic limitation statement.

Recommended output document names:

- `docs/model/clinical_v2_sampling_experiment_summary.md`
- `docs/model/clinical_v2_high_confidence_dataset_summary.md`
- `docs/model/clinical_v2_variant_comparison_summary.md` if final comparison is produced later

## Decision Rule

Use this decision hierarchy:

1. Reject any variant that worsens lesion-routing false negatives materially.
2. Reject any variant that materially degrades combined macro-F1 or balanced accuracy.
3. Prefer variants that improve SCIN performance without collapsing Fitzpatrick17k performance.
4. Prefer variants that reduce Eczema → Urticaria confusion and Urticaria false positives.
5. If two variants are similar, prefer the simpler and more reproducible one.
6. If no variant clearly improves the baseline, keep the current Clinical V2 model and document the failed improvement attempts.

## Communication Rules

All documentation and app-facing wording must keep these boundaries:

- The model output is educational prototype output, not diagnosis.
- The lesion-routing class is a routing suggestion, not cancer detection.
- Confidence is model confidence, not clinical certainty.
- No treatment advice should be included.
- No clinical-readiness claim should be made.

## Final Decision Log Update

After candidate evaluation is complete, update the decision log with:

- selected clinical model version, or decision to keep baseline;
- reason for promotion or rejection;
- key metrics supporting the decision;
- known limitations;
- issue references for #131, #132, #133, and #148.
