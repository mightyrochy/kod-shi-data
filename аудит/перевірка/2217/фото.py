import json,sys,re,importlib.util
сп=importlib.util.spec_from_file_location("ж",sys.argv[1]); Ж=importlib.util.module_from_spec(сп); сп.loader.exec_module(Ж)
р=json.load(open('/tmp/пс2/рез.json')); стор=0; нові_всього=0
for x in р:
    if 'фото' not in x['зм']: continue
    a,b=x['зм']['фото']; a=a or []
    нові=[s for s in b if s not in a and not Ж._НЕ_ФОТО.search(s)]
    if нові: стор+=1; нові_всього+=len(нові); print(x['n'],x['h'],len(нові),нові[:2])
print('сторінок з новими фото після фільтра _НЕ_ФОТО:',стор,'нових фото:',нові_всього)
