from pathlib import Path
import sys, os, ast, subprocess, copy, itertools, json
import runpy, io, contextlib

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root/'джерела'))
os.chdir(root/'джерела')
import мовний_шар as М, паспорт_нагоди as П, сценарій as С
base='5fc912a01fe93e5c180422131ce6a6798c2b3c27'
head='05a5a814ab1575100689d5c6392c05c71b04eda2'

def function(ref, path, name, namespace):
    source=subprocess.check_output(['git','show',ref+':'+path],cwd=root).decode('utf-8')
    tree=ast.parse(source)
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    scope=dict(namespace)
    exec(compile(ast.Module(body=[node],type_ignores=[]),ref+':'+path,'exec'),scope)
    return scope[name]

old_typical=function(base,'джерела/паспорт_нагоди.py','_типова_нагода',vars(П))
new_typical=function(head,'джерела/паспорт_нагоди.py','_типова_нагода',vars(П))
old_layer=function(base,'джерела/мовний_шар.py','паспорт_з_шару',vars(М))
new_layer=function(head,'джерела/мовний_шар.py','паспорт_з_шару',vars(М))
assert С.ВИЗНАЧАЛЬНІ == ('нагода','місце','дрес_код','ошатність')
count=0
for values in itertools.product([None,'','невідомо',[],{},0,'значення'],repeat=4):
    for event in ({},{'перекладено_шаром':True,'подія':'концерт'},{'перекладено_шаром':False,'подія':'концерт'}):
        p=dict(zip(С.ВИЗНАЧАЛЬНІ,values),**event)
        assert old_typical(copy.deepcopy(p)) == new_typical(copy.deepcopy(p)),p
        count+=1
print('Типова нагода: порівнянь %d, розбіжностей 0'%count)

count=0
photo={'ід':'ф1','фото':'ф1','назва':'спідниця','слот':'низ','колір':'хакі','ошатність':6,'чия':'моя','закріплена':True}
seen=[]
for event,formality,previous,scenario,photos in itertools.product(
    [None,{'free_text':'похід на концерт','lang':'uk'}],
    [None,{'from':4,'to':6},{'from':0,'to':0}],
    [{},{'ошатність':[4,6]},{'нагода':'щоденне'},{'місце':'театр'}],
    [{},{'ошатність':[4,6]},{'нагода':'щоденне'},{'місце':'театр'}],
    [None,[photo]]):
    internal={}
    if event is not None: internal['event']=event
    if formality is not None: internal['formality']=formality
    kwargs=dict(паспорт_досі=previous,речі_з_фото=photos,слова_ходу='Збери образ під цю спідницю для походу на концерт')
    try:
        П._типова_нагода=old_typical
        before=old_layer(copy.deepcopy(internal),copy.deepcopy(scenario),**copy.deepcopy(kwargs))
        П._типова_нагода=new_typical
        after=new_layer(copy.deepcopy(internal),copy.deepcopy(scenario),**copy.deepcopy(kwargs))
    finally:
        П._типова_нагода=new_typical
    assert before==after,(internal,scenario,previous,before,after)
    count+=1
    if event and not previous and not scenario and photos and formality is None:
        seen.append(dict(паспорт=after['паспорт'],обовязкове=after['обовʼязкове']))
print('Мовний шар: порівнянь %d, розбіжностей 0'%count)
print('Концерт із фото без смуги: '+json.dumps(seen,ensure_ascii=False))

for name in ['шлях_шар_невідомо.py','шлях_шар_сторож.py']:
    outputs=[]
    for layer,typical in [(old_layer,old_typical),(new_layer,new_typical)]:
        М.паспорт_з_шару=layer
        П._типова_нагода=typical
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            runpy.run_path(str(root/'джерела'/'проби'/name))
        outputs.append(output.getvalue())
    assert outputs[0]==outputs[1],name
    print('Діагностика %s: вивід голови тотожний базі; %s'%(name,outputs[1].splitlines()[-1]))

# Стара діагностика невідомого шукає також службове none, хоча називає лічбу «невідомо».
path=root/'джерела'/'проби'/'шлях_шар_невідомо.py'
source=path.read_text(encoding='utf-8').replace('у_рядку += 1',
    "у_рядку += 1\n        print('Збіг діагностики:', [рядки[max(0, м.start()-35):м.end()+35] for м in НЕВІД.finditer(рядки)])")
exec(compile(source,str(path),'exec'),{'__file__':str(path)})

outputs=[]
for layer,typical in [(old_layer,old_typical),(new_layer,new_typical)]:
    М.паспорт_з_шару=layer
    П._типова_нагода=typical
    output=io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            runpy.run_path(str(root/'джерела'/'проби'/'io_K-IO-04_bez_foto.py'))
    except AssertionError:
        status='AssertionError'
    else:
        status='успіх'
    outputs.append((status,output.getvalue()))
assert outputs[0]==outputs[1]
assert outputs[1][0]=='AssertionError'
print('Проба io_K-IO-04_bez_foto.py: AssertionError на базі й голові; вивід тотожний')
