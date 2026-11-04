"""Зводить факти записів; не оцінює доречність образів і не змінює бази."""
from collections import Counter
from pathlib import Path
import json

OUT = Path(__file__).resolve().parent
PLAN = json.loads((OUT/'план.json').read_text(encoding='utf-8'))

def walk(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value,list):
        for child in value:
            yield from walk(child)

facts=[]
for scene, questions in PLAN['scenes'].items():
    folder=OUT/scene
    fact={'сцена':scene,'PR':[q['pr'] for q in questions],'стан':'не записано'}
    if (folder/'результат.json').exists():
        result=json.loads((folder/'результат.json').read_text(encoding='utf-8'))
        fact.update(стан='запис завершено',rc=result.get('rc'),секунд=result.get('секунд'),sha=result.get('sha'))
        log=(folder/'лог.txt').read_text(encoding='utf-8')
        fact['червоні']=[s.strip() for s in log.splitlines() if '✗' in s]
        if (folder/'знімки/доказ.json').exists():
            proof=json.loads((folder/'знімки/доказ.json').read_text(encoding='utf-8'))
            fact['доказ']=proof.get('вердикт')
            fact['факт']=proof.get('факт')
        if (folder/'вердикти.txt').exists():
            report=json.loads((folder/'вердикти.txt').read_text(encoding='utf-8'))
            passport=report.get('спільне',{}).get('паспорт',{})
            fact['паспорт']={k:passport.get(k) for k in ('подія','нагода','місце','дрес_код','ошатність','рух','пора','темп_c','джерело_полів','картка_запиту')}
            runs=report.get('прогони',[])
            verdicts=[v for run in runs for v in run.get('вердикти',[])]
            fact['руки']=[{'рука':v.get('рука'),'склад':v.get('склад'),'питань':len(v.get('питання_поля',[]))} for v in verdicts]
            rules=Counter()
            for record in walk(verdicts):
                rule=record.get('правило')
                if rule in ('K-KOH-08','K-KOH-07','K-SHO-03','K-WEA-06'):
                    small={k:record[k] for k in ('правило','ярлик','де','значення','сила','напрям','severity','суть') if k in record}
                    if 'суть' in small: small['суть']=str(small['суть'])[:240]
                    rules[json.dumps(small,ensure_ascii=False,sort_keys=True)]+=1
            fact['записи_правил']=[dict(json.loads(k),повторень=n) for k,n in rules.items()]
    facts.append(fact)
(OUT/'факти.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for fact in facts:
    print(fact['сцена'],fact['стан'],'rc='+str(fact.get('rc')),'червоних='+str(len(fact.get('червоні',[]))))
