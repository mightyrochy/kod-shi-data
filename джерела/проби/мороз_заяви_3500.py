"""Проба (рядок 3500): чим заяви суду кажуть погоду, коли вона сказала лише «мороз» (паспорт `погода_відчуття=frost`,
`темп_c` нема), проти −15 °C — образ сукня + бомбер ж-04775 (ЖИВІ-13 №8, рука 1), заглушка, каталог_повний.
Друкує: заяви K-WEA-01 з полями `temperature_c` / `weather_feel` і лічбу таких заяв у всьому вердикті (суд, аксесуари,
крок редагування). Число коду (−10 °C) — лише порогам суду, не заявам. Моделі не кличе.
Запуск: cd джерела && python3 проби/мороз_заяви_3500.py"""
import json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed as Ф, bridge as B, міст_пакет as МП
ОБРАЗ = ["ж-01507@wearme.ua", "ж-08693@vittorossi.ua", "ж-08121@welfare.ua", "ж-04775@wearme.ua", "ж-08657@likeangel.com.ua"]


def заяви(x):
    """Усі заяви (`{code, values}`) вердикту, де б вони не стояли."""
    if isinstance(x, dict):
        if "code" in x and isinstance(x.get("values"), dict):
            yield x
        for v in x.values():
            yield from заяви(v)
    elif isinstance(x, list):
        for v in x:
            yield from заяви(v)


база = json.load(open("стенд_вх.json", encoding="utf-8"))
кат_файл = Ф.каталог_на_диску("каталог_повний.xml")
for назва, погода in (("мороз без числа", dict(погода_відчуття="frost", опади="сніг")),
                      ("−15 °C, сніг", dict(темп_c=-15, опади="сніг"))):
    сц = {k: v for k, v in база["сценарій"].items() if k != "темп_c"}
    вх = dict(база, каталог=кат_файл, гілка=0, сценарій=сц, паспорт=dict(погода), випадок="робочий день, пішки")
    МП._КЕШ_ПАКЕТА.clear()
    B.виклик("запити", json.dumps(вх, ensure_ascii=False))
    в = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ОБРАЗ), ensure_ascii=False))).get("вердикт") or {}
    о = (в.get("образи") or [{}])[0]
    print("== %s" % назва)
    for z in о.get("знахідки") or []:
        if z.get("правило") == "K-WEA-01":
            print("   K-WEA-01 %s/%s:" % (z["сила"], z["регістр"]), [(x["code"], {k: x["values"][k] for k in
                  ("temperature_c", "weather_feel") if k in x["values"]}) for x in z.get("заяви") or []])
    вс = list(заяви(в))
    print("   заяв у вердикті з temperature_c %d, з weather_feel %d" % (
        sum("temperature_c" in x["values"] for x in вс), sum("weather_feel" in x["values"] for x in вс)),
          sorted({(x["code"], x["values"].get("temperature_c")) for x in вс if "temperature_c" in x["values"]}))
