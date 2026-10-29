"""Зберігає експорт вердиктів та виводить рішення всіх чотирьох рук для читання."""
import gzip
import hashlib
import json
import pathlib
import sys

файл = pathlib.Path(sys.argv[1])
вихід = pathlib.Path(__file__).resolve().parent
сирий = файл.read_bytes()
дані = json.loads(сирий.decode('utf-8-sig'))
зведення = []
for прогін in дані['прогони']:
    for вердикт in прогін['вердикти']:
        етапи = вердикт.get('етапи') or {}
        зведення.append(dict(рука=вердикт['рука'], склад=вердикт.get('склад'),
            речі=вердикт.get('речі_образу'), діагноз=етапи.get('діагноз_руки'),
            виклики=[dict(крок=в.get('крок'), повнота=в.get('повнота'), вибір=в.get('вибір'))
                     for в in етапи.get('виклики') or []
                     if в.get('повнота') or в.get('вибір')],
            поля_суду=list(етапи.get('суд') or {})))
факт = dict(sha256=hashlib.sha256(сирий).hexdigest(), байтів=len(сирий),
             вердиктів=дані['вердиктів'], зведення=зведення)
(вихід / 'вердикти.json.gz').write_bytes(gzip.compress(сирий, mtime=0))
(вихід / 'вердикти-огляд.json').write_text(json.dumps(факт, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(факт, ensure_ascii=False, indent=2))
