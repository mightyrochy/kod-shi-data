import os,json,sys,subprocess,pathlib,base64,datetime,itertools
P=pathlib.Path('/dev/shm/final-ready-batches-1655');R=str(P/'repo');E={**os.environ,'GIT_NO_LAZY_FETCH':'1','TMPDIR':str(P/'tmp')}
def git(*a,input=None,check=True):return subprocess.run(['git','-c','core.quotepath=false','--git-dir='+R,*a],input=input,env=E,capture_output=True,check=check)
def exists(s):return git('cat-file','-e',s,check=False).returncode==0
def ingest(kind,d):
 s=d['sha']
 if kind=='blobs':raw=base64.b64decode(d['content']) if d.get('encoding')=='base64' else d['content'].encode();typ='blob'
 elif kind=='trees':raw=b''.join(x['mode'].lstrip('0').encode()+b' '+x['path'].encode()+b'\0'+bytes.fromhex(x['sha']) for x in d['tree']);typ='tree'
 else:
  typ='commit';v=d.get('verification') or {};payload=v.get('payload');sig=v.get('signature')
  if payload:
   a,b=payload.split('\n\n',1);raw=(a+'\ngpgsig '+sig.replace('\n','\n ')+'\n\n'+b).encode()
  else:
   root='tree '+d['tree']['sha']+'\n'+''.join('parent '+p['sha']+'\n' for p in d['parents'])
   def ident(role,tz):
    x=d[role];ts=int(datetime.datetime.fromisoformat(x['date'].replace('Z','+00:00')).timestamp());return f"{role} {x['name']} <{x['email']}> {ts} {tz}\n"
   raw=None
   for tz1,tz2 in itertools.product(['+0000','+0300','+0200','-0700','-0800'],repeat=2):
    candidate=(root+ident('author',tz1)+ident('committer',tz2)+'\n'+d['message']).encode()
    for c in [candidate,candidate+b'\n']:
     if git('hash-object','-t','commit','--stdin',input=c).stdout.decode().strip()==s:raw=c;break
    if raw is not None:break
   assert raw is not None,('cannot reconstruct',s)
 out=git('hash-object','-w','-t',typ,'--stdin',input=raw).stdout.decode().strip();assert out==s,(out,s)
if __name__=='__main__':
 if sys.argv[1]=='ingest':
  for x in json.loads(pathlib.Path(sys.argv[2]).read_text()):ingest(x['kind'],x['data'])
 else:
  queue=[('commits',s) for s in sys.argv[2:]];seen=set();missing=[]
  while queue:
   k,s=queue.pop()
   if (k,s) in seen:continue
   seen.add((k,s))
   if exists(s) and not (P/'repo/objects'/s[:2]/s[2:]).exists():continue
   if not exists(s):missing.append({'kind':k,'sha':s});continue
   if k=='commits':
    data=git('cat-file','commit',s).stdout.decode();headers=data.split('\n\n',1)[0].splitlines()
    queue += [('trees',x[5:]) for x in headers if x.startswith('tree ')]+[('commits',x[7:]) for x in headers if x.startswith('parent ')]
   elif k=='trees':
    for x in git('ls-tree','-z',s).stdout.split(b'\0'):
     if not x:continue
     meta,path=x.split(b'\t',1);mode,typ,sha=meta.decode().split()
     if typ=='tree':queue.append(('trees',sha))
  (P/'missing.json').write_text(json.dumps(missing));print(json.dumps({'missing':len(missing),'objects':missing[:80]}))
