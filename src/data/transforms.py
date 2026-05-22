from __future__ import annotations

from torchvision import transforms


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_train_transforms(image_size, strategy: str = "baseline"):
    """Training augmentations. strategy: 'baseline' | 'mild_clinical' | 'robust_clinical'."""
    if strategy == "mild_clinical":
        return transforms.Compose(
            [
                transforms.RandomResizedCrop(image_size, scale=(0.85, 1.0), ratio=(0.9, 1.1)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=10),
                transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.05, hue=0.0),
                transforms.ToTensor(),
                transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ]
        )
    if strategy == "robust_clinical":
        return transforms.Compose(
            [
                transforms.RandomResizedCrop(image_size, scale=(0.80, 1.0), ratio=(0.9, 1.1)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=15),
                transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.05, hue=0.0),
                transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 0.5)),
                transforms.RandomGrayscale(p=0.02),
                transforms.ToTensor(),
                transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ]
        )
    # default: "baseline" — original dermoscopic transforms preserved exactly
    return transforms.Compose(
        [
            transforms.RandomResizedCrop(
                image_size,
                scale=(0.9, 1.0),
                ratio=(0.95, 1.05),
            ),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            transforms.ColorJitter(
                brightness=0.1,
                contrast=0.1,
                saturation=0.05,
                hue=0.02,
            ),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def get_eval_transforms(image_size):
    """Stable evaluation transforms without heavy augmentation."""
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )
