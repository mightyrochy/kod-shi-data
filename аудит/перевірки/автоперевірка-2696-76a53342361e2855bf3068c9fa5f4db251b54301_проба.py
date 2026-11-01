import io, json, os, pathlib, re, subprocess, sys, tarfile
repo = pathlib.Path.cwd()
tmp = pathlib.Path(os.environ['TEMP']) / 'review2696'
tmp.mkdir(exist_ok=True)
base = '8d604055debbabef950165fb2c0e50d1f31bb0ed'
head = '76a53342361e2855bf3068c9fa5f4db251b54301'
gitdir = subprocess.check_output(['git','rev-parse','--absolute-git-dir'], text=True).strip()
prefix = pathlib.Path('аудит/адаптери/gemini')
results = []
def tree(label, sha):
    dest = tmp / label
    dest.mkdir(exist_ok=True)
    data = subprocess.check_output(['git','archive',sha,str(prefix).replace('\\','/')])
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(dest, filter='data')
    env = dict(os.environ, GIT_DIR=gitdir, GIT_WORK_TREE=str(dest), GIT_INDEX_FILE=str(tmp/(label+'.index')), PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    subprocess.run(['git','read-tree',sha], env=env, check=True)
    return dest, env

def run(label, command, dest, env, expected, verbose=False):
    p = subprocess.run(command, cwd=dest, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode('utf-8',errors='replace')
    (tmp/(re.sub(r'[^\w.-]', '_',label)+'.log')).write_text(out,encoding='utf-8')
    results.append(dict(label=label, command=command, rc=p.returncode, expected=expected, output=out))
    print(f'{label}: rc={p.returncode}; очікувано={expected}', flush=True)
    if verbose or p.returncode != expected:
        print(out,flush=True)
    return p.returncode

before, be = tree('base',base)
after, ae = tree('head',head)
script = prefix/'перевірка/перевірити_хеші.py'
cmd = [sys.executable,'-X','utf8',str(script)]
run('ДО: стара звірка на базі',cmd,before,be,0,True)
old = (before/script).read_bytes()
(before/script).write_bytes((after/script).read_bytes())
run('ДО: нова звірка на базі',cmd,before,be,1,True)
(before/script).write_bytes(old)
run('ПІСЛЯ: нова звірка на голові',cmd,after,ae,0,True)
manifest = after/prefix/'m9v/хеші.psd1'
table = after/prefix/'НАЛАШТУВАННЯ.md'
original = {p:p.read_bytes() for p in (manifest,table)}
names = dict(re.findall(r"'([\w.]+\.ps1)'\s*=\s*'([^']*)'",manifest.read_text(encoding='utf-8-sig')))
for name, value in names.items():
    variants = {'63':value[:-1], '65':value+'A', 'lower':value.lower(), 'nonhex':'Z'+value[1:], 'empty':'', 'wrong64':('A' if value[0]!='A' else 'B')+value[1:]}
    for variant, broken in variants.items():
        for path,data in original.items():
            path.write_bytes(data.replace(value.encode(),broken.encode()))
        run(name+'-'+variant,cmd,after,ae,1)
        for path,data in original.items(): path.write_bytes(data)
# Перевірка кожного джерела окремо.
value = names['wrapper_chain.ps1']
for path in original:
    path.write_bytes(original[path].replace(value.encode(),value[:-1].encode()))
    run('окремо-'+path.name,cmd,after,ae,1)
    path.write_bytes(original[path])
# Той самий Python-блок, який виконує змінений shell-стенд.
source=(after/prefix/'перевірка/сценарії_m9v.sh').read_text(encoding='utf-8')
block=re.findall(r"<<'P'[^\n]*\n(.*?)\nP",source,re.S)[0]
blockfile=tmp/'m9v-hash-block.py'
blockfile.write_text(block,encoding='utf-8')
blockcmd=[sys.executable,'-X','utf8',str(blockfile),str(after/prefix)]
run('m9v: голова, хеш-блок',blockcmd,after,ae,0,True)
for variant,broken in {'63':value[:-1],'65':value+'A','lower':value.lower(),'nonhex':'Z'+value[1:],'empty':'','wrong64':'A'+value[1:]}.items():
    for path,data in original.items(): path.write_bytes(data.replace(value.encode(),broken.encode()))
    run('m9v-'+variant,blockcmd,after,ae,1)
    for path,data in original.items(): path.write_bytes(data)
# Повний суміжний стенд без інсталяції чи запуску обгортки.
ae['TMPDIR'] = str(tmp/'bash-tmp').replace('\\','/')
pathlib.Path(ae['TMPDIR']).mkdir(exist_ok=True)
run('повний сценарії_m9v.sh',[r'C:\Program Files\Git\bin\bash.exe',str(prefix/'перевірка/сценарії_m9v.sh').replace('\\','/')],after,ae,0,True)
(tmp/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
failed = [r['label'] for r in results if r['rc'] != r['expected']]
print('ПІДСУМОК: запусків',len(results),'невідповідностей',len(failed),failed)
sys.exit(bool(failed))
