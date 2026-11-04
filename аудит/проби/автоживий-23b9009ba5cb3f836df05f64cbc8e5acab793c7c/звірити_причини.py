"""Читає записану відповідь чинним читачем, без виклику моделі."""
import json
from pathlib import Path
import re
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT / 'джерела'))
import вибір_палітри as palette

record = ROOT / 'аудит/проби/нічні/20261104/ж4_робота/VIDPOVIDI/seed3_06_вибір_палітри_стилістка_.txt'
raw = re.split(r'── ВІДПОВІДЬ[^\n]*\n', record.read_text(encoding='utf-8'))[-1].strip()
answer, reason, _ = palette._СВ.СХЕМИ_ВІДПОВІДІ['ВИБІР_ПАЛІТРИ'].прочитати(raw)
result = {'код': '23b9009ba5cb3f836df05f64cbc8e5acab793c7c', 'сцена': 'ж4_робота',
          'файл': str(record.relative_to(ROOT)), 'помилка_формату': reason, 'прочитано': answer}
for field in ('scheme_reasons', 'base_reasons'):
    rejected = []
    accepted = palette._причини(answer.get(field), rejected)
    result[field] = {'прийнято': accepted, 'відхилено': rejected}
(OUT / 'причини_читач.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
