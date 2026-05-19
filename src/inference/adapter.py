from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import BinaryIO

import torch
from PIL import Image

from src.inference.predict import ImageInputError, predict_image
from src.inference.response_schema import build_error_response, build_success_response


def run_inference(
    model_id: str,
    image_input: str | Path | Image.Image | BinaryIO,
    top_k: int = 3,
    project_root: str | Path | None = None,
    device: str | torch.device | None = None,
    debug: bool = False,
) -> dict:
    """
    Run local image inference and return the canonical response schema.

    In normal mode, expected failures are converted to JSON-serializable error
    responses. With debug=True, exceptions are re-raised for local development.
    """
    try:
        prediction_result = predict_image(
            model_id=model_id,
            image_input=image_input,
            project_root=project_root,
            device=device,
        )
        return build_success_response(
            prediction_result=prediction_result,
            top_k=top_k,
        )
    except Exception as error:
        if debug:
            raise
        return _build_expected_error_response(error)


def _build_expected_error_response(error: Exception) -> dict:
    error_code, message = _map_error(error)
    return build_error_response(
        error_code=error_code,
        message=message,
        details=None,
    )


def _map_error(error: Exception) -> tuple[str, str]:
    if isinstance(error, KeyError):
        if "Unknown model_id" not in str(error):
            return (
                "inference_failed",
                "Inference failed before a response could be completed.",
            )
        return (
            "unknown_model_id",
            "The requested model_id is not registered or the model metadata is unavailable.",
        )
    if isinstance(error, FileNotFoundError):
        return (
            "missing_model_artifact",
            "A required model artifact or input file could not be found.",
        )
    if isinstance(error, ImageInputError):
        return (
            "invalid_image",
            "The provided image input could not be read as a valid image.",
        )
    if isinstance(error, (TypeError, ValueError)):
        if _looks_like_postprocess_error(error):
            return (
                "postprocess_failed",
                "The model output could not be converted into the response schema.",
            )
        return (
            "invalid_input",
            "The provided inference input is invalid.",
        )
    return (
        "inference_failed",
        "Inference failed before a response could be completed.",
    )


def _looks_like_postprocess_error(error: Exception) -> bool:
    message = str(error)
    postprocess_markers = [
        "top_k",
        "probabilities",
        "class_names",
        "confidence",
        "prediction_result",
    ]
    return any(marker in message for marker in postprocess_markers)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local inference and print the canonical JSON response."
    )
    parser.add_argument(
        "--model-id",
        required=True,
        help="Model registry ID, for example dermoscopic_baseline_v1.",
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to the image to run inference on.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of ranked predictions to include.",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root for resolving registry paths.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Optional torch device override, for example cpu, cuda, or mps.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Re-raise exceptions instead of returning canonical error responses.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    response = run_inference(
        model_id=args.model_id,
        image_input=args.image,
        top_k=args.top_k,
        project_root=args.project_root,
        device=args.device,
        debug=args.debug,
    )
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
