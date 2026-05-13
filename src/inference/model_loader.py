from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn

from src.inference.model_registry import get_model_config
from src.model.model import create_model


@dataclass
class LoadedModel:
    """All metadata and state for a loaded model from the registry."""
    model: nn.Module
    class_names: list[str]
    device: torch.device
    model_id: str
    input_type: str
    architecture: str
    num_classes: int
    checkpoint_path: str
    class_to_idx_path: str
    image_size: int


def select_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _load_class_to_idx(path: Path) -> dict[str, int]:
    if not path.exists():
        raise FileNotFoundError(f"class_to_idx not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        mapping = json.load(f)
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError(f"class_to_idx must be a non-empty JSON object: {path}")
    return {str(k): int(v) for k, v in mapping.items()}


def load_model_from_registry(
    model_id: str,
    *,
    project_root: Optional[Path] = None,
    device: Optional[torch.device] = None,
) -> LoadedModel:
    """
    Load a model by model_id using the registry.

    Resolves all paths relative to project_root (defaults to the repo root
    inferred from this file's location). Supports CUDA, MPS, and CPU.

    Returns a LoadedModel carrying the loaded nn.Module plus all registry
    metadata (model_id, input_type, architecture, num_classes, checkpoint_path,
    class_to_idx_path, image_size, class_names).

    Raises FileNotFoundError if the checkpoint or class_to_idx file is missing.
    Raises KeyError if model_id is not in the registry.
    """
    config = get_model_config(model_id)
    architecture = config["architecture"]
    if architecture != "efficientnet_b0":
        raise NotImplementedError(
            f"Model '{model_id}' declares architecture '{architecture}', but the "
            "registry loader currently supports only 'efficientnet_b0'."
        )

    root = project_root or Path(__file__).resolve().parents[2]

    checkpoint_path = root / config["checkpoint_path"]
    class_to_idx_path = root / config["class_to_idx_path"]

    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found for '{model_id}': {checkpoint_path}\n"
            "Run training before loading this model."
        )

    class_to_idx = _load_class_to_idx(class_to_idx_path)
    class_names = [name for name, _ in sorted(class_to_idx.items(), key=lambda x: x[1])]

    # num_classes=None in the registry means infer from class_to_idx
    num_classes = config["num_classes"]
    if num_classes is None:
        num_classes = len(class_names)
    elif num_classes != len(class_names):
        raise ValueError(
            f"Registry num_classes={num_classes} does not match "
            f"class_to_idx size={len(class_names)} for '{model_id}'."
        )

    if device is None:
        device = select_device()

    checkpoint = torch.load(checkpoint_path, map_location=device)
    if "model_state_dict" not in checkpoint:
        raise KeyError(f"Checkpoint for '{model_id}' is missing 'model_state_dict'.")

    model = create_model(num_classes=num_classes, pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    return LoadedModel(
        model=model,
        class_names=class_names,
        device=device,
        model_id=model_id,
        input_type=config["input_type"],
        architecture=architecture,
        num_classes=num_classes,
        checkpoint_path=str(checkpoint_path),
        class_to_idx_path=str(class_to_idx_path),
        image_size=config["image_size"],
    )
