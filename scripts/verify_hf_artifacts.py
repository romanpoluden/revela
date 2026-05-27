"""
Verify that the Hugging Face hosted artifacts match the canonical local checksums.

Downloads both model checkpoints from HF into a temp directory, hashes them,
and asserts against the expected SHA256 values established in D8.5 (#195).

Usage (run from the project root):
    python scripts/verify_hf_artifacts.py

Exit codes:
    0 — all hashes match
    1 — one or more mismatches, or download failure
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

EXPECTED: dict[str, dict] = {
    "clinical_skin_condition_v1": {
        "repo_id": "RevelaCap/clinical-skin-condition-v1",
        "files": {
            "best_model.pth": "eba9a581505c60cee98152c790c4113a1549c691248d518cc5d1e7097feb20bc",
            "class_to_idx.json": "54cfa7c59ff278e52b86b52b8be281300ea14141093e26992ab88d9efb5d55f2",
        },
    },
    "dermoscopic_cancer_risk_bcn_mnh_v1": {
        "repo_id": "RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1",
        "files": {
            "best_model.pth": "71a20d7cf8137c0ac5a1d43c24892a97b308e51f0c29407a19696c75d323c385",
            "class_to_idx.json": "303efc9ca936a78b573c4cdc30e4767af77efc90edd8e1d901e92cab101a0d96",
        },
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("ERROR: huggingface_hub not installed. Run: pip install huggingface_hub")
        return 1

    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for model_id, spec in EXPECTED.items():
            print(f"\n{model_id}")
            for filename, expected_hash in spec["files"].items():
                try:
                    local = hf_hub_download(
                        repo_id=spec["repo_id"],
                        filename=filename,
                        local_dir=str(Path(tmpdir) / model_id),
                    )
                except Exception as exc:
                    msg = f"  FAIL  {filename} — download error: {exc}"
                    print(msg)
                    failures.append(msg)
                    continue

                actual = sha256(Path(local))
                if actual == expected_hash:
                    print(f"  PASS  {filename}")
                else:
                    msg = (
                        f"  FAIL  {filename}\n"
                        f"        expected: {expected_hash}\n"
                        f"        actual:   {actual}"
                    )
                    print(msg)
                    failures.append(msg)

    print()
    if failures:
        print(f"FAILED — {len(failures)} mismatch(es)")
        return 1
    print("All HF artifacts verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
