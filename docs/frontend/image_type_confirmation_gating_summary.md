# Image Type Confirmation Gating Summary

## Problem

The analyze screen supports separate clinical-photo and dermoscopic-image modes, but the app does not automatically detect whether an uploaded image matches the selected mode. A wrong-modality upload can route to the wrong model and produce misleading educational output.

## Implemented UI behavior

- Added a global warning near the image-type selector explaining that the user must choose the image type carefully.
- Added explicit clinical-photo upload instructions for regular, non-dermoscopic camera photos.
- Added explicit dermoscopic-image upload instructions for dermoscopic or magnified lesion images only.
- Added a mode-specific confirmation checkbox before analysis can be started.
- Cleared stale confirmations when the selected image mode changes or when the uploaded file changes.
- Reset analysis state when the image mode, uploaded file, or confirmation checkbox changes.

## Exact confirmation gating rule

`Analyze case` is enabled only when all of these are true:

- a valid image is uploaded
- there is no image error
- inference is not already running
- the active mode-specific image-type confirmation checkbox is checked

## Intentionally not changed

- Model routing was preserved:
  - Clinical photo uses `clinical_skin_condition_v1` with `top_k=3`.
  - Dermoscopic image uses `dermoscopic_cancer_risk_bcn_mnh_v1` with `top_k=4`.
- The inference adapter, model registry, taxonomy, training code, and model code were not changed.
- Existing clinical and dermoscopic rendering flows were preserved.
- No automatic clinical-vs-dermoscopic classification was added.
- No diagnosis, treatment, clinical-readiness, or safety reassurance claims were added.

## Verification commands

```bash
python -m py_compile app.py
python -m streamlit run app.py --server.headless true --server.port 8502 --server.address 127.0.0.1
grep -nEi "diagnos|detected|confirmed|safe|treatment" app.py
```
