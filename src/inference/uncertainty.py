from __future__ import annotations

import argparse
import json
from numbers import Real


DEFAULT_THRESHOLDS = {
    "high_confidence": 0.70,
    "medium_confidence": 0.40,
}


BUCKET_LABELS = {
    "high_confidence": "High model confidence",
    "medium_confidence": "Medium model confidence",
    "low_confidence": "Low model confidence",
}


BUCKET_EXPLANATIONS = {
    "high_confidence": (
        "The model assigned a relatively high probability to its top output. "
        "This is model confidence, not clinical certainty."
    ),
    "medium_confidence": (
        "The model assigned a moderate probability to its top output. "
        "This is model confidence, not clinical certainty."
    ),
    "low_confidence": (
        "The model assigned a low probability to its top output. "
        "This is model confidence, not clinical certainty."
    ),
}


def get_uncertainty_bucket(confidence: float, thresholds: dict | None = None) -> dict:
    """Convert a top-1 confidence score into a generic uncertainty bucket."""
    confidence_value = _validate_confidence(confidence)
    threshold_values = _validate_thresholds(thresholds or DEFAULT_THRESHOLDS)

    if confidence_value >= threshold_values["high_confidence"]:
        bucket = "high_confidence"
    elif confidence_value >= threshold_values["medium_confidence"]:
        bucket = "medium_confidence"
    else:
        bucket = "low_confidence"

    return {
        "bucket": bucket,
        "confidence": confidence_value,
        "confidence_percent": round(confidence_value * 100, 2),
        "label": BUCKET_LABELS[bucket],
        "explanation": BUCKET_EXPLANATIONS[bucket],
    }


def _validate_confidence(confidence: float) -> float:
    if isinstance(confidence, bool) or not isinstance(confidence, Real):
        raise TypeError("confidence must be numeric.")

    confidence_value = float(confidence)
    if confidence_value < 0.0 or confidence_value > 1.0:
        raise ValueError("confidence must be between 0 and 1 inclusive.")
    return confidence_value


def _validate_thresholds(thresholds: dict) -> dict[str, float]:
    required_keys = ["high_confidence", "medium_confidence"]
    missing_keys = [key for key in required_keys if key not in thresholds]
    if missing_keys:
        missing_text = ", ".join(missing_keys)
        raise KeyError(f"thresholds is missing required keys: {missing_text}")

    high_threshold = _validate_confidence(thresholds["high_confidence"])
    medium_threshold = _validate_confidence(thresholds["medium_confidence"])
    if medium_threshold > high_threshold:
        raise ValueError(
            "thresholds['medium_confidence'] must be less than or equal to "
            "thresholds['high_confidence']."
        )

    return {
        "high_confidence": high_threshold,
        "medium_confidence": medium_threshold,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test generic model-confidence uncertainty buckets."
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Print example buckets for representative confidence values.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=None,
        help="Print the uncertainty bucket for one confidence value.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.example:
        examples = [
            get_uncertainty_bucket(0.8062),
            get_uncertainty_bucket(0.55),
            get_uncertainty_bucket(0.24),
        ]
        print(json.dumps(examples, indent=2))
        return

    if args.confidence is not None:
        print(json.dumps(get_uncertainty_bucket(args.confidence), indent=2))
        return

    raise SystemExit("Run with --example or --confidence <value>.")


if __name__ == "__main__":
    main()
