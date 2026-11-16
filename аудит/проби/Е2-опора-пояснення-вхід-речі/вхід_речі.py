# -*- coding: utf-8 -*-
"""Вхід про річ ДО → ПІСЛЯ на записаних прогонах «як людина» 1, 3, 4 (наряд Е2-опора-пояснення-вхід-речі).

ДО — що реально пішло в модель: дріт `ОПИС` (речі образу й запасні) і перелік речей перекладачки з обмінів прогону.
ПІСЛЯ — те саме через складач гілки (`знання_речі.певне`, `мовний_шар.промпт`) на речах, відновлених із дроту ДО:
вид — ключем ядра, колір — кодом виміру кадру (hex), а не словом запису, кадр іншого кольору, кадри, ознаки. Повтор входу, не відповідей: відповіді моделі
правки не міряють (наряд). Запуск з кореня: python3 аудит/проби/Е2-опора-пояснення-вхід-речі/вхід_речі.py"""
import collections, glob, gzip, json, os, re, sys
sys.path.insert(0, "джерела")
import внутрішня_мова as ВМ, знання_речі as ЗН, мовний_шар as МШ

СЛУЖБОВІ = {"n", "photos", "no_photo", "hers", "photo_other_colour"}
ПЕРЕКЛАД = re.compile(r"^(\S+) — (.*)$")


def річ_з_дроту(x):
    return dict(н=x.get("n"), слот=ВМ.ключ("slot", x["kind"]) if x.get("kind") else None,
                тип=ВМ.ключ("item_type", x["type"]) if x.get("type") else None,
                частина={"top": "верх", "bottom": "низ"}.get(x.get("set_half")), код_кольору=x.get("color"),
                hex=x.get("hex"), кадр_колір=x.get("photo_other_colour"), фото_номери=x.get("photos"),
                без_кадру=x.get("no_photo"), її_річ=x.get("hers"),
                ознаки={к: v for к, v in x.items() if к not in СЛУЖБОВІ | {"kind", "type", "set_half", "color", "hex"}})


def дріт_опису(т):
    і = т.find('"outfit": {"id"')
    if і < 0:
        return None
    д, _ = json.JSONDecoder().raw_decode("{" + т[і:])
    return д


л = collections.Counter()
приклади, розбіжні = [], []
for шлях in sorted(glob.glob("аудит/проби/живий-як-людина-[134]/стенд/службове/*/обміни.jsonl.gz")):
    прогін, сцена = шлях.split("/")[2][-1], шлях.split("/")[-2][:2]
    for рядок, з in enumerate(gzip.open(шлях, "rt"), 1):
        з = json.loads(з)
        try:
            тексти = [b["text"] for m in json.loads(з["запит"])["messages"] for b in (m["content"] if isinstance(
                m["content"], list) else [dict(type="text", text=m["content"])]) if b.get("type") == "text"]
        except (ValueError, KeyError, TypeError):
            continue
        for т in тексти:
            д = дріт_опису(т) if '"about_items"' in т or "about_items" in т else None
            if д:
                л["викликів опису"] += 1
                речі = д["outfit"]["items"] + ((д.get("swap_spares") or {}).get("spares") or [])
                for x in речі:
                    до = {к for к in x if к not in СЛУЖБОВІ}
                    після = {к for к in ЗН.певне(річ_з_дроту(x)) if к not in СЛУЖБОВІ}
                    л["речей"] += 1
                    л["властивостей ДО"] += len(до)
                    л["властивостей ПІСЛЯ"] += len(після)
                    л["без певності ДО"] += len(до - після)
                    л["колір без виміру ДО"] += 1 if x.get("color") and not x.get("hex") else 0
                    л["колір без виміру ПІСЛЯ"] += 1 if "color" in після and "hex" not in після else 0
                    п_ = ЗН.певне(річ_з_дроту(x))
                    if x.get("color") and x.get("hex"):
                        л["колір з виміром ДО"] += 1
                        if п_.get("color") != x["color"]:
                            л["колір слова ≠ код виміру кадру (ПІСЛЯ — код виміру)"] += 1
                            if len(розбіжні) < 8:
                                розбіжні.append("%s с%s ряд.%d %s: слово %s, hex %s → %s" % (
                                    прогін, сцена[1], рядок, x.get("n"), x["color"], x["hex"], п_.get("color")))
                    л["ознак запису ДО"] += len(до - {"kind", "type", "set_half", "color", "hex"})
                    л["ознак запису ПІСЛЯ"] += len(після - {"kind", "type", "set_half", "color", "hex"})
                    if до - після and len(приклади) < 6 and x.get("color") and not x.get("hex"):
                        приклади.append("%s с%s ряд.%d %s: ДО %s → ПІСЛЯ %s" % (прогін, сцена[1], рядок, x.get("n"),
                                        sorted(до), sorted(після)))
            if "Речі образу — перелік речей картки" in т:
                л["викликів перекладачки з переліком"] += 1
                абзац = т.split("Речі образу — перелік речей картки", 1)[1].split("\n\n", 1)[0]
                рядки = [ПЕРЕКЛАД.match(р) for р in абзац.splitlines()[1:]]
                рядки = [р for р in рядки if р and ("code:" in р.group(2) or "text н=" in р.group(2))]
                л["код кольору біля речі ДО"] += sum("colour code:" in р.group(2) for р in рядки)
                л["правило «код на місці слова» ДО"] += int("whatever word the English text uses" in абзац
                                                            or "stands in their place" in абзац)
                речі, розмітка = [], []
                for р in рядки:
                    поля = dict(re.findall(r"(kind code|colour code): (\S+)", р.group(2)))
                    про = re.search(r"about it: text н=(\d+)", р.group(2))
                    річ = dict(н=р.group(1), тип=ВМ.ключ("item_type", поля.get("kind code")) or None,
                               код_кольору=поля.get("colour code"))
                    if про:
                        розмітка.append(dict(н=int(про.group(1)), ключ="т%s" % про.group(1), текст="x"))
                        річ["опис"] = "т%s" % про.group(1)
                    речі.append(річ)
                п = МШ.промпт(розмітка or [dict(н=1, ключ="т", текст="x")], речі)
                л["код кольору біля речі ПІСЛЯ"] += п.count("colour code:")
                л["правило «код на місці слова» ПІСЛЯ"] += int("whatever word the English text uses" in п
                                                               or "stands in their place" in п)
for к, v in л.items():
    print("%s: %d" % (к, v))
print("приклади (колір без виміру):")
print("\n".join(приклади))
print("приклади (слово ≠ вимір):")
print("\n".join(розбіжні))
