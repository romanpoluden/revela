# Two-Model Inference Strategy

Issue: #123 - D3.7: Update inference and app schema for dermoscopic cancer-risk model

## Purpose

Revela should use a two-model strategy because clinical photos and dermoscopic images are different visual domains with different product roles. The app should not silently send every image through one universal model, and it should not expose legacy smoke-test behavior as if it were the final product.

This document defines the intended app-level inference behavior for a polished Streamlit demo and future app layer. It does not implement Streamlit, change model code, change taxonomy, or claim clinical readiness.

Revela remains an educational dermatology AI training aid. It is not a diagnostic product, not treatment guidance, and not clinically validated.

## Current Model Roles

| Model ID / artifact | Input type | Role | Status |
|---|---|---|---|
| `clinical_skin_condition_v1` / `clinical_v2_effnet_b0` | Clinical photo | Clinical-photo condition/routing model | Trained and evaluated |
| `dermoscopic_cancer_risk_v2` | Dermoscopic image | Future dermoscopic cancer-risk model | Planned / retraining and evaluation dependent |
| `dermoscopic_baseline_v1` | Dermoscopic image | Developer smoke-test model only | Not public product behavior |

The current registry alias for the clinical model is `clinical_skin_condition_v1`, backed by `models/clinical_v2_effnet_b0/`. The old `dermoscopic_baseline_v1` is useful for validating local inference plumbing, but its old 3-class taxonomy must not drive public UI, copy, routing, or demo claims.

## User-Facing Input Modes

The app should offer explicit image-type modes:

1. Clinical photo
2. Dermoscopic image

The user should choose the mode before upload or be shown a clear segmented control/tab structure. The app should not infer image type silently unless a separate image-type classifier is later built and evaluated.

## Model Selection Logic

| User mode | Model behavior |
|---|---|
| Clinical photo | Run `clinical_skin_condition_v1` |
| Dermoscopic image | Run `dermoscopic_cancer_risk_v2` once available |
| Dermoscopic image before `dermoscopic_cancer_risk_v2` is available | Disable dermoscopic analysis or show "coming soon / not available" |

The public UI should not fall back to `dermoscopic_baseline_v1`. That model can remain available to developers for smoke tests such as checking model loading, preprocessing, top-k formatting, uncertainty buckets, and response schema assembly.

## Clinical Model Behavior

The clinical model currently has five classes:

1. `Eczema / dermatitis`
2. `Urticaria / allergic reaction`
3. `Folliculitis / acne-like`
4. `Psoriasis / papulosquamous`
5. `Lesion — dermoscopic review recommended`

Common-condition classes should produce educational, condition-oriented output. The app can say that the image is most similar to a class in the model taxonomy, show the top predictions, and explain that confidence is model confidence.

The app should say:

- "The model output is most aligned with `<class label>` in this prototype taxonomy."
- "This is educational model output, not diagnosis."
- "Confidence is model confidence, not clinical certainty."
- "Review image quality, context, and differential possibilities."

The app should not say:

- "You have `<class label>`."
- "This diagnoses `<class label>`."
- "Treatment is..."
- "No clinician review is needed."
- "The model is clinically validated."

### Clinical Lesion-Routing Class

`Lesion — dermoscopic review recommended` is a routing class. It is not cancer detection, not melanoma detection, and not a malignancy label.

The app may say:

- "This clinical-photo output routes the case toward dermoscopic review in the prototype workflow."
- "This class means the model found the image closer to the lesion-routing class than to the common-condition classes."
- "A dermoscopic image may be useful for the next educational review step when the dermoscopic model is available."

The app must not say:

- "Cancer detected."
- "Melanoma detected."
- "High cancer risk."
- "This lesion is malignant."

## Dermoscopic Cancer-Risk Model Behavior

The planned dermoscopic model is `dermoscopic_cancer_risk_v2`. Its expected 4-class taxonomy is:

1. `Melanoma`
2. `Non-melanoma skin cancer`
3. `Benign nevus`
4. `Other non-cancer / indeterminate lesion`

The output should be framed as an educational cancer-risk category from a dermoscopic model, not a clinical diagnosis. Final wording and UI emphasis depend on #119 retraining and #120 evaluation, especially cancer/malignant recall, melanoma recall, false-negative behavior, macro-F1, balanced accuracy, and confusion matrix review.

The fourth class must remain `Other non-cancer / indeterminate lesion`. Do not rename it to "safe", "benign", or "low risk" because it can include pre-malignant or indeterminate cases.

## Public App Behavior Before Dermoscopic Model Is Ready

Before `dermoscopic_cancer_risk_v2` artifacts and evaluation are available, the public app should:

- Hide the dermoscopic mode, or
- Show dermoscopic mode as disabled / coming soon, or
- Show a non-inference placeholder explaining that dermoscopic analysis is not available in this build.

The public app should not expose `dermoscopic_baseline_v1`. The baseline may be used only by developers for smoke tests and local plumbing validation.

## Canonical Response Schema Alignment

The app-facing inference adapter should use the canonical response schema from `docs/model/inference_response_schema.md`.

Required success fields:

- `model_id`
- `input_type`
- `predictions`
- `top_prediction`
- `uncertainty`
- `safety_note`
- `model_limitations`
- `recommended_next_step`

The existing local pipeline already supports:

- model loading via registry
- single-image prediction
- top-k predictions
- uncertainty bucket
- canonical response construction
- local inference adapter

The app should consume the canonical response rather than rebuilding model-specific response shapes in the UI.

## Streamlit UI Implications

A polished Streamlit demo can use this structure:

- Page header: short educational product framing and prototype limitation.
- Main tabs or segmented control:
  - `Clinical photo`
  - `Dermoscopic image`
- Upload panel inside each mode.
- Results panel:
  - top prediction
  - top-k predictions
  - confidence / uncertainty bucket
  - concise safety note
  - model limitations
- Transparency panel:
  - active model ID
  - input type
  - taxonomy
  - evaluation summary link or compact metrics
- "About the model" expander:
  - dataset notes
  - held-out metrics
  - known limitations

Warnings should be visible but not overwhelming. Use one persistent safety note near the result, plus an expandable details section for limitations and metrics. Avoid repeating alarming copy after every prediction line.

Clinical metrics can reference the current evaluation summary:

- Combined accuracy: 0.6554
- Macro-F1: 0.6420
- Balanced accuracy: 0.6571
- Lesion-routing F1: 0.8282

These should be presented as prototype evaluation metrics, not clinical validation.

## Safety Wording Rules

Always follow these rules:

- Do not claim diagnosis.
- Do not provide treatment advice.
- Do not claim clinical certainty.
- Do not claim clinical validation.
- Say confidence is model confidence, not clinical certainty.
- Say clinical lesion-routing is not cancer detection.
- Say dermoscopic cancer-risk output is not clinical diagnosis.
- Do not claim the model detects all melanoma or all cancer cases.
- Do not treat `Other non-cancer / indeterminate lesion` as "safe".

## Example Response Narratives

### Clinical Common-Condition Result

"The model's top educational output is `Eczema / dermatitis` with medium model confidence. This means the image is most aligned with that class in the current prototype taxonomy. This is not a diagnosis, and confidence is not clinical certainty. Review the image context and the other ranked outputs."

### Clinical Lesion-Routing Result

"The model's top educational output is `Lesion — dermoscopic review recommended`. In this prototype, that is a routing output suggesting that dermoscopic review may be the appropriate next educational step when available. This is not cancer detection, not melanoma detection, and not a diagnosis."

### Dermoscopic Cancer-Risk Placeholder

"The dermoscopic model will return an educational cancer-risk category such as `Melanoma`, `Non-melanoma skin cancer`, `Benign nevus`, or `Other non-cancer / indeterminate lesion`. The result should be presented as a model output for learning and review, not as a clinical diagnosis. Final wording depends on retraining and held-out evaluation."

### Unsupported Dermoscopic Mode

"Dermoscopic analysis is not available in this demo build yet. The production-facing app should not use the old smoke-test dermoscopic baseline. Please use the clinical-photo mode or wait until the dermoscopic cancer-risk model has been trained and evaluated."

## Open Questions And Dependencies

- #119: Retrain dermoscopic CNN using the finalized cancer-risk taxonomy.
- #120: Evaluate the dermoscopic cancer-risk CNN, including melanoma/cancer recall and false-negative behavior.
- #131: Perform clinical model error analysis by source, class, and raw label.
- #132/#133: Improve clinical model performance after error analysis.
- Decide exactly how the Streamlit demo should expose disabled dermoscopic mode before `dermoscopic_cancer_risk_v2` is ready.
- Decide whether model metrics appear inline on the result page or in a separate transparency/about panel.

## Implementation Boundary

This document does not require code changes. The current local inference plumbing should remain generic and registry-driven. Streamlit can be implemented later against the local adapter without changing the model response contract.
