# -*- coding: utf-8 -*-
"""Інвентар обробників показу для роботи над коренем Е2; це ще не прилад місць.

Читає всі JS у джерела/показ і вбудовані скрипти та атрибути подій показ.html.
Повертає JSON з розташуванням і синтаксичними викликами. Наявність виклику не
доводить досяжності, призначення дії чи показу результату в розмові.
"""
import json
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys


class HTML(HTMLParser):
    def __init__(self, файл):
        super().__init__(convert_charrefs=True)
        self.файл = файл
        self.фрагменти = []
        self.скрипт = False

    def handle_starttag(self, тег, атрибути):
        атр = dict(атрибути)
        рядок = self.getpos()[0]
        for ім, значення in атрибути:
            if ім in ('onclick', 'onchange', 'oninput', 'onsubmit', 'onkeydown', 'onkeyup') and значення:
                self.фрагменти.append(dict(файл=self.файл, рядок=рядок, код=значення, атрибут=ім))
        self.скрипт = тег == 'script' and 'src' not in атр and атр.get('type', '') in ('', 'text/javascript', 'module')

    def handle_endtag(self, тег):
        if тег == 'script':
            self.скрипт = False

    def handle_data(self, текст):
        if self.скрипт:
            self.фрагменти.append(dict(файл=self.файл, рядок=self.getpos()[0], код=текст))


def інвентар(корінь):
    корінь = Path(корінь)
    дж = корінь / 'джерела'
    html = HTML('джерела/показ.html')
    html.feed((дж / 'показ.html').read_text(encoding='utf-8'))
    html.close()
    частини = html.фрагменти
    for шлях in sorted((дж / 'показ').glob('*.js')):
        частини.append(dict(файл=шлях.relative_to(корінь).as_posix(), рядок=1,
                            код=шлях.read_text(encoding='utf-8')))
    скрипт = Path(__file__).with_suffix('.cjs')
    процес = subprocess.run(['node', str(скрипт)], input=json.dumps(частини, ensure_ascii=False),
                            encoding='utf-8', capture_output=True, check=True)
    return json.loads(процес.stdout)


if __name__ == '__main__':
    try:
        print(json.dumps(інвентар(sys.argv[1] if len(sys.argv) > 1 else '.'), ensure_ascii=False, indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError) as помилка:
        print(f'інвентар не прочитано: {помилка}\n{getattr(помилка, "stderr", "")}', file=sys.stderr)
        sys.exit(1)
