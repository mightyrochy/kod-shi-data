"""Пише вхід і вихід кожного виклику node приладу: аргументи — корінь дерева, тека, вид (старий|новий)."""
import gzip, json, os, sys, hashlib
from pathlib import Path
корінь, тека, вид = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
os.chdir(корінь); sys.path.insert(0, str(корінь / 'джерела/прилади'))
import корінь_річ_запис_речі as к
лічба = [0]; виходи = []
стара = к.Прогін.node
if вид == 'старий':
    def node(self, вхід):
        (тека / f'{вид}_{лічба[0]}.json.gz').write_bytes(gzip.compress(json.dumps(вхід, ensure_ascii=False).encode()))
        вих = стара(self, вхід); виходи.append(hashlib.sha256(json.dumps(вих, ensure_ascii=False, sort_keys=True).encode()).hexdigest()); лічба[0] += 1
        return вих
else:
    старе_закрити = к.ВхідNode.закрити
    def закрити(self):
        рядки = старе_закрити(self)
        (тека / f'{вид}_{лічба[0]}.ndjson.gz').write_bytes(gzip.compress(''.join(р + '\n' for р in рядки).encode()))
        return рядки
    к.ВхідNode.закрити = закрити
    def node(self, вхід, вузли=()):
        вих = стара(self, вхід, вузли); виходи.append(hashlib.sha256(json.dumps(вих, ensure_ascii=False, sort_keys=True).encode()).hexdigest()); лічба[0] += 1
        return вих
к.Прогін.node = node
try: к.main(sys.argv[4:])
finally: (тека / f'{вид}_виходи.json').write_text(json.dumps(виходи))
