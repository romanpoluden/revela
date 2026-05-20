"""Smoke test for dermoscopic_cancer_risk_bcn_mnh_v1 local inference — D5.1 (#163).

Run from repo root:
    python scripts/smoke_test_dermoscopic_inference.py
    python scripts/smoke_test_dermoscopic_inference.py --image path/to/image.jpg
    python scripts/smoke_test_dermoscopic_inference.py --model-id dermoscopic_cancer_risk_bcn_mnh_v1
"""
from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, ".")  # must be run from repo root

from src.inference.adapter import run_inference

_DEFAULT_IMAGE = "data/mel_nevus_histo/images/ISIC_0000002.jpg"
_DEFAULT_MODEL = "dermoscopic_cancer_risk_bcn_mnh_v1"

REQUIRED_FIELDS = [
    "model_id",
    "input_type",
    "architecture",
    "image_size",
    "predictions",
    "top_prediction",
    "uncertainty",
    "safety_note",
    "model_limitations",
    "recommended_next_step",
]

REQUIRED_CLASSES = [
    "Melanoma",
    "Non-melanoma skin cancer",
    "Benign nevus",
    "Other non-cancer / indeterminate lesion",
]

FORBIDDEN_PHRASES = [
    "cancer detected",
    "melanoma detected",
    "diagnosis confirmed",
    "benign / safe certainty",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test dermoscopic inference.")
    parser.add_argument(
        "--image",
        default=_DEFAULT_IMAGE,
        help=f"Path to a dermoscopic image (default: {_DEFAULT_IMAGE})",
    )
    parser.add_argument(
        "--model-id",
        default=_DEFAULT_MODEL,
        help=f"Registry model ID to test (default: {_DEFAULT_MODEL})",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    TEST_IMAGE = args.image
    MODEL_ID = args.model_id

    print(f"Model:  {MODEL_ID}")
    print(f"Image:  {TEST_IMAGE}")
    print()

    result = run_inference(image_input=TEST_IMAGE, model_id=MODEL_ID, top_k=4)

    if result.get("error"):
        print("FAIL — inference returned error response:")
        print(json.dumps(result, indent=2))
        raise SystemExit(1)

    for field in REQUIRED_FIELDS:
        assert field in result, f"Missing field in response: {field}"
    print("Schema fields:     PASS")

    assert len(result["predictions"]) == 4, (
        f"Expected 4 predictions, got {len(result['predictions'])}"
    )
    pred_classes = [p["label"] for p in result["predictions"]]
    for cls in REQUIRED_CLASSES:
        assert cls in pred_classes, f"Missing class in predictions: {cls}"
    for pred in result["predictions"]:
        assert 0.0 <= pred["confidence"] <= 1.0, (
            f"Confidence out of range: {pred}"
        )
    print("Predictions:       PASS (4 classes, confidences in range)")

    response_text = json.dumps(result).lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase.lower() not in response_text, (
            f"Forbidden phrase found in response: '{phrase}'"
        )
    print("Safety wording:    PASS (no forbidden phrases)")

    # Invalid input handling
    bad = run_inference(image_input="nonexistent.jpg", model_id=MODEL_ID)
    assert bad.get("error") is True, (
        "Invalid input did not return safe error response"
    )
    assert "error_code" in bad, "Error response missing error_code"
    print("Error handling:    PASS (safe error response confirmed)")

    print()
    print("Smoke test PASSED")
    print()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
