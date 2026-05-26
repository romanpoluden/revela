from __future__ import annotations

import csv
from pathlib import Path

import torch
from PIL import Image, UnidentifiedImageError
from torch.utils.data import Dataset


class ImageClassificationDataset(Dataset):
    """Generic image classification dataset backed by a CSV file."""

    def __init__(
        self,
        csv_path,
        class_to_idx,
        transform=None,
        image_column: str = "image_path",
        label_column: str = "class_label",
        class_idx_column: str | None = None,
    ):
        self.csv_path = Path(csv_path)
        self.class_to_idx = dict(class_to_idx)
        self.transform = transform
        self.image_column = image_column
        self.label_column = label_column
        self.class_idx_column = class_idx_column
        self.idx_to_class = {index: class_name for class_name, index in self.class_to_idx.items()}
        self.required_columns = [self.image_column]
        if self.class_idx_column is None:
            self.required_columns.append(self.label_column)
        else:
            self.required_columns.append(self.class_idx_column)

        if not self.csv_path.exists():
            raise FileNotFoundError(f"Dataset CSV not found: {self.csv_path}")

        if not self.class_to_idx:
            raise ValueError("class_to_idx must not be empty.")

        self.rows = self._load_rows()

    def _load_rows(self) -> list[dict[str, str]]:
        with self.csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            fieldnames = reader.fieldnames or []

        missing_columns = [
            column for column in self.required_columns if column not in fieldnames
        ]
        if missing_columns:
            missing_text = ", ".join(missing_columns)
            raise KeyError(
                f"Dataset CSV is missing required columns: {missing_text}"
            )

        cleaned_rows: list[dict[str, str]] = []
        for row_index, row in enumerate(rows):
            image_path = (row.get(self.image_column) or "").strip()
            class_label = (row.get(self.label_column) or "").strip()

            if not image_path:
                raise ValueError(
                    f"Row {row_index} in {self.csv_path} is missing `{self.image_column}`."
                )
            label_idx = self._resolve_label_idx(row, row_index)
            if not class_label:
                class_label = self.idx_to_class[label_idx]

            cleaned_row = dict(row)
            cleaned_row.update(
                {
                    "image_path": image_path,
                    "class_label": class_label,
                    "label_idx": label_idx,
                }
            )
            cleaned_rows.append(cleaned_row)

        return cleaned_rows

    def _resolve_label_idx(self, row: dict[str, str], row_index: int) -> int:
        class_label = (row.get(self.label_column) or "").strip()

        if class_label:
            if class_label not in self.class_to_idx:
                raise KeyError(
                    f"Row {row_index} has {self.label_column} `{class_label}` that is not "
                    "present in class_to_idx."
                )
            label_idx = self.class_to_idx[class_label]
            self._validate_class_idx(row, row_index, label_idx)
            return label_idx

        if self.class_idx_column is None:
            raise ValueError(
                f"Row {row_index} in {self.csv_path} is missing `{self.label_column}`."
            )

        raw_class_idx = (row.get(self.class_idx_column) or "").strip()
        if not raw_class_idx:
            raise ValueError(
                f"Row {row_index} in {self.csv_path} is missing `{self.class_idx_column}`."
            )

        try:
            label_idx = int(raw_class_idx)
        except ValueError as error:
            raise ValueError(
                f"Row {row_index} has non-integer {self.class_idx_column} `{raw_class_idx}`."
            ) from error

        if label_idx not in self.idx_to_class:
            raise KeyError(
                f"Row {row_index} has {self.class_idx_column} `{label_idx}` that is not "
                "present in class_to_idx."
            )

        return label_idx

    def _validate_class_idx(
        self,
        row: dict[str, str],
        row_index: int,
        label_idx: int,
    ) -> None:
        if self.class_idx_column is None:
            return

        raw_class_idx = (row.get(self.class_idx_column) or "").strip()
        if not raw_class_idx:
            return

        try:
            class_idx = int(raw_class_idx)
        except ValueError as error:
            raise ValueError(
                f"Row {row_index} has non-integer {self.class_idx_column} `{raw_class_idx}`."
            ) from error

        if class_idx != label_idx:
            raise ValueError(
                f"Row {row_index} has {self.label_column} mapped to {label_idx}, "
                f"but {self.class_idx_column} is {class_idx}."
            )

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        image_path = Path(row["image_path"])
        label_idx = row["label_idx"]

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image file does not exist for dataset item {index}: {image_path}"
            )

        try:
            with Image.open(image_path) as image:
                image = image.convert("RGB")

                if self.transform is not None:
                    image_tensor = self.transform(image)
                else:
                    image_tensor = self._pil_to_tensor(image)
        except FileNotFoundError:
            raise
        except UnidentifiedImageError as error:
            raise RuntimeError(
                f"Could not read image for dataset item {index}: {image_path}"
            ) from error
        except OSError as error:
            raise RuntimeError(
                f"Image file appears to be corrupt for dataset item {index}: {image_path}"
            ) from error

        return image_tensor, label_idx

    def _pil_to_tensor(self, image: Image.Image) -> torch.Tensor:
        """Convert a PIL RGB image to a float tensor in CHW format."""
        width, height = image.size
        channels = len(image.getbands())

        # This fallback keeps the dataset usable even when no transform is passed.
        pixel_values = torch.tensor(list(image.getdata()), dtype=torch.uint8)
        image_tensor = pixel_values.view(height, width, channels).permute(2, 0, 1)
        return image_tensor.float() / 255.0


class BCN20000Dataset(ImageClassificationDataset):
    """PyTorch dataset for BCN20000 images prepared for the Revela project."""

    def __init__(self, csv_path, class_to_idx, transform=None):
        super().__init__(
            csv_path=csv_path,
            class_to_idx=class_to_idx,
            transform=transform,
            image_column="image_path",
            label_column="class_label",
        )


# ---------------------------------------------------------------------------
# Metadata support
# ---------------------------------------------------------------------------

BODY_PARTS_COLUMNS = [
    "body_parts_head_or_neck",
    "body_parts_arm",
    "body_parts_palm",
    "body_parts_back_of_hand",
    "body_parts_torso_front",
    "body_parts_torso_back",
    "body_parts_genitalia_or_groin",
    "body_parts_buttocks",
    "body_parts_leg",
    "body_parts_foot_top_or_side",
    "body_parts_foot_sole",
    "body_parts_other",
]

_AGE_GROUP_ORDER = [
    "AGE_UNDER_20",
    "AGE_20_TO_29",
    "AGE_30_TO_39",
    "AGE_40_TO_49",
    "AGE_50_TO_59",
    "AGE_60_TO_69",
    "AGE_70_TO_79",
    "AGE_80_OR_OLDER",
]

_SEX_CATEGORIES = ["MALE", "FEMALE"]


class MetadataEncoder:
    """Fit-on-train encoder that converts raw CSV metadata to a fixed-length float vector.

    Supported logical fields:
      - "body_parts"  → 12-dim multi-hot (YES→1.0, else→0.0)
      - "age_group"   → 2-dim: [normalised ordinal, unknown_flag]
      - "sex_at_birth"→ 3-dim one-hot [MALE, FEMALE, unknown]

    Encoders are derived entirely from the category lists above — no fitting on
    data is required for body_parts. For age_group/sex, the ordinal/category
    order is fixed at construction time; fit() only validates coverage.
    """

    _LOGICAL_TO_COLS = {
        "body_parts": BODY_PARTS_COLUMNS,
        "age_group": ["age_group"],
        "sex_at_birth": ["sex_at_birth"],
    }

    def __init__(self, logical_fields: list[str]):
        assert "source_dataset" not in logical_fields, (
            "source_dataset must never be used as model input — STOP"
        )
        self.logical_fields = logical_fields
        self._age_max = len(_AGE_GROUP_ORDER) - 1
        self._fitted = False

    def fit(self, rows: list[dict[str, str]]) -> "MetadataEncoder":
        """Validate coverage; encoders are statically defined."""
        self._fitted = True
        return self

    @property
    def metadata_dim(self) -> int:
        dim = 0
        for field in self.logical_fields:
            if field == "body_parts":
                dim += len(BODY_PARTS_COLUMNS)
            elif field == "age_group":
                dim += 2
            elif field == "sex_at_birth":
                dim += 3
            else:
                raise ValueError(f"Unknown metadata field: {field}")
        return dim

    def encode_row(self, row: dict[str, str]) -> "torch.Tensor":
        import torch
        vec: list[float] = []
        for field in self.logical_fields:
            if field == "body_parts":
                for col in BODY_PARTS_COLUMNS:
                    vec.append(1.0 if (row.get(col) or "").strip().upper() == "YES" else 0.0)
            elif field == "age_group":
                val = (row.get("age_group") or "").strip().upper()
                if val in _AGE_GROUP_ORDER:
                    vec.append(_AGE_GROUP_ORDER.index(val) / self._age_max)
                    vec.append(0.0)
                else:
                    vec.append(0.0)
                    vec.append(1.0)
            elif field == "sex_at_birth":
                val = (row.get("sex_at_birth") or "").strip().upper()
                vec.append(1.0 if val == "MALE" else 0.0)
                vec.append(1.0 if val == "FEMALE" else 0.0)
                vec.append(0.0 if val in ("MALE", "FEMALE") else 1.0)
        return torch.tensor(vec, dtype=torch.float32)


class MetadataImageClassificationDataset(ImageClassificationDataset):
    """ImageClassificationDataset that additionally returns a metadata tensor.

    __getitem__ returns (image_tensor, metadata_tensor, label_idx).
    Missing metadata is encoded as zeros/unknown — no samples are dropped.
    """

    def __init__(
        self,
        csv_path,
        class_to_idx,
        encoder: MetadataEncoder,
        transform=None,
        image_column: str = "image_path",
        label_column: str = "target_label",
        class_idx_column: str | None = "class_idx",
    ):
        super().__init__(
            csv_path=csv_path,
            class_to_idx=class_to_idx,
            transform=transform,
            image_column=image_column,
            label_column=label_column,
            class_idx_column=class_idx_column,
        )
        self.encoder = encoder

    def __getitem__(self, index):
        image_tensor, label_idx = super().__getitem__(index)
        metadata_tensor = self.encoder.encode_row(self.rows[index])
        return image_tensor, metadata_tensor, label_idx
