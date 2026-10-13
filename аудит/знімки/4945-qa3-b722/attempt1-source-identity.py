import sys
sys.dont_write_bytecode = True
import base64, hashlib, io, json, re, subprocess, zipfile
from pathlib import Path
REPO=Path('/workspace/replace4945')
OUT=Path(__file__).parent
ART=Path('/workspace/replace4945-ui-final-evidence/index.html')
HEAD='b722c8867f671c612e71c5f5828f8befbf642111'
BASE='7c90a0093b5d7dc8587a90c541eaf11e23b9a3be'
SHA='1c376f922b1a2c10492d710b6b1e98200dcab9a0aeab99ec7b9fbf2536f821df'
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args])
def sha(b): return hashlib.sha256(b).hexdigest()
assert git('rev-parse','HEAD').decode().strip()==HEAD
assert git('status','--porcelain')==b''
raw=ART.read_bytes(); assert sha(raw)==SHA
html=raw.decode(); src=git('show',HEAD+':джерела/показ.html').decode()
sys.path.insert(0,str(REPO/'джерела'))
import build_артефакт as B
pattern=re.compile(r'const МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"')
m=pattern.search(html); assert m
z=zipfile.ZipFile(io.BytesIO(base64.b64decode(m[1])))
mods=[]
for n in z.namelist():
    if not n.endswith('.py'): continue
    original=git('show',HEAD+':джерела/'+n)
    local=(REPO/'джерела'/n).read_bytes()
    assert original==local,n+': local differs from frozen git'
    packed=z.read(n); assert B._стрип(str(REPO/'джерела'/n))==packed,n+': packed differs'
    assert git('show','736ff2a503710877859bf592becd4acd8f880c8d:джерела/'+n)==original,n+': module changed since 736'
    mods.append({'file':n,'sourceSHA256':sha(original),'packedSHA256':sha(packed)})
assert len(mods)==156
clean=B._чистка_показу(src)
keys=re.findall(r'__[А-ЯІЇЄҐа-яіїєґA-Za-z0-9_]+__',clean)
keys=list(dict.fromkeys(keys))
assert len(keys)==8,keys
pieces=re.split('('+'|'.join(map(re.escape,keys))+')',clean)
regex=''; placeholders={}
for piece in pieces:
    if piece in keys:
        group='v'+str(keys.index(piece)); regex+='(?P<'+group+'>.*?)'; placeholders[piece]=group
    else: regex+=re.escape(piece)
match=re.fullmatch(regex,html,re.S); assert match,'Template differs outside build placeholders'
values={k:match[g] for k,g in placeholders.items()}
assert values['__ДОВІДНИК_ПОКАЗУ__']==B._довідник_показу(str(REPO/'джерела'))
assert values['__ВИБІРКА_ПОКАЗУ__']==B._вибірка_показу(str(REPO/'джерела'))
assert values['__ПРОМПТ_КОЛІР_ПОКАЗУ__']==B._промпт_кольору_показу(str(REPO/'джерела'))
assert values['__ВІДБИТОК__']==B._відбиток(str(REPO/'джерела'),[x['file'][:-3] for x in mods])
basehtml=git('show',BASE+':джерела/показ.html').decode()
styles=lambda x:re.findall(r'<style.*?</style>',x,re.S)
assert styles(src)==styles(basehtml),'Styles differ'
assert re.findall(r'aria-[\w-]+=[\'\"][^\'\"]*[\'\"]',src)==re.findall(r'aria-[\w-]+=[\'\"][^\'\"]*[\'\"]',basehtml),'ARIA literals differ'
feed=values['__ФІД_ПОКАЗУ__']; rows=z.read(feed).count(b'<offer ')
assert rows==11993
r={'head':HEAD,'tree':git('rev-parse','HEAD^{tree}').decode().strip(),'base':BASE,'artifact':str(ART),'artifactSHA256':SHA,'sourceModulesExact':len(mods),'modulesUnchangedFrom736':len(mods),'htmlTemplateExact':True,'sourceTemplateSHA256':sha(src.encode()),'CSSExactToBase':True,'ARIALiteralsExactToBase':True,'catalogueRows':rows,'placeholders':{k:{'length':len(v),'sha256':sha(v.encode())} for k,v in values.items()},'modules':mods}
(OUT/'source-identity.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k not in ['modules','placeholders']},ensure_ascii=False))
