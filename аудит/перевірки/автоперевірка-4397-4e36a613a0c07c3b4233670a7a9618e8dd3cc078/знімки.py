"""Нативний показ бази й голови, 390×844, FOTO=1; без мовної моделі."""
import base64
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as XML
from playwright.sync_api import sync_playwright

ДОКАЗИ = Path(__file__).resolve().parent
КОРІНЬ = ДОКАЗИ.parents[2]
ТИМЧАСОВО = КОРІНЬ.parent / 'tmp'
os.environ['FOTO'] = '1'
фото = {}
for _, вузол in XML.iterparse(gzip.open(КОРІНЬ / 'каталог_повний.xml.gz'), events=['end']):
    if вузол.tag == 'offer':
        if вузол.get('id') in ('ж-00133', 'ж-08677'):
            адреса = вузол.findtext('picture')
            файл = ДОКАЗИ / (вузол.get('id') + '.webp')
            if файл.exists():
                дані, тип = файл.read_bytes(), 'image/webp'
            else:
                запит = urllib.request.Request(адреса, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(запит, timeout=40) as відповідь:
                    дані = відповідь.read()
                    тип = відповідь.headers.get_content_type()
                файл.write_bytes(дані)
            фото[вузол.get('id')] = dict(назва=вузол.findtext('name'), адреса=адреса,
                                        кадр='data:'+тип+';base64,'+base64.b64encode(дані).decode())
        вузол.clear()
        if len(фото) == 2:
            break
журнал = []
with sync_playwright() as п:
    браузер = п.chromium.launch(headless=True, args=['--disable-gpu'])
    for назва, тека in [('ДО', 'check4397-base'), ('ПІСЛЯ', 'check4397-head')]:
        дерево = ТИМЧАСОВО / тека
        код = """
import json
import суд_погода as П
import реєстр_сила as С
речі=[dict(id='колготи',назва='Колготки (технічна проба)',слот='колготи',L=29.5),
      dict(id='ж-00133',назва='Сукня',слот='сукня',L=50),
      dict(id='ж-08677',назва='Черевики',слот='взуття',L=10)]
сирі=[з for з in П.панчішні(речі) if з['правило']=='K-HOS-02']
вих=[з for з in С.обмежити_вагу(сирі) if not з.pop('під_підлогою',False)]
print(json.dumps(вих,ensure_ascii=False))
"""
        знахідки = json.loads(subprocess.check_output([sys.executable, '-X', 'utf8', '-c', код],
                                                     cwd=дерево/'джерела', encoding='utf-8'))
        html = дерево/'джерела/перевірка-4397.html'
        збірка = """
const fs=require('fs'),h=require('./показ_шаблон.js');
fs.writeFileSync('перевірка-4397.html',h.підставитиШаблон(h.зібратиШаблонПоказу('показ.html'),{
__МОДУЛІ_ПОКАЗУ__:'ЗАГЛУШКА',__ЗБІРКА_ПОКАЗУ__:'перевірка-4397',__ВІДБИТОК__:'перевірка',
__ФІД_ПОКАЗУ__:'каталог_повний.xml',__КАТАЛОГ_ПОКАЗУ__:'каталог перевірки',
__ДОВІДНИК_ПОКАЗУ__:h.прочитатиДовідникJSON(process.cwd()),
__ПРОМПТ_КОЛІР_ПОКАЗУ__:'',__ВИБІРКА_ПОКАЗУ__:'[]'}));
"""
        subprocess.run(['node', '-e', збірка], cwd=дерево/'джерела', check=True)
        сторінка = браузер.new_page(viewport={'width':390, 'height':844}, device_scale_factor=1)
        помилки = []
        сторінка.on('pageerror', lambda e: помилки.append(str(e)))
        сторінка.route('https://**/*', lambda маршрут: маршрут.abort())
        сторінка.goto(html.as_uri(), wait_until='load')
        сторінка.wait_for_function("typeof рендер === 'function'")
        сторінка.wait_for_function("Екран.стан.запущено === true")
        речі = [dict(id='колготи',назва='Колготки (технічна проба)',слот='колготи')]
        for ід, слот in [('ж-00133','сукня'), ('ж-08677','взуття')]:
            речі.append(dict(id=ід, назва=фото[ід]['назва'], слот=слот, фото=фото[ід]['кадр']))
        картка = dict(рука='1',ітерацій=1,викликів=0,текст='Технічна проба K-HOS-02 без виклику моделі.',
                       опис='Контроль',підпис='образ',речі=речі,мітки=[],знахідки=знахідки,питання=[],
                       етапи=dict(викликів=0,виклики=[]),свідомі=[],невиконано=None,
                       різноманітність=None,мова=[],мова_спроб=0,мова_видано='так',фото_не_ті=[],дібрав_код_слоти=[])
        пакет = dict(в='ПОКАЗ-V1',збірка=тека,каталог='каталог_повний.xml',профіль='Контроль',
                     розклад='1',прогін='пр-перевірка-4397',випадок_рядок='Технічна проба погодного правила',
                     пул=27525,картки=[картка])
        сторінка.evaluate("p => {П=p;рендер();режим('образи');показатиОбраз(0);}", пакет)
        сторінка.locator('#к-0').scroll_into_view_if_needed()
        сторінка.wait_for_function("[...document.querySelectorAll('#к-0 img')].every(i=>i.complete)")
        сторінка.screenshot(path=str(ДОКАЗИ/(назва+'-390x844.png')), animations='disabled')
        сторінка.locator('#к-0').screenshot(path=str(ДОКАЗИ/(назва+'-картка.png')), animations='disabled')
        журнал.append(dict(дерево=тека,знахідок=len(знахідки),помилки=помилки,
                           текст=сторінка.locator('#к-0').inner_text(),
                           фото=сторінка.locator('#к-0 img').evaluate_all('(xs)=>xs.map(x=>({width:x.naturalWidth,height:x.naturalHeight}))')))
        сторінка.close()
    браузер.close()
(ДОКАЗИ/'знімки.json').write_text(json.dumps(dict(FOTO=os.environ['FOTO'],входи='L*=29.5/50/10 — синтетичні; фото з каталогу не є виміром L*',
                                                 фото={k:v['адреса'] for k,v in фото.items()},журнал=журнал),
                                           ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(журнал,ensure_ascii=False))
