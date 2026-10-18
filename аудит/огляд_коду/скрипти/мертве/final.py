import json,re,collections,math,statistics
SP='/tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/V'; J=SP+'/wt/джерела'
meta={l.split('\t')[0]:l.rstrip('\n').split('\t') for l in open(SP+'/s/meta.tsv')}; hd=meta.pop('файл')
static=json.load(open(SP+'/статично_зламані.json'))
first={}
for l in open(SP+'/проби_сирі.jsonl'): r=json.loads(l); first[r['f']]=r
re_={}
for l in open(SP+'/проби_повтор.jsonl'): r=json.loads(l); re_[r['f']]=r
FAIL=re.compile(r'ВПАЛО\s*[:=]?\s*[1-9]|✗(?!\s*[:=]?\s*0\b)|\bFAIL\b|не так|ПОМИЛКА',re.I)
HEAVY=re.compile(r'каталог_на_диску|каталог_brief|каталог_повний|import[^\n]*\b(feed|Ф)\b|from feed|стенд_знімок|тест_живого|zhnyvarka|requests|urllib|ComfyUI')
def exc(o):
    m=re.findall(r'^(\w*(?:Error|Exception|Exit|Iteration)\w*)[:\s]',o,re.M); return m[-1] if m else ''
def cls(r):
    o=r['out']; rc=r['code']
    if rc in(-24,152,-9) or (r['cpu'] or 0)>=60: return 'тайм-аут (CPU>60с)'
    if rc==0:
        return 'друкує ознаку провалу (ловить зараз)' if FAIL.search(o) else 'чисто'
    e=exc(o)
    if ('argv' in o and e=='IndexError') or re.search(r"git', '(show|ls-tree|log|diff)|origin/claude|LM Studio|URLError|Потрібні два|треба тека",o) or (e=='ModuleNotFoundError' and re.search(r"No module named '(cv2|numpy|PIL|playwright|tokenizers|tiktoken)'",o)):
        return 'не зламана: потребує аргумент/мережу/модель/гілку/пакет'
    if e in('ImportError','ModuleNotFoundError'): return 'зламана змінами: ImportError'
    if e=='AttributeError': return 'зламана змінами: AttributeError'
    if e=='KeyError': return 'зламана змінами: KeyError (дані/словник)'
    if e=='NameError': return 'зламана: NameError'
    if e in('AssertionError','StopIteration'): return 'ловить зараз: падає на твердженні/очікуванні'
    if e=='FileNotFoundError': return 'зламана змінами: FileNotFoundError'
    if e: return 'падає: '+e+' (розбір даних)'
    return 'rc!=0 без винятку'
fin={}
for f,r in first.items():
    rr=re_.get(f,r)
    c=cls(rr); fin[f]=(c,rr)
cnt=collections.Counter(c for c,_ in fin.values())
n=len(fin)
print('вибірка',n,'з',len(meta))
for c,v in cnt.most_common(): print('%3d  %4.1f%%  %s'%(v,100*v/n,c))
# stratified extrapolation
def heavy(f): return bool(HEAVY.search(open(J+'/проби/'+f,encoding='utf-8').read()))
H={f:heavy(f) for f in meta}
Ns=collections.Counter(H.values()); ns=collections.Counter(H[f] for f in fin)
print('страти: heavy',Ns[True],'вибрано',ns[True],'; light',Ns[False],'вибрано',ns[False])
est=collections.Counter()
for c in cnt:
    for s in(True,False):
        k=sum(1 for f,(cc,_) in fin.items() if cc==c and H[f]==s)
        est[c]+=Ns[s]*k/max(1,ns[s])
print('екстраполяція на',len(meta))
for c,v in est.most_common(): print('%5.0f  %s'%(v,c))
# cpu
cpu=[(r['cpu'] or 0) for f,(c,r) in fin.items()]
w=sum(Ns[s]*sum((r['cpu'] or 0) for f,(c,r) in fin.items() if H[f]==s)/max(1,ns[s]) for s in(True,False))
print('сума CPU у вибірці, с',round(sum(cpu)),'медіана',statistics.median(cpu),'; екстраполяція суми CPU на 1152, год',round(w/3600,1))
# static-broken among sample
sb=[f for f in fin if f in static]; print('статично зламані у вибірці',sb)
# write
with open(SP+'/проби.tsv','w') as o:
    o.write('\t'.join(hd)+'\tprogin\tрядків_heavy\tкод\tcpu_с\tстіна_с\tклас\tстатично_зламана\tхвіст\n')
    for f,m in meta.items():
        if f in fin:
            c,r=fin[f]; tail=re.sub(r'\s+',' ',(r['out'].split('--STDERR--')[-1].strip() or r['out'].split('--STDERR--')[0].strip()))[-140:]
            o.write('\t'.join(m)+'\tтак\t%d\t%s\t%s\t%s\t%s\t%s\t%s\n'%(H[f],r['code'],r['cpu'],r['wall'],c,';'.join(static.get(f,[])),tail))
        else:
            o.write('\t'.join(m)+'\tні\t%d\t\t\t\tне_запускали\t%s\t\n'%(H[f],';'.join(static.get(f,[]))))
# by-age / family in sample
by=collections.defaultdict(collections.Counter)
for f,(c,_) in fin.items():
    by[meta[f][3][:7]]['broken' if c.startswith(('зламана','падає')) else 'ok' ]+=1
print(dict(by))
fam=collections.defaultdict(collections.Counter)
for f,(c,_) in fin.items(): fam[meta[f][2]]['бр' if c.startswith(('зламана','падає')) else 'ін']+=1
print({k:dict(v) for k,v in fam.items() if v['бр']>=2})
# mention vs class
mm=collections.defaultdict(collections.Counter)
for f,(c,_) in fin.items():
    m=meta[f]; key='згадана' if (int(m[4]) or int(m[5]) or int(m[6]) or int(m[7])) else 'без згадок'
    mm[key]['зламана' if c.startswith(('зламана','падає')) else ('чисто' if c=='чисто' else 'інше')]+=1
print({k:dict(v) for k,v in mm.items()})
