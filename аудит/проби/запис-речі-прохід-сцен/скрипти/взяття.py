"""Мірило (б): взяття на рядок-запит серед «переписаних» (колір у пулі невідомий: hex порожній) і решти рядків запиту, що мають ід у мапі (`мапа_ід.py`). Запуск з кореня: python3 -I <файл> <сцена/прохід/рядок> <тека відповідей ДО> <тека ПІСЛЯ>"""
import sys,json,glob,csv,gzip,collections
sys.path.insert(0,'.')
from pathlib import Path
К=Path('/home/user/kod-shi-data')
import importlib.util
сп=importlib.util.spec_from_file_location("п",К/"аудит/звіти/крамниці-рівна-черга/вимір.py"); П=importlib.util.module_from_spec(сп); sys.modules['п']=П; сп.loader.exec_module(П)
def взяття(тека):
    c=collections.Counter(); k=0
    for ф in sorted(Path(тека).glob('*.json')):
        o=json.loads(ф.read_text(encoding='utf-8'))
        try:
            в=П.розібрати_json(o['відповідь']); ns={П.номер(x) for ou in в['outfits'] for x in ou['items']}-{None}
        except Exception: continue
        k+=1
        for n in ns: c[n]+=1
    return c,k
запит=sys.argv[1]; до=sys.argv[2]; після=sys.argv[3]
записи={к.split('@')[0] for к in json.load(gzip.open(К/'аудит/проби/запис-речі-прохід-сцен/дані/записи_речі.json.gz','rt',encoding='utf-8'))}
мп=json.load(gzip.open(К/'аудит/проби/запис-речі-прохід-сцен/дані/мапа_ід.json.gz','rt',encoding='utf-8'))[запит]
рядки=[{'n':n,'ід':v[0]} for n,v in мп.items() if v[0]]
сц,пр,л=запит.split('/')
обмін=П.рядки(f"{П.МІСТ}/{сц}/обміни.jsonl")[int(л)-1]
пак=П.розібрати_json(П.текст_запиту(json.loads(обмін['запит'])))
cols=пак['pool']['cols']; ih=cols.index('hex')
пер={r[0] for r in пак['pool']['rows'] if r[ih] is None}
for назва,т in (('ДО',до),('ПІСЛЯ',після)):
    c,k=взяття(К/т)
    for гр,множ in (('переписані',[r['n'] for r in рядки if r['n'] in пер]),('решта',[r['n'] for r in рядки if r['n'] not in пер])):
        print(назва,k,гр,len(множ), round(100*sum(c[n] for n in множ)/(len(множ)*k),2))
