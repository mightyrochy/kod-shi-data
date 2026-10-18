import json,re,sys,collections,statistics
SP='/tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/V'
meta={l.split('\t')[0]:l.rstrip('\n').split('\t') for l in open(SP+'/s/meta.tsv')}
static=json.load(open(SP+'/статично_зламані.json'))
rs=[json.loads(l) for l in open(SP+'/проби_сирі.jsonl')]
FAIL=re.compile(r'ВПАЛО\s*[:=]?\s*[1-9]|✗(?!\s*[:=]?\s*0\b)|\bFAIL\b|не так|ПОМИЛКА',re.I)
def cls(r):
    o=r['out']; rc=r['code']
    if rc in(-24,152,-9) or (r['cpu'] or 0)>=60: return 'тайм-аут(CPU>60с)'
    if rc==124: return 'тайм-аут(стіна 600с)'
    if rc!=0:
        m=re.findall(r'^(\w*(?:Error|Exception|Exit|Interrupt)\w*)[:\s]',o,re.M)
        t=m[-1] if m else ('SystemExit' if 'SystemExit' in o else '')
        if t in('ImportError','ModuleNotFoundError'): return 'зламана:ImportError'
        if t in('AttributeError','KeyError','FileNotFoundError','NameError','TypeError','IndexError','ValueError','AssertionError','SyntaxError'): return 'зламана/падає:'+t
        if t: return 'падає:'+t
        return 'rc!=0 (без винятку; ознака провалу за кодом)'
    if FAIL.search(o): return 'друкує ознаку провалу'
    return 'чисто'
out=open(SP+'/проби.tsv','w'); out.write('файл\tрядків\tсім\'я\tдата\tyml\tREADME\tдошка\tзгадок_у_коді\tкод\tcpu_с\tстіна_с\tклас\tстатично_зламана\tхвіст\n')
cnt=collections.Counter(); ex=collections.defaultdict(list)
for r in rs:
    c=cls(r); cnt[c]+=1; ex[c].append(r['f'])
    m=meta[r['f']]; tail=re.sub(r'\s+',' ',r['out'].split('--STDERR--')[-1].strip() or r['out'].split('--STDERR--')[0].strip())[-160:]
    out.write('\t'.join(m)+'\t%s\t%s\t%s\t%s\t%s\t%s\n'%(r['code'],r['cpu'],r['wall'],c,';'.join(static.get(r['f'],[])),tail))
n=len(rs)
print('прогнано',n,'з',len(meta)-1)
for c,v in cnt.most_common(): print(v,c)
print('CPU сума',round(sum((r['cpu'] or 0) for r in rs),1),'wall сума',round(sum(r['wall'] for r in rs),1),'медіана cpu',statistics.median((r['cpu'] or 0) for r in rs))
for c in cnt:
    if c!='чисто': print(c,ex[c][:6])
