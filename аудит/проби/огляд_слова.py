# -*- coding: utf-8 -*-
# Аркуш ручного огляду ОДНОГО СЛОВА поля кольору (хвиля 2, п.4 наряду «оком: аркуші по 12 речей на кожне
# нове вікно»). Той самий вибір кадру, що на картці (`фід_фото.кадри_речі`), і поруч — що про річ думає код:
# у яке слово складає, який hex дали жнива і чи цей hex ПІДТВЕРДЖЕНИЙ свідком (правило вибірки #314).
# Запуск: python3 аудит/проби/огляд_слова.py <тека> електрик кориця капучіно ...   (потрібні PIL, curl, мережа)
import sys, os, subprocess, concurrent.futures as cf
S = os.path.abspath(sys.argv[1]); os.makedirs(S, exist_ok=True)
Д = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'джерела')
sys.path.insert(0, Д); os.chdir(Д)
import feed as F; F.каталог_на_диску('каталог_повний.xml')
import фід_каталог as ФК, фід_фото as ФФ, фід_збагачення as FZ, фід_розбір as FR, verify as V, colorspace as cs
from PIL import Image, ImageDraw, ImageFont
оф = FR.читати_yml('каталог_повний.xml')[0]
зб, сп, хо = F.читати_збагачення(), ФФ._спільні_фото(оф), ФФ._хости_крамниць(оф)
кат = {r['id']: r for r in ФК._прочитати_каталог('каталог_повний.xml', 0)['каталог']}
н = lambda s: ' '.join(str(s or '').lower().split())
ш = lambda р: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', р) if os.path.exists(
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf') else ImageFont.load_default()
def тягнути(url, шлях):
    if os.path.exists(шлях) and os.path.getsize(шлях) > 900: return шлях
    r = subprocess.run(['curl', '-sS', '-m', '30', '-o', шлях, url], capture_output=True)
    return шлях if r.returncode == 0 and os.path.exists(шлях) and os.path.getsize(шлях) > 900 else None
for слово in sys.argv[2:]:
    речі = [o for o in оф if н(o.get('колір_сирий')) == слово and len(ФК._СЕП_КОЛЬОРУ.split(н(o.get('колір_сирий')))) == 1]
    видно, бачені = [], set()
    for o in речі:
        z = зб.get(o['id']) or {}; k = z.get('колір_основний') or {}
        д = z.get('фото') or o.get('group_id') or o['id']
        if д in бачені: continue
        бачені.add(д)
        кадри = ФФ.кадри_речі(o, сп.get(o.get('магазин')) or {}, хо, z.get('фото'))
        if кадри: видно.append((o, z, k, кадри[0]))
        if len(видно) >= 12: break
    if not видно: print('%-14s — жодного кадру' % слово); continue
    with cf.ThreadPoolExecutor(6) as p:
        файли = list(p.map(lambda t: тягнути(t[3], os.path.join('/tmp', 'ф_' + t[0]['id'].replace('/', '_') + '.img')), видно))
    К, Р, ПІД = 4, 300, 74
    аркуш = Image.new('RGB', (К * Р, ((len(видно) + К - 1) // К) * (Р + ПІД)), 'white')
    d = ImageDraw.Draw(аркуш); дрібн, сер = ш(13), ш(16)
    for i, ((o, z, k, url), ф) in enumerate(zip(видно, файли)):
        x, y = (i % К) * Р, (i // К) * (Р + ПІД)
        try:
            im = Image.open(ф).convert('RGB'); im.thumbnail((Р, Р)); аркуш.paste(im, (x + (Р - im.width) // 2, y))
        except Exception: d.text((x + 8, y + Р // 2), 'фото не відкрилось', font=сер, fill='red')
        р = кат.get(o['id']) or {}
        свідок = FZ.колір_збагачення(z)[2] if z else '—'
        hx = (k or {}).get('hex') or '—'
        лаб = ('L%.0f C%.0f' % cs.lch(cs.hx(hx))[:2]) if hx != '—' else ''
        if hx != '—': d.rectangle([x + Р - 34, y + 4, x + Р - 6, y + 32], fill=hx, outline='black')
        d.text((x + 4, y + Р + 2), o['id'][:34], font=дрібн, fill='black')
        d.text((x + 4, y + Р + 18), 'код: %s' % (р.get('колір_ім') or '—'), font=сер, fill='#004488')
        d.text((x + 4, y + Р + 38), 'жнива: %s %s v%s' % (hx, лаб, z.get('версія') or 1), font=дрібн, fill='black')
        d.text((x + 4, y + Р + 54), 'свідок: %s' % свідок[:40], font=дрібн, fill='#886600')
    шлях = os.path.join(S, 'слово_%s.jpg' % слово.replace(' ', '_').replace('/', '_'))
    аркуш.save(шлях, quality=88)
    print('%-14s речей %2d · аркуш %s' % (слово, len(видно), шлях))
