import os, sys, pathlib, json
src=pathlib.Path(sys.argv[1]).resolve(); sys.path.insert(0,str(src)); os.chdir(src)
import bridge as B, pipeline as P, feed as F
input_data=json.load(open('стенд_вх.json',encoding='utf-8'))
input_data.update(каталог=F.каталог_на_диску('каталог_brief.xml'), сід=3)
call=lambda name,data:json.loads(B.виклик(name,json.dumps(data,ensure_ascii=False)))
pack=call('запити',input_data)['пакети']['1']['пул']
items=[pack[s][0]['н'] for s in ('верх','низ','взуття','сумка','шарф','верхній_шар')]+[pack['взуття'][1]['н']]
outfit=dict(ід='о1',речі=items,структура=dict(ок=False,блокери=[dict(код='слот_двічі',речі=[items[2],items[-1]],суть='слот_двічі:взуття')]))
seen=[]; full_judge=P.перевірити_від_моделі
def judge(ids,*args,**kwargs):
    result=full_judge(ids,*args,**kwargs)
    seen.append(dict(ід=list(ids),знахідок=len(result.get('знахідки') or [])))
    return result
P.перевірити_від_моделі=judge
try:
    result=call('від_моделі',dict(input_data,ітерація=2,відповідь='ВИБІР_V1',вибір_над=dict(образи=[outfit]),текст_моделі=json.dumps(dict(версія='1',обрано='о1',прибрати=[items[-1]]),ensure_ascii=False)))
finally:P.перевірити_від_моделі=full_judge
assert 'помилка' not in result,result
choice=result['вибір']; assert len(choice['ід'])==6 and len(choice['прибрано'])==1,choice
assert any(s['ід']==choice['ід'] and s['знахідок']>0 for s in seen),seen
assert {i['id'] for i in result['речі']}==set(choice['ід']),result['речі']
print(json.dumps(dict(до_номерів=items,прибрано=choice['прибрано'],після_ід=choice['ід'],повний_суд=seen,знахідок=len(result.get('знахідки') or [])),ensure_ascii=False,indent=2))
result['каталог_картки']=[i for i in B.каталог_останнього_пакета() if i['id'] in choice['ід']]
pathlib.Path(sys.argv[2]).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
