"""Відтворює охоплення джерел Python приладом голови PR без викликів моделі."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    корінь = Path(sys.argv[1]).resolve()
    шлях = корінь / 'джерела/прилади/корінь_е2_вікно.py'
    опис = importlib.util.spec_from_file_location('прилад', шлях)
    прилад = importlib.util.module_from_spec(опис)
    опис.loader.exec_module(прилад)

    def число(тека):
        місця, _ = прилад.місця(str(тека))
        return sum(bool(м['пункти']) for м in місця)

    база = число(корінь)
    print(f'Голова: місць: {база}')
    код = '''import json, urllib.request
def запит(промпт):
    тіло = json.dumps({"messages": [{"role": "user", "content": промпт}], "max_tokens": 600}).encode()
    return urllib.request.urlopen(urllib.request.Request("http://x/v1/chat/completions", data=тіло))
'''
    with tempfile.TemporaryDirectory(dir=os.environ['TEMP'], prefix='охоплення_2467_') as т:
        дерево = Path(т)
        shutil.copytree(корінь / 'джерела/показ', дерево / 'джерела/показ')
        for файл in ('жнива_промпти.py', 'каталог_розбір_прогін.py'):
            shutil.copy2(корінь / 'джерела' / файл, дерево / 'джерела' / файл)
        assert число(дерево) == база
        for розміщення in ('джерела/новий_клієнт.py', 'джерела/клієнти/новий_клієнт.py', 'zhnyvarka/новий_клієнт.py'):
            файл = дерево / розміщення
            файл.parent.mkdir(parents=True, exist_ok=True)
            файл.write_text(код, encoding='utf-8')
            print(f'Той самий новий клієнт у {розміщення}: {база} -> {число(дерево)}; очікувано {база + 1}')
            файл.unlink()
        звідки = дерево / 'джерела/каталог_розбір_прогін.py'
        куди = дерево / 'zhnyvarka/каталог_розбір_прогін.py'
        shutil.move(str(звідки), str(куди))
        print(f'Наявний клієнт каталогу перенесено без зміни коду у zhnyvarka/: {база} -> {число(дерево)}; очікувано {база}')

    for ім, тека in прилад.СЕРІЇ:
        файли = sorted((корінь / тека).glob('*/знімки/модель_виклики.json'))
        відмови, входи = [], []
        for файл in файли:
            for виклик in json.loads(файл.read_text(encoding='utf-8')).get('виклики', []):
                помилка = str(виклик.get('помилка') or '')
                відмова = прилад.ВІДМОВА_ВІКНА.search(помилка)
                if відмова:
                    відмови.append(файл.parent.parent.name)
                if виклик['тип'] == 'ВЕРДИКТ_V1→ОБРАЗИ_V1':
                    входи.append(max(виклик.get('вхід') or 0, int(відмова.group(1)) if відмова else 0))
        print(f'{ім}: записів запитів {len(файли)}; відмови у {sorted(set(відмови))}; максимум входу ремонту {max(входи)}')

    for _ in range(2):
        результат = subprocess.run([sys.executable, '-X', 'utf8', '-I', str(шлях)], capture_output=True, check=True)
        print('SHA256 stdout:', hashlib.sha256(результат.stdout).hexdigest())


if __name__ == '__main__':
    main()
