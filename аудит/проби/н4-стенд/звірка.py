# Звірка сцени стенда Н4: Ч1, запит руки 1 (день), запит палітри (день), картка ядра
import json, sys
т = sys.argv[1]
L = [json.loads(l) for l in open(т + '/обміни.jsonl', encoding='utf8')]
ч1 = [д for д in L if д['запит'] and д['запит'].startswith('{"task":{"role":"You read a woman')]
for і, д in enumerate(ч1): print('Ч1', і + 1, (д['відповідь'] or '')[:700].replace('\n', ' '))
рука = [д for д in L if д['запит'] and '"You are the Lyusterko stylist. Build' in д['запит'][:200]]
if рука:
    з = json.loads(рука[0]['запит']); day = None
    def знайти(о):
        global day
        if isinstance(о, dict):
            if 'stages' in о and 'unknown' in о: day = о; return
            for в in о.values(): знайти(в)
        elif isinstance(о, list):
            for в in о: знайти(в)
    знайти(з)
    print('РУКА day:', json.dumps(day, ensure_ascii=False)[:1500])
    к = [в for в in (з.get('case') or {}, ) ]
    def кейс(о):
        if isinstance(о, dict):
            if 'intent' in о and 'refusals' in о: return о
            for в in о.values():
                р = кейс(в)
                if р: return р
        if isinstance(о, list):
            for в in о:
                р = кейс(в)
                if р: return р
    print('РУКА case:', json.dumps(кейс(з), ensure_ascii=False)[:900])
пал = [д for д in L if д['тип'].startswith('вибір палітри')]
if пал:
    з = json.loads(пал[0]['запит']); print('ПАЛІТРА day:', json.dumps(з.get('day'), ensure_ascii=False)[:600])
try:
    к = json.load(open(т + '/знімки/n4_kartka_stsenariiu.json'))
    с = к.get('ситуація') or {}
    print('ЕТАПИ:', json.dumps((с.get('сказала') or {}).get('етапи'), ensure_ascii=False)[:600])
    print('НЕ ЗАПИСАНО:', (к.get('картка') or {}).get('не_записано'))
except Exception as е: print('картки нема', е)
