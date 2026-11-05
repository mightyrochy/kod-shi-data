"""Перевіряє покриття матриці й відмови збирача на справжніх результатах обгортки."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def головний():
    """Звіряє набір і відтворює провал справжнього стенда, пропуск та дубль артефактів."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--журнали', type=Path, required=True)
    аргументи = парсер.parse_args()
    дерево = Path(__file__).resolve().parents[2]
    шлях = дерево / 'аудит/проби/доробка_менше_прогонів.py'
    опис = importlib.util.spec_from_file_location('раннер_обгортки', шлях)
    раннер = importlib.util.module_from_spec(опис)
    опис.loader.exec_module(раннер)
    очікувані = {назва for назва, _ in раннер.перелік_запусків(дерево)}
    латка = (дерево / 'аудит/латки/CI-швидше/workflow.patch').read_text(encoding='utf-8')
    назви = re.findall(r"^\+\s+- '(.*?)'\s*$", латка, re.M)
    assert Counter(назви) == Counter(очікувані), (назви, очікувані)
    print(f'матриця: усі {len(очікувані)} стендів рівно по одному')
    assert раннер.зібрати(аргументи.журнали, очікувані) == 0
    записи = []
    for файл in sorted(аргументи.журнали.rglob('результати.json')):
        записи.extend(json.loads(файл.read_text(encoding='utf-8')))
    with tempfile.TemporaryDirectory(prefix='стенд_ci_') as тека:
        тека = Path(тека)
        зламаний = тека / 'нічний.ps1'
        зламаний.write_text("param([string]$WrapperRoot)\nWrite-Output 'FAIL свідомий провал'\nexit 1\n",
                            encoding='utf-8-sig')
        вихід = subprocess.run([sys.executable, str(шлях), '--дерево', str(дерево), '--журнали', str(тека / 'зламаний'),
                                '--нічний', str(зламаний), '--лише', 'перевірити_нічний_маркер.ps1'],
                               capture_output=True)
        assert вихід.returncode == 1, вихід.stdout + вихід.stderr
        print('Свідомий провал нічного стенда:')
        print((вихід.stdout + вихід.stderr).decode('utf-8', errors='replace'))
        провал = json.loads((тека / 'зламаний/результати.json').read_text(encoding='utf-8'))[0]
        assert провал['код_процесу'] == 1 and провал['код'] == 1, провал
        випадки = [
            ('свідомо зламаний стенд', [провал if р['стенд'] == провал['стенд'] else р for р in записи]),
            ('стенд не запускався', записи[1:]),
            ('подвійний запуск', записи + записи[:1]),
            ('чужий стенд', записи + [dict(записи[0], стенд='невідомий.ps1')]),
            ('немає тверджень', [dict(записи[0], тверджень=0), *записи[1:]]),
            ('немає коду процесу', [{к: з for к, з in записи[0].items() if к != 'код_процесу'}, *записи[1:]]),
            ('порожні артефакти', []),
        ]
        for номер, (назва, результати) in enumerate(випадки):
            частина = тека / str(номер)
            частина.mkdir()
            (частина / 'результати.json').write_text(json.dumps(результати, ensure_ascii=False), encoding='utf-8')
            assert раннер.зібрати(частина, очікувані) == 1, назва
            print(f'збирач: {назва} — червоний, як очікувано')
        пошкоджений = тека / 'пошкоджений'
        пошкоджений.mkdir()
        (пошкоджений / 'результати.json').write_text('{', encoding='utf-8')
        assert раннер.зібрати(пошкоджений, очікувані) == 1
        print('збирач: пошкоджений JSON — червоний, як очікувано')
    return 0


if __name__ == '__main__':
    sys.exit(головний())
