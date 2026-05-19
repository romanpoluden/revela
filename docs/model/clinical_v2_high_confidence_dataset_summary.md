# Clinical v2 High-Confidence SCIN Dataset Summary

## Why V2.10 was needed

V2.8 / issue #131 showed a clear source gap: combined macro-F1 was 0.6420, Google SCIN macro-F1 was 0.4028, Fitzpatrick17k macro-F1 was 0.6366, google_scin error rate was 0.4278, and fitzpatrick17k error rate was 0.2956. V2.10 builds high-confidence SCIN variants to reduce potential SCIN label noise for future retraining experiments.

## Method

- Started from the frozen `data/processed/clinical_v2` CSVs to preserve the existing taxonomy, class indices, source labels, and split assignments.
- Identified SCIN rows with `source_dataset == "google_scin"`.
- Parsed `weighted_skin_condition_label` with `ast.literal_eval`, falling back to JSON parsing, accepting only dictionaries with finite numeric scores.
- Added `scin_top_weighted_label` and `scin_top_weighted_label_score` for SCIN rows.
- Preserved all Fitzpatrick17k rows.
- Preserved the existing SCIN split, which was built case-aware by `case_id`.
- Preserved the existing Fitzpatrick17k row-level split; Fitzpatrick17k still lacks case_id/patient_id/lesion_id in this dataset.

## Thresholds attempted

- Top weighted label score >= 0.67
- Top weighted label score >= 0.75

## Baseline clinical_v2 counts

Total rows: 10019

### Baseline by split

| split | rows |
| --- | --- |
| test | 1515 |
| train | 6986 |
| val | 1518 |

### Baseline by source

| source_dataset | rows |
| --- | --- |
| fitzpatrick17k | 6354 |
| google_scin | 3665 |

### Baseline by target class

| target_label | rows |
| --- | --- |
| Eczema / dermatitis | 2904 |
| Folliculitis / acne-like | 1544 |
| Lesion — dermoscopic review recommended | 2480 |
| Psoriasis / papulosquamous | 2006 |
| Urticaria / allergic reaction | 1085 |

### Baseline by source and target class

| source_dataset | Eczema / dermatitis | Urticaria / allergic reaction | Folliculitis / acne-like | Psoriasis / papulosquamous | Lesion — dermoscopic review recommended |
| --- | --- | --- | --- | --- | --- |
| fitzpatrick17k | 843 | 463 | 1023 | 1615 | 2410 |
| google_scin | 2061 | 622 | 521 | 391 | 70 |

## High-confidence 0.67 variant

Output directory: `data/processed/clinical_v2_high_confidence_067`

Total rows: 7907
SCIN rows retained: 1553
SCIN cases retained: 752
Suitable for retraining experiment: yes

### Counts by split

| split | rows |
| --- | --- |
| test | 1194 |
| train | 5494 |
| val | 1219 |

### Counts by source

| source_dataset | rows |
| --- | --- |
| fitzpatrick17k | 6354 |
| google_scin | 1553 |

### Counts by target class

| target_label | rows |
| --- | --- |
| Eczema / dermatitis | 1737 |
| Folliculitis / acne-like | 1266 |
| Lesion — dermoscopic review recommended | 2437 |
| Psoriasis / papulosquamous | 1703 |
| Urticaria / allergic reaction | 764 |

### Counts by source and target class

| source_dataset | Eczema / dermatitis | Urticaria / allergic reaction | Folliculitis / acne-like | Psoriasis / papulosquamous | Lesion — dermoscopic review recommended |
| --- | --- | --- | --- | --- | --- |
| fitzpatrick17k | 843 | 463 | 1023 | 1615 | 2410 |
| google_scin | 894 | 301 | 243 | 88 | 27 |

## High-confidence 0.75 variant

Output directory: `data/processed/clinical_v2_high_confidence_075`

Total rows: 7251
SCIN rows retained: 897
SCIN cases retained: 437
Suitable for retraining experiment: yes

### Counts by split

| split | rows |
| --- | --- |
| test | 1094 |
| train | 5052 |
| val | 1105 |

### Counts by source

| source_dataset | rows |
| --- | --- |
| fitzpatrick17k | 6354 |
| google_scin | 897 |

### Counts by target class

| target_label | rows |
| --- | --- |
| Eczema / dermatitis | 1367 |
| Folliculitis / acne-like | 1154 |
| Lesion — dermoscopic review recommended | 2423 |
| Psoriasis / papulosquamous | 1663 |
| Urticaria / allergic reaction | 644 |

### Counts by source and target class

| source_dataset | Eczema / dermatitis | Urticaria / allergic reaction | Folliculitis / acne-like | Psoriasis / papulosquamous | Lesion — dermoscopic review recommended |
| --- | --- | --- | --- | --- | --- |
| fitzpatrick17k | 843 | 463 | 1023 | 1615 | 2410 |
| google_scin | 524 | 181 | 131 | 48 | 13 |

## Suitability

The 0.67 variant is suitable for a retraining experiment because it retains a substantial SCIN subset across all target classes while reducing lower-confidence weighted-label rows.
The 0.75 variant is also suitable for a narrower retraining experiment if lower SCIN coverage is acceptable; it keeps all target classes but further reduces SCIN representation.

## Limitations

- Filtering may reduce SCIN coverage, especially for smaller classes.
- The Fitzpatrick17k split limitation remains: rows are split at image level because case_id/patient_id/lesion_id are unavailable.
- These datasets are for retraining experiments only and make no clinical-readiness claim.
- No taxonomy change was made.
- The clinical model is not diagnostic, and the lesion class remains a routing output only.
