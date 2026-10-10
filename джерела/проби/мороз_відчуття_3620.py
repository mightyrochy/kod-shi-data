"""Проба (рядки 3620, 3621): чим модель бачить погоду, коли вона сказала лише відчуття («мороз», «спека») — і чим,
коли назвала градуси. А) оцінка з фото: `_сцена_для_моделі` → `weather`. Б) пакет руки 1 стилістці: заяви нот шару
`outer_layer_*`. Число коду (−10, 20, 28) — лише правилам; назване нею число лишається числом. Моделі не кличе.
Запуск: cd джерела && python3 проби/мороз_відчуття_3620.py"""
import json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed as Ф, bridge as B, міст_пакет as МП, сценарій as СЦ, оцінка_образу as О


def заяви(x, коди):
    if isinstance(x, dict):
        if x.get("code") in коди:
            yield x
        for v in x.values():
            yield from заяви(v, коди)
    elif isinstance(x, list):
        for v in x:
            yield from заяви(v, коди)


print("А) weather моделі оцінки:")
for п in ({"погода_відчуття": "frost"}, {"погода_відчуття": "warm"}, {"погода_відчуття": "hot", "опади": "дощ"},
          {"погода_відчуття": "frost", "темп_c": -15}, {"темп_c": 22}):
    print("  ", п, "→", О._сцена_для_моделі({"сцена": СЦ.з_показу(п, None)[0]})[1])
print("Б) заяви нот шару у пакеті руки 1:")
база = json.load(open("стенд_вх.json", encoding="utf-8")); кат = Ф.каталог_на_диску("каталог_повний.xml")
for назва, пас in (("спека без числа", {"погода_відчуття": "hot"}), ("тепло без числа", {"погода_відчуття": "warm"}),
                   ("назвала 28 °C", {"темп_c": 28})):
    сц = {k: v for k, v in база["сценарій"].items() if k != "темп_c"}
    МП._КЕШ_ПАКЕТА.clear()
    пак = json.loads(B.виклик("запити", json.dumps(dict(база, каталог=кат, гілка=0, сценарій=сц, паспорт=пас,
                                                        випадок="робочий день, пішки"), ensure_ascii=False)))
    print("  ", назва, "→", sorted({(z["code"], json.dumps(z.get("values"), ensure_ascii=False))
                                    for z in заяви(пак, ("outer_layer_removed_by_temperature", "outer_layer_kept_despite_warmth"))}))
