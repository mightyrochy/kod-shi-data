"""РЕЧІ-ЗАМІР (5287): з тек прогонів `<фігура>_s<сід>/vidpovidi` бере відповіді кроку «ОЦІНКА: речі на фото»
і друкує таблицю; сирі відповіді кладе в `сирі/`. Запуск: python аналіз.py <тека_прогонів> <тека_результату>"""
import sys, re, json, glob, os
ВХ, ВИХ = sys.argv[1], sys.argv[2]
os.makedirs(ВИХ + '/сирі', exist_ok=True)
ІСТИНА = [('ф1', 'outerwear'), ('ф1', 'top'), ('ф1', 'bottom'), ('ф2', 'shoes'), ('ф2', 'shoes')]  # 5 речей наряду
def слот(с): return 'top' if 'top' in (с or '') else с
рядки, зведення = [], []
for т in sorted(glob.glob(ВХ + '/f2*_s*')):
    ім = os.path.basename(т); фіг, сід = re.match(r'f2(\w)_s(\d+)', ім).groups()
    файли = sorted(glob.glob(т + '/vidpovidi/*ОЦІНКА_речі_на_фото*'))
    if not файли: рядки.append((фіг, сід, 0, 'нема виклику', '', '', '', '')); continue
    for нф, ф in enumerate(файли, 1):
        t = open(ф, encoding='utf-8').read()
        з = re.search(r'── ВІДПОВІДЬ \((\d+) симв\., ([\d.]+) с, HTTP (\d+)\) ──\n', t)
        тіло, сек = (t[з.end():].strip(), з.group(2)) if з else ('', '?')
        try:
            о = json.loads(тіло); it = (о.get('answer') or о).get('items'); ок = isinstance(it, list)
        except Exception: it, ок = [], False
        ним = list(ІСТИНА); названо = 0
        for р in it or []:
            к = (р.get('photo'), слот(р.get('slot')))
            if к in ним: ним.remove(к); названо += 1
        взуття = sum(1 for р in it or [] if р.get('slot') == 'shoes')
        весь = sum(1 for р in it or [] if (lambda f: f and f['right'] - f['left'] >= 850 and f['bottom'] - f['top'] >= 850 or
                   f and (f['right'] - f['left']) * (f['bottom'] - f['top']) >= 0.6e6)(р.get('frame')))
        окремо = len(it or []) - весь
        json.dump({'файл': ім, 'відповідь_сира': тіло}, open(f'{ВИХ}/сирі/{ім}_{нф}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        рядки.append((фіг, сід, нф, f'{названо}/5 (усього {len(it or [])})', 'так' if взуття else 'ні', f'{окремо} окремо, {весь} на весь кадр', 'так' if ок else 'НІ', сек))
        зведення.append((нф, названо, len(it or []), bool(взуття), весь, окремо, ок, float(сек) if сек != '?' else 0))
print('| фігура ф2 | сід | виклик | речей із 5 | взуття | рамки | JSON | с |\n|---|---|---|---|---|---|---|---|')
for р in рядки: print('| ' + ' | '.join(map(str, р)) + ' |')
for назва, вибір in (('виклик 1 (сцена оцінки, картка)', [з for з in зведення if з[0]==1]), ('усі виклики кроку (виклик 2 — повторна оцінка в 6б)', зведення)):
    n = len(вибір)
    if n: print(f'\nПідсумок, {назва}, {n}: рівно 5 із 5 — {sum(1 for з in вибір if з[1]==5 and з[2]==5)}; взуття — {sum(1 for з in вибір if з[3])}; '
          f'не JSON/порожньо — {sum(1 for з in вибір if not з[6] or not з[2])}; рамок на весь кадр — {sum(з[4] for з in вибір)} з {sum(з[2] for з in вибір)}; '
          f'середній час {sum(з[7] for з in вибір)/n:.1f} с')
