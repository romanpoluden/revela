from __future__ import annotations

import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0

try:
    from torchvision.models import EfficientNet_B0_Weights
except ImportError:
    EfficientNet_B0_Weights = None

_IMAGE_EMBED_DIM = 1280
_META_HIDDEN = 32
_META_OUT = 16


class MetadataAwareClinicalV2(nn.Module):
    """EfficientNet-B0 image backbone + small metadata MLP → fused classifier.

    Image evidence dominates: the metadata branch is intentionally narrow
    (<5% of total params). Missing metadata is handled by a zeros vector
    (explicit unknown encoding) — no samples are dropped.

    source_dataset must never appear in metadata_fields — asserted at init.
    """

    def __init__(
        self,
        num_classes: int,
        metadata_dim: int,
        metadata_fields: list[str],
        pretrained: bool = True,
        dropout: float = 0.3,
    ):
        super().__init__()

        assert "source_dataset" not in metadata_fields, (
            "source_dataset must never be used as model input — STOP"
        )

        if pretrained and EfficientNet_B0_Weights is not None:
            base = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
        elif pretrained:
            base = efficientnet_b0(pretrained=True)
        else:
            base = efficientnet_b0(weights=None if EfficientNet_B0_Weights is not None else False)

        self.backbone = nn.Sequential(base.features, base.avgpool, nn.Flatten())

        self.metadata_mlp = nn.Sequential(
            nn.Linear(metadata_dim, _META_HIDDEN),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(_META_HIDDEN, _META_OUT),
            nn.ReLU(),
        )

        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(_IMAGE_EMBED_DIM + _META_OUT, num_classes),
        )

        self.metadata_fields = list(metadata_fields)
        self.metadata_dim = metadata_dim

        meta_params = sum(p.numel() for p in self.metadata_mlp.parameters())
        total_params = sum(p.numel() for p in self.parameters())
        meta_pct = meta_params / total_params * 100
        print(
            f"MetadataAwareClinicalV2: total={total_params/1e6:.2f}M | "
            f"meta_branch={meta_params:,} ({meta_pct:.2f}%) | "
            f"fields={metadata_fields} | metadata_dim={metadata_dim}"
        )
        assert meta_pct < 5.0, (
            f"Metadata branch is {meta_pct:.2f}% of total params — must be <5% "
            "to keep image evidence dominant — STOP"
        )

    def forward(self, image: torch.Tensor, metadata: torch.Tensor) -> torch.Tensor:
        img_emb = self.backbone(image)
        meta_emb = self.metadata_mlp(metadata)
        fused = torch.cat([img_emb, meta_emb], dim=1)
        return self.classifier(fused)
