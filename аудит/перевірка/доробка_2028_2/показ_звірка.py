"""Звіряє DOM з мостом і складає огляди знімків для перевірки очима."""
import gzip
import json
import pathlib
import re
from PIL import Image, ImageDraw, ImageFont


def головна():
    """Перевіряє кожен чип і стрічку, зберігає контактні аркуші схем."""
    тека = pathlib.Path(__file__).resolve().parent
    сцени = json.loads(gzip.decompress((тека / "екрани.json.gz").read_bytes()))
    дані = {с["сцена"]: с for с in сцени}
    rgb = lambda h: tuple(int(h.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    css = lambda s: tuple(map(int, re.findall(r"\d+", s))) if s else None
    чипів = стрічок = 0
    for схема in ("аналогова", "тріада"):
        факти = json.loads((тека / схема / "показ.json").read_text(encoding="utf-8"))
        огляд = Image.new("RGB", (390 * 4, 492 * 4), "white")
        малюнок = ImageDraw.Draw(огляд)
        шрифт = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
        for і, ф in enumerate(факти):
            гілки = дані[ф["сцена"]][ф["режим"]]["гілки"]
            assert len(ф["чипи"]) - 1 == len(гілки)
            for чип, гілка in zip(ф["чипи"][1:], гілки):
                assert [css(s) for s in чип["кольори"]] == [rgb(h) for h in гілка["зразки"]]
                чипів += 1
            обрана = next(г for г in гілки if г["схема"] == схема)
            assert [css(s) for s in ф["стрічка"] if s] == [rgb(h) for h in обрана["зразки"]]
            стрічок += 1
            x, y = (і % 4) * 390, (і // 4) * 492
            малюнок.text((x + 6, y + 5), ф["сцена"] + " " + ф["режим"], fill="black", font=шрифт)
            знімок = Image.open(тека / схема / (ф["сцена"] + "-" + ф["режим"] + ".png"))
            огляд.paste(знімок.crop((0, 150, 390, 610)), (x, y + 32))
        огляд.save(тека / ("огляд-" + схема + ".jpg"), quality=92)
    р = dict(чипів=чипів, стрічок=стрічок, знімків=стрічок, ширина=390, висота=844)
    (тека / "показ-вимір.json").write_text(json.dumps(р, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(р, ensure_ascii=False))


if __name__ == "__main__":
    головна()
