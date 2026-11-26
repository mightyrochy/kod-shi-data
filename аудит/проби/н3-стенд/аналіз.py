"""Аналіз прогону стенда Н3: python3 аналіз.py <тека прогону> → підсумок у stdout і <тека>/підсумок.json."""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

Т = Path(sys.argv[1])
стан = json.loads((Т / 'стан.json').read_text())
обміни = [json.loads(л) for л in (Т / 'обміни.jsonl').read_text().splitlines() if л.strip()]


def час(с):
    return datetime.fromisoformat(с.replace('Z', '+00:00'))


def тіло(о):
    try:
        return json.loads(о.get('запит') or '')
    except ValueError:
        return None


def ряди(т):
    for поле in ('pool', 'candidates'):
        if т and isinstance(т.get(поле), dict):
            к = т[поле]['cols']
            return {tuple(р[к.index(x)] for x in ('n', 'price', 'kind', 'color') if x in к) for р in т[поле]['rows']}
    if т and isinstance(т.get('groups'), dict) and 'cols' in т['groups']:
        к = т['groups']['cols']
        return {tuple(р[к.index(x)] for x in ('n', 'price', 'kind', 'color')) for рр in т['groups']['groups'].values() for р in рр}
    return set()


звіт = стан['ядро']['звіт']
взято = {з['рука']: з['взято'] for з in звіт if з.get('заява') == 'pool_coverage'}
знято_скл = {з['рука']: з['скільки'] for з in звіт if з.get('заява') == 'pool_rows_trimmed' and з.get('крок') == 'складання'}
# складання: пул руки 1 і 2 (кількість рядків = взято − знято); частини/турнір — пул ширший, тож ключі рядків збираємо з усіх
пули = {1: set(), 2: set()}
рядки = []
for і, о in enumerate(обміни):
    т = тіло(о)
    роль = ((т or {}).get('task') or {}).get('role', '') if isinstance(т, dict) else ''
    вид = ('складання' if 'Build outfits' in роль else 'ремонт' if 'Improve the outfits' in роль else
           'вибір' if 'Choose one' in роль else 'турнір' if 'Pick the items' in роль else
           'опис' if (о.get('запит') or '').startswith('Catalogue photo') or 'Describe' in роль else
           'рука3/4-образ' if 'Put together one outfit' in роль else 'рука3/4-перелік' if 'list its items' in роль
           else о.get('тип'))
    рука = None
    if вид == 'рука3/4-образ':
        рука = 3 if т.get('person') else 4
    рядки.append(dict(і=і, вид=вид, рука=рука, т=т, о=о))
# руки 3/4 перелік: опис у переліку = відповідь прози тієї руки
проза = {р['о'].get('відповідь', '').strip()[:200]: р['рука'] for р in рядки if р['вид'] == 'рука3/4-образ'}
for р in рядки:
    if р['вид'] == 'рука3/4-перелік':
        опис = (р['т'] or {}).get('description', '')
        р['рука'] = next((рк for п, рк in проза.items() if п and опис.strip().startswith(п[:120])), None)
# складання рук 1–2: за числом рядків пулу (рука 2 — інший пул)
скл = [р for р in рядки if р['вид'] in ('складання', 'турнір')]
for р in скл:
    н = len(ряди(р['т']))
    for рк in (1, 2):
        if рк in взято and рк in знято_скл and н == взято[рк] - знято_скл[рк]:
            р['рука'] = рк
for р in скл:
    if р['рука']:
        пули[р['рука']] |= ряди(р['т'])
for р in рядки:
    if р['рука'] is None and р['вид'] in ('складання', 'ремонт', 'вибір', 'опис', 'турнір'):
        rr = ряди(р['т'])
        if not rr and р['вид'] == 'опис':
            # опис: номери речей образу
            пер = (р['т'] or {}).get('outfit', {}).get('items', []) if р['т'] else []
            rr = {(x.get('n'),) for x in пер}
            оц = {рк: len({k[:1] for k in пули[рк]} & rr) for рк in (1, 2)}
        else:
            оц = {рк: len(пули[рк] & rr) - len(rr - пули[рк]) for рк in (1, 2)}
        if оц and max(оц.values()) > 0 and оц[1] != оц[2]:
            р['рука'] = max(оц, key=оц.get)

руки = {}
for р in рядки:
    о = р['о']
    поч = час(о['час']); кін = поч + timedelta(seconds=float(о.get('с') or 0))
    if р['рука']:
        д = руки.setdefault(р['рука'], dict(викликів=0, поч=поч, кін=кін, види=[]))
        д['викликів'] += 1; д['поч'] = min(д['поч'], поч); д['кін'] = max(д['кін'], кін)
        д['види'].append(f"{р['вид']}:{о.get('статус')}:{о.get('с')}с")
старт = min(час(о['час']) for о in обміни) if обміни else None
перший_збір = min((час(р['о']['час']) for р in рядки if р['рука']), default=None)

print('== картки (порядок показу)')
for к in стан['картки']:
    кя = к.get('ядро') or {}
    речі = к.get('речі') or []
    print(f"рука {к['рука']} · збій {к['збій'] or '—'} · позиція {кя.get('позиція')} · образ {кя.get('образ')} = вирок {кя.get('вирок')}: {кя.get('образ') == кя.get('вирок')}")
    print('   речі:', '; '.join(f"{р['слот']}: {(р.get('назва') or '')[:40]}" + (f" · {р['крамниця']} {р['ціна']} ₴" if р.get('крамниця') else '') for р in речі))
    print('   крамниць/цін:', sum(1 for р in речі if р.get('крамниця') or р.get('ціна')), '· ядро склад = речі картки:',
          [р.get('ід') for р in кя.get('речі', [])] == [р.get('id') for р in речі])
print('== поява карток у DOM:', стан.get('поява_карток'))
print('== діагноз:'); [print('  ', str(д)[:400]) for д in стан['діагноз']]
print('== час рук (від першого виклику руки до кінця останнього), с:')
for рк in sorted(руки):
    д = руки[рк]
    print(f"   рука {рк}: {(д['кін'] - перший_збір).total_seconds():.1f} с · викликів {д['викликів']} · {', '.join(д['види'])}")
без = [р for р in рядки if р['рука'] is None and р['вид'] in ('складання', 'ремонт', 'вибір', 'опис', 'турнір', 'рука3/4-перелік')]
print('   без руки:', [(р['і'], р['вид']) for р in без])
for з in звіт:
    if з.get('заява') in ('hand_2_breakage', 'hand_2_breakage_judge', 'tournament', 'pool_parts') or 'збій' in з:
        print('  звіт:', json.dumps(з, ensure_ascii=False)[:700])
print('== моделі:', sorted({m for о in обміни for m in (о.get('modelUsage') or {})}), '· викликів', len(обміни),
      '· статуси', sorted({о.get('статус') for о in обміни}))
json.dump(dict(руки={рк: dict(викликів=д['викликів'], с=(д['кін'] - перший_збір).total_seconds()) for рк, д in руки.items()},
               поява=стан.get('поява_карток'), карток=len(стан['картки'])),
          open(Т / 'підсумок.json', 'w'), ensure_ascii=False, indent=1)
