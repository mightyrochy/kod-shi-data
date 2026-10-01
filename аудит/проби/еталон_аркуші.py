# -*- coding: utf-8 -*-
# Аркуші ручної перевірки еталону (наряд РЗ-Е, п.10 CLAUDE.md): на кожну річ — два перші кадри картки і таблиця полів:
# правда з фото і що кажуть (а) текст крамниці, (б) продукт сьогодні, (в) qwen3-vl, (г) розбір MamayLM; клітинка
# зафарбована вердиктом (зелений — правильно, червоний — хибно, помаранч — вигадано, сірий — невідомо/нема поля,
# блакитний — не судиться). Під таблицею — рядок features розбору з судом очима. 6 речей на аркуш.
# Запуск: python3 аудит/проби/еталон_аркуші.py <тека>   (PIL, curl; кадри — з кеша /tmp/фото_огляд або з мережі)
import sys, os, json, hashlib, subprocess
from PIL import Image, ImageDraw, ImageFont
ТЕКА = os.path.abspath(sys.argv[1]); os.makedirs(ТЕКА, exist_ok=True); os.makedirs('/tmp/фото_огляд', exist_ok=True)
Е = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'джерела', 'проби', 'еталон_розбору.json'),
                   encoding='utf-8'))
КОЛІР = {'правильно': (190, 236, 190), 'хибно': (250, 170, 170), 'вигадано': (255, 200, 120), 'невідомо': (235, 235, 235),
         'нема поля': (250, 250, 250), 'не судиться': (200, 225, 250)}
шр = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
шрж = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
def кадр(u):
    p = '/tmp/фото_огляд/' + hashlib.md5(u.encode()).hexdigest() + '.img'
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        subprocess.run(['curl', '-sS', '-L', '-m', '40', '-o', p, u], capture_output=True)
    try:
        im = Image.open(p).convert('RGB'); im.thumbnail((230, 330)); return im
    except Exception:                                 # noqa: BLE001 — битий кадр видно на аркуші підписом
        return None
def показ(в):
    if в is None or в == []:
        return '—'
    if isinstance(в, list):
        return ','.join('/'.join(ч) if isinstance(ч, list) else str(ч) for ч in в)
    return str(в)
def переносити(т, ширина, шрифт, д):
    рядки, поточний = [], ''
    for сл in str(т).split():
        if д.textlength((поточний + ' ' + сл).strip(), font=шрифт) > ширина and поточний:
            рядки.append(поточний); поточний = сл
        else:
            поточний = (поточний + ' ' + сл).strip()
    return рядки + [поточний] if поточний else рядки
Ш, В = 1180, 520                                         # одна річ: 2 кадри зліва, таблиця справа
for а in range(0, len(Е['речі']), 6):
    арк = Image.new('RGB', (Ш * 2 + 30, В * 3 + 20), 'white'); д = ImageDraw.Draw(арк)
    for і, р in enumerate(Е['речі'][а:а + 6]):
        X, Y = 10 + (і % 2) * (Ш + 10), 10 + (і // 2) * В
        д.rectangle([X, Y, X + Ш, Y + В - 8], outline=(180, 180, 180))
        д.text((X + 6, Y + 4), '#%d · %s · %s' % (р['н'], р['id'], р['група']), fill='black', font=шрж)
        for к, u in enumerate(р['кадри'][:2]):
            im = кадр(u)
            if im:
                арк.paste(im, (X + 6 + к * 236, Y + 24))
            else:
                д.text((X + 10 + к * 236, Y + 60), 'кадр не відкрився', fill='red', font=шр)
        ТX, кол = X + 480, (88, 150, 112, 112, 112, 112)
        for к, н in enumerate(('поле', 'правда з фото', '(а) текст', '(б) продукт', '(в) qwen', '(г) MamayLM')):
            д.text((ТX + sum(кол[:к]) + 3, Y + 24), н, fill='black', font=шрж)
        for ряд, п in enumerate(Е['поля']):
            yy = Y + 42 + ряд * 19
            пр = р['правда'][п]
            д.text((ТX + 3, yy), п, fill='black', font=шр)
            д.text((ТX + кол[0] + 3, yy), (пр if isinstance(пр, str) else (показ(пр) or '[] коду нема'))[:24], fill='black', font=шр)
            for к, дж in enumerate('абвг'):
                x0 = ТX + sum(кол[:к + 2])
                в = р['вердикти'][дж][п]
                д.rectangle([x0, yy - 1, x0 + кол[к + 2] - 2, yy + 16], fill=КОЛІР[в])
                зн = р['джерела'][дж][п]
                д.text((x0 + 3, yy), ('' if зн == 'нема поля' else показ(зн))[:17], fill='black', font=шр)
        yy = Y + 42 + len(Е['поля']) * 19 + 6
        ф = р['features']
        for т, колір in [('деталь з фото: ' + р['деталь'], 'black'),
                         ('(г) features: %s' % ф['рядок'], 'black'),
                         ('суд очима: деталь %s%s' % ('є' if ф['деталь'] else 'НЕМА', ' · ВИГАДКА: ' + ф['вигадка'] if ф['вигадка'] else ''),
                          (170, 60, 0) if ф['вигадка'] or not ф['деталь'] else (0, 110, 0))] + \
                ([('примітка: ' + р['примітка'], (90, 90, 90))] if р['примітка'] else []):
            for рядок in переносити(т, Ш - 490, шр, д)[:3]:
                if yy < Y + В - 22:
                    д.text((ТX, yy), рядок, fill=колір, font=шр); yy += 15
    арк.save('%s/еталон_%02d.png' % (ТЕКА, а // 6 + 1), optimize=True)
print('аркушів %d у %s' % ((len(Е['речі']) + 5) // 6, ТЕКА))
