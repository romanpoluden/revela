# Hugging Face Runtime Artifact Loading

**Related issue:** #204  
**Status:** Implemented in branch `d8-6-hf-fallback`

---

## Purpose

The Streamlit app should be able to run in a clean deployment environment where local `models/` folders do not already exist.

This runtime fallback keeps inference local to the Streamlit process. Hugging Face is used only as artifact storage. The app does not call Hugging Face Inference Endpoints and does not use a remote prediction API.

---

## Runtime Behavior

Model loading is local-first:

1. The inference loader checks the registry paths for the required model files.
2. If `best_model.pth` and `class_to_idx.json` already exist locally, the app loads them exactly as before.
3. If either required file is missing and the model has a configured Hugging Face repo, the resolver downloads required files into the expected local `models/` folder.
4. The existing PyTorch model loader then loads the downloaded files from the local path.
5. Prediction outputs and response schema remain unchanged.

---

## Implemented Files

```text
src/inference/artifact_resolver.py
src/inference/model_loader.py
requirements.txt
```

`src/inference/artifact_resolver.py` contains the hosted artifact mapping and the download logic.

`src/inference/model_loader.py` calls `resolve_model_artifacts(...)` before loading the checkpoint and class mapping.

`requirements.txt` includes:

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

## Local Existing-Artifact Verification

With local model folders present, run:

```bash
python -m py_compile app.py
python -m py_compile src/inference/artifact_resolver.py
python -m py_compile src/inference/model_loader.py
python -m py_compile src/prompting/llm_prompt_builder.py
```

Then run inference with local artifacts:

```bash
python -m src.inference.adapter \
  --model-id clinical_skin_condition_v1 \
  --image <clinical_demo_image> \
  --top-k 3 \
  --debug

python -m src.inference.adapter \
  --model-id dermoscopic_cancer_risk_bcn_mnh_v1 \
  --image <dermoscopic_demo_image> \
  --top-k 4 \
  --debug
```

Expected result: inference runs without needing to download files.

---

## Clean-Environment / Missing-Artifact Verification

Temporarily move local artifact folders away:

```bash
mv models/clinical_v2_effnet_b0 models/clinical_v2_effnet_b0.local_backup
mv models/bcn_mnh_cancer_risk_effnet_b0 models/bcn_mnh_cancer_risk_effnet_b0.local_backup
```

Then run inference again:

```bash
python -m src.inference.adapter \
  --model-id clinical_skin_condition_v1 \
  --image <clinical_demo_image> \
  --top-k 3 \
  --debug

python -m src.inference.adapter \
  --model-id dermoscopic_cancer_risk_bcn_mnh_v1 \
  --image <dermoscopic_demo_image> \
  --top-k 4 \
  --debug
```

Expected result:

- `models/clinical_v2_effnet_b0/best_model.pth` is restored from Hugging Face.
- `models/clinical_v2_effnet_b0/class_to_idx.json` is restored from Hugging Face.
- `models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth` is restored from Hugging Face.
- `models/bcn_mnh_cancer_risk_effnet_b0/class_to_idx.json` is restored from Hugging Face.
- Both inference calls return the existing canonical response schema.

Restore local backups if needed:

```bash
rm -rf models/clinical_v2_effnet_b0
rm -rf models/bcn_mnh_cancer_risk_effnet_b0
mv models/clinical_v2_effnet_b0.local_backup models/clinical_v2_effnet_b0
mv models/bcn_mnh_cancer_risk_effnet_b0.local_backup models/bcn_mnh_cancer_risk_effnet_b0
```

---

## Streamlit Verification

Run:

```bash
python -m streamlit run app.py
```

Verify:

- app starts without pre-copied local model artifacts;
- clinical-photo flow can run;
- dermoscopic-image flow can run;
- clinical-to-dermoscopic follow-up still works when a lesion-routing clinical image is available;
- prompt export remains visible after inference.

---

## Scope Boundaries

This change does not:

- change model weights;
- retrain models;
- change disease taxonomies;
- change prediction schemas;
- add Hugging Face Inference Endpoints;
- add a public API server;
- add direct ChatGPT or Claude API calls;
- make diagnosis, treatment, clinical-readiness, or patient-use claims.

Hugging Face is used only to restore model files before local PyTorch inference.
