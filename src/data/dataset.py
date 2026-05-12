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

            cleaned_rows.append(
                {
                    "image_path": image_path,
                    "class_label": class_label,
                    "label_idx": label_idx,
                }
            )

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
