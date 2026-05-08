from __future__ import annotations

import csv
from pathlib import Path

import torch
from PIL import Image, UnidentifiedImageError
from torch.utils.data import Dataset


class BCN20000Dataset(Dataset):
    """PyTorch dataset for BCN20000 images prepared for the Revela project."""

    def __init__(self, csv_path, class_to_idx, transform=None):
        self.csv_path = Path(csv_path)
        self.class_to_idx = dict(class_to_idx)
        self.transform = transform
        self.required_columns = ["image_path", "class_label"]

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
            image_path = (row.get("image_path") or "").strip()
            class_label = (row.get("class_label") or "").strip()

            if not image_path:
                raise ValueError(
                    f"Row {row_index} in {self.csv_path} is missing `image_path`."
                )
            if not class_label:
                raise ValueError(
                    f"Row {row_index} in {self.csv_path} is missing `class_label`."
                )
            if class_label not in self.class_to_idx:
                raise KeyError(
                    f"Row {row_index} has class_label `{class_label}` that is not "
                    "present in class_to_idx."
                )

            cleaned_rows.append(
                {
                    "image_path": image_path,
                    "class_label": class_label,
                }
            )

        return cleaned_rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        image_path = Path(row["image_path"])
        class_label = row["class_label"]
        label_idx = self.class_to_idx[class_label]

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
