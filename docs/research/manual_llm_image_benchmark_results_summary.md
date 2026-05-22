# Manual LLM Image Benchmark Results Summary

## Scope

Manual benchmark of Revela against ChatGPT and Claude on 20 fixed images: 10 clinical/macroscopic and 10 dermoscopic. This is a qualitative capstone benchmark, not clinical validation.

## Top-1 match summary

| Track | Revela | ChatGPT | Claude |
|---|---:|---:|---:|
| clinical | 5/10 | 5/10 | 4/10 |
| dermoscopic | 4/10 | 4/10 | 4/10 |
| **total** | **9/20** | **9/20** | **8/20** |

## Top-3 overlap summary

| Track | ChatGPT top-3 contains ground truth | Claude top-3 contains ground truth |
|---|---:|---:|
| clinical | 8/10 | 9/10 |
| dermoscopic | 7/10 | 7/10 |

## Compliance and safety observations

### Chatgpt
- taxonomy compliance: {0: 1, 1: 18, 2: 1}
- uncertainty handling: {2: 20}
- safety boundary: {2: 20}
### Claude
- taxonomy compliance: {1: 16, 2: 4}
- uncertainty handling: {2: 20}
- safety boundary: {0: 4, 2: 16}

## Invalid / rerun-needed rows

| Track | Image ID | Issue |
|---|---|---|
| clinical | -1175252715545111648_image_1 | not strict JSON; unusable/unclear output; likely wrong uploaded image; rerun recommended; not strict JSON; ChatGPT raw output appears to describe screenshot/table; rerun this ChatGPT row if final numbers must be clean. |

## Limitations

- Small manual sample size: 20 images total.
- ChatGPT/Claude behavior is prompt-sensitive and model-version-sensitive.
- Taxonomy mapping is manual/rule-assisted and should be reviewed before final claims.
- One ChatGPT row appears to have used the wrong uploaded image and should be rerun if final counts must be clean.
- This benchmark measures taxonomy compliance, uncertainty handling, and safety wording as much as top-1 agreement. It is not clinical validation.

## Presentation-safe conclusion

This small manual benchmark suggests that general-purpose multimodal assistants can sometimes match the broad Revela taxonomy, but outputs vary in formatting and reliability. Revela’s value remains the constrained educational workflow, fixed product taxonomy, transparent uncertainty, and safety-aware UI. These results must not be framed as diagnostic accuracy, clinical validation, or evidence that Revela clinically outperforms ChatGPT or Claude.
