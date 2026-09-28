#!/usr/bin/env python3
"""ІН-1: готує знімки для інструкції з проходів стенда.

Джерела:
  ZH  — прохід `аудит/проби/рв6_стенд.js` із ЖИВОЮ моделлю (ZHYVA=sonnet): усе,
        де на екрані стоять СЛОВА моделі — палітра, картка образу, оцінка.
  DOD — власний короткий скрипт Playwright на тій самій збірці: те, де моделі не
        треба (знайомство, порожній сценарій, аркуші правки, блок вивантаження).

Обрізи вибрані так, щоб не зачепити смугу нижньої панелі: вона `position: fixed`
і на довгому знімку лягає поперек сторінки. Там, де знімок робив власний скрипт,
панель на час кадру ховалась, і обрізати нема чого.
"""
import os, sys
from PIL import Image

ZH = '/tmp/znimky_zh'
DOD = '/tmp/znimky_dod'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'знімки')

# ім'я -> (тека, файл, обріз (left, top, right, bottom) або None)
НАРІЗКА = {
    '01-znaiomstvo-pro-tebe':  (DOD, 'znaiomstvo_1.png',           (0, 0, 780, 1608)),
    '02-znaiomstvo-do-lytsia': (DOD, 'znaiomstvo_2.png',           (0, 0, 780, 1600)),
    '03-znaiomstvo-fihura':    (DOD, 'znaiomstvo_3.png',           (0, 0, 780, 1360)),
    '04-scenarii-porozhnii':   (DOD, 'scenarii_porozhnii.png',     (0, 0, 780, 1420)),
    '05-scenarii-rozmova':     (ZH,  'ekran_scenarii_povnyi_seed3.png', (0, 0, 390, 745)),
    '05b-scenarii-riadky':     (DOD, 'scenarii_kartka_zapovnena.png', (0, 0, 780, 1300)),
    '06-nahoda-plytky':        (DOD, 'redaktor_nahoda_arkush_vikno.png', (0, 600, 780, 1688)),
    '07-koly-pohoda':          (DOD, 'redaktor_koly.png',          None),
    '08-makiiazh':             (DOD, 'redaktor_makiiazh.png',      None),
    '09-prykrasy':             (DOD, 'redaktor_prykrasy.png',      None),
    '10-ne-khochu':            (DOD, 'redaktor_veto.png',          None),
    '11-palitra':              (ZH,  'ekran_palitra_seed3.png',    (0, 0, 350, 700)),
    '11b-palitra-skhemy':      (ZH,  'ekran_palitra_seed3.png',    (0, 1000, 350, 1572)),
    '12-ochikuvannia':         (ZH,  'zbyrannia_04_seed3.png',     (0, 0, 390, 700)),
    '13-obrazy':               (ZH,  'ekran_obrazy_seed3.png',     (0, 0, 350, 600)),
    '14-kartka-obrazu':        (ZH,  'kartka_poz2_ruka1_seed3.png', (0, 0, 350, 660)),
    '15-verdykt':              (ZH,  'kartka_poz2_ruka1_seed3.png', (0, 2980, 350, 3660)),
    '16-otsinka-ekran':        (ZH,  'ekran_otsinka_seed3.png',    (0, 0, 350, 700)),
    '17-otsinka-kartka':       (ZH,  'otsinka_kartka_seed3.png',   (0, 0, 350, 700)),
    '18-profil':               (DOD, 'profil.png',                 (0, 0, 780, 1700)),
    '19-usi-obrazy':           (ZH,  'ekran_biblioteka_seed3.png', (0, 0, 350, 930)),
    '20-zhurnal':              (DOD, 'zhurnal.png',                None),
}

def main():
    os.makedirs(OUT, exist_ok=True)
    бракує = []
    for ім, (тека, файл, обріз) in sorted(НАРІЗКА.items()):
        ш = os.path.join(тека, файл)
        if not os.path.exists(ш):
            бракує.append(ш); continue
        im = Image.open(ш).convert('RGB')
        if обріз:
            im = im.crop(обріз)
        ціль = os.path.join(OUT, ім + '.png')
        im.save(ціль, optimize=True)
        print('%-26s %-44s %s' % (ім, файл, im.size))
    if бракує:
        print('НЕМА:', *бракує, sep='\n  '); sys.exit(1)

if __name__ == '__main__':
    main()
