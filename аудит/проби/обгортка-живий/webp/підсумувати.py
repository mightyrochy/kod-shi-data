"""Рахує доставку кадрів окремо від усіх звірок живої сцени."""
import json
from pathlib import Path
import re

ТЕКА = Path(__file__).resolve().parent
ПІДСУМОК = {}
for сцена in ('б1_концерт_стримано', 'ж1_вокал_просто_зручно'):
    тека = ТЕКА / сцена
    лог = (тека / 'лог.txt').read_text(encoding='utf-8')
    виклики = json.loads((тека / 'знімки/модель_виклики.json').read_text(encoding='utf-8'))['виклики']
    фото = [в for в in виклики if в.get('кадри') or в.get('фото_не_дійшло')]
    кадри = [к for в in фото for к in в['кадри']]
    втрати = sum(в.get('фото_не_дійшло', 0) for в in виклики)
    картки = list((тека / 'знімки').glob('kartka_poz*_seed3.png'))
    дані = dict(результат=json.loads((тека / 'результат.json').read_text(encoding='utf-8')),
        отримано=len(кадри) + втрати, передано=len(кадри), втрачено=втрати,
        webp=sum(к['вхід']['тип'] == 'image/webp' for к in кадри),
        хибний_MIME=sum(к['вхід']['тип'] != к['вхід']['заявлений_тип'] for к in кадри),
        HTTP_400=sum(в['статус'] == 400 for в in виклики),
        фото_виклики=[{'тип': в['тип'], 'http': в['статус'], 'кадрів': len(в['кадри'])} for в in фото],
        успішних=len(re.findall(r'^  ✔', лог, re.M)),
        провали=[р for р in лог.splitlines() if р.startswith('  ✗')],
        картки=[п.name for п in картки])
    дані['мірило_фото'] = втрати == 0 and bool(кадри) and all(в['статус'] == 200 for в in фото)
    ПІДСУМОК[сцена] = дані
(ТЕКА / 'підсумок.json').write_text(json.dumps(ПІДСУМОК, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(ПІДСУМОК, ensure_ascii=False, indent=2))
raise SystemExit(int(not all(д['мірило_фото'] and len(д['картки']) == 4 for д in ПІДСУМОК.values())))
