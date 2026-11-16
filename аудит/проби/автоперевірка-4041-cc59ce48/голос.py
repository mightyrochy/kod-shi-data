"""Відтворення 16123: python голос.py <дерево голови PR>; без каталогу й моделі."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(sys.argv[1]).resolve() / 'джерела'))
import формальність as F
from реєстр_константи import C, REGISTRY

E = [dict(річ='спорт', слот='сукня', тип='спортивний'),
     dict(річ='клатч', слот='сумка', тип='клатч'),
     dict(річ='човники', слот='взуття', тип='човники')]
key = 'свідомий_розрив_частка'
results = []
original = C[key]
try:
    for value in (original, 0.3):
        C[key] = value
        findings = F.формальність_образу(E, dict(код='business_casual'))
        results.append(dict(значення=value, знахідки=[{k: z.get(k) for k in ('правило', 'сила', 'сила_нп', 'також_правила')}
                                                   for z in findings if z.get('правило') == 'K-KOH-02']))
finally:
    C[key] = original
print(json.dumps(dict(константа=key, прав=REGISTRY[key]['прав'], результати=results), ensure_ascii=False, indent=2))
