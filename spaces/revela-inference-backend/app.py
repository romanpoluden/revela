from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from huggingface_hub import hf_hub_download
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel
from torchvision import models, transforms


LOGGER = logging.getLogger("revela_backend")
logging.basicConfig(level=logging.INFO)

APP_VERSION = "d9.1-hf-fastapi-backend-v1"
MODEL_ROOT = Path("/tmp/revela_models")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


@dataclass(frozen=True)
class ModelConfig:
    model_id: str
    repo_id: str
    input_type: str
    architecture: str
    image_size: int
    top_k_default: int
    max_top_k: int
    local_dir: Path


MODEL_CONFIGS: dict[str, ModelConfig] = {
    "clinical_skin_condition_v1": ModelConfig(
        model_id="clinical_skin_condition_v1",
        repo_id="RevelaCap/clinical-skin-condition-v1",
        input_type="clinical",
        architecture="efficientnet_b0",
        image_size=224,
        top_k_default=3,
        max_top_k=5,
        local_dir=MODEL_ROOT / "clinical_v2_effnet_b0",
    ),
    "dermoscopic_cancer_risk_bcn_mnh_v1": ModelConfig(
        model_id="dermoscopic_cancer_risk_bcn_mnh_v1",
        repo_id="RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1",
        input_type="dermoscopic",
        architecture="efficientnet_b0",
        image_size=224,
        top_k_default=4,
        max_top_k=4,
        local_dir=MODEL_ROOT / "bcn_mnh_cancer_risk_effnet_b0",
    ),
}


class Prediction(BaseModel):
    rank: int
    class_index: int
    label: str
    confidence: float
    confidence_percent: float


class HealthResponse(BaseModel):
    status: str
    version: str
    device: str
    supported_model_ids: list[str]
    loaded_model_ids: list[str]


class LoadedModel:
    def __init__(self, config: ModelConfig, model: nn.Module, class_names: list[str]) -> None:
        self.config = config
        self.model = model
        self.class_names = class_names


LOADED_MODELS: dict[str, LoadedModel] = {}

app = FastAPI(
    title="Revela Inference Backend",
    version=APP_VERSION,
    description="Educational prototype inference backend. Not diagnostic.",
)


def create_model(num_classes: int) -> nn.Module:
    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


def resolve_artifacts(config: ModelConfig) -> tuple[Path, Path]:
    config.local_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = config.local_dir / "best_model.pth"
    class_to_idx_path = config.local_dir / "class_to_idx.json"

    if checkpoint_path.exists() and class_to_idx_path.exists():
        return checkpoint_path, class_to_idx_path

    for filename in ("best_model.pth", "class_to_idx.json"):
        LOGGER.info("Downloading %s from %s", filename, config.repo_id)
        hf_hub_download(
            repo_id=config.repo_id,
            filename=filename,
            local_dir=str(config.local_dir),
            local_dir_use_symlinks=False,
        )

    return checkpoint_path, class_to_idx_path


def load_class_names(class_to_idx_path: Path) -> list[str]:
    import json

    with class_to_idx_path.open("r", encoding="utf-8") as file:
        class_to_idx = json.load(file)

    if not isinstance(class_to_idx, dict) or not class_to_idx:
        raise ValueError(f"Invalid class_to_idx mapping: {class_to_idx_path}")

    return [name for name, _ in sorted(class_to_idx.items(), key=lambda item: int(item[1]))]


def load_model(model_id: str) -> LoadedModel:
    if model_id in LOADED_MODELS:
        return LOADED_MODELS[model_id]

    config = MODEL_CONFIGS.get(model_id)
    if config is None:
        raise HTTPException(status_code=400, detail=f"Unsupported model_id: {model_id}")

    try:
        checkpoint_path, class_to_idx_path = resolve_artifacts(config)
        class_names = load_class_names(class_to_idx_path)
        checkpoint = torch.load(checkpoint_path, map_location=DEVICE)

        if "model_state_dict" not in checkpoint:
            raise KeyError("Checkpoint missing model_state_dict")

        model = create_model(num_classes=len(class_names))
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(DEVICE)
        model.eval()

    except HTTPException:
        raise
    except Exception as error:
        LOGGER.exception("Failed to load model %s", model_id)
        raise HTTPException(status_code=500, detail=f"Could not load model artifacts for {model_id}") from error

    loaded = LoadedModel(config=config, model=model, class_names=class_names)
    LOADED_MODELS[model_id] = loaded
    LOGGER.info("Loaded model %s on %s", model_id, DEVICE)
    return loaded


def preprocess_image(image: Image.Image, image_size: int) -> torch.Tensor:
    transform = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    return transform(image).unsqueeze(0).to(DEVICE)


def read_image(upload: UploadFile) -> Image.Image:
    try:
        image_bytes = upload.file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image is empty")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return image
    except HTTPException:
        raise
    except UnidentifiedImageError as error:
        raise HTTPException(status_code=400, detail="Uploaded file is not a readable image") from error
    except Exception as error:
        LOGGER.exception("Failed to read uploaded image")
        raise HTTPException(status_code=400, detail="Could not read uploaded image") from error


def uncertainty_from_confidence(confidence: float) -> dict[str, Any]:
    confidence_percent = round(confidence * 100, 2)
    if confidence < 0.4:
        bucket = "low_confidence"
        label = "Low model confidence"
        explanation = "The model did not assign a strong probability to its top output. This is model confidence, not clinical certainty."
    elif confidence < 0.7:
        bucket = "medium_confidence"
        label = "Medium model confidence"
        explanation = "The model assigned a moderate probability to its top output. This is model confidence, not clinical certainty."
    else:
        bucket = "high_confidence"
        label = "High model confidence"
        explanation = "The model assigned a relatively high probability to its top output. This is model confidence, not clinical certainty."

    return {
        "bucket": bucket,
        "confidence": confidence,
        "confidence_percent": confidence_percent,
        "label": label,
        "explanation": explanation,
    }


def build_response(loaded: LoadedModel, probabilities: torch.Tensor, top_k: int) -> dict[str, Any]:
    config = loaded.config
    k = max(1, min(top_k, config.max_top_k, len(loaded.class_names)))
    top_probabilities, top_indices = torch.topk(probabilities, k=k)

    predictions: list[dict[str, Any]] = []
    for rank, (probability, index) in enumerate(zip(top_probabilities.tolist(), top_indices.tolist()), start=1):
        predictions.append(
            {
                "rank": rank,
                "class_index": int(index),
                "label": loaded.class_names[int(index)],
                "confidence": float(probability),
                "confidence_percent": round(float(probability) * 100, 2),
            }
        )

    top_prediction = predictions[0]
    confidence = float(top_prediction["confidence"])
    uncertainty = uncertainty_from_confidence(confidence)
    low_certainty_threshold = 0.6
    low_certainty = confidence < low_certainty_threshold or uncertainty["bucket"] == "low_confidence"

    return {
        "model_id": config.model_id,
        "model_name": None,
        "input_type": config.input_type,
        "architecture": config.architecture,
        "image_size": config.image_size,
        "predictions": predictions,
        "top_prediction": top_prediction,
        "uncertainty": uncertainty,
        "low_certainty": low_certainty,
        "low_certainty_reason": (
            f"Top model confidence {top_prediction['confidence_percent']}% is below the conservative 60% low-certainty threshold."
            if low_certainty
            else None
        ),
        "low_certainty_message": (
            "The model output is uncertain. Use this only for educational review. Review the top outputs, image quality, and clinical context, and consider additional image/context review. This is not a diagnosis and does not recommend treatment."
            if low_certainty
            else None
        ),
        "low_certainty_rule": "low_certainty is true when top confidence is below 0.60 (60%) or uncertainty.bucket is low_confidence.",
        "low_certainty_threshold": low_certainty_threshold,
        "safety_note": "Prototype educational output only. This response is not a diagnosis and does not recommend treatment.",
        "model_limitations": [
            "Predictions are model outputs from a finite taxonomy, not clinical conclusions.",
            "Confidence is model confidence, not clinical certainty.",
            "Performance may vary across image quality, skin tone, lighting, and source dataset.",
        ],
        "recommended_next_step": "Use this output as a prototype aid for review, not as a standalone medical decision.",
    }


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        device=str(DEVICE),
        supported_model_ids=list(MODEL_CONFIGS.keys()),
        loaded_model_ids=list(LOADED_MODELS.keys()),
    )


@app.post("/predict")
def predict(
    model_id: str = Form(...),
    top_k: int | None = Form(None),
    image: UploadFile = File(...),
) -> dict[str, Any]:
    loaded = load_model(model_id)
    selected_top_k = top_k if top_k is not None else loaded.config.top_k_default

    if selected_top_k < 1:
        raise HTTPException(status_code=400, detail="top_k must be at least 1")

    pil_image = read_image(image)
    tensor = preprocess_image(pil_image, loaded.config.image_size)

    with torch.no_grad():
        logits = loaded.model(tensor)
        probabilities = torch.softmax(logits, dim=1).squeeze(0).cpu()

    return build_response(loaded, probabilities, selected_top_k)
