import urllib.request,pathlib,re,json,hashlib,base64,time
from packaging.tags import cpython_tags,compatible_tags
from packaging.requirements import Requirement
from packaging.markers import default_environment
p=pathlib.Path('/dev/shm/security5685/repo');out=pathlib.Path('/dev/shm/qa5685-r2');results={}
class Response:
 def __init__(self,url,timeout):
  self.r=urllib.request.urlopen(url,timeout=timeout);self.url=self.r.url;self.status_code=self.r.status;self.headers=self.r.headers
 def raise_for_status(self):assert self.status_code==200
 def json(self):return json.load(self.r)
 def iter_content(self,n):
  while True:
   b=self.r.read(n)
   if not b:break
   yield b
class Session:
 def get(self,url,timeout=90,stream=False):return Response(url,timeout)
s=Session()
def grab(url,alg='sha256'):
 r=s.get(url,timeout=90,stream=True);r.raise_for_status();h=hashlib.new(alg);n=0
 for b in r.iter_content(262144):h.update(b);n+=len(b)
 return {'url':r.url,'status':r.status_code,'bytes':n,'hash':h.hexdigest(),'base64':base64.b64encode(h.digest()).decode(),'cors':r.headers.get('Access-Control-Allow-Origin')}
html=(p/'джерела/показ.html').read_text();url=re.search(r'<script defer src="([^"]+)" integrity="([^"]+)" crossorigin="anonymous"',html)
r=grab(url[1],'sha384');r['match']=url[2]=='sha384-'+r['base64'];assert r['match'];results['pyodide']=r
fonts=[]
for u in re.findall(r'https://cdn.jsdelivr.net/gh/MacPaw/Fixel@[^"\s]+',html):
 new=grab(u);old=grab(re.sub(r'@[0-9a-f]{40}/','@main/',u));assert new['hash']==old['hash'];fonts.append({'immutable':new,'main':old,'same_bytes':True})
results['fonts']=fonts;out.joinpath('network.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print('CDN script actual bytes/SRI/CORS + 4 fonts byte-identical OK',flush=True)
lock=json.loads((p/'джерела/package-lock.json').read_text());npm=[]
for name,rec in lock['packages'].items():
 if not name:continue
 assert re.match(r'https://registry.npmjs.org/',rec['resolved']);assert rec['integrity'].startswith('sha512-')
 r=grab(rec['resolved'],'sha512');assert rec['integrity']=='sha512-'+r['base64'];npm.append({'package':name,'version':rec['version'],**r})
results['npm']=npm;out.joinpath('network.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print('npm tarball actual bytes integrity OK',len(npm),flush=True)
# wheel metadata and hash provenance; validate one compatible CPython 3.12 Linux wheel per unique lock entry.
entries={}
for f in (p/'.github/requirements').glob('*.txt'):
 for line in f.read_text().splitlines():
  m=re.fullmatch(r'([^#= ]+)==([^ ]+) --hash=sha256:([0-9a-f]{64})',line)
  if m:entries[m[1].lower().replace('_','-')]=(m[2],m[3])
py=[];env=default_environment();env.update(python_version='3.12',python_full_version='3.12.12',sys_platform='linux',platform_system='Linux',platform_machine='x86_64',extra='')
for name,(version,sha) in entries.items():
 meta=s.get(f'https://pypi.org/pypi/{name}/{version}/json',timeout=60);meta.raise_for_status();data=meta.json();files=[x for x in data['urls'] if x['digests']['sha256']==sha and x['filename'].endswith('.whl')];assert len(files)==1,(name,'wheel missing')
 wheel=files[0];fn=wheel['filename'];assert ('cp312' in fn or 'py3-none-any' in fn or 'py2.py3-none-any' in fn or 'py3-none-manylinux' in fn or 'abi3-manylinux' in fn),(name,fn)
 if 'linux' in fn:assert 'x86_64' in fn,(name,fn)
 for raw in data['info'].get('requires_dist') or []:
  req=Requirement(raw)
  if req.marker and not req.marker.evaluate(env):continue
  dep=req.name.lower().replace('_','-');assert dep in entries,(name,'unlocked',raw);assert req.specifier.contains(entries[dep][0]),(name,'bad version',raw)
 r=grab(wheel['url']);assert r['hash']==sha;py.append({'name':name,'version':version,'filename':fn,'requires_dist':data['info'].get('requires_dist'),'requires_python':data['info']['requires_python'],**r});print('wheel',name,version,'OK',flush=True)
results['python']=py;out.joinpath('network.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print('ALL NETWORK PASS',flush=True)
