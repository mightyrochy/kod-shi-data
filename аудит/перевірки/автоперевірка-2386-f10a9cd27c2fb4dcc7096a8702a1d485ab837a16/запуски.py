"""Запускає батарею й сім'ї проб на призначеній голові, зберігаючи повний вивід."""
import json, os, subprocess, sys, time
from pathlib import Path

дерево = Path(sys.argv[1]).resolve()
докази = Path(sys.argv[2]).resolve()
докази.mkdir(parents=True, exist_ok=True)
оточення = dict(os.environ, PYTHONIOENCODING='utf-8')
команди = [([sys.executable, 'стенд_знімок.py', '--дим'], дерево/'джерела')]
команди += [([sys.executable, str(п.relative_to(дерево))], дерево) for п in sorted((дерево/'джерела/проби').glob('каталог_зависла_крамниця*.py'))]
команди += [([sys.executable, п], дерево) for п in ['джерела/проби/каталог_рецепт_повтор.py', 'джерела/проби/каталог_цикл_53.py', 'джерела/проби/картка_вузол_5_1.py', 'джерела/проби/каталог_проблеми_г_стеля.py', 'джерела/проби/каталог_проблеми_г_крамниці.py', 'аудит/жнива_5_3/читачі_повтор.py', 'джерела/прилади/згорнути_дошку.py']]
команди[-1][0].append('--лише-перевірити')
команди += [([sys.executable, п], дерево/'джерела') for п in ['тест_протоколу.py', 'audit_contracts.py']]
команди += [(['node', 'тест_показу.js'], дерево/'джерела'), ([sys.executable, 'тест_живого_шляху.py'], дерево/'джерела'), ([sys.executable, 'прилади/розділи_гейтів.py'], дерево/'джерела')]
результати = []
for номер, (команда, тека) in enumerate(команди, 1):
    файл = докази/f'команда-{номер:02}.txt'
    початок = time.monotonic()
    print(f'ПОЧАТОК {номер}: {команда}', flush=True)
    with файл.open('w', encoding='utf-8') as ф:
        ф.write('ТЕКА: '+str(тека)+'\nКОМАНДА: '+subprocess.list2cmdline(команда)+'\n'); ф.flush()
        код = subprocess.run(команда, cwd=тека, env=оточення, stdout=ф, stderr=subprocess.STDOUT).returncode
        ф.write(f'\nКОД: {код}\n')
    результат = dict(номер=номер, команда=команда, тека=str(тека), код=код, секунд=round(time.monotonic()-початок, 2), вивід=файл.name)
    результати.append(результат)
    (докази/'команди.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'КІНЕЦЬ {номер}: код {код}, секунд {результат["секунд"]}', flush=True)
