from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from typing import Any


def get_top_k_predictions(
    probabilities,
    class_names: Sequence[str],
    top_k: int = 3,
) -> list[dict[str, float | int | str]]:
    """Convert 1D class probabilities into ranked prediction entries."""
    probability_values = _to_1d_float_list(probabilities)
    class_name_values = list(class_names)

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k must be a positive integer.")
    if len(probability_values) != len(class_name_values):
        raise ValueError(
            "class_names length must match probabilities length: "
            f"{len(class_name_values)} != {len(probability_values)}."
        )

    ranked_indices = sorted(
        range(len(probability_values)),
        key=lambda index: probability_values[index],
        reverse=True,
    )
    selected_indices = ranked_indices[: min(top_k, len(ranked_indices))]

    return [
        {
            "rank": rank,
            "class_index": class_index,
            "label": class_name_values[class_index],
            "confidence": probability_values[class_index],
            "confidence_percent": round(probability_values[class_index] * 100, 2),
        }
        for rank, class_index in enumerate(selected_indices, start=1)
    ]


def _to_1d_float_list(values) -> list[float]:
    if hasattr(values, "detach") and callable(values.detach):
        values = values.detach().cpu().tolist()
    elif hasattr(values, "tolist") and callable(values.tolist):
        values = values.tolist()

    if isinstance(values, (str, bytes)):
        raise TypeError("probabilities must be a 1D numeric sequence, not a string.")
    if not isinstance(values, Sequence):
        raise TypeError("probabilities must be a 1D numeric sequence.")

    probabilities = list(values)
    if any(isinstance(value, (list, tuple)) for value in probabilities):
        raise ValueError("probabilities must be 1D.")
    if any(_is_array_like(value) for value in probabilities):
        raise ValueError("probabilities must be 1D.")

    try:
        return [float(value) for value in probabilities]
    except (TypeError, ValueError) as error:
        raise TypeError("probabilities must contain numeric values.") from error


def _is_array_like(value: Any) -> bool:
    return hasattr(value, "tolist") and callable(value.tolist)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test top-k inference post-processing."
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Print a mocked top-k prediction example.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.example:
        raise SystemExit("Run with --example to print a mocked top-k example.")

    probabilities = [0.12, 0.8062, 0.0738]
    class_names = ["class_a", "class_b", "class_c"]
    top_predictions = get_top_k_predictions(probabilities, class_names, top_k=3)
    print(json.dumps(top_predictions, indent=2))


if __name__ == "__main__":
    main()
