"""Докат розбору без моделі (5.4-Г): готова відповідь, яку пускає нинішня схема (V5), у модель вдруге не йде;
відповідь поза нею (19 пунктів при стелі 18, цитата довша за стелю, пари v3 частини 1) — іде, хоч запит той самий."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import каталог_розбір as КР, каталог_розбір_прогін as П, фід_каталог as ФК, фід_розбір as ФР

мін = {"codes": "item_type=unknown", "features": ""}
зайвий = dict(мін, codes=мін["codes"] + ";decor=sequins=пайетки" * КР.СТЕЛЯ_ПУНКТІВ)
довга = dict(мін, codes="item_type=dress_generic=" + "сукня" * 11)
v3 = {"item_type": {"quote": "", "value": КР.UNKNOWN}}
відповіді = [мін, зайвий, довга, v3, мін]
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
assert КР.за_схемою(json.dumps(мін)) and not any(КР.за_схемою(json.dumps(в)) for в in (зайвий, довга, v3))
assert sorted(пішло[:len(ід)]) == list(range(len(ід))) and другий == [1, 2, 3], пішло
print("докат: перший запуск — у модель %d з %d; другий — лише %s (поза нинішньою схемою), готові %s взято"
      % (len(ід), len(ід), другий, [0, 4]))
