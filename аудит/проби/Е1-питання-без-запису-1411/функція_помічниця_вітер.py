"""Е1-питання-без-запису-1411, друга половина проби ж2_помічниця_вітер_реагенти: вхід мосту `помічниця`, перехоплений
у Chromium (функція_помічниця_вітер.js), читає справжній Python-міст (`міст_помічниця.помічниця`); у стані промпта —
wind_band і road_salt за плитками, без плиток — нема. Запуск: python3 -X utf8 функція_помічниця_вітер.py <вихід.json>"""
import json, re, sys
sys.path.insert(0, "джерела")
import міст_помічниця as М
вх = json.load(open(sys.argv[1], encoding="utf-8"))
очік = {"сильний вітер, реагенти є": ("strong", True), "безвітря, реагентів нема": ("calm", False), "плитки не торкались": (None, None)}
ok = True
for назва, д in вх.items():
    промпт = json.loads(М.помічниця(json.dumps(д, ensure_ascii=False)))["промпт"]
    пр = промпт if isinstance(промпт, str) else json.dumps(промпт, ensure_ascii=False)
    в = re.search(r'"wind_band": ?("[a-z_]+"|null)', пр); р = re.search(r'"road_salt": ?(true|false|null)', пр)
    знайдено = (json.loads(в[1]) if в else "нема", json.loads(р[1]) if р else "нема")
    чекали = очік[назва] if очік[назва] != (None, None) else ("нема", "нема")
    чи = знайдено == чекали
    ok &= чи
    print(("✓ " if чи else "✗ ") + f"{назва}: wind_band, road_salt у стані промпта = {знайдено} (очікували {чекали})")
sys.exit(0 if ok else 1)
