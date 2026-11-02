"""ДО/ПІСЛЯ застосування обходу до v1 (з кореня репозиторію; ДО — з HEAD)."""
import gzip, json, subprocess, io, collections, csv, re
def load(f): return [json.loads(l) for l in f][1:]
new=load(io.TextIOWrapper(gzip.open('каталог_записи_v1.jsonl.gz'),encoding='utf-8'))
old=load(io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(subprocess.check_output(['git','show','HEAD:каталог_записи_v1.jsonl.gz']))),encoding='utf-8'))
ув=[р['домен'] for р in csv.DictReader((l for l in open('zhnyvarka/магазини.tsv',encoding='utf-8') if not l.startswith('#')),delimiter='\t') if р['стан']=='увімкнено']
вим=[р['домен'] for р in csv.DictReader((l for l in open('zhnyvarka/магазини.tsv',encoding='utf-8') if not l.startswith('#')),delimiter='\t') if р['стан']!='увімкнено']
dom=lambda r:re.sub(r'^www\.','',r['адреса'].split('/')[2])
for n,d in(('ДО',old),('ПІСЛЯ',new)):
    c=collections.Counter(dom(r) for r in d)
    знято=lambda r:[p[1] for p in r['параметри'] if p[0]=='знято']
    з07=sum(знято(r)==['2026-09-07'] for r in d)
    print(n,len(d),'увімк. з нулем',sum(c[x.removeprefix('www.')]==0 for x in ув),'з',len(ув),'вимкнених речей',sum(c[x.removeprefix('www.')] for x in вим),'знято 07.09',з07,round(100*з07/len(d),1),'збирачі',dict(collections.Counter(r.get('збирач') for r in d)),'схеми',dict(collections.Counter(r.get('схема') for r in d)))
