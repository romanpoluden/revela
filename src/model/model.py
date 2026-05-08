from __future__ import annotations

import torch.nn as nn
from torchvision.models import efficientnet_b0

try:
    from torchvision.models import EfficientNet_B0_Weights
except ImportError:  # pragma: no cover - fallback for older torchvision
    EfficientNet_B0_Weights = None


def create_model(num_classes: int, pretrained: bool = True):
    """Create an EfficientNet-B0 model with a custom classifier head."""
    if num_classes <= 0:
        raise ValueError("num_classes must be greater than 0.")

    if pretrained and EfficientNet_B0_Weights is not None:
        model = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
    elif pretrained:  # pragma: no cover - compatibility fallback
        model = efficientnet_b0(pretrained=True)
    else:
        if EfficientNet_B0_Weights is not None:
            model = efficientnet_b0(weights=None)
        else:  # pragma: no cover - compatibility fallback
            model = efficientnet_b0(pretrained=False)

    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


def count_trainable_parameters(model) -> int:
    """Count parameters that will be updated during training."""
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
