"""Виконати синтаксис, проби AST і офлайн-проби розбору та вибору одним прогоном."""
import json, os, py_compile, subprocess, sys, time
from pathlib import Path

корінь = Path(__file__).resolve().parents[3]
джерела = корінь / 'джерела'
звіти = Path(__file__).resolve().parent
os.chdir(джерела)
результат = []
середовище = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', NODE_PATH=str(джерела / 'node_modules'))
середовище.pop('MODEL', None)
файли = [ф for ф in джерела.rglob('*') if 'node_modules' not in ф.parts]
помилки = []
for ф in файли:
    try:
        if ф.suffix == '.py':
            py_compile.compile(str(ф), doraise=True)
        elif ф.suffix == '.js':
            subprocess.run(['node', '--check', str(ф)], check=True, capture_output=True)
    except Exception as х:
        помилки.append(f'{ф}: {х}')
результат.append(dict(назва='синтаксис', python=sum(ф.suffix == '.py' for ф in файли), js=sum(ф.suffix == '.js' for ф in файли), помилки=помилки, код=int(bool(помилки))))
проби = sorted((джерела / 'проби').glob('поділ_*_ast.py'))
проби += sorted((джерела / 'проби').glob('вибір_*.py')) + sorted((джерела / 'проби').glob('свідомі_*.py'))
проби += [джерела / 'проби' / ім for ім in ('ремонт_понад_просили.py', 'стійкий_розбір_208.py', 'шлях_виклики_свідомі_поза_образом.py')]
for проба in проби:
    початок = time.monotonic()
    with (звіти / (проба.stem + '.log')).open('w', encoding='utf-8') as лог:
        код = subprocess.run([sys.executable, str(проба)], env=середовище, stdout=лог, stderr=subprocess.STDOUT).returncode
    результат.append(dict(назва=проба.name, код=код, секунд=round(time.monotonic()-початок, 2)))
    print(проба.name, код, flush=True)
    (звіти / 'батарея.json').write_text(json.dumps(результат, ensure_ascii=False, indent=2), encoding='utf-8')
sys.exit(any(р['код'] for р in результат))
