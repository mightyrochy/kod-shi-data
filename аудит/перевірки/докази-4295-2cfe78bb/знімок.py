"""Картка записаної її речі в показі голови, Chromium 390×844, без мережі й моделі."""
from pathlib import Path
import json
import subprocess
import sys
from playwright.sync_api import sync_playwright

дерево = Path(sys.argv[1]).resolve()
докази = Path(__file__).resolve().parent
sys.path.insert(0, str(дерево / 'джерела/прилади'))
sys.path.insert(0, str(дерево / 'джерела'))
import річ_запис_її_річ as Я
import мовний_шар as М
import річ_з_фото as РФ

запис = 'аудит/проби/Е1-нічний-живий-20261107/ж4_робота_спідниця_фото/VIDPOVIDI/seed3_01_мовний_шар_хід_розмови.txt'
_, картки = Я.прогнати(*Я.прочитати(дерево, запис), 'розмова', (М, РФ))
код = r'''
const path = require('node:path');
const джерела = path.join(process.argv[1], 'джерела');
const Ш = require(path.join(джерела, 'показ_шаблон.js'));
console.log(Ш.підставитиШаблон(Ш.зібратиШаблонПоказу(path.join(джерела, 'показ.html')), {
  __МОДУЛІ_ПОКАЗУ__: '', __ЗБІРКА_ПОКАЗУ__: 'офлайн', __ВІДБИТОК__: 'офлайн',
  __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: Ш.прочитатиДовідникJSON(джерела),
}).replace(/<script[^>]+src="https:[^"]+"[^>]*><\/script>/g, ''));
'''
html = subprocess.run(['node', '-e', код, str(дерево)], check=True, capture_output=True, encoding='utf-8').stdout
with sync_playwright() as p:
    браузер = p.chromium.launch(headless=True, args=['--disable-gpu'])
    try:
        сторінка = браузер.new_page(viewport=dict(width=390, height=844))
        сторінка.route('**/*', lambda route: route.fulfill(content_type='text/html; charset=utf-8', body=html)
                       if route.request.url == 'http://127.0.0.1:42176/' else route.abort())
        сторінка.on('pageerror', lambda e: print('PAGEERROR', e))
        сторінка.goto('http://127.0.0.1:42176/')
        сторінка.wait_for_function("typeof рендер === 'function' && Екран.стан.запущено")
        сторінка.evaluate('''речі => {
          П = {картки: [{речі, опис: 'Образ із твоєю спідницею.', як_носити: [], свідомі: []}],
               збірка: 'офлайн', каталог: '', профіль: '', вердикти: []};
          рендер();
        }''', картки)
        сторінка.locator('#картки').wait_for(state='visible')
        сторінка.evaluate('''() => Promise.all(document.getAnimations().filter(а =>
          а.effect.getTiming().iterations !== Infinity).map(а => а.finished.catch(() => {})))''')
        сторінка.screenshot(path=str(докази / 'голова-390x844.png'))
        текст = сторінка.locator('#картки').inner_text()
        (докази / 'знімок.txt').write_text(текст + '\n', encoding='utf-8')
        print(текст)
    finally:
        браузер.close()
