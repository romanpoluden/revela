from __future__ import annotations

from collections import Counter


ECZEMA_CLASS = "Eczema / dermatitis"
URTICARIA_CLASS = "Urticaria / allergic reaction"
PSORIASIS_CLASS = "Psoriasis / papulosquamous"
LESION_ROUTING_CLASS = "Lesion — dermoscopic review recommended"


def count_confusion(
    confusion_matrix: list[list[int]],
    class_names: list[str],
    true_class: str,
    predicted_class: str,
) -> int:
    class_to_idx = {class_name: index for index, class_name in enumerate(class_names)}
    return int(confusion_matrix[class_to_idx[true_class]][class_to_idx[predicted_class]])


def compute_focus_error_metrics(
    true_labels: list[int],
    predicted_labels: list[int],
    confusion_matrix: list[list[int]],
    class_names: list[str],
) -> dict:
    class_to_idx = {class_name: index for index, class_name in enumerate(class_names)}
    lesion_idx = class_to_idx[LESION_ROUTING_CLASS]
    urticaria_idx = class_to_idx[URTICARIA_CLASS]

    lesion_false_negative_predictions = [
        predicted_label
        for true_label, predicted_label in zip(true_labels, predicted_labels)
        if true_label == lesion_idx and predicted_label != lesion_idx
    ]
    predicted_label_counts = Counter(
        class_names[predicted_label]
        for predicted_label in lesion_false_negative_predictions
    )

    urticaria_false_positives = sum(
        1
        for true_label, predicted_label in zip(true_labels, predicted_labels)
        if predicted_label == urticaria_idx and true_label != urticaria_idx
    )

    return {
        "lesion_routing_false_negatives": len(lesion_false_negative_predictions),
        "lesion_routing_false_negative_predicted_labels": dict(
            predicted_label_counts.most_common()
        ),
        "eczema_to_urticaria": count_confusion(
            confusion_matrix, class_names, ECZEMA_CLASS, URTICARIA_CLASS
        ),
        "eczema_to_psoriasis": count_confusion(
            confusion_matrix, class_names, ECZEMA_CLASS, PSORIASIS_CLASS
        ),
        "psoriasis_to_eczema": count_confusion(
            confusion_matrix, class_names, PSORIASIS_CLASS, ECZEMA_CLASS
        ),
        "psoriasis_to_urticaria": count_confusion(
            confusion_matrix, class_names, PSORIASIS_CLASS, URTICARIA_CLASS
        ),
        "lesion_to_psoriasis": count_confusion(
            confusion_matrix, class_names, LESION_ROUTING_CLASS, PSORIASIS_CLASS
        ),
        "urticaria_false_positives": urticaria_false_positives,
    }
