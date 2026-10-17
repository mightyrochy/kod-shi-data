# -*- coding: utf-8 -*-
"""Читає фід крамниці-партнера (YML Prom/Rozetka чи Google Merchant, можна .gz) і друкує рівень Р0–Р3 й чого бракує.
Чому так: ключі рівнів — `аудит/дослідження_research/каталог_партнерів_рівні.json`, спільні зі специфікацією; проба
бачить лише, чи поле є (п.12), а зі значень — роль «на моделі» (чи `on_model`) й роздільники кольору. Без аргументу — приклади."""
import sys, gzip, json, pathlib, collections
from xml.etree import ElementTree as ET
_ТЕКА = pathlib.Path(__file__).resolve().parents[2] / "аудит/дослідження_research"
_К = json.loads((_ТЕКА / "каталог_партнерів_рівні.json").read_text(encoding="utf-8"))
_G, _Т, _Р = "{http://base.google.com/ns/1.0}", lambda е: "".join(е.itertext()).strip(), lambda р: "Р%d" % р if р >= 0 else "нижче Р0"
_ВАР = lambda п: (п.get("модель"), п.get("Колір"))                     # варіант: модель + колір
def поля(о):
    """Офер YML чи item Google → ({ключ специфікації: текст, фото: кількість}, [адреси фото])."""
    д, г = _К["google" if о.tag == "item" else "yml"], о.tag == "item"
    п = {д.get(к.replace(_G, ""), к.replace(_G, "") if г else None): в for к, в in [*о.attrib.items(), *((е.tag, _Т(е)) for е in о)]
         if в}
    п |= {е.get("name"): _Т(е) for е in о.findall("param")} | {
        е.findtext(_G + "attribute_name"): е.findtext(_G + "attribute_value") for е in о.iter(_G + "product_detail")}
    фото = [_Т(е) for е in о if е.tag in ("picture", _G + "image_link", _G + "additional_image_link") and _Т(е)]
    return dict(п, фото=len(фото)), фото
def рівень(п, фото, кратний, спільні):
    """Повертає (досягнутий рівень 0–3, -1 — нижче Р0; чого бракує до наступного). Р1 має ще три правила формату."""
    for н, р in enumerate(_К["рівні"]):
        нема = [" | ".join(г) for г in р["поля"] if not any(п.get(к) for к in г)]
        нема += [к for к, роль in р.get("коли", {}).items() if not п.get(к) and any(
            р in п.get("Ролі фото", "") for р in (роль, _К["ролі"][роль]))]
        нема += [] if н != 1 else ["Розмір"] * bool(кратний and not п.get("Розмір")) + ["один колір на офер"] * any(
            з in п.get("Колір", "") for з in ",;|/") + ["свої фото варіанта"] * any(спільні[ф] > 1 for ф in фото)
        if нема:
            return н - 1, нема
    return 3, []
def звіт(шлях):
    """Друкує рівень фіда (найвищий, якого досягли ≥ «поріг» оферів), розподіл оферів і чого бракує до наступного."""
    к = ET.parse(gzip.open(шлях) if шлях.suffix == ".gz" else шлях).getroot()
    оф = [(о.get("id") or о.findtext(_G + "id"), *поля(о)) for о in [*к.iter("offer"), *к.iter("item")]]
    групи, посил = collections.Counter(_ВАР(п) for _, п, _ in оф), {_Т(е) for е in к.iter("offerRef")}   # offerRef — образ Р3
    спільні = collections.Counter(ф for ф, _ in {(ф, _ВАР(п)) for _, п, фф in оф for ф in фф})       # варіантів на фото
    образи = {_ВАР(п) for і, п, _ in оф if і in посил}
    підс = [(і, *рівень(dict(п, образ=_ВАР(п) in образи), фф, п.get("модель") and групи[_ВАР(п)] > 1, спільні)) for і, п, фф in оф]
    if not підс:
        return print("%s: порожній фід — нижче Р0" % шлях.name)
    ч = collections.Counter(р for _, р, _ in підс)
    фід = max(р for р in range(-1, 4) if sum(ч[x] for x in range(р, 4)) >= _К["поріг"] * len(підс))
    print("%s: рівень фіда %s · оферів %d (%s)" % (шлях.name, _Р(фід), len(підс), " · ".join("%s %d" % (_Р(р), ч[р]) for р in range(3, -2, -1))))
    [print("  offer %s: %s%s" % (ід, _Р(р), ", до %s бракує: %s" % (_Р(р + 1), ", ".join(нема)) if нема else ""))
     for ід, р, нема in (підс if len(підс) <= 50 else [])]
    бракує = collections.Counter(х for _, р, н in підс if р == фід for х in н).most_common(12)
    print("  до %s бракує (оферів): %s" % (_Р(фід + 1), dict(бракує)) if фід < 3 else "  вищий рівень")
if __name__ == "__main__":
    [звіт(ш) for ш in [*map(pathlib.Path, sys.argv[1:])] or sorted(_ТЕКА.glob("каталог_партнерів_р*.xml"))]
