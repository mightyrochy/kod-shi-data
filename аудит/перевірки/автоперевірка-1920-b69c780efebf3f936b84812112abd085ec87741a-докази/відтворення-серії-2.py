import json
from pathlib import Path
import re
import subprocess
import sys
import types

ROOT = Path(sys.argv[2]).resolve()
OUT = Path(sys.argv[3]).resolve()
SOURCE = '3f02007953d0ce29071188185c8d1302bfef7a6c'
sys.path.insert(0, str(ROOT / 'джерела'))
if sys.argv[1] == 'base':
    text = subprocess.check_output(['git', 'show', 'ee22ba1723a2762b2053709c7570ca11b13c6186:джерела/мовний_шар.py'], cwd=ROOT).decode('utf-8')
    module = types.ModuleType('мовний_шар')
    module.__file__ = str(ROOT / 'джерела/мовний_шар.py')
    sys.modules[module.__name__] = module
    exec(compile(text, module.__file__, 'exec'), module.__dict__)
import мовний_шар as М
import паспорт_нагоди as П
import сценарій as С
import пакет_моделі as ПМ
import дріт_моделі as Д
from міст_відповіді import _випадок_кодами

files = subprocess.check_output(['git', '-c', 'core.quotepath=false', 'ls-tree', '-r', '--name-only', SOURCE, 'аудит/проби/б1/ДО-2710'], cwd=ROOT).decode('utf-8').splitlines()
rows = []
for file in files:
    if not file.endswith('seed3_01_мовний_шар_хід_розмови.txt'):
        continue
    text = subprocess.check_output(['git', 'show', SOURCE + ':' + file], cwd=ROOT).decode('utf-8')
    record = re.fullmatch(r'── ПРОМПТ \(\d+ симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \([^\n]*\) ──\n(.*)\n', text, re.S)
    source = json.JSONDecoder().raw_decode(record[1])[0]
    parsed = М.прийняти_розмову(record[2])
    passport = М.паспорт_з_шару(parsed['внутрішня'], {}, слова_ходу=source['her_new_message'], частини=parsed['частини'], не_взято=parsed['не_взято'])['паспорт']
    scene, _ = П.з_показу({}, passport)
    case = ПМ.випадок_для_пакета(passport, '', scene)
    day = С.день_кодами(scene)
    wire = Д.випадок(case, day)
    judge = _випадок_кодами({'пакет': {'випадок': case}}, {'day': Д.день_на_дріт(day)})
    rows.append(dict(сцена=Path(file).parent.parent.name, запит=source['her_new_message'],
                     подія=passport.get('подія'), складання=wire.get('event'), ремонт=judge.get('event'),
                     вхідний_намір=parsed['внутрішня'].get('intent'), намір=wire.get('intent'), намір_суду=judge.get('intent'),
                     незнайомі=parsed['незнайомі']))
mode = sys.argv[1]
(OUT / ('серія2-' + mode + '.json')).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(dict(версія=mode, записів=len(rows),
                      опис={key:sum(bool(row[key]) for row in rows) for key in ('подія','складання','ремонт')},
                      намір_є=sum(bool(row['намір']) for row in rows),
                      намір_збережено=sum(row['вхідний_намір'] == row['намір'] == row['намір_суду'] for row in rows),
                      без_опису=[row['сцена'] for row in rows if not row['складання']],
                      наміри=[(row['сцена'],row['вхідний_намір'],row['намір'],row['намір_суду']) for row in rows]), ensure_ascii=False, indent=2))
