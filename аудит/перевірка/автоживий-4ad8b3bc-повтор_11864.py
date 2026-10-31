# -*- coding: utf-8 -*-
"""Повтор KeyError 'слот' у оцінці з чату (автоживий 4ad8b3bc, сцена 6б). Моделі нема.
Запуск: git worktree add /tmp/wt 4ad8b3bc; gunzip -k /tmp/wt/джерела/каталог_brief.xml.gz;
        cd /tmp/wt/джерела && python3 -W ignore <цей файл> <вердикти.txt сцени ж1_оціни_образ_6б>
Речі, паспорт і розміри кадрів — із запису; пікселі синтезовано з виміряних hex (знімків кадрів у записі нема)."""
import base64, json, sys
sys.path.insert(0, '.')
o = json.load(open(sys.argv[1], encoding='utf-8'))
пр = o['прогони'][2]['вердикти'][0]; e = пр['етапи']
вх = dict(o['прогони'][2]['спільне']['вхід_прогону'])
кол = {'ф1': (0x81, 0x88, 0x6d), 'ф1·2': (0x6f, 0x21, 0x30), 'ф2': (0xe6, 0xdf, 0xd2), 'ф2·2': (0x1d, 0x1c, 0x1c)}
пк = {}
for ід, п in e['пікселі'].items():
    w, h = п['ширина'], п['висота']; б = bytearray()
    for y in range(h):
        for x in range(w):
            б += bytes(кол[ід] if (w * .15 < x < w * .85 and h * .15 < y < h * .85) else (255, 255, 255))
    пк[ід] = dict(ширина=w, висота=h, дані=base64.urlsafe_b64encode(bytes(б)).decode())
import оцінка_образу as О
d = dict(вх, каталог='каталог_brief.xml', кеш_кольорів='/tmp/кеш.json', речі=e['речі']['речі'], пікселі=пк,
         крамниця=True, сценарій_паспорта=e['сценарій_паспорта'])
for з_паспортом in (False, True):
    d2 = dict(d) if з_паспортом else {к: v for к, v in d.items() if к != 'сценарій_паспорта'}
    try:
        с = О.суд(d2)
        print('паспорт=%s: OK, зміни %s' % (з_паспортом, [z['звідки'] for z in с['зміни']]))
    except KeyError as ex:
        print('паспорт=%s: KeyError %s' % (з_паспортом, ex))
