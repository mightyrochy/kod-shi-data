"""Точний повтор на записаних входах: python повтор_палітри.py <репо> <джерела голови>."""
import json, os, pathlib, re, subprocess, sys, types
repo, src = map(pathlib.Path, sys.argv[1:3]); os.chdir(src); sys.path.insert(0, str(src))
import вибір_палітри as після, збирач_промптів as З
head = '6028f963a49c8a9d2c274385fb85699652b393e4'
base = 'ac752f5c626c91162bb985a498f206f6a19a371c'
def git(*args):
    return subprocess.check_output(['git','-C',str(repo),'-c','core.quotepath=false',*args],encoding='utf-8')
до = types.ModuleType('палітра_до')
exec(compile(git('show',base+':джерела/вибір_палітри.py'),'база','exec'),до.__dict__)
files = [f for f in git('ls-tree','-r','--name-only',head,'аудит/проби/б1/ДО-2610').splitlines()
         if '_вибір_палітри_' in f and ('/ж1_робота/' in f or '/ж2_побачення_вечір/' in f)]
results = []
for f in files:
    raw = git('show',head+':'+f).replace('\r\n','\n')
    prompt, response = raw.split('\n\n── ВІДПОВІДЬ',1)
    response = response.split('──\n',1)[1]
    obj, _ = json.JSONDecoder().raw_decode(prompt[prompt.index('{"task"'):])
    data = {k:v for k,v in obj.items() if k!='task'}
    prompts = [json.dumps(З.зібрати(m.ВИБІР,data),ensure_ascii=False) for m in (до,після)]
    who = re.search(r'/ж(\d+)_',f).group(1)
    woman = json.loads((src.parent/f'аудит/проби/жінки/ж{who}.json').read_text(encoding='utf-8'))
    measures = dict(woman.get('мірки') or dict(зріст=168,плечі=98,груди=92,талія=74,стегна=99)); height = measures.pop('зріст')
    inp = dict(зріст=height,обхвати=measures,шкіра=woman['skin'],волосся=woman['hair'],очі=woman['eyes'],
               паспорт=dict(нагода='робота' if who=='1' else 'побачення',місце='офіс_корпоративний' if who=='1' else 'ресторан_високий'))
    readings = [m.прийняти(inp,response) for m in (до,після)]
    assert readings[0]==readings[1],f
    assert len(prompts[1])<len(prompts[0]),f
    assert 'scheme_reasons' in prompts[1] and 'base_reasons' in prompts[1] and 'reason_codes' in prompts[1]
    results.append(dict(запис=f,довжини=list(map(len,prompts)),читач_однаковий=True,
                        причини=readings[1]['вибір']['причини'],відхилено=readings[1]['відхилено']))
assert len(results)==6,len(results)
print(json.dumps(dict(база=base,голова=head,записів=len(results),результати=results),ensure_ascii=False,indent=2))
