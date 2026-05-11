"""
Smoke test for the config-driven model loader.

Verifies that a model from the registry can be loaded end-to-end:
  registry lookup -> path resolution -> class_to_idx -> checkpoint -> nn.Module

Usage (run from the project root):
    python scripts/smoke_test_model_loader.py
    python scripts/smoke_test_model_loader.py --model-id dermoscopic_baseline_v1

Exit codes:
    0 — loaded successfully, or checkpoint not yet trained (SKIPPED)
    1 — unexpected error
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from project root without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.inference.model_loader import LoadedModel, load_model_from_registry, select_device
from src.inference.model_registry import REGISTRY


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test the config-driven model loader.")
    parser.add_argument(
        "--model-id",
        default="dermoscopic_baseline_v1",
        choices=list(REGISTRY.keys()),
        help="Registry model_id to load (default: dermoscopic_baseline_v1).",
    )
    return parser.parse_args()


def _print_result(result: LoadedModel) -> None:
    param_count = sum(p.numel() for p in result.model.parameters())
    print("OK — model loaded successfully.")
    print(f"  model_id:          {result.model_id}")
    print(f"  input_type:        {result.input_type}")
    print(f"  architecture:      {result.architecture}")
    print(f"  num_classes:       {result.num_classes}")
    print(f"  class_names:       {result.class_names}")
    print(f"  image_size:        {result.image_size}")
    print(f"  device:            {result.device}")
    print(f"  parameters:        {param_count:,}")
    print(f"  checkpoint_path:   {result.checkpoint_path}")
    print(f"  class_to_idx_path: {result.class_to_idx_path}")


def main() -> None:
    args = parse_args()
    model_id = args.model_id

    print(f"Smoke test: loading '{model_id}' on {select_device()} ...")

    try:
        result = load_model_from_registry(model_id)
    except FileNotFoundError as exc:
        print(f"\nSKIPPED — checkpoint not found:")
        print(f"  {exc}")
        print("Train the model first, then re-run this smoke test.")
        sys.exit(0)
    except Exception as exc:
        print(f"\nFAILED — {type(exc).__name__}: {exc}")
        sys.exit(1)

    _print_result(result)


if __name__ == "__main__":
    main()
