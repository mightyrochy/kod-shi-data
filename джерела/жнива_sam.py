# -*- coding: utf-8 -*-
"""GroundingDINO + SAM у власному середовищі; один запит — один процес.

На stdout пише лише PNG маски. Завершення процесу звільняє всю відеопам'ять,
тому модель не залишається на карті між запитами жнив і живим прогоном.
"""
import io
import os
import sys

ЗОВНІШНІ_ВХОДИ = {
    "boxes": "GroundingDinoProcessor.post_process_grounded_object_detection: рамки знайдених речей xyxy.",
    "original_sizes": "SamProcessor: вихідні розміри фото (висота, ширина) для відновлення маски.",
    "reshaped_input_sizes": "SamProcessor: розміри фото після масштабування до входу SAM, до padding.",
}


def маска(шлях, слово):
    """Знаходить рамки слова GroundingDINO й об'єднує маски SAM цих рамок."""
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor, SamModel, SamProcessor

    пристрій = "cpu"
    torch.set_num_threads(min(8, os.cpu_count() or 1))
    фото = Image.open(шлях).convert("RGB")
    детектор = "IDEA-Research/grounding-dino-tiny"
    сегментатор = "facebook/sam-vit-base"
    ревізія = "a2bb814dd30d776dcf7e30523b00659f4f141c71"
    процесор = AutoProcessor.from_pretrained(детектор, revision=ревізія, local_files_only=True)
    модель = AutoModelForZeroShotObjectDetection.from_pretrained(
        детектор, revision=ревізія, local_files_only=True).to(пристрій).eval()
    вхід = процесор(images=фото, text=слово + ".", return_tensors="pt").to(пристрій)
    with torch.inference_mode():
        вихід = модель(**вхід)
    рамки = процесор.post_process_grounded_object_detection(
        вихід, вхід.input_ids, box_threshold=0.3, text_threshold=0.25,
        target_sizes=[фото.size[::-1]])[0]["boxes"].cpu().tolist()
    del модель, вихід, вхід
    if not рамки:
        return Image.fromarray(np.zeros(фото.size[::-1], dtype="uint8"))
    ревізія = "70c1a07f894ebb5b307fd9eaaee97b9dfc16068f"
    процесор = SamProcessor.from_pretrained(сегментатор, revision=ревізія, local_files_only=True)
    модель = SamModel.from_pretrained(сегментатор, revision=ревізія, local_files_only=True).to(пристрій).eval()
    вхід = процесор(images=фото, input_boxes=[рамки], return_tensors="pt").to(пристрій)
    with torch.inference_mode():
        вихід = модель(**вхід, multimask_output=False)
    маски = процесор.image_processor.post_process_masks(
        вихід.pred_masks.cpu(), вхід["original_sizes"].cpu(), вхід["reshaped_input_sizes"].cpu())[0]
    return Image.fromarray(маски.numpy().any(axis=(0, 1)).astype("uint8") * 255)


def головна():
    """Віддає PNG маски; залежності не бачать однойменного продуктового profile.py."""
    тека = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [п for п in sys.path if os.path.abspath(п) != тека]
    # Пакети моделей можуть друкувати діагностику; stdout — бінарний контракт.
    from contextlib import redirect_stdout
    with redirect_stdout(sys.stderr):
        зображення = маска(sys.argv[1], sys.argv[2])
    буфер = io.BytesIO()
    зображення.save(буфер, format="PNG")
    sys.stdout.buffer.write(буфер.getvalue())


if __name__ == "__main__":
    головна()
