import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, 'джерела/прилади')
from читачі_записів import дерево

назви = ['27c5d4686ce699a0e799e2c827c6efe94c0e8881',
         '82be13cee9aae268b807203a81397f8406d1b7d5',
         'origin/claude/zhyvi-13', 'origin/claude/zhyvi-14']
ревізії = {}
файли = {}
for назва in назви:
    р = subprocess.run(['git', 'rev-parse', '--verify', назва + '^{commit}'], capture_output=True)
    ша = р.stdout.decode().strip() if р.returncode == 0 else None
    ревізії[назва] = ша
    файли[назва] = {п: в[1] for п, в in дерево(ша).items()
                   if п.startswith('аудит/') and re.search(r'/VIDPOVIDI/.*\.txt$', п)} if ша else {}
    print(назва, 'файлів', len(файли[назва]), flush=True)

блоби = sorted(set(ша for перелік in файли.values() for ша in перелік.values()))
відповіді = {}
for і in range(0, len(блоби), 1024):
    пачка = блоби[і:і + 1024]
    в = subprocess.run(['git', 'cat-file', '--batch'], input=''.join(ш + '\n' for ш in пачка).encode(),
                       stdout=subprocess.PIPE, check=True).stdout
    зсув = 0
    for ша in пачка:
        кінець = в.index(b'\n', зсув)
        розмір = int(в[зсув:кінець].split()[2])
        текст = io.TextIOWrapper(io.BytesIO(в[кінець + 1:кінець + 1 + розмір]), encoding='utf-8').read()
        зсув = кінець + розмір + 2
        текст = текст.partition('\n── ВІДПОВІДЬ')[2].partition('\n')[2].strip()
        відповіді[ша] = текст if '{' in текст else ''


def входи(голова):
    вихід = {}
    for назва in [голова, *назви[2:]]:
        for шлях, ша in sorted(файли[назва].items()):
            текст = відповіді[ша]
            if текст:
                ключ = hashlib.md5(текст.encode()).hexdigest()
                if ключ in вихід:
                    assert вихід[ключ]['текст'] == текст, 'Колізія MD5'
                else:
                    вихід[ключ] = {'текст': текст, 'джерело': назва + ':' + шлях}
    return вихід


до, після = входи(назви[0]), входи(назви[1])
зняті, додані = до.keys() - після.keys(), після.keys() - до.keys()
підсумок = {'ревізії': ревізії, 'відповідей_до': len(до), 'відповідей_після': len(після),
            'знятих_унікальних': len(зняті), 'доданих_унікальних': len(додані),
            'приклади_знятих': [до[к]['джерело'] for к in sorted(зняті)[:20]],
            'однакові': set(в['текст'] for в in до.values()) == set(в['текст'] for в in після.values())}
Path('../tmp/повнота-replay.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(підсумок, ensure_ascii=False))
