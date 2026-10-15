import sys,json,hashlib,re
from hydrate import *
main='47ac855c51b249c6112f0ba0ca64924a50bc32e4';B='аудит/БЕКЛОГ.md';S={};BP={};MB=git('show',main+':'+B)
def rows(b):return {int(m[1]):l for l in b.decode().splitlines(keepends=True) if(m:=re.match(r'^\|\s*(\d+)\s*\|',l))}
mr=rows(MB)
for file in P.glob('pushed-*.json'):
 d=json.loads(file.read_text());n=d['n'];p=json.load(open(P/f'prep-{n}.json'));fb=git('show',d['tree']+':'+B);fr=rows(fb);s=fb.decode()
 for i in d['own_board_rows']:s=s.replace(fr[i],mr.get(i,''),1)
 ownnonrow=''
 if s.encode()!=MB:
  assert n==1082 and s.encode()==MB+b'\n'
  b=git('show',d['base']+':'+B);o=git('show',d['old']+':'+B);r=rows(o);assert o.replace(r[5685].encode(),b'')==b+b'\n';ownnonrow='\n';s=s[:-1]
 assert s.encode()==MB,(n,'foreignboardbytes')
 BP[n]={'main_sha256':hashlib.sha256(MB).hexdigest(),'final_sha256':hashlib.sha256(fb).hexdigest(),'normalized_foreign_equals_main':True,'own_nonrow_addition':ownnonrow,'duplicates':0,'main_order_preserved':True,'main_ids':len(mr),'final_ids':len(fr),'own_rows':{str(i):{'old':rows(git('show',d['old']+':'+B)).get(i),'main':mr.get(i),'final':fr[i]} for i in d['own_board_rows']}}
 paths=d['own_exact']+d['combined'];bs={}
 for path in paths:bs[path]={'old_blob':git('rev-parse',d['old']+':'+path).decode().strip(),'new_blob':git('rev-parse',d['tree']+':'+path).decode().strip(),'kind':'exact' if path in d['own_exact'] else 'combined'}
 S[n]={k:v for k,v in d.items() if k not in ['elements','commit','ref']};S[n]['source_bytes']=bs;S[n]['ci']=json.load(open(P/f'ci-{n}.json'))
(P/'board-proofs.json').write_text(json.dumps(BP,ensure_ascii=False,indent=2));(P/'summary-draft.json').write_text(json.dumps(S,ensure_ascii=False,indent=2));print('proof',len(S),'allforeignboardexact')

