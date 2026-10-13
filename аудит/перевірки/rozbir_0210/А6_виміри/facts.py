import json,re,glob,os,sys
def rd(fn):
    t=open(fn,encoding='utf8').read()
    m=re.match(r'── ПРОМПТ \((\d+) симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \(([^)]*)\) ──\n(.*)\n$',t,re.S)
    return m.group(2),m.group(4)
def J(s):
    try: return json.loads(s)
    except: return None
for r in sorted(os.listdir('/tmp/a6/runs')):
    if not r.startswith('ж'): continue
    V=sorted(glob.glob(f'/tmp/a6/runs/{r}/x/VIDPOVIDI/*.txt'))
    pk=[f for f in V if 'ПАКЕТ' in f]; rp=[f for f in V if 'ВЕРДИКТ_V1_ОБРАЗИ' in f]; vb=[f for f in V if 'ВИБІР' in f]; op=[f for f in V if 'ОПИС' in f]; pal=[f for f in V if 'палітри' in f]
    out=[r]
    if pk:
        o=J(rd(pk[0])[0]); out.append('ПАКЕТ case='+json.dumps(o.get('case'),ensure_ascii=False)); out.append(' day='+json.dumps(o.get('day'),ensure_ascii=False))
        p=o.get('person',{}); out.append(' body='+json.dumps(p.get('body'),ensure_ascii=False)[:400]+' scheme='+str(p.get('palette',{}).get('scheme'))+' base='+json.dumps(p.get('palette',{}).get('base'),ensure_ascii=False))
        out.append(' style_rules='+json.dumps(o.get('style_rules'),ensure_ascii=False)[:500])
    rb=[f for f in rp if len(rd(f)[0])>20000]
    if rb:
        o=J(rd(rb[0])[0]); out.append('РЕМОНТ case='+json.dumps(o.get('case'),ensure_ascii=False)+' day='+json.dumps(o.get('day'),ensure_ascii=False))
    if vb:
        o=J(rd(vb[0])[0]); out.append('ВИБІР case='+json.dumps(o.get('case'),ensure_ascii=False)[:300]+' day='+json.dumps(o.get('day'),ensure_ascii=False)[:200])
    if op:
        o=J(rd(op[0])[0]); out.append('ОПИС case='+json.dumps(o.get('case'),ensure_ascii=False)[:300]+' your_day='+json.dumps(o.get('your_day_sentence'),ensure_ascii=False)[:200])
    print('\n'.join(out)); print()
