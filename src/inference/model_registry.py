from __future__ import annotations

# TEMPORARY BASELINE NOTE:
# "dermoscopic_baseline_v1" is a 3-class smoke-test checkpoint trained on BCN20000.
# Its taxonomy (Melanoma / Benign nevus / Other lesion) is not the final production
# taxonomy. Do not hard-code app logic around these 3 class names.
# Future models below will supersede it once their checkpoints are trained.

REGISTRY: dict[str, dict] = {
    "dermoscopic_baseline_v1": {
        "input_type": "dermoscopic",
        "architecture": "efficientnet_b0",
        "num_classes": 3,
        "config_path": "config/bcn20000_config.yaml",
        "checkpoint_path": "models/bcn20000_effnet_b0/best_model.pth",
        "class_to_idx_path": "models/bcn20000_effnet_b0/class_to_idx.json",
        "image_size": 224,
    },
    "dermoscopic_cancer_risk_v2": {
        "input_type": "dermoscopic",
        "architecture": "efficientnet_b0",
        "num_classes": 4,
        "config_path": "config/bcn20000_cancer_risk_config.yaml",
        "checkpoint_path": "models/bcn20000_cancer_risk_effnet_b0/best_model.pth",
        "class_to_idx_path": "models/bcn20000_cancer_risk_effnet_b0/class_to_idx.json",
        "image_size": 224,
    },
    "dermoscopic_cancer_risk_bcn_mnh_v1": {
        "input_type": "dermoscopic",
        "architecture": "efficientnet_b0",
        "num_classes": 4,
        "config_path": "config/bcn_mnh_cancer_risk_config.yaml",
        "checkpoint_path": "models/bcn_mnh_cancer_risk_effnet_b0/best_model.pth",
        "class_to_idx_path": "models/bcn_mnh_cancer_risk_effnet_b0/class_to_idx.json",
        "image_size": 224,
    },
    "clinical_skin_condition_v1": {
        "input_type": "clinical",
        "architecture": "efficientnet_b0",
        "num_classes": None,  # taxonomy not yet finalized; inferred from class_to_idx at load time
        "config_path": "config/clinical_v2_config.yaml",
        "checkpoint_path": "models/clinical_v2_effnet_b0/best_model.pth",
        "class_to_idx_path": "models/clinical_v2_effnet_b0/class_to_idx.json",
        "image_size": 224,
    },
}


def get_model_config(model_id: str) -> dict:
    """Return a copy of the registry entry for model_id."""
    if model_id not in REGISTRY:
        available = ", ".join(REGISTRY.keys())
        raise KeyError(f"Unknown model_id '{model_id}'. Available: {available}")
    return dict(REGISTRY[model_id])
