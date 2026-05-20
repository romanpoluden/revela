from __future__ import annotations

import argparse
import json
from typing import Any

from src.inference.postprocess import get_top_k_predictions
from src.inference.uncertainty import (
    get_low_certainty_handling,
    get_uncertainty_bucket,
)


DEFAULT_SAFETY_NOTE = (
    "Prototype educational output only. This response is not a diagnosis and "
    "does not recommend treatment."
)
DEFAULT_MODEL_LIMITATIONS = [
    "Predictions are model outputs from a finite taxonomy, not clinical conclusions.",
    "Confidence is model confidence, not clinical certainty.",
    "Performance may vary across image quality, skin tone, lighting, and source dataset.",
]
DEFAULT_RECOMMENDED_NEXT_STEP = (
    "Use this output as a prototype aid for review, not as a standalone medical decision."
)


def build_success_response(
    prediction_result: dict,
    top_k: int = 3,
    safety_note: str | None = None,
    model_limitations: list[str] | None = None,
    recommended_next_step: str | None = None,
) -> dict[str, Any]:
    """Build the canonical JSON-serializable inference success response."""
    required_keys = [
        "model_id",
        "input_type",
        "architecture",
        "image_size",
        "class_names",
        "probabilities",
        "predicted_class_index",
        "predicted_class_label",
        "predicted_confidence",
    ]
    missing_keys = [key for key in required_keys if key not in prediction_result]
    if missing_keys:
        missing_text = ", ".join(missing_keys)
        raise KeyError(f"prediction_result is missing required keys: {missing_text}")

    predictions = get_top_k_predictions(
        probabilities=prediction_result["probabilities"],
        class_names=prediction_result["class_names"],
        top_k=top_k,
    )
    top_prediction = predictions[0] if predictions else None
    uncertainty = get_uncertainty_bucket(
        confidence=prediction_result["predicted_confidence"]
    )
    low_certainty_handling = get_low_certainty_handling(
        top_confidence=prediction_result["predicted_confidence"],
        uncertainty_bucket=uncertainty["bucket"],
    )

    return {
        "model_id": prediction_result["model_id"],
        "model_name": prediction_result.get("model_name"),
        "input_type": prediction_result["input_type"],
        "architecture": prediction_result["architecture"],
        "image_size": prediction_result["image_size"],
        "predictions": predictions,
        "top_prediction": top_prediction,
        "uncertainty": uncertainty,
        "low_certainty": low_certainty_handling["low_certainty"],
        "low_certainty_reason": low_certainty_handling["low_certainty_reason"],
        "low_certainty_message": low_certainty_handling["low_certainty_message"],
        "low_certainty_rule": low_certainty_handling["rule"],
        "low_certainty_threshold": low_certainty_handling["threshold"],
        "safety_note": safety_note or DEFAULT_SAFETY_NOTE,
        "model_limitations": model_limitations or list(DEFAULT_MODEL_LIMITATIONS),
        "recommended_next_step": recommended_next_step
        or DEFAULT_RECOMMENDED_NEXT_STEP,
    }


def build_error_response(
    error_code: str,
    message: str,
    details: dict | list | str | None = None,
) -> dict[str, Any]:
    """Build the canonical JSON-serializable inference error response."""
    return {
        "error": True,
        "error_code": str(error_code),
        "message": str(message),
        "details": details,
    }


def _example_prediction_result() -> dict:
    return {
        "model_id": "clinical_skin_condition_v1",
        "model_name": "Clinical skin condition prototype",
        "input_type": "clinical",
        "architecture": "efficientnet_b0",
        "image_size": 224,
        "class_names": [
            "Eczema / dermatitis",
            "Urticaria / allergic reaction",
            "Folliculitis / acne-like",
            "Psoriasis / papulosquamous",
            "Lesion — dermoscopic review recommended",
        ],
        "probabilities": [0.08, 0.11, 0.07, 0.18, 0.56],
        "predicted_class_index": 4,
        "predicted_class_label": "Lesion — dermoscopic review recommended",
        "predicted_confidence": 0.56,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print an example canonical inference response."
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Print a mocked success and error response example.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.example:
        raise SystemExit("Run with --example to print mocked response examples.")

    payload = {
        "success": build_success_response(_example_prediction_result(), top_k=3),
        "error": build_error_response(
            error_code="invalid_image",
            message="The uploaded file could not be read as an image.",
            details={"accepted_inputs": ["path", "PIL.Image", "file-like object"]},
        ),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
