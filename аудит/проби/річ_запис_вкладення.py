"""Відтворює зауваження 4463179975 в HTML-читачі та справжньому Chromium."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'zhnyvarka'))
import жниварка
from виконавець import ЗЛІПОК_DOM, картка_з_dom
from playwright.sync_api import sync_playwright


def main():
    """Друкує поля двох збирачів і відхиляє підміну основної речі."""
    html = '<article class="product"><h1>Основна сукня</h1><div class="desc">Опис основної сукні</div><aside class="related"><article class="product"><h1>Чужа спідниця</h1><div class="desc">Опис чужої спідниці</div></article></aside></article>'
    рецепт = {'блок': '.product', 'опис': '.desc'}
    факти = жниварка.факти_з_картки(html, 'https://shop.test/product/1', рецепт)
    картка = картка_з_dom('https://shop.test/product/1', html, {}, факти)
    with sync_playwright() as p:
        браузер = p.chromium.launch(headless=True)
        сторінка = браузер.new_page()
        сторінка.set_content(html)
        dom = сторінка.evaluate(ЗЛІПОК_DOM, рецепт)
        браузер.close()
    print(json.dumps(dict(факти={к: факти.get(к) for к in ('назва', 'опис', 'межа_блоку')},
                          картка={к: картка.get(к) for к in ('назва', 'опис')},
                          зліпок={к: dom[к] for к in ('h1', 'text')}), ensure_ascii=False))
    return int(any(з['назва'] != 'Основна сукня' or з['опис'] != 'Опис основної сукні' for з in (факти, картка))
               or dom['h1'] != 'Основна сукня' or 'Чужа' in dom['text'])


if __name__ == '__main__':
    raise SystemExit(main())
