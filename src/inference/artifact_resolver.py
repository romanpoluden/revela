from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.inference.model_registry import get_model_config


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class HostedModelArtifacts:
    """Hugging Face artifact metadata for a registered model."""

    repo_id: str
    required_files: tuple[str, ...]
    optional_files: tuple[str, ...] = ()


HOSTED_MODEL_ARTIFACTS: dict[str, HostedModelArtifacts] = {
    "clinical_skin_condition_v1": HostedModelArtifacts(
        repo_id="RevelaCap/clinical-skin-condition-v1",
        required_files=("best_model.pth", "class_to_idx.json"),
        optional_files=("training_history.csv",),
    ),
    "dermoscopic_cancer_risk_bcn_mnh_v1": HostedModelArtifacts(
        repo_id="RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1",
        required_files=("best_model.pth", "class_to_idx.json"),
        optional_files=("training_history.csv",),
    ),
}


def resolve_model_artifacts(
    model_id: str,
    *,
    project_root: Optional[Path] = None,
) -> dict[str, Path]:
    """
    Resolve required model artifacts for a registry model.

    Resolution is local-first. If the checkpoint and class mapping already exist
    at the paths declared in the model registry, nothing is downloaded. If either
    required file is missing and the model has a configured Hugging Face repo,
    the required files are downloaded into the expected local model directory.

    This helper intentionally does not change the model registry or prediction
    schema. It only makes the existing registry paths available at runtime.
    """

    root = project_root or Path(__file__).resolve().parents[2]
    config = get_model_config(model_id)

    checkpoint_path = root / config["checkpoint_path"]
    class_to_idx_path = root / config["class_to_idx_path"]

    required_paths = {
        "checkpoint_path": checkpoint_path,
        "class_to_idx_path": class_to_idx_path,
    }

    if _all_required_paths_exist(required_paths):
        return required_paths

    hosted = HOSTED_MODEL_ARTIFACTS.get(model_id)
    if hosted is None:
        missing = _format_missing(required_paths)
        raise FileNotFoundError(
            f"Missing model artifacts for '{model_id}' and no Hugging Face fallback is configured.\n"
            f"Missing: {missing}"
        )

    target_dir = _expected_target_dir(checkpoint_path, class_to_idx_path)
    target_dir.mkdir(parents=True, exist_ok=True)

    _download_from_hugging_face(
        repo_id=hosted.repo_id,
        filenames=hosted.required_files,
        target_dir=target_dir,
        required=True,
    )
    _download_from_hugging_face(
        repo_id=hosted.repo_id,
        filenames=hosted.optional_files,
        target_dir=target_dir,
        required=False,
    )

    if not _all_required_paths_exist(required_paths):
        missing = _format_missing(required_paths)
        raise FileNotFoundError(
            f"Hugging Face artifact download for '{model_id}' completed, but required files "
            f"are still missing. Missing: {missing}"
        )

    return required_paths


def _all_required_paths_exist(paths: dict[str, Path]) -> bool:
    return all(path.exists() and path.is_file() for path in paths.values())


def _format_missing(paths: dict[str, Path]) -> str:
    missing = [str(path) for path in paths.values() if not path.exists()]
    return ", ".join(missing) if missing else "none"


def _expected_target_dir(checkpoint_path: Path, class_to_idx_path: Path) -> Path:
    if checkpoint_path.parent != class_to_idx_path.parent:
        raise ValueError(
            "Hugging Face fallback expects checkpoint and class_to_idx files to share "
            f"one model directory, got {checkpoint_path.parent} and {class_to_idx_path.parent}."
        )
    return checkpoint_path.parent


def _download_from_hugging_face(
    *,
    repo_id: str,
    filenames: tuple[str, ...],
    target_dir: Path,
    required: bool,
) -> None:
    if not filenames:
        return

    try:
        from huggingface_hub import hf_hub_download
    except ImportError as error:
        raise ImportError(
            "Missing dependency 'huggingface_hub'. Install project requirements before "
            "using Hugging Face model artifact fallback."
        ) from error

    for filename in filenames:
        try:
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(target_dir),
                local_dir_use_symlinks=False,
            )
        except Exception as error:
            if required:
                raise RuntimeError(
                    f"Could not download required model artifact '{filename}' from "
                    f"Hugging Face repo '{repo_id}' into '{target_dir}'."
                ) from error
            LOGGER.warning(
                "Optional model artifact '%s' could not be downloaded from Hugging Face repo '%s' into '%s': %s",
                filename,
                repo_id,
                target_dir,
                error,
            )
