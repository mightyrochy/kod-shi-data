import base64, hashlib, io, json, re, subprocess, sys, zipfile
from pathlib import Path

ROOT=Path('/workspace/replace4945')
OUT=Path(__file__).parent
HEAD='0a664f440b208a4023cbeb9a01bc4461ae37ab84'
OLD='b722c8867f671c612e71c5f5828f8befbf642111'
MAIN='16a13b727f35aec508bf01d7fc6070049481a785'
BASE='7c90a0093b5d7dc8587a90c541eaf11e23b9a3be'
ART=Path('/workspace/replace4945-compose-evidence/index.html')
def git(*args): return subprocess.check_output(['git','-C',str(ROOT),*args])
def digest(b): return hashlib.sha256(b).hexdigest()
assert git('rev-parse','HEAD').decode().strip()==HEAD
assert git('status','--porcelain')==b''
assert git('show','-s','--format=%P',HEAD).decode().strip()==OLD+' '+MAIN
raw=ART.read_bytes(); html=raw.decode()
assert digest(raw)=='e3622fdfdddcbbe2d9b9f5921ce9c4d72cd64ca2604ed5713dcaadd2334d7864'
sys.path.insert(0,str(ROOT/'джерела'))
import build_артефакт as B
pat=r'const МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"'
packed=base64.b64decode(re.search(pat,html)[1])
old_html=Path('/workspace/replace4945-ui-final-evidence/index.html').read_text()
old_packed=base64.b64decode(re.search(pat,old_html)[1])
assert packed==old_packed,'Packed archive changed'
archive=zipfile.ZipFile(io.BytesIO(packed))
modules=[]
for name in archive.namelist():
    if not name.endswith('.py'): continue
    source=git('show',HEAD+':джерела/'+name)
    assert source==git('show',OLD+':джерела/'+name)==(ROOT/'джерела'/name).read_bytes()
    assert archive.read(name)==B._стрип(str(ROOT/'джерела'/name))
    modules.append({'file':name,'sourceSHA256':digest(source),'packedSHA256':digest(archive.read(name))})
assert len(modules)==156
source=git('show',HEAD+':джерела/показ.html').decode()
clean=B._чистка_показу(source)
keys=[x for x in dict.fromkeys(re.findall(r'__[А-ЯІЇЄҐа-яіїєґA-Za-z0-9_]+__',clean)) if x not in ('__ЗАУВАЖЕННЯ__','__ПРОЗА__')]
assert len(keys)==8
parts=re.split('('+'|'.join(map(re.escape,keys))+')',clean)
pattern=''.join('(?P<v%d>.*?)'%keys.index(x) if x in keys else re.escape(x) for x in parts)
match=re.fullmatch(pattern,html,re.S); assert match,'Template outside placeholders differs'
values={k:match['v'+str(i)] for i,k in enumerate(keys)}
for key,fn in [('__ДОВІДНИК_ПОКАЗУ__',B._довідник_показу),('__ВИБІРКА_ПОКАЗУ__',B._вибірка_показу),('__ПРОМПТ_КОЛІР_ПОКАЗУ__',B._промпт_кольору_показу)]:
    assert values[key]==fn(str(ROOT/'джерела'))
assert values['__ВІДБИТОК__']==B._відбиток(str(ROOT/'джерела'),[m['file'][:-3] for m in modules])
assert archive.read(values['__ФІД_ПОКАЗУ__']).count(b'<offer ')==11993
merge_files=[]
paths=git('diff','--name-only',BASE,MAIN).decode().splitlines()
old_changed=set(git('diff','--name-only',BASE,OLD).decode().splitlines())
(OUT/'tmp').mkdir(exist_ok=True)
for path in paths:
    current=git('show',HEAD+':'+path)
    if path not in old_changed:
        assert current==git('show',MAIN+':'+path),path
        merge_files.append({'file':path,'proof':'exact-main'})
    else:
        tmp=[]
        for tag,ref in [('ours',OLD),('base',BASE),('theirs',MAIN)]:
            f=OUT/'tmp'/('merge-'+tag);f.write_bytes(git('show',ref+':'+path));tmp.append(str(f))
        p=subprocess.run(['git','merge-file','-p',*tmp],capture_output=True)
        assert p.returncode==0,(path,p.stderr.decode())
        assert p.stdout==current,path+': differs from clean three-way merge'
        merge_files.append({'file':path,'proof':'exact-conflict-free-three-way'})
latest=git('rev-parse','origin/main').decode().strip()
assert latest=='1f86448e65c036d799a23ab28be16081d75ed631'
assert set(git('diff','--name-only',MAIN,latest).decode().splitlines())=={'index.html','джерела/аудит/ДОСЯЖНІСТЬ.md'}
for rule in ['AGENTS.md','CLAUDE.md']:
    assert git('show',HEAD+':'+rule)==git('show',MAIN+':'+rule)
report={'head':HEAD,'tree':git('rev-parse',HEAD+'^{tree}').decode().strip(),'parents':[OLD,MAIN],'base':BASE,
 'artifact':str(ART),'artifactSHA256':digest(raw),'sourceModulesExact':156,'sourceModulesUnchangedFromB722':156,
 'packedArchiveIdenticalB722':True,'packedArchiveSHA256':digest(packed),'htmlTemplateExact':True,
 'catalogueRows':11993,'mainComposition':merge_files,'rulesExactMain':True,'latestMain':latest,'latestMainGeneratedOnly':True,
 'modules':modules,'placeholders':{k:{'length':len(v),'sha256':digest(v.encode())} for k,v in values.items()}}
(OUT/'source-identity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('modules','placeholders','mainComposition')},ensure_ascii=False))
print('mainCompositionFiles',len(merge_files),'PASS')
