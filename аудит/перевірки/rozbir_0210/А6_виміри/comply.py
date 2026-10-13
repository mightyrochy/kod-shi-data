import json,re,glob,os,collections as C,statistics as st
def rd(f):
    t=open(f,encoding='utf8').read(); m=re.match(r'── ПРОМПТ \((\d+) симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \(([^)]*)\) ──\n(.*)\n$',t,re.S); return m.group(2),m.group(4)
def pj(a):
    a2=a.strip(); fence=a2.startswith('```')
    if fence: a2=re.sub(r'^```\w*\n|\n```$','',a2)
    try: return json.loads(a2),fence,None
    except Exception as e: return None,fence,str(e)[:60]
S=C.Counter(); ex=C.defaultdict(list); runs_with=C.defaultdict(set)
def bad(k,r,txt=''):
    S[k]+=1; runs_with[k].add(r)
    if len(ex[k])<3: ex[k].append(f'{r}: {txt}'[:200])
for f in sorted(glob.glob('/tmp/a6/runs/*/x/VIDPOVIDI/*.txt')):
    r=f.split('/')[4]; n=os.path.basename(f)
    if not re.search('ПАКЕТ|ВЕРДИКТ_V1_ОБРАЗИ|ВИБІР|ОПИС',n): continue
    p,a=rd(f); o=json.loads(p); A,fence,err=pj(a)
    kind='ПАКЕТ' if 'ПАКЕТ' in n else 'ВИБІР' if 'ВИБІР' in n else 'ОПИС' if 'ОПИС' in n else ('РЕМОНТ' if len(p)>20000 else 'ПОВНОТА')
    S[kind+' файлів']+=1
    if fence: bad(kind+': код-огорожа ```',r)
    if A is None: bad(kind+': невалідний JSON',r,err); continue
    if kind in('ПАКЕТ','РЕМОНТ','ПОВНОТА'):
        outs=A.get('outfits') or []
        want=o.get('outfits_wanted') or (len(o.get('verdict') or []) if kind=='ПОВНОТА' else None)
        S[kind+' образів']+=len(outs)
        if want and len(outs)!=want: bad(kind+': образів ≠ outfits_wanted',r,f'{len(outs)} vs {want}')
        if kind=='ПАКЕТ': known={x['n'] for x in o['pool']}
        else:
            known={i['n'] for v in o['verdict'] for i in v['your_outfit']['items']}
            sh=o.get('showcase') or {}
            for m in re.findall(r'"n": "([^"]+)"',json.dumps(sh,ensure_ascii=False)): known.add(m)
        use=C.Counter()
        for x in outs:
            its=x.get('items') or []
            for i in its:
                base=re.sub(r'/(top|bottom)$','',i)
                if base not in known: bad(kind+': річ не з входу',r,f"{x.get('id')} {i}")
                use[base]+=1
            if kind=='ПАКЕТ' and not (4<=len(its)<=7): bad(kind+': речей поза 4–7',r,f"{x.get('id')} {len(its)}")
            d=x.get('day') or ''
            if len(d.split())>25: bad(kind+': day > 25 слів',r,f"{len(d.split())}: {d[:80]}")
            if kind in('РЕМОНТ','ПОВНОТА') and re.search(r'formality|office_corporate|^[a-z_]+,',d): bad(kind+': day — факти/коди замість речення',r,d[:90])
        if kind=='ПАКЕТ':
            poles=C.Counter(x.get('pole') for x in outs)
            named=[p_['id'] for p_ in o.get('poles',[]) if p_['id']!='free']
            for p_ in named:
                if poles[p_]!=1: bad('ПАКЕТ: іменована ідея не рівно 1 раз',r,f'{p_}={poles[p_]}')
            unav=o.get('poles_unavailable') or []
            for p_ in unav:
                if poles[p_]: bad('ПАКЕТ: ідея з poles_unavailable',r,p_)
            # below_band / in_arc false без deliberate
            pool={x['n']:x for x in o['pool']}
            for x in outs:
                dl={d_.get('item') for d_ in (x.get('deliberate') or [])}
                for i in x.get('items') or []:
                    it=pool.get(re.sub(r'/(top|bottom)$','',i)) or {}
                    if it.get('below_band') and i not in dl: bad('ПАКЕТ: below_band без deliberate',r,f"{x.get('id')} {i} {it.get('below_band')}")
                    if it.get('in_arc') is False and i not in dl: bad('ПАКЕТ: поза аркою без deliberate',r,f"{x.get('id')} {i}")
            if any(v>2 for v in use.values()): bad('ПАКЕТ: річ у >2 образах',r,str([k for k,v in use.items() if v>2])[:80])
        if kind=='РЕМОНТ':
            if any(v>2 for v in use.values()): bad('РЕМОНТ: річ у >2 образах (правило ≤2)',r,str([k for k,v in use.items() if v>2])[:80])
            ver={v['your_outfit']['id']:v for v in o['verdict']}
            for x in outs:
                v=ver.get(x.get('id'))
                if not v: bad('РЕМОНТ: id образу не з вердикту',r,x.get('id')); continue
                gates=[fi['id'] for fi in (v.get('findings') or []) if fi.get('register')=='gate']
                done={d_.get('finding') for d_ in (x.get('done') or [])}
                S['РЕМОНТ гейтів у збережених']+=len(gates)
                miss=[g for g in gates if g not in done]
                if miss: bad('РЕМОНТ: гейт без запису в done',r,f"{x.get('id')} {miss[:3]}")
                S['РЕМОНТ done fixed']+=sum(1 for d_ in (x.get('done') or []) if d_.get('action')=='fixed')
                S['РЕМОНТ done declined']+=sum(1 for d_ in (x.get('done') or []) if d_.get('action')=='declined')
                S['РЕМОНТ done partly']+=sum(1 for d_ in (x.get('done') or []) if d_.get('action')=='partly')
    if kind=='ВИБІР':
        ver={v['your_outfit']['id']:v for v in o['verdict']}
        ch=A.get('chosen'); v=ver.get(ch)
        if not v: bad('ВИБІР: chosen не з вердикту',r,str(ch)); continue
        nsent=len([s for s in re.split(r'(?<=[.!?])\s+',(A.get('why') or '').strip()) if s])
        if nsent>2: bad('ВИБІР: why > 2 речень',r,f'{nsent}')
        if (v.get('structure') or {}).get('ok') is False and any((w.get('structure') or {}).get('ok')!=False for w in o['verdict']): bad('ВИБІР: обрано з блокером, хоча є без',r,ch)
        gates=[x_['id'] for code,lst in (o.get('remarks_by_code') or {}).items() for x_ in lst if x_.get('outfit')==ch and x_.get('register')=='gate']
        acc={x_.get('finding') for x_ in (A.get('accept') or [])}
        if any(g not in acc for g in gates): bad('ВИБІР: гейт обраного не прийнято в accept',r,f'{ch} {gates[:3]}')
        S['ВИБІР обрано o1']+= (ch=='o1')
    if kind=='ОПИС':
        t=A.get('text') or ''
        if re.search(r'#\d+·\d+|#[0-9a-f]{6}\b',t): bad('ОПИС: номер/hex у тексті',r,re.search(r'#\d+·\d+|#[0-9a-f]{6}\b',t).group(0))
        if re.search(r'\b(try|add|could add|you can add|consider adding|for example in a)\b',t,re.I): bad('ОПИС: порада додати річ поза образом (кандидат)',r,re.search(r'[^.]*\b(try|add|could add|consider adding)\b[^.]*\.',t,re.I).group(0)[:150] if re.search(r'[^.]*\b(try|add|could add|consider adding)\b[^.]*\.',t,re.I) else '')
        if A.get('swap'): S['ОПИС swap']+=1
        if A.get('wrong_photos'): S['ОПИС wrong_photos']+=len(A['wrong_photos'])
        S['ОПИС text симв сума']+=len(t)
for k in sorted(S): print(k, S[k], ('прогонів '+str(len(runs_with[k]))) if k in runs_with else '')
print()
for k,v in ex.items(): print('##',k); [print('   ',x) for x in v]
