"""Перевіряє рецепти зліпка на збережених HTML у Chromium без запитів до мережі.

Запуск із кореня: python -X utf8 аудит/проби/річ_запис_браузер.py --поля файл.json.gz --вихід тека
Скрипти крамниць вимкнені, усі зовнішні запити відхиляються.
"""
import argparse
import gzip
import json
from pathlib import Path
import sys

КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / 'zhnyvarka'))
from виконавець import ЗЛІПОК_DOM
from жниварка import рецепт_селекторів
from playwright.sync_api import sync_playwright


def main():
    """Звіряє назви браузерного блоку з HTML-читачем на всіх 144 сторінках."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--поля', type=Path, required=True)
    парсер.add_argument('--вихід', type=Path, required=True)
    арг = парсер.parse_args()
    with gzip.open(арг.поля, 'rt', encoding='utf8') as файл:
        сторінки = json.load(файл)['сторінки']
    арг.вихід.mkdir(parents=True, exist_ok=True)
    результати = []
    with sync_playwright() as рушій:
        браузер = рушій.chromium.launch(headless=True)
        контекст = браузер.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844},
                                       service_workers='block')
        сторінка = контекст.new_page()
        контекст.route('**/*', lambda шлях: шлях.fulfill(status=200, content_type='text/html; charset=utf-8', body=тіло)
                       if шлях.request.is_navigation_request() and шлях.request.url == запис['url'].split('#')[0]
                       and шлях.request.frame == сторінка.main_frame else шлях.abort())
        for запис in сторінки:
            тіло = gzip.decompress((КОРІНЬ / 'аудит/проби/річ_запис_каталог_2026_10_30' / запис['файл']).read_bytes()).decode('utf8')
            сторінка.goto(запис['url'], wait_until='domcontentloaded')
            рецепт = рецепт_селекторів(запис['крамниця'])
            dom = сторінка.evaluate(ЗЛІПОК_DOM, рецепт)
            очікувана = запис['назва'] or ''
            збіг = not очікувана or dom['h1'][:200] == очікувана
            результати.append(dict(url=запис['url'], рецепт=рецепт, збіг=збіг, назва_html=очікувана,
                                   назва_dom=dom['h1'], рядків=len(dom['rows'])))
        браузер.close()
    (арг.вихід / 'браузер.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding='utf8')
    збої = [р for р in результати if not р['збіг']]
    print(f'Chromium: {len(результати)} сторінки; розбіжних назв: {len(збої)}')
    for рядок in збої:
        print(json.dumps(рядок, ensure_ascii=False))
    return int(bool(збої))


if __name__ == '__main__':
    raise SystemExit(main())
