"""Один знімок 390×844 з незміненого index.html призначеної голови."""
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

тут = Path(__file__).resolve().parent
дерево = Path(sys.argv[1]).resolve()
with sync_playwright() as п:
    браузер = п.chromium.launch(headless=True, args=['--disable-gpu'])
    сторінка = браузер.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=1)
    помилки = []
    сторінка.on('pageerror', lambda помилка: помилки.append(str(помилка)))
    сторінка.goto((дерево / 'index.html').as_uri(), wait_until='load')
    сторінка.screenshot(path=str(тут / 'екран-390x844.png'))
    дані = {'title': сторінка.title(), 'pageerror': помилки, 'text': сторінка.locator('body').inner_text()[:2500]}
    (тут / 'екран.json').write_text(json.dumps(дані, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(дані, ensure_ascii=False))
    браузер.close()
