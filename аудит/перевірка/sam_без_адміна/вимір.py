# -*- coding: utf-8 -*-
"""Повторює маски на незмінних 60 речах збереженої вибірки, без мовної моделі."""
import collections
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def головна():
    """Міряє ДО/ПІСЛЯ тим самим конвеєром ATR → SAM → запасна та пише докази."""
    корінь = Path(__file__).resolve().parents[3]
    джерела = корінь / "джерела"
    sys.path.insert(0, str(джерела))
    os.environ["OSS_PATH"] = str(корінь / "open-source-stylist")
    os.environ["LEFFA_PATH"] = str(Path.home() / ".cache/liusterko/sam/Leffa")
    import жнива_маски as М
    from PIL import Image
    import numpy as np

    вибірка = джерела / "аудит/збагачення_v2_вибірка.json"
    дані = json.loads(вибірка.read_text(encoding="utf-8"))
    вихід = Path(__file__).with_name("вимір.json")
    звіт = dict(вибірка=str(вибірка.relative_to(корінь)),
                sha256=hashlib.sha256(вибірка.read_bytes()).hexdigest(), речі=[])
    приклад = False
    for річ in дані["речі"]:
        фото = джерела / "аудит" / річ.get("фото_показу", "НЕМА")
        запис = dict(id=річ["id"], слот=річ["слот"])
        if not фото.is_file():
            запис["пропущено"] = "у вихідній вибірці немає фото"
        else:
            початок = time.monotonic()
            запис["фото_sha256"] = hashlib.sha256(фото.read_bytes()).hexdigest()
            os.environ["ЖНИВА_SAM_PYTHON"] = str(Path(__file__).with_name("НЕМА_python"))
            до = М.маска_речі(str(фото), річ["слот"])
            запис["до"] = dict(маска=dict(частка=до[1], джерело=до[3], чому=до[2]))
            del os.environ["ЖНИВА_SAM_PYTHON"]
            після = М.маска_речі(str(фото), річ["слот"])
            запис["після"] = dict(маска=dict(частка=після[1], джерело=після[3], чому=після[2]))
            арр = М._мітки_atr(str(фото))
            регіони = М.СЛОТ_РЕГІОНИ.get(М.група_слота(річ["слот"])) or []
            атр = М.маска_atr(str(фото), регіони, арр)
            запис["atr_пікселів"] = int(np.count_nonzero(атр[0])) if атр[0] is not None else 0
            запис["sam_пікселів"] = int(np.count_nonzero(після[0])) if після[3] == "SAM" else 0
            запис["секунд"] = round(time.monotonic() - початок, 2)
            if запис["atr_пікселів"] == 0 and запис["sam_пікселів"] > 0 and not приклад:
                м = Image.fromarray(після[0])
                м.save(Path(__file__).with_name("маска.png"))
                im = Image.open(фото).convert("RGB")
                панелі = [im, м.convert("RGB"), Image.composite(im, Image.new("RGB", im.size, "#606060"), м)]
                знімок = Image.new("RGB", (im.width * 3, im.height))
                for i, панель in enumerate(панелі):
                    знімок.paste(панель, (i * im.width, 0))
                знімок.thumbnail((1500, 900))
                знімок.save(Path(__file__).with_name("приклад.jpg"), quality=92)
                звіт["приклад"] = запис["id"]
                приклад = True
        звіт["речі"].append(запис)
        вихід.write_text(json.dumps(звіт, ensure_ascii=False, indent=2), encoding="utf-8")
        print(len(звіт["речі"]), запис["id"], запис.get("після", {}), запис.get("секунд", ""), flush=True)
    звіт["до"] = dict(collections.Counter(р["до"]["маска"]["джерело"] for р in звіт["речі"] if "до" in р))
    звіт["після"] = dict(collections.Counter(р["після"]["маска"]["джерело"] for р in звіт["речі"] if "після" in р))
    вихід.write_text(json.dumps(звіт, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ДО:", звіт["до"], "ПІСЛЯ:", звіт["після"], "приклад:", звіт.get("приклад"), flush=True)
    assert звіт["до"].get("SAM", 0) == 0 and звіт["після"].get("SAM", 0) > 0 and приклад


if __name__ == "__main__":
    головна()
