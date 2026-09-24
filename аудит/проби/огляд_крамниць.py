# -*- coding: utf-8 -*-
# Аркуші ручного огляду каталогу (п.10 CLAUDE.md): з КОЖНОЇ крамниці до 12 речей (спершу по одній з кожного
# слота, решта випадково, сід 23), для кожної — фото, яке показує КАРТКА, і те, що про річ думає код (колір і його
# джерело/спір, крій, довжина, візерунок, тип, назва). Куратор переглядає аркуші очима. Так 23.09 знайдено рядки
# 139 (слот за словом-ключем) і 142–144 (фото≠колір, мертві фото, назви).
# Запуск: python3 аудит/проби/огляд_крамниць.py <тека_для_аркушів>   (потрібні PIL, curl, мережа; ~5 хв)
import sys, os, json, random, collections, subprocess, hashlib, math, concurrent.futures as cf
S = os.path.abspath(sys.argv[1]); os.makedirs(S, exist_ok=True); os.makedirs('/tmp/фото_огляд', exist_ok=True)
Д = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'джерела')
sys.path.insert(0, Д); os.chdir(Д)
import feed as F; F.каталог_на_диску('каталог_повний.xml')
import фід_каталог as ФК
from PIL import Image, ImageDraw, ImageFont
кат = ФК._прочитати_каталог('каталог_повний.xml', 0)['каталог']
# ТЕ САМЕ ФОТО, ЩО НА КАРТЦІ: кличемо ту саму функцію, яку кличе показ. Доти тут стояв вирізаний
# текстом із `міст_опис.показ` `_фото_речі` (він був замиканням і звідси не викликався); з 23.09 правило
# живе в `фід_фото.кадри_речі` — одне місце на картку, пробу й цей аркуш (рядок 143).
import фід_фото as ФФ
_оф = F.читати_yml('каталог_повний.xml')[0]
_зб, _спільні, _хости = F.читати_збагачення(), ФФ._спільні_фото(_оф), ФФ._хости_крамниць(_оф)
_за_ід = {o['id']: o for o in _оф}
def фото_картки(x):
    o = _за_ід.get(x.get('id')) or x
    р = ФФ.кадри_речі(o, _спільні.get(o.get('магазин')) or {}, _хости, (_зб.get(o.get('id')) or {}).get('фото'))
    return р[0] if р else None
по = collections.defaultdict(list)
for x in кат: по[x.get('магазин')].append(x)
rnd = random.Random(23); вибір = {}
for м, xs in sorted(по.items()):
    сл = collections.defaultdict(list)
    for x in xs: сл[x.get('слот')].append(x)
    s = [rnd.choice(ys) for _, ys in sorted(сл.items(), key=lambda kv: -len(kv[1]))]
    решта = [x for x in xs if x not in s]; rnd.shuffle(решта); вибір[м] = (s + решта)[:12]
def шлях(u): return '/tmp/фото_огляд/' + hashlib.md5(u.encode()).hexdigest() + '.img'
def тягти(u):
    p = шлях(u)
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        subprocess.run(['curl', '-sS', '-L', '-m', '40', '-o', p, u], capture_output=True)
    return p
урли = [фото_картки(x) for xs in вибір.values() for x in xs]
with cf.ThreadPoolExecutor(12) as ex: list(ex.map(тягти, [u for u in урли if u]))
def lab_rgb(lab):
    L, a, b = lab; fy = (L + 16) / 116; fx = fy + a / 500; fz = fy - b / 200
    f = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    X, Y, Z = 0.95047 * f(fx), 1.0 * f(fy), 1.08883 * f(fz)
    r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z; g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z; bb = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
    c = lambda v: max(0, min(255, round(255 * (1.055 * v ** (1 / 2.4) - 0.055 if v > 0.0031308 else 12.92 * v))))
    return (c(r), c(g), c(bb))
шр = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
шрж = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
Ш, ВФ, ВТ = 270, 330, 150
for м, xs in вибір.items():
    арк = Image.new('RGB', (Ш * 4, (ВФ + ВТ) * 3 + 36), 'white'); д = ImageDraw.Draw(арк)
    д.text((8, 8), '%s · у каталозі %d речей · слоти: %s' % (м, len(по[м]), ', '.join('%s %d' % (k, v) for k, v in sorted(collections.Counter(x.get('слот') for x in по[м]).items(), key=lambda kv: -kv[1]))), fill='black', font=шрж)
    for i, x in enumerate(xs):
        X, Y = (i % 4) * Ш, 36 + (i // 4) * (ВФ + ВТ)
        u = фото_картки(x)
        try:
            im = Image.open(шлях(u)).convert('RGB'); im.thumbnail((Ш - 10, ВФ - 10)); арк.paste(im, (X + 5, Y + 5))
        except Exception as e:
            д.text((X + 10, Y + 20), 'на картці без фото (арка)' if not u else 'фото не відкрилось', fill='red', font=шр)
        lab = x.get('lab')
        if lab: д.rectangle([X + Ш - 45, Y + ВФ + 4, X + Ш - 8, Y + ВФ + 30], fill=lab_rgb(lab), outline='black')
        рядки = ['%s · %s' % (x.get('id', '').split('@')[0], x.get('слот')),
                 'колір: %s%s' % (x.get('колір_назва'), ('  (фото: %s)' % x.get('колір_назва_фото')) if x.get('колір_назва_фото') and x.get('колір_назва_фото') != x.get('колір_назва') else ''),
                 'джерело: %s%s' % (x.get('колір_джерело'), ' · СПІР' if x.get('колір_спір') else ''),
                 'крій: %s · довж: %s' % (x.get('крій'), x.get('довжина_рівень')),
                 'візерунок: %s · тип: %s' % (x.get('візерунок'), x.get('тип')),
                 (x.get('назва') or '')[:38], (x.get('назва') or '')[38:76]]
        for k, t in enumerate(рядки): д.text((X + 6, Y + ВФ + 4 + k * 19), t[:40], fill='black', font=шр)
    арк.save('%s/%s.jpg' % (S, м), quality=82)
print('крамниць', len(вибір), 'речей', sum(len(v) for v in вибір.values()))
