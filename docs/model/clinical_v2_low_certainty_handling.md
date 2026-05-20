# Clinical V2 Low-Certainty Handling

## Purpose

Clinical V2 outputs are educational model outputs, not clinical conclusions. Low-certainty handling makes weak model signals visible in the response and Streamlit UI without retraining the model, changing the taxonomy, changing the registry, or changing prediction scores.

The app still preserves the top-3 ranked outputs. The low-certainty fields only adjust wording around those outputs.

## Current Confidence Fields

The canonical inference response already includes:

- `predictions`: ranked top-k model outputs with raw confidence and percent confidence.
- `top_prediction`: the first entry from `predictions`.
- `uncertainty`: a bucket from `get_uncertainty_bucket()` based on top-1 confidence.

Existing uncertainty buckets are:

- `high_confidence`: top confidence >= 0.70.
- `medium_confidence`: top confidence >= 0.40 and < 0.70.
- `low_confidence`: top confidence < 0.40.

These values describe model confidence only. They are not clinical certainty.

## MVP Rule

Low certainty is true when:

```text
top confidence < 0.60 OR uncertainty.bucket == "low_confidence"
```

The `low_confidence` bucket is included explicitly so the rule remains connected to the existing uncertainty field. In practice, the 0.60 threshold also covers that bucket.

## Why 0.60 Is Conservative

The existing `medium_confidence` bucket starts at 0.40, but a 0.40-0.59 top score can still be a weak educational signal. Using 0.60 flags much of the lower and middle-confidence range for softer wording, while leaving the ranked model outputs unchanged.

This favors transparent uncertainty communication over presenting a low-confidence top output as a strong finding.

## Response Fields

Successful canonical responses now include:

```json
{
  "low_certainty": true,
  "low_certainty_reason": "Top model confidence 56.00% is below the conservative 60% low-certainty threshold.",
  "low_certainty_message": "The model output is uncertain. Use this only for educational review. Review the top outputs, image quality, and clinical context, and consider additional image/context review. This is not a diagnosis and does not recommend treatment.",
  "low_certainty_rule": "low_certainty is true when top confidence is below 0.60 or uncertainty.bucket is low_confidence.",
  "low_certainty_threshold": 0.6
}
```

For higher-confidence outputs, `low_certainty` is `false` and the message/reason fields are `null`.

## UI Handling

When `low_certainty` is true, Streamlit shows the low-certainty message near the uncertainty section. The top-3 outputs remain visible so users can review the ranked model outputs, image quality, and context together.

Required wording:

> The model output is uncertain. Use this only for educational review. Review the top outputs, image quality, and clinical context, and consider additional image/context review. This is not a diagnosis and does not recommend treatment.

## Non-Goals

- No retraining.
- No taxonomy changes.
- No model registry changes.
- No prediction score changes.
- No diagnosis, treatment, or clinical-readiness claims.
