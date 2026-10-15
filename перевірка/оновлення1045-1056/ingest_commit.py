from pathlib import Path
import sys,json,itertools
from datetime import datetime
sys.path.insert(0,str(Path(__file__).parent));from composition import git
for arg in sys.argv[1:]:
 x=json.load(open(arg));root='tree '+x['tree']['sha']+'\n'+''.join('parent '+p['sha']+'\n' for p in x['parents']);a=x['author'];c=x['committer'];ts=lambda v:int(datetime.fromisoformat(v.replace('Z','+00:00')).timestamp());raw=None
 for at,ct,end in itertools.product(['+0000','+0300','+0200','-0700','-0800'],['+0000','+0300','+0200','-0700','-0800'],['','\n']):
  candidate=(root+f"author {a['name']} <{a['email']}> {ts(a['date'])} {at}\ncommitter {c['name']} <{c['email']}> {ts(c['date'])} {ct}\n\n"+x['message']+end).encode()
  if git('hash-object','-t','commit','--stdin',input=candidate).decode().strip()==x['sha']:raw=candidate;break
 assert raw is not None,x['sha'];assert git('hash-object','-w','-t','commit','--stdin',input=raw).decode().strip()==x['sha'];print('ingested own',x['sha'])
