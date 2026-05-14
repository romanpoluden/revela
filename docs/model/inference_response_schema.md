# Inference Response Schema

This schema combines:

- `predict_image()` raw model inference
- `get_top_k_predictions()` ranked prediction entries
- `get_uncertainty_bucket()` generic model-confidence bucket

It is taxonomy-agnostic and must support clinical and dermoscopic model families, including:

- `clinical_skin_condition_v1` / `clinical_v2_effnet_b0`
- `dermoscopic_baseline_v1` for smoke testing only
- future `dermoscopic_cancer_risk_v2`

Inference responses are educational prototype outputs, not diagnosis. Confidence values are model confidence, not clinical certainty. The clinical lesion-routing class means dermoscopic review is recommended by the routing taxonomy; it is not cancer detection.

## Success Response

Canonical fields:

```json
{
  "model_id": "clinical_skin_condition_v1",
  "model_name": "Clinical skin condition prototype",
  "input_type": "clinical",
  "architecture": "efficientnet_b0",
  "image_size": 224,
  "predictions": [],
  "top_prediction": {},
  "uncertainty": {},
  "safety_note": "Prototype educational output only. This response is not a diagnosis and does not recommend treatment.",
  "model_limitations": [],
  "recommended_next_step": "Use this output as a prototype aid for review, not as a standalone medical decision."
}
```

Field notes:

- `model_id`: Registry identifier used to load the model.
- `model_name`: Optional display name when available.
- `input_type`: Model input family such as `clinical` or `dermoscopic`.
- `architecture`: Model architecture, for example `efficientnet_b0`.
- `image_size`: Deterministic inference image size.
- `predictions`: Ranked top-k model outputs. These are not diagnoses.
- `top_prediction`: First item from `predictions`.
- `uncertainty`: Generic bucket based on top-1 model confidence.
- `safety_note`: Generic prototype safety note.
- `model_limitations`: Generic limitations to show near the result.
- `recommended_next_step`: Generic next step for prototype review, not treatment advice.

Prediction entry:

```json
{
  "rank": 1,
  "class_index": 0,
  "label": "Example class",
  "confidence": 0.8062,
  "confidence_percent": 80.62
}
```

Uncertainty entry:

```json
{
  "bucket": "high_confidence",
  "confidence": 0.8062,
  "confidence_percent": 80.62,
  "label": "High model confidence",
  "explanation": "The model assigned a relatively high probability to its top output. This is model confidence, not clinical certainty."
}
```

## Error Response

Canonical fields:

```json
{
  "error": true,
  "error_code": "invalid_image",
  "message": "The uploaded file could not be read as an image.",
  "details": {
    "accepted_inputs": ["path", "PIL.Image", "file-like object"]
  }
}
```

Suggested `error_code` values:

- `unknown_model_id`
- `missing_model_artifact`
- `invalid_image`
- `invalid_input`
- `inference_failed`
- `postprocess_failed`

## Example: Clinical Model

```json
{
  "model_id": "clinical_skin_condition_v1",
  "model_name": "Clinical skin condition prototype",
  "input_type": "clinical",
  "architecture": "efficientnet_b0",
  "image_size": 224,
  "predictions": [
    {
      "rank": 1,
      "class_index": 0,
      "label": "Eczema / dermatitis",
      "confidence": 0.62,
      "confidence_percent": 62.0
    },
    {
      "rank": 2,
      "class_index": 3,
      "label": "Psoriasis / papulosquamous",
      "confidence": 0.21,
      "confidence_percent": 21.0
    },
    {
      "rank": 3,
      "class_index": 1,
      "label": "Urticaria / allergic reaction",
      "confidence": 0.09,
      "confidence_percent": 9.0
    }
  ],
  "top_prediction": {
    "rank": 1,
    "class_index": 0,
    "label": "Eczema / dermatitis",
    "confidence": 0.62,
    "confidence_percent": 62.0
  },
  "uncertainty": {
    "bucket": "medium_confidence",
    "confidence": 0.62,
    "confidence_percent": 62.0,
    "label": "Medium model confidence",
    "explanation": "The model assigned a moderate probability to its top output. This is model confidence, not clinical certainty."
  },
  "safety_note": "Prototype educational output only. This response is not a diagnosis and does not recommend treatment.",
  "model_limitations": [
    "Predictions are model outputs from a finite taxonomy, not clinical conclusions.",
    "Confidence is model confidence, not clinical certainty.",
    "Performance may vary across image quality, skin tone, lighting, and source dataset."
  ],
  "recommended_next_step": "Use this output as a prototype aid for review, not as a standalone medical decision."
}
```

## Example: Clinical Lesion-Routing Output

```json
{
  "model_id": "clinical_skin_condition_v1",
  "model_name": "Clinical skin condition prototype",
  "input_type": "clinical",
  "architecture": "efficientnet_b0",
  "image_size": 224,
  "predictions": [
    {
      "rank": 1,
      "class_index": 4,
      "label": "Lesion — dermoscopic review recommended",
      "confidence": 0.56,
      "confidence_percent": 56.0
    },
    {
      "rank": 2,
      "class_index": 3,
      "label": "Psoriasis / papulosquamous",
      "confidence": 0.18,
      "confidence_percent": 18.0
    },
    {
      "rank": 3,
      "class_index": 1,
      "label": "Urticaria / allergic reaction",
      "confidence": 0.11,
      "confidence_percent": 11.0
    }
  ],
  "top_prediction": {
    "rank": 1,
    "class_index": 4,
    "label": "Lesion — dermoscopic review recommended",
    "confidence": 0.56,
    "confidence_percent": 56.0
  },
  "uncertainty": {
    "bucket": "medium_confidence",
    "confidence": 0.56,
    "confidence_percent": 56.0,
    "label": "Medium model confidence",
    "explanation": "The model assigned a moderate probability to its top output. This is model confidence, not clinical certainty."
  },
  "safety_note": "Prototype educational output only. This response is not a diagnosis and does not recommend treatment.",
  "model_limitations": [
    "Predictions are model outputs from a finite taxonomy, not clinical conclusions.",
    "The lesion-routing class is not cancer detection.",
    "Confidence is model confidence, not clinical certainty."
  ],
  "recommended_next_step": "Use this output as a prototype aid for review, not as a standalone medical decision."
}
```

## Example: Future Dermoscopic Cancer-Risk Model

Labels below are placeholders for schema shape only. The final taxonomy should come from the model registry and `class_to_idx.json`.

```json
{
  "model_id": "dermoscopic_cancer_risk_v2",
  "model_name": "Dermoscopic cancer-risk prototype",
  "input_type": "dermoscopic",
  "architecture": "efficientnet_b0",
  "image_size": 224,
  "predictions": [
    {
      "rank": 1,
      "class_index": 2,
      "label": "placeholder_risk_group_c",
      "confidence": 0.48,
      "confidence_percent": 48.0
    },
    {
      "rank": 2,
      "class_index": 1,
      "label": "placeholder_risk_group_b",
      "confidence": 0.31,
      "confidence_percent": 31.0
    },
    {
      "rank": 3,
      "class_index": 0,
      "label": "placeholder_risk_group_a",
      "confidence": 0.15,
      "confidence_percent": 15.0
    }
  ],
  "top_prediction": {
    "rank": 1,
    "class_index": 2,
    "label": "placeholder_risk_group_c",
    "confidence": 0.48,
    "confidence_percent": 48.0
  },
  "uncertainty": {
    "bucket": "medium_confidence",
    "confidence": 0.48,
    "confidence_percent": 48.0,
    "label": "Medium model confidence",
    "explanation": "The model assigned a moderate probability to its top output. This is model confidence, not clinical certainty."
  },
  "safety_note": "Prototype educational output only. This response is not a diagnosis and does not recommend treatment.",
  "model_limitations": [
    "Predictions are model outputs from a finite taxonomy, not clinical conclusions.",
    "Confidence is model confidence, not clinical certainty.",
    "Dermoscopic model outputs require appropriate review context."
  ],
  "recommended_next_step": "Use this output as a prototype aid for review, not as a standalone medical decision."
}
```

## Smoke-Test Baseline Note

`dermoscopic_baseline_v1` is a 3-class BCN20000 smoke-test model. Its classes must not define final product behavior, copy, routing, or UI assumptions. Production behavior should be driven by the active model registry entry and its `class_to_idx.json`.
