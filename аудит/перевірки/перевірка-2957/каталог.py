"""Промпт ДО/ПІСЛЯ на повному каталозі; дані моста для мобільного диму."""
import json, os, pathlib, subprocess, sys, types
repo,src,out=map(pathlib.Path,sys.argv[1:4]);os.chdir(src);sys.path.insert(0,str(src))
import bridge as B, вибір_палітри as В, збирач_промптів as З, feed as Ф
woman=json.loads((src.parent/'аудит/проби/жінки/ж4.json').read_text(encoding='utf-8'))
measures=dict(woman['мірки']);height=measures.pop('зріст')
inp=dict(зріст=height,обхвати=measures,шкіра=woman['skin'],волосся=woman['hair'],очі=woman['eyes'],
         каталог=Ф.каталог_на_диску('каталог_повний.xml'),
         паспорт=dict(нагода='робота',місце='офіс_корпоративний',дрес_код='business_casual'))
до=types.ModuleType('палітра_до')
text=subprocess.check_output(['git','-C',str(repo),'show',
 'ac752f5c626c91162bb985a498f206f6a19a371c:джерела/вибір_палітри.py'],encoding='utf-8')
exec(compile(text,'база','exec'),до.__dict__)
prompts=[json.loads(m.вибір_палітри(inp))['промпт'] for m in (до,В)]
p=В.перелік(inp);data=В.дані_промпта(p)
answer=json.dumps(dict(scheme=p['схеми'][0]['код'],base=data['bases'][0]['id'],saturation='medium',
                       scheme_reasons=['why_first_advice'],base_reasons=['why_first_advice']))
choices=[m.прийняти(inp,answer) for m in (до,В)]
assert choices[0]==choices[1]
assert len(prompts[0])-len(prompts[1])==33
palette=json.loads(B.виклик('палітри',json.dumps(inp,ensure_ascii=False)))
(out/'палітра-дані.json').write_text(json.dumps(dict(вхід=inp,палітра=palette,вибір=choices[1]),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(каталог=inp['каталог'],довжини=list(map(len,prompts)),читач_однаковий=True,
 причини=choices[1]['вибір']['причини'],схем=len(data['schemes']),основ=len(data['bases']),
 основ_з_лічбою_одягу=sum('clothing' in x for x in data['bases'])),ensure_ascii=False,indent=2))
