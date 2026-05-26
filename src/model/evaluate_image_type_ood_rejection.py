"""
Stage 4: OOD / unsupported-image rejection evaluation for the image-type classifier.

Creates small programmatic fixture images that represent unsupported or
problematic inputs, runs validation checks and then the trained classifier,
and measures how well confidence thresholding rejects them.

Fixture images are generated on demand (not committed to the repo) and saved to
--fixture-dir for inspection. Existing fixtures are reused across runs.

Example
-------
python -m src.model.evaluate_image_type_ood_rejection \\
    --model-dir  models/image_type_classifier_v1 \\
    --output-dir outputs/metrics \\
    --fixture-dir tests/fixtures/ood_image_type \\
    --thresholds 0.70 0.80 0.85 0.90 0.95
"""

from __future__ import annotations

import argparse
import csv
import json
import struct
import zlib
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from src.data.transforms import get_eval_transforms
from src.model.model import build_model
from src.model.train import select_device

# ── Constants ────────────────────────────────────────────────────────────────

CLASS_NAMES = ["clinical_macroscopic", "dermoscopic"]
MIN_SIDE = 32          # pixels — anything smaller is rejected by validation
MAX_ASPECT_RATIO = 10  # width/height or height/width above this → rejected
MIN_VARIANCE = 5.0     # pixel variance below this → near-blank rejection

# ── Fixture definitions ───────────────────────────────────────────────────────

def _arr(w: int, h: int, rgb) -> np.ndarray:
    """Return H×W×3 uint8 array filled with a constant RGB tuple."""
    a = np.zeros((h, w, 3), dtype=np.uint8)
    a[:, :] = rgb
    return a


def _noise(w: int, h: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, (h, w, 3), dtype=np.uint8)


def _supported_sample() -> np.ndarray:
    """Return a plausible 224×224 skin-tone patch as a stand-in supported base."""
    rng = np.random.default_rng(42)
    base = np.full((224, 224, 3), [210, 170, 130], dtype=np.uint8)
    base = (base + rng.integers(-20, 20, base.shape)).clip(0, 255).astype(np.uint8)
    return base


def _corrupt_jpeg_bytes() -> bytes:
    """Return bytes that begin with a valid JPEG SOI but have truncated content."""
    soi = b"\xff\xd8\xff\xe0"  # JPEG Start Of Image + APP0 marker
    fake_app0 = b"\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    # deliberately omit the rest of the JPEG data
    return soi + fake_app0 + b"\xde\xad\xbe\xef"


FIXTURES: list[dict] = [
    # ── Blank / solid colour ─────────────────────────────────────────────────
    {
        "name": "blank_white",
        "ood_type": "blank_white",
        "array": lambda: _arr(224, 224, [255, 255, 255]),
        "format": "JPEG",
    },
    {
        "name": "blank_black",
        "ood_type": "blank_black",
        "array": lambda: _arr(224, 224, [0, 0, 0]),
        "format": "JPEG",
    },
    {
        "name": "solid_red",
        "ood_type": "solid_color",
        "array": lambda: _arr(224, 224, [200, 50, 50]),
        "format": "JPEG",
    },
    {
        "name": "solid_green",
        "ood_type": "solid_color",
        "array": lambda: _arr(224, 224, [50, 200, 50]),
        "format": "JPEG",
    },
    # ── Noise ────────────────────────────────────────────────────────────────
    {
        "name": "random_noise",
        "ood_type": "random_noise",
        "array": lambda: _noise(224, 224, seed=1),
        "format": "JPEG",
    },
    {
        "name": "low_contrast_noise",
        "ood_type": "low_contrast",
        "array": lambda: (_arr(224, 224, [128, 128, 128])
                          + _noise(224, 224, seed=2).astype(np.int16) * 4 // 100
                          ).clip(0, 255).astype(np.uint8),
        "format": "JPEG",
    },
    # ── Extreme geometry ─────────────────────────────────────────────────────
    {
        "name": "tiny_image_16x16",
        "ood_type": "too_small",
        "array": lambda: _noise(16, 16, seed=3),
        "format": "JPEG",
    },
    {
        "name": "tiny_image_8x8",
        "ood_type": "too_small",
        "array": lambda: _noise(8, 8, seed=4),
        "format": "JPEG",
    },
    {
        "name": "extreme_aspect_wide",
        "ood_type": "extreme_aspect_ratio",
        "array": lambda: _noise(1024, 32, seed=5),
        "format": "JPEG",
    },
    {
        "name": "extreme_aspect_tall",
        "ood_type": "extreme_aspect_ratio",
        "array": lambda: _noise(32, 1024, seed=6),
        "format": "JPEG",
    },
    # ── Transformed supported images ─────────────────────────────────────────
    {
        "name": "overexposed_transformed",
        "ood_type": "unsupported_or_problematic_transformed",
        "array": lambda: np.clip(_supported_sample().astype(np.int32) * 4, 0, 255).astype(np.uint8),
        "format": "JPEG",
    },
    {
        "name": "underexposed_transformed",
        "ood_type": "unsupported_or_problematic_transformed",
        "array": lambda: (_supported_sample().astype(np.int32) // 8).astype(np.uint8),
        "format": "JPEG",
    },
    {
        "name": "heavily_blurred_transformed",
        "ood_type": "unsupported_or_problematic_transformed",
        "array": lambda: _blur_array(_supported_sample(), radius=30),
        "format": "JPEG",
    },
    # ── Document / screenshot-like (text grid pattern) ───────────────────────
    {
        "name": "document_text_like",
        "ood_type": "document_screenshot",
        "array": lambda: _text_grid(224, 224),
        "format": "JPEG",
    },
    # ── Corrupted file ───────────────────────────────────────────────────────
    {
        "name": "corrupted_jpeg",
        "ood_type": "corrupted_file",
        "array": None,  # raw bytes, not ndarray
        "format": "RAW",
        "raw_bytes": _corrupt_jpeg_bytes(),
    },
]


def _blur_array(arr: np.ndarray, radius: int) -> np.ndarray:
    from PIL import ImageFilter
    img = Image.fromarray(arr)
    blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
    return np.array(blurred)


def _text_grid(w: int, h: int) -> np.ndarray:
    """White background with a regular black line grid (mimics printed text)."""
    a = np.full((h, w, 3), 255, dtype=np.uint8)
    for y in range(0, h, 12):
        a[y : y + 1, 8 : w - 8] = 0  # horizontal rule
    return a


# ── Fixture generation ────────────────────────────────────────────────────────

def generate_fixtures(fixture_dir: Path) -> list[dict]:
    """Write fixtures to disk if not already present. Return list of records."""
    fixture_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for spec in FIXTURES:
        suffix = ".jpg" if spec["format"] in ("JPEG", "RAW") else ".png"
        path = fixture_dir / f"{spec['name']}{suffix}"

        if not path.exists():
            if spec["format"] == "RAW":
                path.write_bytes(spec["raw_bytes"])
            else:
                arr = spec["array"]()
                Image.fromarray(arr).save(path, format="JPEG", quality=95)

        records.append({
            "path": path,
            "name": spec["name"],
            "ood_type": spec["ood_type"],
        })
    return records


# ── Validation checks ─────────────────────────────────────────────────────────

def validate_image(path: Path) -> tuple[str, str]:
    """
    Run pre-inference validation checks.

    Returns (status, reason) where status is 'ok' or 'rejected'.
    """
    try:
        with Image.open(path) as img:
            img.verify()  # checks file integrity without fully decoding
    except Exception as exc:
        return "rejected", f"cannot_decode:{type(exc).__name__}"

    try:
        with Image.open(path) as img:
            img_rgb = img.convert("RGB")
            w, h = img_rgb.size
    except Exception as exc:
        return "rejected", f"decode_error:{type(exc).__name__}"

    min_side = min(w, h)
    if min_side < MIN_SIDE:
        return "rejected", f"too_small:{w}x{h}"

    aspect = max(w, h) / max(min_side, 1)
    if aspect > MAX_ASPECT_RATIO:
        return "rejected", f"extreme_aspect:{w}x{h}_ratio{aspect:.1f}"

    arr = np.array(img_rgb, dtype=np.float32)
    variance = float(arr.var())
    if variance < MIN_VARIANCE:
        return "rejected", f"near_blank:variance={variance:.2f}"

    return "ok", ""


# ── Model inference ───────────────────────────────────────────────────────────

def load_model(model_dir: Path, device: torch.device):
    class_to_idx_path = model_dir / "class_to_idx.json"
    config_path = model_dir / "training_config.json"
    checkpoint_path = model_dir / "best_model.pth"

    for p in (class_to_idx_path, config_path, checkpoint_path):
        if not p.exists():
            raise FileNotFoundError(f"Missing artifact: {p}")

    with class_to_idx_path.open() as f:
        class_to_idx = json.load(f)
    with config_path.open() as f:
        train_cfg = json.load(f)

    backbone = train_cfg.get("backbone", "efficientnet_b0")
    image_size = train_cfg.get("image_size", 224)

    model = build_model(backbone_name=backbone, num_classes=len(class_to_idx), pretrained=False)
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()
    return model, class_to_idx, image_size


def infer_image(path: Path, model, image_size: int, transform, device: torch.device):
    """Return (predicted_idx, confidence, probs_list) or raise on error."""
    with Image.open(path) as img:
        tensor = transform(img.convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze().cpu().tolist()
    confidence = max(probs)
    predicted_idx = probs.index(confidence)
    return predicted_idx, confidence, probs


# ── Threshold helpers ─────────────────────────────────────────────────────────

def accepted_at(confidence: float, threshold: float) -> bool:
    return confidence >= threshold


def final_state(confidence: float, predicted_class: str, threshold: float) -> str:
    if accepted_at(confidence, threshold):
        return predicted_class
    return "uncertain_or_unsupported"


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 4: OOD rejection evaluation for image-type classifier."
    )
    parser.add_argument("--model-dir", default="models/image_type_classifier_v1")
    parser.add_argument("--output-dir", default="outputs/metrics")
    parser.add_argument("--fixture-dir", default="tests/fixtures/ood_image_type")
    parser.add_argument(
        "--thresholds", nargs="+", type=float,
        default=[0.70, 0.80, 0.85, 0.90, 0.95],
    )
    parser.add_argument("--device", default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_dir = Path(args.model_dir)
    output_dir = Path(args.output_dir)
    fixture_dir = Path(args.fixture_dir)
    thresholds = sorted(args.thresholds)

    output_dir.mkdir(parents=True, exist_ok=True)

    device = select_device() if args.device == "auto" else torch.device(args.device)
    print(f"Device: {device}")

    # ── Generate / load fixtures ──────────────────────────────────────────────
    fixtures = generate_fixtures(fixture_dir)
    print(f"Fixtures: {len(fixtures)} images in {fixture_dir}")

    # ── Load model ────────────────────────────────────────────────────────────
    model, class_to_idx, image_size = load_model(model_dir, device)
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    clin_idx = class_to_idx["clinical_macroscopic"]
    derm_idx = class_to_idx["dermoscopic"]
    transform = get_eval_transforms(image_size)
    print(f"Model loaded from {model_dir}")

    # ── Per-image evaluation ──────────────────────────────────────────────────
    pred_rows = []
    for fix in fixtures:
        path: Path = fix["path"]
        ood_type: str = fix["ood_type"]

        val_status, val_reason = validate_image(path)

        row: dict = {
            "image_path": str(path),
            "ood_type": ood_type,
            "validation_status": val_status,
            "validation_reason": val_reason,
            "model_ran": False,
            "predicted_image_type": "",
            "confidence": "",
            "clinical_macroscopic_probability": "",
            "dermoscopic_probability": "",
        }

        if val_status == "ok":
            try:
                pred_idx, conf, probs = infer_image(path, model, image_size, transform, device)
                predicted_class = idx_to_class[pred_idx]
                row.update({
                    "model_ran": True,
                    "predicted_image_type": predicted_class,
                    "confidence": round(conf, 6),
                    "clinical_macroscopic_probability": round(probs[clin_idx], 6),
                    "dermoscopic_probability": round(probs[derm_idx], 6),
                })
            except Exception as exc:
                row.update({
                    "validation_status": "rejected",
                    "validation_reason": f"inference_error:{type(exc).__name__}:{exc}",
                })

        # Threshold columns
        for t in thresholds:
            col = f"accepted_at_{f'{t:.2f}'.replace('.', '_')}"
            if row["model_ran"]:
                row[col] = accepted_at(float(row["confidence"]), t)
            else:
                row[col] = False  # rejected by validation → not accepted at any threshold

        t90_col = "accepted_at_0_90"
        if row["model_ran"] and row[t90_col]:
            row["final_state_at_0_90"] = row["predicted_image_type"]
        else:
            row["final_state_at_0_90"] = "uncertain_or_unsupported"

        pred_rows.append(row)

    # ── Print per-image results ───────────────────────────────────────────────
    print(f"\n{'OOD type':<40} {'val':<10} {'model':<6} {'predicted':<24} {'conf':>8} {'state@0.90'}")
    print("-" * 115)
    for r in pred_rows:
        conf_str = f"{r['confidence']:.4f}" if r["confidence"] != "" else "—"
        print(f"{r['ood_type']:<40} {r['validation_status']:<10} "
              f"{'yes' if r['model_ran'] else 'no':<6} "
              f"{r['predicted_image_type'] or '—':<24} "
              f"{conf_str:>8}  {r['final_state_at_0_90']}")

    # ── Save predictions CSV ──────────────────────────────────────────────────
    pred_path = output_dir / "image_type_classifier_ood_predictions.csv"
    _write_csv(pred_path, pred_rows)
    print(f"\nSaved: {pred_path}")

    # ── Threshold summary ─────────────────────────────────────────────────────
    total = len(pred_rows)
    val_rejected = sum(1 for r in pred_rows if r["validation_status"] == "rejected")
    model_ran = [r for r in pred_rows if r["model_ran"]]

    summary_rows = []
    for t in thresholds:
        col = f"accepted_at_{f'{t:.2f}'.replace('.', '_')}"
        thresh_accepted = [r for r in model_ran if r[col]]
        thresh_rejected = len(model_ran) - len(thresh_accepted)
        total_rejected = val_rejected + thresh_rejected
        total_rejected_rate = total_rejected / total if total > 0 else 0.0

        # "Incorrectly accepted" = an OOD image that the model accepted at this threshold
        # (all model-reached images are OOD, so any acceptance is incorrect)
        incorrectly_accepted = len(thresh_accepted)
        wrong_as_clin = sum(1 for r in thresh_accepted if r["predicted_image_type"] == "clinical_macroscopic")
        wrong_as_derm = sum(1 for r in thresh_accepted if r["predicted_image_type"] == "dermoscopic")

        summary_rows.append({
            "threshold": t,
            "total_ood_count": total,
            "validation_rejected_count": val_rejected,
            "model_evaluated_count": len(model_ran),
            "threshold_rejected_count": thresh_rejected,
            "total_rejected_count": total_rejected,
            "total_rejected_rate": round(total_rejected_rate, 6),
            "incorrectly_accepted_count": incorrectly_accepted,
            "incorrectly_accepted_as_clinical": wrong_as_clin,
            "incorrectly_accepted_as_dermoscopic": wrong_as_derm,
        })

    rej_path = output_dir / "image_type_classifier_ood_rejection_results.csv"
    _write_csv(rej_path, summary_rows)
    print(f"Saved: {rej_path}")

    # ── Print threshold table ─────────────────────────────────────────────────
    print(f"\n{'thresh':>8}  {'val_rej':>7}  {'thr_rej':>7}  {'total_rej':>9}  "
          f"{'rej_rate':>9}  {'wrong_acc':>9}  {'→clin':>6}  {'→derm':>6}")
    print("-" * 75)
    for r in summary_rows:
        print(f"{r['threshold']:>8.2f}  {r['validation_rejected_count']:>7}  "
              f"{r['threshold_rejected_count']:>7}  {r['total_rejected_count']:>9}  "
              f"{r['total_rejected_rate']:>9.4f}  "
              f"{r['incorrectly_accepted_count']:>9}  "
              f"{r['incorrectly_accepted_as_clinical']:>6}  "
              f"{r['incorrectly_accepted_as_dermoscopic']:>6}")

    # ── False accepts CSV (images that passed validation AND threshold at 0.90) ─
    false_accepts_90 = [r for r in pred_rows
                        if r["model_ran"] and r.get("accepted_at_0_90", False)]
    if false_accepts_90:
        fa_path = output_dir / "image_type_classifier_ood_false_accepts.csv"
        _write_csv(fa_path, false_accepts_90)
        print(f"\nFalse accepts at 0.90 ({len(false_accepts_90)}): {fa_path}")
    else:
        print("\nNo false accepts at threshold 0.90.")

    # ── Summary ───────────────────────────────────────────────────────────────
    r90 = next(r for r in summary_rows if r["threshold"] == 0.90)
    print(f"\n── OOD rejection summary at threshold 0.90 ──────────────")
    print(f"  Total fixtures:        {total}")
    print(f"  Validation rejected:   {r90['validation_rejected_count']}")
    print(f"  Model evaluated:       {r90['model_evaluated_count']}")
    print(f"  Threshold rejected:    {r90['threshold_rejected_count']}")
    print(f"  Total rejected:        {r90['total_rejected_count']} ({r90['total_rejected_rate']:.1%})")
    print(f"  Incorrectly accepted:  {r90['incorrectly_accepted_count']}")
    print()


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
