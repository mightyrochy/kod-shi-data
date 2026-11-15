"""Знімок артефакту дерева PR 390×844 без викликів моделі; два аргументи: html, png."""
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

with sync_playwright() as п:
    браузер = п.chromium.launch(headless=True, args=["--disable-gpu"])
    сторінка = браузер.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
    сторінка.goto(Path(sys.argv[1]).resolve().as_uri(), wait_until="domcontentloaded")
    сторінка.evaluate("async () => { await document.fonts.ready; await new Promise(requestAnimationFrame); }")
    сторінка.screenshot(path=sys.argv[2], animations="disabled")
    print(json.dumps(dict(розмір=[390, 844], заголовок=сторінка.title(),
                         текст=сторінка.locator("body").inner_text()[:2000]), ensure_ascii=False))
    браузер.close()
