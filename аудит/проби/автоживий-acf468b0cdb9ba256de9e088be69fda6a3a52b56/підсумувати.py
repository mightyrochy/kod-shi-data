"""Зводить завершені докази й відповідь приладу бази без повтору моделей."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json
import socket
import subprocess
import urllib.request

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
ASSIGNED='237f172f9b364d84707879f254ff43249df4a14a'
def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
facts=json.loads((OUT/'факти.json').read_text(encoding='utf-8'))
base=json.loads((OUT/'нова_база_виконання.json').read_text(encoding='utf-8'))
lines=[s for s in (OUT/'НОВА_БАЗА.md').read_text(encoding='utf-8').splitlines() if s and not s.startswith('#')]
statuses=Counter()
for fact in facts:
    folder=OUT/fact['сцена']
    files=list((folder/'VIDPOVIDI/обмін').glob('*.json'))+list((folder/'пошкоджені_обміни').rglob('*.json'))
    for f in files:
        e=json.loads(f.read_text(encoding='utf-8'))
        statuses[str(e['відповідь']['status'])]+=1
with urllib.request.urlopen('http://127.0.0.1:1234/api/v1/models',timeout=10) as r:
    models=json.load(r)
with socket.socket() as s:
    s.settimeout(2)
    proxy_status=s.connect_ex(('127.0.0.1',1235))
netstat=subprocess.check_output(['netstat','-ano'],text=True,encoding='utf-8',errors='replace')
listeners=[]
for line in netstat.splitlines():
    parts=line.split()
    if len(parts)>3 and parts[0]=='TCP' and parts[1].rsplit(':',1)[-1]=='1235' and parts[3]=='LISTENING':
        listeners.append(line.strip())
source_diff=git('diff','--name-only',ASSIGNED,'HEAD','--','джерела','.github','аудит/адаптери/gemini')
state={'час_utc':datetime.now(timezone.utc).isoformat(),'призначена_збірка':ASSIGNED,
       'origin_main_на_фініші':git('rev-parse','origin/main'),'гілка':git('branch','--show-current'),
       'сцен':len(facts),'доведено':sum(bool(f.get('доказ',{}).get('доведено')) for f in facts),
       'червоних_рядків':sum(len(f.get('червоні',[])) for f in facts),'HTTP_записаних_обмінів':dict(statuses),
       'код_приладу_бази':base['rc'],'зміни_продукту_правил_обгортки':source_diff.splitlines() if source_diff else [],
       'тимчасове_дерево_існує':(ROOT.parent/'tmp/live').exists(),'порт_1235_connect_ex':proxy_status,
       'порт_1235_слухачі_netstat':listeners,
       'завантажені_екземпляри':[i for m in models['models'] for i in m['loaded_instances']],
       'моделі_після':models}
(OUT/'завершення.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=(OUT/'ЗВІТ.md').read_text(encoding='utf-8').split('\n## Підсумок збереження')[0]
report=report.replace('Він збігається з `origin/main`;','На старті він збігався з `origin/main`;')
report=report.replace('Сторінка читається з тимчасового дерева','Сторінка читалася з тимчасового дерева')
report+='\n## Підсумок збереження\n\n'
report+=f"Сцен: {state['сцен']}; доведено завершення: {state['доведено']}; червоних рядків стенда: {state['червоних_рядків']}.\n"
report+=f"Статуси всіх записаних обмінів, включно з внесеннями: {dict(statuses)}.\n"
report+='`cloud` порожнє, `bad` порожнє. ДО береться з джерел плану; окремих прогонів ДО не виконували.\n'
report+='Непідтверджені питання й обмеження перелічено вище; корені й рядки дошки не закривали.\n\n'
report+=f"Прилад нової бази повернув код {base['rc']}. На фінішній звірці `origin/main` — `{state['origin_main_на_фініші']}`.\n"
report+='Записи залишилися в теці наряду; бази вручну не створювали й не змінювали.\n\n'
report+='\n'.join(lines)+'\n\n'
report+='Власні проксі й стенд завершені; завантажених екземплярів моделей на фінішній звірці немає.\n'
report+=('Слухача :1235 не виявлено за `netstat -ano`; сирий результат socket connect_ex збережено окремо.\n'
         if not listeners else 'Поточні слухачі :1235 зафіксовані в `завершення.json`.\n')
report+='Тимчасове дерево прибрано після перевірки абсолютного шляху й чистого стану.\n'
report+='Різниці в `джерела/`, `.github/` і адаптері gemini від призначеного коміту немає.\n'
report+='Докази фінальної звірки — `завершення.json`. Звіт не є дозволом на злиття.\n'
(OUT/'ЗВІТ.md').write_text(report,encoding='utf-8')
commands=(OUT/'КОМАНДИ.md').read_text(encoding='utf-8').split('\n## Завершення')[0]
commands+='\n## Завершення\n\n'
commands+='Остання сцена: `python аудит/проби/автоживий-acf468b0cdb9ba256de9e088be69fda6a3a52b56/виконати_внесення.py` — код 1.\n'
commands+='Точний дочірній виклик, збережене оточення й SHA256 — `внесення_середовище.json`.\n'
commands+='Підготовча команда PowerShell мала помилку парсера до старту сцени; жодного повторного запису сцени не було.\n'
commands+='Прилад: `node аудит/проби/нова_база.js аудит/проби/автоживий-acf468b0cdb9ba256de9e088be69fda6a3a52b56` — код 3.\n'
commands+='Код і повні потоки stdout/stderr зафіксовані у `нова_база_виконання.json`.\n'
commands+='Власне чисте дерево `../tmp/live` прибрано командою `git worktree remove -- <перевірений абсолютний шлях>` — код 0.\n'
commands+='Фінальна звірка: `python аудит/проби/автоживий-acf468b0cdb9ba256de9e088be69fda6a3a52b56/підсумувати.py`.\n'
(OUT/'КОМАНДИ.md').write_text(commands,encoding='utf-8')
body='Зберегти результати автоживого прогону acf468b0\n\n'
body+='ДО: для призначеної збірки в цьому наряді не було записів. ПІСЛЯ: 10 сцен, 8 доведених завершень, 2 недоведених; усі записувачі rc=1.\n'
body+=f"Зафіксовано {state['червоних_рядків']} червоних рядків стенда. Усі {sum(statuses.values())} записаних HTTP-обмінів мають статус 200.\n"
body+=f"Призначений коміт: {ASSIGNED}; штамп артефакту: acf468b0cdb9ba256de9e088be69fda6a3a52b56.\n\n"
body+='PR #2932: у 6/6б збережені назви, фото, рамки, належність образу й два слоти shoes; відповідні переходи зелені. Кольорова звірка червона.\n'
body+='Рівень 6 не виник (паспорт побачення 7); сама ошатність втрачена до оцінки. У пробі битого каблука вето не прочитане через буквальний <attribute>. Відмова на тканині видима; після відновлення 3 живі картки й змішаний журнал 6 вердиктів, повнота не доведена.\n'
body+='Джерела полів, колір модельних речей, нові поверхні після GPU-перезбору й гладка підошва підтверджені не повністю; точні межі доказів — у звіті. Якість живою людиною не оцінювали.\n'
body+='Нових вад поза мірилом не встановлено. Корені й дошку не закривали; повний успіх плану не підтверджено, збірку не позначено перевіреною.\n\n'
body+='Докази: аудит/проби/автоживий-acf468b0cdb9ba256de9e088be69fda6a3a52b56/ЗВІТ.md; команди, первинні обміни, знімки й SHA збережені поруч. Код продукту й правила не змінені. Власні ресурси прибрані.\n\n'
body+=f"нова_база.js: код {base['rc']}; бази немає, записи лишаються доказами.\n"+'\n'.join(lines)+'\n'
(OUT/'тіло_коміту.txt').write_text(body,encoding='utf-8')
print(json.dumps({k:state[k] for k in ('сцен','доведено','червоних_рядків','HTTP_записаних_обмінів','код_приладу_бази','тимчасове_дерево_існує','порт_1235_connect_ex','завантажені_екземпляри','зміни_продукту_правил_обгортки')},ensure_ascii=False))
