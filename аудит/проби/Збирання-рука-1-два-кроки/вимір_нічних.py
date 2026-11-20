#!/usr/bin/env python3
"""Крок 1 наряду `Збирання-рука-1-два-кроки` на нічному наборі стендом у хмарі (claude -p, руки 1–2 разом).

python3 -I аудит/проби/Збирання-рука-1-два-кроки/вимір_нічних.py [тека=аудит/проби/нічні/20261120]  (з кореня)

Секунди кроків — рядки «↔ модель #N <форма> … → X с» `лог.txt` (руки 1 і 2 йдуть паралельно, тож кроки обох рук
разом: ланцюг у них той самий). Ремонт змінив обраний образ — вибір (`ВЕРДИКТ_V1→ВИБІР_V1`) називає id; ремонт, чия
відповідь дала цей образ із тим самим складом, що в запиті вибору, — пара; склад того ж id у вердикті запиту ремонту
(образ складання) проти складу після ремонту. Чистий у складанні — `structure.ok` образу у вердикті ремонту (гейтів
нічний запис не несе). Нових викликів моделі нема."""
import glob, json, os, re, sys

тека = sys.argv[1] if len(sys.argv) > 1 else 'аудит/проби/нічні/20261120'
КРОК = (('ПАКЕТ_V1→ОБРАЗИ_V1', 'складання'), ('ВЕРДИКТ_V1→ОБРАЗИ_V1', 'ремонт'), ('ВЕРДИКТ_V1→ВИБІР_V1', 'вибір'),
        ('ОПИС_V1', 'опис'), ('ПОВНОТА', 'повнота'))


def обмін(шлях):
    д = json.load(open(шлях, encoding='utf-8'))
    з = д['запит']['messages'][0]['content']
    з = з if isinstance(з, str) else ' '.join(ч.get('text', '') for ч in з if isinstance(ч, dict))
    т = д['відповідь'].get('body')
    т = json.loads(т) if isinstance(т, str) else (т or {})
    в = ''.join(ч.get('text', '') for ч in т.get('content', []) if isinstance(ч, dict))
    def j(s):
        try:
            return json.loads(s[s.index('{'):s.rindex('}') + 1])
        except Exception:
            return None
    return j(з), j(в)


сек, пари = {}, []
for сц in sorted(glob.glob(os.path.join(тека, '*', 'лог.txt'))):
    сцена = os.path.basename(os.path.dirname(сц))
    for р in open(сц, encoding='utf-8'):
        м = re.search(r'↔ модель #\d+ (\S+).*→ ([\d.]+) с', р)
        if м:
            for мітка, к in КРОК:
                if м.group(1).startswith(мітка):
                    сек.setdefault(к, []).append(float(м.group(2)))
    ремонти, вибори = [], []
    for ф in sorted(glob.glob(os.path.join(os.path.dirname(сц), 'VIDPOVIDI', 'обмін', '*.json'))):
        з, в = обмін(ф)
        if not (з and в):
            continue
        роль = (з.get('task') or {}).get('role', '')
        if роль.startswith('You are the stylist') and 'Improve the outfits' in роль:
            ремонти.append((з, в))
        elif 'Choose one of your outfits' in роль:
            вибори.append((з, в))
    for з, в in вибори:
        х = в.get('chosen')
        після = next((frozenset(о['your_outfit']['items']) for о in з.get('verdict', [])
                      if о['your_outfit'].get('id') == х), None)
        пара = next(((зр, вр) for зр, вр in ремонти for о in вр.get('outfits', [])
                     if о.get('id') == х and frozenset(о.get('items', [])) == після), None)
        if not пара:
            пари.append(dict(сцена=сцена, обрано=х, змінив=None, чистий=None))
            continue
        до = next((о for о in пара[0].get('verdict', []) if о['your_outfit'].get('id') == х), None)
        пари.append(dict(сцена=сцена, обрано=х, змінив=(frozenset(до['your_outfit']['items']) != після) if до else None,
                         чистий=((до or {}).get('structure') or {}).get('ok'),
                         чистих=sum(1 for о in пара[0].get('verdict', []) if (о.get('structure') or {}).get('ok')),
                         з=len(пара[0].get('verdict', []))))

for п in пари:
    print('%s · обрано %s · ремонт змінив обраний: %s · обраний без блокерів у складанні: %s · чистих %s/%s' % (
        п['сцена'], п['обрано'], п['змінив'], п['чистий'], п.get('чистих'), п.get('з')))
for к, сс in sorted(сек.items()):
    сс = sorted(сс)
    print('крок %-10s викликів %2d · с: мін %.1f · медіана %.1f · макс %.1f' % (к, len(сс), сс[0], сс[len(сс) // 2],
                                                                               сс[-1]))
з = [п for п in пари if п['змінив'] is not None]
print('вибір руки 1–2: %d; ремонт НЕ змінив обраний образ: %d з %d; обраний без блокерів уже в складанні: %d з %d' % (
    len(пари), sum(1 for п in з if not п['змінив']), len(з), sum(1 for п in з if п['чистий']), len(з)))
for сц in sorted(glob.glob(os.path.join(тека, '*', 'лог.txt'))):
    for р in open(сц, encoding='utf-8'):
        м = re.search(r'рука 1: картка за ([\d.]+) с', р)
        if м:
            print('рука 1: картка за %s с · %s' % (м.group(1), os.path.basename(os.path.dirname(сц))))
