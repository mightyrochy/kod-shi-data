# -*- coding: utf-8 -*-
"""Будує синтаксичний граф усіх JS/HTML продукту, без тестів, проб і приладів.

Реєстрація події не є виконанням callback. Передані у фабрику замикання
розкриває аналіз областей імен і аргументів до нерухомої точки в Node/Acorn.
"""
import json
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys


class HTML(HTMLParser):
    """Виділяє скрипти й атрибути всіх подій, зберігаючи рядки джерела."""

    def __init__(self, файл):
        super().__init__(convert_charrefs=True)
        self.файл = файл
        self.фрагменти = []
        self.скрипт = False

    def handle_starttag(self, тег, атрибути):
        """Виділяє код з атрибутів і починає вбудований скрипт."""
        атр = dict(атрибути)
        for ім, значення in атрибути:
            if ім.startswith('on') and значення:
                self.фрагменти.append(dict(файл=self.файл, рядок=self.getpos()[0],
                    код=f"__html__.{ім} = function(event){{{значення}}};"))
        if тег == 'script':
            self.скрипт = 'src' not in атр and атр.get('type', '') in ('', 'text/javascript', 'module')

    def handle_endtag(self, тег):
        """Закінчує вбудований скрипт."""
        if тег == 'script':
            self.скрипт = False

    def handle_data(self, текст):
        """Додає код з точним початковим рядком."""
        if self.скрипт:
            self.фрагменти.append(dict(файл=self.файл, рядок=self.getpos()[0], код=текст))


def джерела(корінь):
    """Знаходить усі JS/HTML продукту на будь-якій глибині джерела/."""
    for шлях in sorted((Path(корінь) / 'джерела').rglob('*')):
        відносний = шлях.relative_to(корінь)
        if any(ч in ('прилади', 'проби', 'лабораторія', 'node_modules', '__pycache__') for ч in відносний.parts):
            continue
        if шлях.suffix not in ('.js', '.mjs', '.html') or шлях.name.startswith(('тест_', 'стенд_', 'проба.')):
            continue
        yield шлях


def граф(корінь):
    """Читає дерево продукту й повертає граф функцій та реєстрації дій."""
    корінь = Path(корінь).resolve()
    частини, файли = [], []
    for шлях in джерела(корінь):
        файл = шлях.relative_to(корінь).as_posix()
        файли.append(файл)
        код = шлях.read_text(encoding='utf-8-sig')
        if шлях.suffix == '.html':
            html = HTML(файл)
            html.feed(код)
            html.close()
            частини.extend(html.фрагменти)
        else:
            частини.append(dict(файл=файл, рядок=1, код=код))
    процес = subprocess.run(['node', str(Path(__file__).with_suffix('.cjs'))],
        input=json.dumps(частини, ensure_ascii=False), encoding='utf-8', capture_output=True, check=True)
    дані = json.loads(процес.stdout)
    дані['файли'] = файли
    return дані


def інвентар(корінь):
    """Зберігає попередній API інвентарю; лічба й нова вибірка беруть граф()."""
    дані = граф(корінь)
    записи = []
    for запис in дані['обробники']:
        ф = дані['функції'][запис['ціль']] if запис['ціль'] is not None else None
        виклики = [к['назва'] for к in ф['виклики'] if к['назва']] if ф else [запис['код']]
        записи.append(dict(запис, виклики=list(dict.fromkeys(виклики))))
    return sorted(записи, key=lambda з: (not з['файл'].endswith('.html'), з['файл'], з['рядок'], з['стовпець']))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    try:
        print(json.dumps(граф(sys.argv[1] if len(sys.argv) > 1 else '.'), ensure_ascii=False, indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError) as помилка:
        print(f'граф не прочитано: {помилка}\n{getattr(помилка, "stderr", "")}', file=sys.stderr)
        sys.exit(1)
