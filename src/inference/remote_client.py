from __future__ import annotations

import io
import os
from typing import Any

from PIL import Image
import requests


DEFAULT_BACKEND_URL = "https://revelacap-revela-inference-backend.hf.space"


class RemoteInferenceError(RuntimeError):
    """Raised when the remote inference backend cannot return a valid response."""


def get_backend_url() -> str:
    """Resolve the remote inference backend URL from env or default demo backend."""
    return os.getenv("REVELA_INFERENCE_BACKEND_URL", DEFAULT_BACKEND_URL).rstrip("/")


def run_remote_inference(
    *,
    model_id: str,
    image_input: Image.Image,
    top_k: int,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """
    Call the Hugging Face FastAPI inference backend.

    This is the primary deployed-demo inference path for Streamlit.
    It keeps Streamlit as frontend and runs PyTorch inference remotely.
    """

    backend_url = get_backend_url()
    endpoint = f"{backend_url}/predict"

    buffer = io.BytesIO()
    image_input.convert("RGB").save(buffer, format="PNG")
    buffer.seek(0)

    files = {
        "image": ("image.png", buffer, "image/png"),
    }
    data = {
        "model_id": model_id,
        "top_k": str(top_k),
    }

    try:
        response = requests.post(
            endpoint,
            data=data,
            files=files,
            timeout=timeout_seconds,
        )
    except requests.RequestException as error:
        raise RemoteInferenceError(
            f"Remote inference backend is unavailable: {error}"
        ) from error

    if response.status_code >= 400:
        raise RemoteInferenceError(
            f"Remote inference backend returned HTTP {response.status_code}: {response.text}"
        )

    try:
        payload = response.json()
    except ValueError as error:
        raise RemoteInferenceError(
            "Remote inference backend returned a non-JSON response."
        ) from error

    if not isinstance(payload, dict):
        raise RemoteInferenceError(
            "Remote inference backend returned an invalid response payload."
        )

    return payload
