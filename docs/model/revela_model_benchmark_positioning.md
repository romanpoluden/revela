# Revela Model Benchmark Positioning

Issue: #166

This document gives presentation-ready benchmark wording for Revela. It is not clinical validation. Revela is an educational prototype, model confidence is not clinical certainty, and the project makes no diagnosis or treatment claims.

## Safe Positioning Statement

Revela demonstrates a transparent educational workflow for skin-image model outputs across two image domains:

- Clinical-photo review with `clinical_skin_condition_v1`
- Dermoscopic review with `dermoscopic_cancer_risk_bcn_mnh_v1`

The project reports internal held-out metrics and source-specific performance, then positions those results against adjacent dermatology AI literature. Because external benchmarks use different datasets, image types, taxonomies, and protocols, the comparison is benchmark positioning rather than a direct leaderboard result.

## Current Revela Metrics

### Clinical V2 Baseline

- Accuracy: `0.6554` / `65.54%`
- Macro-F1: `0.6420` / `64.20%`
- Balanced accuracy: `0.6571` / `65.71%`
- SCIN macro-F1: `0.4028`
- Fitzpatrick17k macro-F1: `0.6366`
- Lesion-routing false negatives: `76`

### Dermoscopic BCN+MNH Model

- Model ID: `dermoscopic_cancer_risk_bcn_mnh_v1`
- Architecture: `efficientnet_b0`
- Taxonomy:
  1. `Melanoma`
  2. `Non-melanoma skin cancer`
  3. `Benign nevus`
  4. `Other non-cancer / indeterminate lesion`
- Exact evaluation metrics: not yet consolidated in benchmark doc.

## Benchmark-Positioning Table

| Source / model | Domain | Reported metrics | Comparability | Presentation use |
|---|---|---:|---|---|
| Revela Clinical V2 baseline | Clinical/macroscopic | Accuracy 65.54%; macro-F1 64.20%; balanced accuracy 65.71% | Internal reference | Show transparent baseline with source-specific caveats |
| DermaCon-IN Swin-B/4W12-384 | Clinical/macroscopic | Accuracy 70.41 ± 0.41; F1 69.69 ± 0.46; balanced accuracy 45.06 ± 0.02 | Partial | Closest clinical-photo benchmark context |
| DermaCon-IN ViT-B/16-384 | Clinical/macroscopic | Accuracy 66.95 ± 0.19; F1 65.78 ± 0.06; balanced accuracy 35.78 ± 0.02 | Partial | Transformer baseline context |
| DermaCon-IN EffNet-B4 | Clinical/macroscopic | Accuracy 64.28 ± 0.34; F1 63.38 ± 0.39; balanced accuracy 35.58 ± 0.01 | Partial | Architecture-adjacent clinical-photo context |
| SCIN | Clinical/macroscopic | Dataset context; Revela SCIN macro-F1 0.4028 | Context only | Explain source-specific reporting |
| Fitzpatrick17k | Clinical/macroscopic | Dataset context; Revela Fitzpatrick17k macro-F1 0.6366 | Context only | Explain fairness/source limitations |
| SAMCL / PUMCH-ISD | Multimodal clinical + dermoscopic | Accuracy 0.822; binary accuracy 0.911; Derm7pt accuracy 0.807 | Adjacent | Future multimodal benchmark context |
| HierAttn | Dermoscopic / smartphone lesion | ISIC2019 accuracy 96.70%; PAD2020 accuracy 91.22% | Partial | Lesion-image benchmark landscape |
| PAD-UFES-20 | Smartphone lesion | Dataset context | Partial / not direct | Smartphone lesion context |
| ISIC / HAM10000 | Dermoscopic | Classic dermoscopic dataset context | Partial / not direct | Familiar dermoscopic benchmark family |
| Revela `dermoscopic_cancer_risk_bcn_mnh_v1` | Dermoscopic | Not yet consolidated in benchmark doc | Internal reference | Present as registered educational dermoscopic branch, not as clinical validation |

## What We Can Say

- Revela is an educational prototype with transparent model output, uncertainty, safety notes, and limitations.
- Revela Clinical V2 reports internal held-out metrics and source-specific results.
- Revela’s clinical-photo metrics are in a range that can be discussed alongside clinical/macroscopic benchmarks such as DermaCon-IN, but not as a direct comparison.
- Source-specific reporting matters because SCIN and Fitzpatrick17k results differ substantially.
- The dermoscopic branch uses a separate model and taxonomy from the clinical-photo branch.
- External benchmarks help frame the landscape, but each has dataset, taxonomy, and protocol differences.

## What We Must Not Say

- Do not say Revela is clinically validated.
- Do not describe Revela metrics as diagnostic accuracy.
- Do not claim doctor-level performance.
- Do not call Revela a cancer detection system.
- Do not say the system is safe for patient use.
- Do not claim Revela outperforms dermatologists or external models.
- Do not turn model confidence into clinical certainty.

## Slide-Ready Conclusion

Revela is best positioned as a transparent educational prototype rather than a clinical tool. Its Clinical V2 baseline reports balanced, source-aware metrics, and its dermoscopic branch is registered as a separate educational model. External dermatology AI benchmarks provide useful context, but current comparisons are partial or adjacent because datasets, taxonomies, and protocols differ. The strongest presentation claim is careful benchmark positioning, not clinical validation.
