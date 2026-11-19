"""Порівнює однакову фікстуру у справжньому рендері зібраних HTML ДО й ПІСЛЯ."""
import json
import pathlib
from PIL import Image, ImageChops

тека = pathlib.Path(__file__).resolve().parent
до, після = тека / "base-картки", тека / "head-картки"
імена = sorted(p.name for p in до.glob("*.png"))
assert len(імена) == 8 and імена == sorted(p.name for p in після.glob("*.png"))
звіт = []
for ім in імена:
    а, б = Image.open(до / ім).convert("RGB"), Image.open(після / ім).convert("RGB")
    межі = ImageChops.difference(а, б).getbbox() if а.size == б.size else "розміри різні"
    звіт.append(dict(файл=ім, розмір=а.size, різниця=межі))
    print(ім, а.size, "різниця:", межі)
текст_рівний = (до / "текст-карток.txt").read_text(encoding="utf-8") == (після / "текст-карток.txt").read_text(encoding="utf-8")
print("Тексти ДО = ПІСЛЯ:", текст_рівний)
(тека / "порівняння-знімків.json").write_text(json.dumps(dict(знімки=звіт, текст_рівний=текст_рівний), ensure_ascii=False, indent=2), encoding="utf-8")
assert текст_рівний and all(р["різниця"] is None for р in звіт if "ціла" in р["файл"])
