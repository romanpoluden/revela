# Clinical v2 Dataset Build Summary

## Purpose

This document supports issue #125.

The processed clinical-image dataset was built using the approved 5-class taxonomy:

1. Eczema / dermatitis
2. Urticaria / allergic reaction
3. Folliculitis / acne-like
4. Psoriasis / papulosquamous
5. Lesion — dermoscopic review recommended

The fifth class is a routing class, not cancer detection.

## Dataset sources

- Official Google SCIN export: `google/scin`
- Fitzpatrick17k local downloaded images

## Important split notes

- SCIN is split by `case_id`; all images from the same case stay in the same split.
- Fitzpatrick17k does not provide clear `case_id`, `patient_id`, or `lesion_id`, so it is split at row/image level.
- Source-specific evaluation is required because Fitzpatrick17k is important for the lesion-routing class.

## Total rows

10019

## Source summary

- SCIN image rows: 3665
- SCIN unique cases: 1692
- Fitzpatrick17k rows: 6354

## Counts by split and class

| split   |   Eczema / dermatitis |   Folliculitis / acne-like |   Lesion — dermoscopic review recommended |   Psoriasis / papulosquamous |   Urticaria / allergic reaction |
|:--------|----------------------:|---------------------------:|------------------------------------------:|-----------------------------:|--------------------------------:|
| test    |                   443 |                        236 |                                       370 |                          306 |                             160 |
| train   |                  2015 |                       1081 |                                      1739 |                         1396 |                             755 |
| val     |                   446 |                        227 |                                       371 |                          304 |                             170 |

## Counts by source dataset and class

| source_dataset   |   Eczema / dermatitis |   Folliculitis / acne-like |   Lesion — dermoscopic review recommended |   Psoriasis / papulosquamous |   Urticaria / allergic reaction |
|:-----------------|----------------------:|---------------------------:|------------------------------------------:|-----------------------------:|--------------------------------:|
| fitzpatrick17k   |                   843 |                       1023 |                                      2410 |                         1615 |                             463 |
| google_scin      |                  2061 |                        521 |                                        70 |                          391 |                             622 |

## Counts by split and source dataset

| split   |   fitzpatrick17k |   google_scin |
|:--------|-----------------:|--------------:|
| test    |              954 |           561 |
| train   |             4447 |          2539 |
| val     |              953 |           565 |

## Output files

- `data/processed/clinical_v2/train.csv`
- `data/processed/clinical_v2/val.csv`
- `data/processed/clinical_v2/test.csv`
- `config/clinical_v2_config.yaml`

## Communication rule

Do not claim cancer detection from the clinical-image model. Use the lesion class only to trigger dermoscopic review.
