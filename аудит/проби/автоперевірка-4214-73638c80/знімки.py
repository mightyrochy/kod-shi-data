"""Нативний показ 390×844 з FOTO=1, без живої моделі.

Заглушено лише зовнішній виклик мовного шару: він повертає штатний fallback,
а його справжні входи збережено. Знімки не доводять якість речення моделі.
"""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
from playwright.sync_api import sync_playwright

root = Path(sys.argv[1]).resolve()
artifact = Path(__file__).resolve().parent
after = json.loads((artifact / 'ПІСЛЯ.json').read_text(encoding='utf-8'))
pair = after['пара']
cached_photo = artifact / 'фото-речі.jpg'
if cached_photo.exists():
    photo_bytes, mime = cached_photo.read_bytes(), 'image/jpeg'
else:
    request = urllib.request.Request(pair['фото'][0], headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        photo_bytes = response.read()
        mime = response.headers.get_content_type()
photo = 'data:' + mime + ';base64,' + base64.b64encode(photo_bytes).decode()
(artifact / 'фото-речі.jpg').write_bytes(photo_bytes)
logs = []

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=['--disable-gpu'])
    for label, directory in [('ДО', 'base4214'), ('ПІСЛЯ', 'head4214')]:
        tree = root.parent / 'tmp' / directory
        data = json.loads((artifact / (label + '.json')).read_text(encoding='utf-8'))
        html = tree / 'джерела/перевірка-4214.html'
        subprocess.run(['node', '-e', """
const fs = require('fs'), h = require('./показ_шаблон.js');
fs.writeFileSync('перевірка-4214.html', h.підставитиШаблон(h.зібратиШаблонПоказу('показ.html'), {
  __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'перевірка-4214', __ВІДБИТОК__: 'перевірка',
  __ФІД_ПОКАЗУ__: 'каталог_повний.xml', __КАТАЛОГ_ПОКАЗУ__: '28890 речей',
  __ДОВІДНИК_ПОКАЗУ__: h.прочитатиДовідникJSON(process.cwd())
}));
"""], cwd=tree / 'джерела', check=True)
        page = browser.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.route('https://**/*', lambda route: route.abort())
        page.goto(html.as_uri(), wait_until='load')
        page.wait_for_function("typeof рендер === 'function'")
        card = dict(рука='1', ітерацій=1, викликів=0, текст='Контроль показу без виклику моделі.',
                    опис='Контроль', підпис='образ', речі=[dict(id=pair['id'], назва=pair['назва'],
                    слот='взуття', фото=photo, ціна=pair.get('ціна'))], мітки=[], знахідки=[],
                    питання=data['сцени'][0]['питання'], етапи=dict(викликів=0, виклики=[]),
                    свідомі=[], невиконано=None, різноманітність=None, мова=[], мова_спроб=0,
                    мова_видано='так', фото_не_ті=[], дібрав_код_слоти=[])
        packet = dict(в='ПОКАЗ-V1', збірка=directory, каталог='каталог_повний.xml',
                      профіль='Контроль', розклад='12', прогін='пр-перевірка-4214',
                      випадок_рядок='Без названого часу', пул=28890,
                      картки=[card, dict(card, рука='2')])
        page.evaluate("""() => {
          window.ВХОДИ_ПЕРЕВІРКИ = [];
          питатиПачкамиП = async (entries) => {
            ВХОДИ_ПЕРЕВІРКИ.push(...entries.map(([key, slot, message]) => ({slot, message})));
            return {записи: [], стани: new Map(entries.map(([key]) =>
              [key, {текст: НАПИС_БЕЗ_ШАРУ_П.card_unchecked, стан: 'fallback'}]))};
          };
        }""")
        page.evaluate("""async (packet) => {
          П = packet;
          for (const card of П.картки) await питаннямиП(card, 'перевірка');
          рендер();
        }""", packet)
        for index in range(2):
            page.evaluate("(i) => { режим('образи'); показатиОбраз(i); }", index)
            page.locator(f'#к-{index} details.питання-коду').evaluate_all('(nodes) => nodes.forEach(n => n.open = true)')
            page.locator(f'#к-{index}').scroll_into_view_if_needed()
            page.screenshot(path=str(artifact / f'{label}-рука-{index+1}-390x844.png'), animations='disabled')
            if index == 0:
                page.locator('#к-0').screenshot(path=str(artifact / f'{label}-рука-повна.png'), animations='disabled')
        page.evaluate("""(args) => {
          const [card, photo] = args;
          мовоюП = async (texts) => {
            ВХОДИ_ПЕРЕВІРКИ.push({evaluation: texts});
            throw new Error('контроль без живої моделі');
          };
          ОЦ.результат = {картка: card}; ОЦ.перелік = {так: true};
          ОЦ.фото = [{дані: photo.split(',')[1], тип: 'image/jpeg'}];
          Екран.змінити({режим: 'оцінка', вхід: Екран.стан.вхід + 1});
          намалюватиКарткуОцінки();
        }""", [data['сцени'][0]['картка'], photo])
        page.locator('#оц-невідоме').evaluate('(node) => node.open = true')
        page.locator('#оц-картка').evaluate('(node) => window.scrollTo(0, node.getBoundingClientRect().top + window.scrollY)')
        page.screenshot(path=str(artifact / f'{label}-оцінка-390x844.png'), animations='disabled')
        page.locator('#оц-картка').screenshot(path=str(artifact / f'{label}-оцінка-повна.png'), animations='disabled')
        # Зовнішній виклик уже заглушений; підготовка текстів і очищення — штатні.
        page.evaluate('async () => { await невідомеОцінкиСловамиП(ОЦ.результат.картка, {мова_шару: []}); }')
        logs.append(dict(дерево=directory, FOTO=os.environ.get('FOTO'), viewport='390x844',
                         входи=page.evaluate('ВХОДИ_ПЕРЕВІРКИ'), помилки=errors,
                         текст=page.locator('#оц-картка').inner_text()))
        page.close()
    browser.close()
(artifact / 'браузер.json').write_text(json.dumps(dict(фото=pair['фото'][0], id=pair['id'],
    назва=pair['назва'], прогін=logs), ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(dict(знімків=10, FOTO=os.environ.get('FOTO'), помилки=[x['помилки'] for x in logs]), ensure_ascii=False))
