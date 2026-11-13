"""Витягає факти з завершених записів; не підміняє їх оцінкою людини."""
import json
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
rows = json.loads((OUT / 'зведення.json').read_text(encoding='utf-8'))
facts = {}

def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

for row in rows:
    folder = ROOT / row['тека']
    log = (folder / 'лог.txt').read_text(encoding='utf-8') if (folder / 'лог.txt').exists() else ''
    item = {'rc': row['rc'], 'запис_завершено': row['запис_завершено'], 'тека': row['тека']}
    item['паспорт_у_лозі'] = [line.strip() for line in log.splitlines() if line.startswith('   ВИМІРИ:') or line.startswith('KARTKA')]
    if (folder / 'знімки/доказ.json').exists():
        proof = json.loads((folder / 'знімки/доказ.json').read_text(encoding='utf-8'))
        item['доказ'] = {key: proof.get(key) for key in ('факт', 'подія', 'вердикт')}
    if (folder / 'вердикти.txt').exists():
        try:
            export = json.loads((folder / 'вердикти.txt').read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            export = {}
        shared = export.get('спільне', {})
        passport = shared.get('паспорт', {})
        item['паспорт'] = {key: passport.get(key) for key in ('нагода', 'пора', 'ошатність', 'смуга_погоди', 'опади', 'мета_зони', 'вето', 'виміри')}
        item['схема_обрана'] = shared.get('пал_схема_обрана')
        courts = []
        for run in export.get('прогони', []):
            for verdict in run.get('вердикти', []):
                if str(verdict.get('рука')) in ('1', '2'):
                    courts.append({'рука': verdict.get('рука'), 'склад': verdict.get('склад'),
                                   'суд': verdict.get('етапи', {}).get('суд')})
        target_codes = ('K-FIT-04', 'R-CHEV-08', 'K-COL-03', 'K-PAL-03', 'K-PAL-18', 'K-COL-06-T', 'R-CHEV-14')
        item['знахідки_кодів'] = {code: [d for d in walk(courts) if code in [v for v in d.values() if isinstance(v, str)]] for code in target_codes}
        item['rise_below_waist_for_taller_goal_у_експорті'] = 'rise_below_waist_for_taller_goal' in json.dumps(export, ensure_ascii=False)
    facts[row['сцена']] = item
(OUT / 'факти_питань.json').write_text(json.dumps(facts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for name in ('ж3_театр_тріада', 'ж4_клуб_приховати', 'ж7_мороз_без_відкритого', 'ж1_весілля_вечір'):
    f = facts[name]
    print(name, json.dumps({k: v for k, v in f.items() if k in ('паспорт', 'схема_обрана', 'rise_below_waist_for_taller_goal_у_експорті')}, ensure_ascii=False))
    for code, matches in f.get('знахідки_кодів', {}).items():
        if matches:
            print(code, len(matches), json.dumps(matches[0], ensure_ascii=False)[:2000])
