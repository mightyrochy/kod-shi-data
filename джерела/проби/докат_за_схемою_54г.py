"""Докат розбору без моделі (5.4-Г): готова відповідь, яку пускає нинішня схема, у модель вдруге не йде; відповідь
під ширшою граматикою (3 оздоби при стелі 2, число 8.25) — іде, хоч запит той самий знак у знак."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import каталог_розбір as КР, каталог_розбір_прогін as П, фід_каталог as ФК, фід_розбір as ФР

def мінімальна(в):
    if "anyOf" in в: return мінімальна(в["anyOf"][-1])
    if "enum" in в: return КР.UNKNOWN if КР.UNKNOWN in в["enum"] else в["enum"][-1]
    if в["type"] == "object": return {к: мінімальна(п) for к, п in в["properties"].items()}
    return [] if в["type"] == "array" else ""

мін = мінімальна(КР.схема_відповіді())
три_оздоби = dict(мін, decor=[{"quote": "", "value": КР.UNKNOWN}] * 3)
дробове = dict(мін, length_cm={"quote": "8.25", "value": 8.25, "unit": "cm"})
відповіді = [мін, три_оздоби, дробове, мін]
офери = ФР.читати_yml(ФК.каталог_на_диску(), показ=False)[0][:len(відповіді)]
ід, запити = [o["id"] for o in офери], [json.dumps(КР.промпт(o), ensure_ascii=False) for o in офери]
пішло = []
def заглушка(повід, ід_моделі, схема=True, годинник=None):
    і = запити.index(повід)
    пішло.append(і)
    return json.dumps(відповіді[і], ensure_ascii=False, separators=(",", ":")), 0.0, None, 0
П._спитати = заглушка
with tempfile.TemporaryDirectory() as тека:
    (Path(тека) / "ід.json").write_text(json.dumps(ід))
    for _ in range(2):
        П.прогін("заглушка", куди=тека, еталон=str(Path(тека) / "ід.json"), паралельно=1)
    другий = sorted(пішло[len(ід):])
assert КР.за_схемою(json.dumps(мін)) and not КР.за_схемою(json.dumps(три_оздоби)) and not КР.за_схемою(json.dumps(дробове))
assert sorted(пішло[:len(ід)]) == list(range(len(ід))) and другий == [1, 2], пішло
print("докат: перший запуск — у модель %d з %d; другий — лише %s (поза нинішньою схемою), готові %s взято"
      % (len(ід), len(ід), другий, [0, 3]))
