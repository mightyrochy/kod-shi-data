"""Незалежна проба PR #4214: повний каталог та два шляхи картки без викликів моделей.

python перевірити.py <дерево> <XML каталогу> <вихід.json>
"""
import json
import os
from pathlib import Path
import sys

tree, catalogue, output = map(lambda x: Path(x).resolve(), sys.argv[1:])
sys.path.insert(0, str(tree / 'джерела'))
os.chdir(tree / 'джерела')
import аксесуари_носіння as wear
import аксесуари_суд as accessory
import міст_відповіді as bridge
import оцінка_образу as evaluation
import фід_розбір as feed
import фід_слот as slots
import фід_взуття as shoes
import colorspace

codes = {'wear_cost_no_duration', 'wear_cost_no_duration_surface'}
offers = list(feed.офери_фіду(str(catalogue)))
pairs = [dict(o, слот='взуття', **shoes.взуттєві_атрибути(o))
         for o in offers if slots.слоти(o)['слот'] == 'взуття']
selected = next(p for p in pairs if 6 <= (p.get('каблук_см') or 0) <= 8 and p.get('фото'))
counts = dict(оферів=len(offers), пар=len(pairs), питань=0, жінці=0, з_часом_питань=0)
for pair in pairs:
    for surface in (None, 'бруківка'):
        findings = wear.вартість_носіння([pair], поверхня=surface)
        for finding in findings:
            if finding.get('правило') != 'K-END-01':
                continue
            counts['питань'] += 1
            message = bridge._питання_кодами(finding)
            counts['жінці'] += bool(message and not bridge._для_всіх(message)
                and any(s.get('code') in codes and s.get('recipient') not in ('journal', 'stylist')
                        for s in message.get('statements', [])))
    counts['з_часом_питань'] += sum(f.get('правило') == 'K-END-01'
        for f in wear.вартість_носіння([pair], дорога_пішки_хв=20, опади='сніг'))

base = json.loads(Path('стенд_вх.json').read_text(encoding='utf-8'))
items = [dict(ід='ф1', фото='ф1', назва=selected['назва'], слот='взуття', колір='чорний',
              ошатність=6, в_образі=True,
              вимір=dict(lab=list(colorspace.hx('#222222')), hex='#222222', слово='чорний'))]
for identifier, name, slot, colour, hex_value in (
        ('ф2', 'жакет', 'верхній_шар', 'хакі', '#7d7f63'),
        ('ф3', 'міні-спідниця', 'низ', 'бордовий', '#6b1f2a')):
    items.append(dict(ід=identifier, фото=identifier, назва=name, слот=slot, колір=colour,
                      ошатність=6, в_образі=True,
                      вимір=dict(lab=list(colorspace.hx(hex_value)), hex=hex_value, слово=colour)))
scenes = [('без часу', {}), ('бруківка', {'поверхня': 'бруківка'}),
          ('сніг', {'опади': 'сніг'}), ('20 хв', {'дорога_пішки_хв': 20}),
          ('8 год', {'тривалість_год': 8}), ('нуль', {'тривалість_год': 0}),
          ('від’ємний', {'дорога_пішки_хв': -1}), ('рядок', {'дорога_пішки_хв': '20'})]
results = []
for name, scene in scenes:
    judged = evaluation.суд(dict(base, речі=items, сценарій_оцінки=scene, крамниця=False))
    card = evaluation.прийняти_оцінку(json.dumps({'answer': 'Ок.', 'verdict': 'wear_as_is'}), judged)['картка']
    unknown = evaluation.невідоме_для_моделі(judged)
    prompt = evaluation.промпт_оцінки(judged)
    findings = wear.вартість_носіння([selected], **scene)
    questions = bridge._лише_її(bridge._пункти_картки([
        dict(правило=f['правило'], повідомлення=bridge._питання_кодами(f),
             для_всіх=bridge._для_всіх(bridge._питання_кодами(f)))
        for f in findings if f.get('правило') == 'K-END-01']))
    card_codes = [v for p in card['не_знаю'] for v in p.get('входи', []) if v in codes]
    model_codes = [c for p in unknown for c in p.get('statements', []) if c in codes]
    result = dict(сцена=name, картка_оцінки=card_codes, модель=model_codes,
                  визначення_у_промпті=all(c in prompt for c in card_codes),
                  окремих_duration_h=sum('duration_h' in p.get('входи', []) for p in card['не_знаю']),
                  A9=[p.get('why') for p in judged.get('без_входу', [])
                      if p.get('point') == 'refusal_reason_physical'],
                  питання=questions, картка=card)
    results.append(result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('питання', 'картка')}, ensure_ascii=False))

output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(dict(лічба=counts, пара=selected, сцени=results),
                            ensure_ascii=False, indent=2, default=str), encoding='utf-8')
print(json.dumps(counts, ensure_ascii=False))
