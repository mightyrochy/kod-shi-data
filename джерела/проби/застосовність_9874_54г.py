# -*- coding: utf-8 -*-
# 5.4-Г застосовність 9874/9875: хто з речей дав вигадане neckline і чи вони серед речей з item_type unknown (код, (б), еталон).
#   python3 проби/застосовність_9874_54г.py <тека>/розбір.json
import json, os, sys, runpy, io, contextlib
ТУТ = os.path.dirname(os.path.abspath(__file__))
шлях = sys.argv[1]
розбір = json.load(open(шлях, encoding='utf-8'))
sys.argv = ['x', шлях, '--код-або-б']
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(ТУТ, 'еталон_частки.py'))
Е = g['Е']
def рядок(р):
    к = розбір.get(р['id']) or {}
    б = р['джерела']['б']
    return '%s | код: slot=%s type=%s neckline=%s | (б): slot=%s type=%s neckline=%s | еталон: slot=%s type=%s neckline=%s' % (
        р['id'], к.get('slot'), к.get('item_type'), к.get('neckline'), б.get('slot'), б.get('item_type'), б.get('neckline'),
        р['правда']['slot'], р['правда']['item_type'], р['правда']['neckline'])
v = [р for р in Е['речі'] if (р.get('вердикти') or {}).get('нове', {}).get('neckline') == 'вигадано']
u = [р for р in Е['речі'] if р['id'] in розбір and (розбір[р['id']].get('item_type') in ('unknown', None))]
print('вигаданих neckline:', len(v))
for р in v: print('  ', рядок(р))
print('речей з item_type unknown у кодах:', len(u))
for р in u: print('  ', рядок(р), '| neckline-вердикт:', (р.get('вердикти') or {}).get('нове', {}).get('neckline'))
print('вигадані neckline серед unknown-типу:', len({р['id'] for р in v} & {р['id'] for р in u}), 'з', len(v))
