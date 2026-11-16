"""Імена точок без певного вікна слова (`palettes.назва`, 14356): ґратка основ і `палітра_практична` на 300 людях
(ті самі сід 26 і шкіра/волосся/очі, що `річ_колір_межі_крок29/вимір.py`). Друкує: клітинок ґратки, імена, імена поза
кодами продукту (латинка, «стик», «невідомо»), кольорів палітр, `назва_як`, назви поза кодами продукту й код
`color_name` кожного імені для стилістки (`внутрішня_мова.код`). Запуск із кореня дерева:
python3 -W ignore <шлях>/вимір.py"""
import json, random, sys
from collections import Counter
sys.path.insert(0, "джерела")
import palettes as П, colorspace as cs, міст_основи as МО, внутрішня_мова as ВМ  # noqa: E402
осн, порядок = МО.ґратка_основ()
поза = lambda ім: ВМ.код("color_name", ім) is None
ім_ґр = Counter(осн[к][1] for к in порядок)
print("ґратка: клітинок", len(порядок), "· поза кодом продукту", sum(н for ім, н in ім_ґр.items() if поза(ім)),
      sorted((ім, н) for ім, н in ім_ґр.items() if поза(ім)))
print("  імена:", "; ".join("%s %d" % п for п in ім_ґр.most_common()))
rnd = random.Random(26)
шк = ["#f3d9c6", "#e8c1a0", "#d9a77f", "#c08a63", "#9a6646", "#6e4630", "#f1d3c2", "#e2b597", "#b9805b", "#5a3825"]
вол = ["#2a1f1a", "#4b3428", "#6d4c35", "#a07850", "#d2b48c", "#e6cf9a", "#8a3b1f", "#b5562b", "#9a9a9a", "#0f0f10"]
очі = ["#4a2f1f", "#6b4a2b", "#7fa6c8", "#3d6e9e", "#5f8a5a", "#7b8b6a", "#8a9aa8", "#2e2a28", "#6a7f9a", "#9b8a5a"]
кол = []
for _ in range(300):
    F = cs.features(cs.hx(rnd.choice(шк)), cs.hx(rnd.choice(вол)), cs.hx(rnd.choice(очі)))
    кол += П.палітра_практична(F).get("кольори") or []
ім = Counter(к["назва"] for к in кол)
print("палітри: кольорів", len(кол), "· назва_як", Counter(к.get("назва_як") for к in кол).most_common(),
      "· поза кодом продукту", sum(н for с, н in ім.items() if поза(с)), sorted((с, н) for с, н in ім.items() if поза(с)))
print("  назви:", "; ".join("%s %d" % п for п in ім.most_common()))
import hashlib  # noqa: E402
print("відбиток складу (hex, роль, сім'я, L, C, h по порядку):",
      hashlib.sha256(json.dumps([(к["hex"], к["роль"], к["сім_я"], к["L"], к["C"], к["h"]) for к in кол]).encode()).hexdigest()[:16])
