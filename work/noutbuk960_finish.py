from pathlib import Path
import json, hashlib, subprocess, platform
root = Path(__file__).resolve().parents[1]
p = root / 'аудит/МЕНЕДЖЕР.md'
s = p.read_text(encoding='utf-8')
old = '- Злиття, рішення власника й живі прогони на ноутбуці — за Claude. Якщо потрібен живий прогін, у тілі PR — `ЖИВИЙ ПІСЛЯ: <сцена> — <питання>`; ноутбук — після 15.10. ChatGPT живих моделей не запускає.'
new = '- Злиття й рішення власника — за Claude. Живі прогони й роботу на ноутбуці веде сесія ChatGPT на ноутбуці; ноутбук вмикає власник (п.18). Якщо потрібен живий прогін, у тілі PR — `ЖИВИЙ ПІСЛЯ: <сцена> — <питання>`; таблицю сцен готує координатор, звіти — коментарем у #963.'
assert s.count(old) == 1
p.write_text(s.replace(old, new), encoding='utf-8')
p = root / 'аудит/РІШЕННЯ_ВЛАСНИКА.md'
s = p.read_text(encoding='utf-8').replace('## п.7 — ручна правка надиктованого тексту всюди (13.10.2026)\n\n\n', '## п.7 — ручна правка надиктованого тексту всюди (13.10.2026)\n\n')
s += '\n## п.18 — живі прогони ChatGPT на ноутбуці (13.10.2026)\n\n- **13.10.2026 ~16:45 UTC:** «Якщо потрібен ноутбук, я можу включити. Chatgpt теж має можливість працювати з ноутбуком.»\n- Джерело — [issue #960, коментар 6150404798](https://github.com/mightyrochy/kod-shi-data/issues/960#issuecomment-6150404798).\n→ Живі прогони й роботу на ноутбуці веде сесія ChatGPT на ноутбуці; ноутбук вмикає власник (п.18). Очікування 15.10 скасовано. Таблицю сцен готує координатор ChatGPT; звіти — коментарем у #963.\n'
p.write_text(s, encoding='utf-8')
p = root / 'аудит/БЕКЛОГ.md'
lines = p.read_text(encoding='utf-8').splitlines(keepends=True)
notes = {'5026': ' Ноутбук #960/6150404798: 8 додаткових кадрів (7 ATR, 1 SAM), 32,47 с; дані й фото `аудит/ноутбук_960/ж-03995.json`. Власний тон прозорої тканини не доведено; окрема Astra ще потрібна.', '4451': ' Ноутбук #960/6150404798: сторінка ricamare доступна, 3 URL/2 різні кадри, ATR; `аудит/ноутбук_960/ж-01706.json` і `ricamare_page.html`. Є сливовий і зелений кадри; два розміри зеленого не є двома незалежними свідками. Окрема Astra ще потрібна.'}
for i, line in enumerate(lines):
    key = line.split('|')[1].strip() if line.startswith('|') else ''
    if key in notes:
        lines[i] = line.rstrip('\r\n').rstrip().removesuffix('|').rstrip() + notes[key] + ' |\n'
p.write_text(''.join(lines), encoding='utf-8')
out = root / 'аудит/ноутбук_960'
meta = dict(code_sha=subprocess.check_output(['git','rev-parse','HEAD'], cwd=root, text=True).strip(), host=platform.node(), date='2026-10-13', assignment='https://github.com/mightyrochy/kod-shi-data/issues/960#issuecomment-6150404798', lm_models_loaded=0, product_update=False, independent_acceptance=False)
meta['files_sha256'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}
meta['pending'] = ['5190: #991 contains plan only; runnable schema/prompt/validator absent', 'Live AFTER: scene table supplied by coordinator pending', '3459(b): palette explanation requires scene-table run', '5026/4451: separate Astra visual acceptance pending']
(out/'мета.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
