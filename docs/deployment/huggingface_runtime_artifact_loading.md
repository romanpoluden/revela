# Hugging Face Artifact Loading for Local Fallback

**Related issue:** #204  
**Architecture parent:** #222  
**Status:** Supported local/development fallback, not the primary deployed demo inference path

---

## Purpose

This document describes the local fallback path for Revela model inference.

Primary D9 demo architecture:

```text
Streamlit frontend -> Hugging Face-hosted inference backend -> canonical JSON response
```

Local fallback architecture:

```text
Local app or CLI -> local PyTorch inference -> Hugging Face artifact download if local model files are missing
```

The fallback is useful for local development, debugging, backup demos, and validating that hosted artifacts can still be restored and loaded locally.

It should not be presented as the primary public deployment architecture.

---

## Runtime Behavior

Model loading is local-first:

1. The inference loader checks the registry paths for the required model files.
2. If `best_model.pth` and `class_to_idx.json` already exist locally, the app loads them exactly as before.
3. If either required file is missing and the model has a configured Hugging Face repo, the resolver downloads required files into the expected local `models/` folder.
4. The existing PyTorch model loader then loads the downloaded files from the local path.
5. Prediction outputs and response schema remain unchanged.

Hugging Face is used only as artifact storage in this fallback path.

---

## Implemented Files

```text
src/inference/artifact_resolver.py
src/inference/model_loader.py
requirements.txt
requirements-dev.txt
```

`src/inference/artifact_resolver.py` contains the hosted artifact mapping and download logic.

`src/inference/model_loader.py` calls `resolve_model_artifacts(...)` before loading the checkpoint and class mapping.

`requirements.txt` contains runtime dependencies only. Notebook-only dependencies are kept in `requirements-dev.txt`.

Runtime dependency added for the fallback:

```text
huggingface_hub>=0.23.0
```

---

## Hosted Artifact Mapping

| Model ID | Hugging Face repo | Expected local path |
|---|---|---|
| `clinical_skin_condition_v1` | `RevelaCap/clinical-skin-condition-v1` | `models/clinical_v2_effnet_b0/` |
| `dermoscopic_cancer_risk_bcn_mnh_v1` | `RevelaCap/dermoscopic-cancer-risk-bcn-mnh-v1` | `models/bcn_mnh_cancer_risk_effnet_b0/` |

Required files for each model:

```text
best_model.pth
class_to_idx.json
```

Optional file downloaded when available:

```text
training_history.csv
```

---

## Verification

With local model folders present, run:

```bash
python -m py_compile app.py
python -m py_compile src/inference/artifact_resolver.py
python -m py_compile src/inference/model_loader.py
python -m py_compile src/prompting/llm_prompt_builder.py
```

To test missing-artifact fallback, move the model folders away and run the two inference commands again with valid local demo images. The resolver should restore the expected model folders from Hugging Face and return the canonical response schema.

---

## Relationship to Remote Inference Work

This fallback does not replace the D9 remote inference work:

- #222 defines the architecture migration.
- #223 builds the Hugging Face-hosted inference backend.
- #224 updates Streamlit to call the remote backend.
- #225 updates final deployment documentation.

After #224 is implemented, the deployed demo should use remote inference by default. This local fallback can remain available for development and backup.
