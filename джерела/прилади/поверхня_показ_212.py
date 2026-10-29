# -*- coding: utf-8 -*-
"""Збережені 40 кадрів → вимір жнив і рамки показу, час та сирі результати ДО/ПІСЛЯ.

Запуск із кореня: python джерела/прилади/поверхня_показ_212.py --вихід <поза git>.
Рамка — обвідний прямокутник маски 2.12; поле 12 %, сторона ≤128 px.
"""
import argparse
import base64
import json
from pathlib import Path
import sys
import time

ДЖЕРЕЛА = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ДЖЕРЕЛА))


def кадри(тека):
    """Читає кадри та будує рамки з масок; RGB для Pyodide зберігає числами."""
    import cv2
    from проби.поверхня_212 import читати
    записи = json.loads((тека / "вимір.json").read_text(encoding="utf-8"))["записи"]
    for з in записи:
        к = з["ключ"]
        if not к.isdigit() or з.get("помилка"):
            continue
        кадр = читати(str(тека / (к + ".jpg")))
        маска = читати(str(тека / (к + ".маска.png")), cv2.IMREAD_GRAYSCALE)
        арр = читати(str(тека / (к + ".atr.png")), cv2.IMREAD_GRAYSCALE)
        if кадр is None or маска is None:
            raise RuntimeError("Нема кадру або маски: " + к)
        h, w = кадр.shape[:2]
        if маска.shape != (h, w):
            маска = cv2.resize(маска, (w, h), interpolation=cv2.INTER_NEAREST)
        yy, xx = (маска > 127).nonzero()
        л, п, в, н = int(xx.min()), int(xx.max()) + 1, int(yy.min()), int(yy.max()) + 1
        дx, дy = (п - л) * .12, (н - в) * .12
        x0, y0, x1, y1 = max(0, round(л - дx)), max(0, round(в - дy)), min(w, round(п + дx)), min(h, round(н + дy))
        виріз = кадр[y0:y1, x0:x1]
        ш, ви = x1 - x0, y1 - y0
        кф = min(1, 128 / max(ш, ви))
        виріз = cv2.resize(виріз, (max(1, round(ш * кф)), max(1, round(ви * кф))), interpolation=cv2.INTER_AREA)
        rgb = виріз[:, :, ::-1].reshape(-1, 3).tolist()
        пікселі = dict(дані=base64.urlsafe_b64encode(bytes(с for пікс in rgb for с in пікс)).decode().rstrip("="),
                       ширина=виріз.shape[1], висота=виріз.shape[0],
                       ядро=dict(ліво=round((л-x0)/ш*1000), право=round((п-x0)/ш*1000),
                                 верх=round((в-y0)/ви*1000), низ=round((н-y0)/ви*1000)))
        yield з, кадр, маска, арр, пікселі, rgb


def main():
    """Міряє обидва виробничі входи без мережі й записує факти поза git."""
    import жнива_колір as Ж
    import річ_з_фото as Р
    from проби.поверхня_212 import споживачеві
    ап = argparse.ArgumentParser(description=__doc__)
    ап.add_argument("--вихід", type=Path, required=True)
    ап.add_argument("--ключі", nargs="*", help="лише названі кадри для досліду розбіжностей")
    ап.add_argument("--показ-із", type=Path, help="повторити лише показ зі збережених RGB та вимірів жнив")
    ап.add_argument("--тека", type=Path, default=ДЖЕРЕЛА.parent / "аудит/проби/поверхня_212")
    а = ап.parse_args()
    if а.показ_із:
        вих = json.loads(а.показ_із.read_text(encoding="utf-8"))
        for з in вих:
            t = time.perf_counter()
            з["показ"] = Р.виміряти(з["пікселі"], рамка=True)
            з["показ_мс"] = (time.perf_counter()-t)*1000
            print(з["ключ"], з["показ"].get("слово"), round(з["показ_мс"]), flush=True)
        а.вихід.write_text(json.dumps(вих, ensure_ascii=False), encoding="utf-8")
        return
    вих = []
    for з, кадр, маска, арр, пікселі, rgb in кадри(а.тека):
        if а.ключі and з["ключ"] not in а.ключі:
            continue
        t = time.perf_counter()
        п = Ж.виміряти_поверхню(кадр, маска, арр, джерело=з.get("маска"))
        ж_мс = (time.perf_counter() - t) * 1000
        осн = Ж.звести_колір(п["сегменти"], None, з.get("слова_крамниці"))[0] if п["придатна"] else None
        сп = споживачеві(осн, з.get("слова_крамниці"), п["візерунок"] == "однотонний")
        t = time.perf_counter()
        в = Р.виміряти(пікселі, рамка=True)
        п_мс = (time.perf_counter() - t) * 1000
        вих.append(dict(ключ=з["ключ"], жнива=п, споживачеві=сп, показ=в, жнива_мс=ж_мс, показ_мс=п_мс,
                        rgb=rgb, пікселі=пікселі))
        print(з["ключ"], п["придатна"], п["візерунок"], в.get("слово"), round(ж_мс), round(п_мс), flush=True)
    а.вихід.parent.mkdir(parents=True, exist_ok=True)
    а.вихід.write_text(json.dumps(вих, ensure_ascii=False), encoding="utf-8")
    print("Виміряно", len(вих), "із 40; відсутні кадри названо у вимір.json")


if __name__ == "__main__":
    main()
