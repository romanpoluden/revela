from __future__ import annotations

from collections import Counter
from typing import Iterable

import torch
from torch.utils.data import WeightedRandomSampler


SUPPORTED_SAMPLER_MODES = {
    "none",
    "class",
    "source_class",
}


def _get_row_value(row: dict, column: str) -> str:
    value = row.get(column)
    if value is None or str(value).strip() == "":
        raise ValueError(f"Missing sampler column value for `{column}`.")
    return str(value)


def _build_group_keys(
    rows: Iterable[dict],
    mode: str,
    class_column: str,
    source_column: str,
) -> list[str]:
    if mode == "none":
        return []

    if mode == "class":
        return [_get_row_value(row, class_column) for row in rows]

    if mode == "source_class":
        return [
            f"{_get_row_value(row, source_column)}::{_get_row_value(row, class_column)}"
            for row in rows
        ]

    supported = ", ".join(sorted(SUPPORTED_SAMPLER_MODES))
    raise ValueError(f"Unsupported sampler mode `{mode}`. Supported modes: {supported}")


def build_weighted_sampler(
    rows: list[dict],
    mode: str,
    class_column: str = "target_label",
    source_column: str = "source_dataset",
    replacement: bool = True,
) -> WeightedRandomSampler | None:
    """Build a weighted sampler for class-aware or source+class-aware training.

    Modes:
    - none: return None and use default DataLoader shuffle behavior.
    - class: balance samples by target class.
    - source_class: balance samples by source_dataset + target class group.
    """
    if mode == "none":
        return None

    group_keys = _build_group_keys(
        rows=rows,
        mode=mode,
        class_column=class_column,
        source_column=source_column,
    )

    group_counts = Counter(group_keys)
    if not group_counts:
        raise ValueError("Cannot build sampler from an empty training dataset.")

    weights = [1.0 / group_counts[group_key] for group_key in group_keys]

    return WeightedRandomSampler(
        weights=torch.as_tensor(weights, dtype=torch.double),
        num_samples=len(weights),
        replacement=replacement,
    )


def summarize_sampler_groups(
    rows: list[dict],
    mode: str,
    class_column: str = "target_label",
    source_column: str = "source_dataset",
) -> dict[str, int]:
    """Return group counts for logging and smoke-test validation."""
    if mode == "none":
        return {}

    group_keys = _build_group_keys(
        rows=rows,
        mode=mode,
        class_column=class_column,
        source_column=source_column,
    )
    return dict(sorted(Counter(group_keys).items()))
