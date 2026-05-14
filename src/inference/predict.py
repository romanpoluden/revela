from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import BinaryIO

import torch
from PIL import Image, UnidentifiedImageError

from src.data.transforms import get_eval_transforms
from src.inference.model_loader import load_model_from_registry
from src.inference.postprocess import get_top_k_predictions


class ImageInputError(ValueError):
    """Raised when an image input cannot be opened as a valid image."""


def predict_image(
    model_id: str,
    image_input: str | Path | Image.Image | BinaryIO,
    project_root: str | Path | None = None,
    device: str | torch.device | None = None,
) -> dict:
    """
    Run taxonomy-agnostic single-image inference for a registered model.

    The model taxonomy, checkpoint, architecture, and image size are resolved via
    the model registry. The returned dictionary is JSON-serializable.
    """
    resolved_device = _resolve_device(device)
    resolved_project_root = Path(project_root) if project_root is not None else None
    loaded_model = load_model_from_registry(
        model_id,
        project_root=resolved_project_root,
        device=resolved_device,
    )

    image = _load_rgb_image(image_input)
    transform = get_eval_transforms(loaded_model.image_size)
    image_tensor = transform(image).unsqueeze(0).to(loaded_model.device)

    loaded_model.model.eval()
    with torch.no_grad():
        logits_tensor = loaded_model.model(image_tensor).squeeze(0).detach().cpu()
        probabilities_tensor = torch.softmax(logits_tensor, dim=0)

    logits = [float(value) for value in logits_tensor.tolist()]
    probabilities = [float(value) for value in probabilities_tensor.tolist()]
    predicted_class_index = int(probabilities_tensor.argmax().item())

    if predicted_class_index >= len(loaded_model.class_names):
        raise RuntimeError(
            "Predicted class index is outside the loaded model class mapping."
        )

    return {
        "model_id": loaded_model.model_id,
        "input_type": loaded_model.input_type,
        "architecture": loaded_model.architecture,
        "image_size": loaded_model.image_size,
        "device": str(loaded_model.device),
        "class_names": list(loaded_model.class_names),
        "logits": logits,
        "probabilities": probabilities,
        "predicted_class_index": predicted_class_index,
        "predicted_class_label": loaded_model.class_names[predicted_class_index],
        "predicted_confidence": probabilities[predicted_class_index],
    }


def _resolve_device(device: str | torch.device | None) -> torch.device | None:
    if device is None:
        return None
    if isinstance(device, torch.device):
        return device
    return torch.device(device)


def _load_rgb_image(image_input: str | Path | Image.Image | BinaryIO) -> Image.Image:
    if isinstance(image_input, Image.Image):
        return image_input.convert("RGB")

    if isinstance(image_input, (str, Path)):
        image_path = Path(image_input)
        if not image_path.exists():
            raise ImageInputError(f"Image file not found: {image_path}")
        if not image_path.is_file():
            raise ImageInputError(f"Image path is not a file: {image_path}")

        try:
            with Image.open(image_path) as image:
                return image.convert("RGB")
        except UnidentifiedImageError as error:
            raise ImageInputError(f"Could not identify image file: {image_path}") from error
        except OSError as error:
            raise ImageInputError(f"Could not read image file: {image_path}") from error

    if hasattr(image_input, "read"):
        try:
            with Image.open(image_input) as image:
                return image.convert("RGB")
        except UnidentifiedImageError as error:
            raise ImageInputError("Could not identify image from file-like input.") from error
        except OSError as error:
            raise ImageInputError("Could not read image from file-like input.") from error

    raise TypeError(
        "image_input must be a path string, pathlib.Path, PIL.Image.Image, or file-like object."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run single-image inference for a registered Revela model."
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
        "--top-k",
        type=int,
        default=None,
        help="Optionally include top-k prediction entries in CLI JSON output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        result = predict_image(
            model_id=args.model_id,
            image_input=args.image,
            project_root=args.project_root,
            device=args.device,
        )
        if args.top_k is not None:
            result["top_predictions"] = get_top_k_predictions(
                probabilities=result["probabilities"],
                class_names=result["class_names"],
                top_k=args.top_k,
            )
    except (ImageInputError, FileNotFoundError, KeyError, RuntimeError, ValueError, TypeError) as error:
        print(f"Prediction failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
