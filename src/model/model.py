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


def build_model(backbone_name: str, num_classes: int, pretrained: bool = True):
    """Create a model with a configurable backbone and custom classifier head."""
    if num_classes <= 0:
        raise ValueError("num_classes must be greater than 0.")

    if backbone_name == "efficientnet_b0":
        return create_model(num_classes=num_classes, pretrained=pretrained)

    if backbone_name == "efficientnet_b2":
        from torchvision.models import efficientnet_b2, EfficientNet_B2_Weights
        weights = EfficientNet_B2_Weights.DEFAULT if pretrained else None
        model = efficientnet_b2(weights=weights)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)
        return model

    if backbone_name == "convnext_tiny":
        from torchvision.models import convnext_tiny, ConvNeXt_Tiny_Weights
        weights = ConvNeXt_Tiny_Weights.DEFAULT if pretrained else None
        model = convnext_tiny(weights=weights)
        in_features = model.classifier[2].in_features
        model.classifier[2] = nn.Linear(in_features, num_classes)
        return model

    if backbone_name == "resnet50":
        from torchvision.models import resnet50, ResNet50_Weights
        weights = ResNet50_Weights.DEFAULT if pretrained else None
        model = resnet50(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        return model

    raise ValueError(f"Unknown backbone: {backbone_name}")


def count_trainable_parameters(model) -> int:
    """Count parameters that will be updated during training."""
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


# Module attribute holding the final classifier ("head") for each backbone. The
# rest of the network is treated as the frozen-able backbone during staged
# fine-tuning.
_HEAD_ATTRIBUTE = {
    "efficientnet_b0": "classifier",
    "efficientnet_b2": "classifier",
    "convnext_tiny": "classifier",
    "resnet50": "fc",
}


def get_head_parameters(model, backbone_name: str):
    """Return the list of parameters belonging to the classifier head."""
    if backbone_name not in _HEAD_ATTRIBUTE:
        raise ValueError(f"Unknown backbone: {backbone_name}")
    head_module = getattr(model, _HEAD_ATTRIBUTE[backbone_name])
    return list(head_module.parameters())


def set_backbone_requires_grad(model, backbone_name: str, requires_grad: bool) -> None:
    """Freeze or unfreeze every parameter except the classifier head.

    Used for head-first staged fine-tuning: the backbone is frozen while the
    head warms up, then unfrozen for full fine-tuning.
    """
    head_parameter_ids = {id(parameter) for parameter in get_head_parameters(model, backbone_name)}
    for parameter in model.parameters():
        if id(parameter) not in head_parameter_ids:
            parameter.requires_grad = requires_grad
