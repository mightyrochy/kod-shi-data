"""Виконує двадцять повних послідовних прогонів показу й зберігає їхні результати."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    """Запускає незмінну команду, зберігаючи код, число звірок і всі рядки провалів."""
    корінь = Path(os.environ.get('LYUSTERKO_TEST_ROOT', Path(__file__).resolve().parents[3]))
    джерела = корінь / 'джерела'
    вихід = Path(__file__).with_name(sys.argv[1] + '.json')
    оточення = dict(os.environ, NODE_PATH='node_modules', PYTHONUTF8='1')
    результати = {
        'команда': 'cd джерела; NODE_PATH=node_modules node тест_показу.js',
        'голова': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=корінь, text=True).strip(),
        'sha256_тесту': hashlib.sha256((джерела / 'тест_показу.js').read_bytes()).hexdigest(),
        'прогони': [],
    }
    for номер in range(1, 21):
        початок = time.monotonic()
        процес = subprocess.run(['node', 'тест_показу.js'], cwd=джерела, env=оточення,
                                capture_output=True, text=True, encoding='utf-8', timeout=600)
        рядки = (процес.stdout + процес.stderr).splitlines()
        запис = {
            'номер': номер, 'код': процес.returncode,
            'секунд': round(time.monotonic() - початок, 2),
            'підсумок': [р for р in рядки if р.startswith(('ВИКОНАНО', 'ВПАЛО', 'ПОКАЗ:'))],
            'провали': [р for р in рядки if '✗' in р or 'не дочекались' in р],
        }
        if процес.returncode and not запис['провали']:
            запис['кінець_виводу'] = рядки[-20:]
        результати['прогони'].append(запис)
        вихід.write_text(json.dumps(результати, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(запис, ensure_ascii=False), flush=True)
    червоних = sum(з['код'] != 0 for з in результати['прогони'])
    print(f'Червоних {червоних}/20', flush=True)
    return int(червоних != 0)


if __name__ == '__main__':
    sys.exit(main())
