# Витяг ланцюга складання→суд→ремонт→вибір з вердикти.txt.gz одного прогону → JSONL
import json, gzip, sys, os, re
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/а4_v.jsonl'
def raw(s):
    try: return json.loads(s) if s else None
    except Exception: 
        m = re.search(r'\{.*\}', s or '', re.S)
        try: return json.loads(m.group(0)) if m else None
        except Exception: return None
def fsum(fs): return round(sum((f.get('сила_нп') or 0) for f in fs), 2)
def gates(fs): return sum(1 for f in fs if f.get('регістр') == 'шлюз' or f.get('регістр') == 'gate')
def regs(fs):
    c = {}
    for f in fs: c[f.get('регістр')] = c.get(f.get('регістр'), 0) + 1
    return c
def nid(x): return 'o' + re.sub(r'\D', '', str(x or ''))
def okey(o): return tuple(sorted(o.get('ід') or []))
rows = []
for run in sorted(os.listdir(R)):
    p = os.path.join(R, run, 'вердикти.txt.gz')
    if not run.startswith('ж') or not os.path.exists(p): continue
    try: d = json.load(gzip.open(p, 'rt'))
    except Exception as ex: print('ПРОПУЩЕНО', run, ex); continue
    for pi, pr in enumerate(d.get('прогони', [])):
        for v in pr.get('вердикти', []):
            r = {'run': run, 'прогін': pi, 'рука': v.get('рука'), 'ітерацій': v.get('ітерацій'),
                 'речей': len(v.get('речі_образу') or []) or len((v.get('склад') or '').split('+')),
                 'схема_вийшла': v.get('схема_вийшла'), 'схема_руки': v.get('пал_схема_руки'),
                 'правило_руки': v.get('правило_руки'), 'правило_діяло': v.get('правило_діяло'),
                 'пара_руки': v.get('пара_руки'), 'свідомі': v.get('свідомі'), 'підпис': v.get('підпис'),
                 'знахідок_фін': len(v.get('знахідки_коду') or []), 'сила_фін': fsum(v.get('знахідки_коду') or []),
                 'питань_фін': len(v.get('питання_коду') or []), 'склад': v.get('склад')}
            e = v.get('етапи') or {}
            st = e.get('виклики') or []
            r['кроки'] = [(s.get('крок'), s.get('крок_спроба'), s.get('помилка'), s.get('перевірено'), s.get('образів'), s.get('обрізано'), bool(s.get('відповідь_помилки')), s.get('чому')) for s in st]
            asm = [s for s in st if s.get('крок') == 'assembly']
            rep = [s for s in st if s.get('крок') == 'repair']
            cmp_ = [s for s in st if s.get('крок') == 'completeness_repair']
            ch = [s for s in st if s.get('крок') == 'choice']
            ds = [s for s in st if s.get('крок') == 'description']
            if asm:
                a = asm[0]; ra = raw(a.get('відповідь_сира')) or {}
                poles = {nid(o.get('id')): o.get('pole') for o in ra.get('outfits', [])}
                ideas = []
                for o in a.get('образи_кроку') or []:
                    fs = o.get('знахідки') or []
                    lid = nid(o.get('номер'))
                    ideas.append({'id': lid, 'pole': poles.get(lid), 'підпис': o.get('підпис'), 'n': len(fs), 'сила': fsum(fs), 'шлюз': gates(fs), 'рег': regs(fs),
                                  'блок': len(o.get('блокери') or []), 'key': okey(o), 'правила': [f.get('правило') for f in fs], 'чекліст_провал': ((o.get('чекліст') or {}).get('надлишок') or {}).get('провал'),
                                  'без_входу': ((o.get('чекліст') or {}).get('надлишок') or {}).get('без_входу'), 'deliberate': len([x for x in ra.get('outfits', []) if nid(x.get('id')) == lid and x.get('deliberate')])})
                r['ідеї'] = ideas
                r['asm_набір'] = (a.get('вердикт_кроку') or {}).get('набір')
            if rep:
                s = rep[0]; rr = raw(s.get('відповідь_сира')) or {}
                r['ремонт_відп'] = [{'id': nid(o.get('id')), 'pole': o.get('pole'), 'caption': o.get('caption'), 'items': o.get('items'), 'done': o.get('done'), 'deliberate': o.get('deliberate')} for o in rr.get('outfits', [])]
                r['ремонт_образи'] = [{'номер': o.get('номер'), 'підпис': o.get('підпис'), 'n': len(o.get('знахідки') or []), 'сила': fsum(o.get('знахідки') or []), 'шлюз': gates(o.get('знахідки') or []),
                                       'блок': [b if isinstance(b, str) else json.dumps(b, ensure_ascii=False) for b in (o.get('блокери') or [])], 'key': okey(o), 'правила': [f.get('правило') for f in o.get('знахідки') or []],
                                       'рег': regs(o.get('знахідки') or [])} for o in s.get('образи_кроку') or []]
                rq = s.get('запит') or {}
                try:
                    pj = json.loads(rq.get('текст') or '{}'); r['ремонт_порядок'] = [x['your_outfit']['id'] for x in pj.get('verdict', [])]
                    fm = {}
                    for x in pj.get('verdict', []):
                        for f in x.get('findings') or []:
                            cs = []
                            for stt in f.get('statements') or []:
                                cs.append(stt if isinstance(stt, str) else next(iter(stt)))
                            fm[f.get('id')] = {'codes': cs, 'items': f.get('items'), 'reg': f.get('register'), 'o': x['your_outfit']['id']}
                    r['ремонт_знахідки'] = fm
                    r['ремонт_вхід_ідеї'] = {x['your_outfit']['id']: [i.get('n') for i in x['your_outfit'].get('items') or []] for x in pj.get('verdict', [])}
                    r['ремонт_шоукейс'] = len(pj.get('showcase') or [])
                except Exception as ex: r['ремонт_порядок'] = None; r['ремонт_помилка'] = str(ex)
            r['повнота_відп'] = [{'сира': raw(s.get('відповідь_сира')), 'повернуто': (s.get('розбір_блоків') or {}).get('повернуто_кодом')} for s in cmp_]
            r['повнота'] = [{'спроба': s.get('крок_спроба'), 'числа': s.get('стадія_числа'), 'образи': [(o.get('номер'), len(o.get('блокери') or [])) for o in s.get('образи_кроку') or []]} for s in cmp_]
            if ch:
                s = ch[0]; vb = s.get('вибір') or {}
                rq = s.get('запит') or {}
                order = (rq.get('порядок') or {}).get('образи')
                try: pj = json.loads(rq.get('текст') or '{}')
                except Exception: pj = {}
                pv = pj.get('verdict', [])
                blk = {x['your_outfit']['id']: (not (x.get('structure') or {}).get('ok', True)) for x in pv}
                caps = {x['your_outfit']['id']: x['your_outfit'].get('caption') for x in pv}
                rc = raw(s.get('відповідь_сира')) or {}
                r['вибір'] = {'порядок': order, 'ids_prompt': [x['your_outfit']['id'] for x in pv], 'обрано': vb.get('обрано'), 'названо': vb.get('названо'), 'чому': vb.get('чому'),
                              'прибрано': vb.get('прибрано'), 'прийнято': vb.get('прийнято'), 'знехтувано': vb.get('знехтувано'), 'замінено': vb.get('замінено'), 'чому_відмова': vb.get('чому_відмова'),
                              'помилки': vb.get('помилки'), 'з_блоком': blk, 'підписи': caps, 'сира': rc, 'rules_has_findings': 'remarks_by_code' in pj}
            if ds:
                s = ds[0]; op = s.get('опис') or {}
                r['опис'] = {'фото_не_те': op.get('фото_не_те'), 'фото_не_ті': op.get('фото_не_ті'), 'помилки': op.get('помилки'), 'обрізано': op.get('обрізано'), 'swap': (raw(s.get('відповідь_сира')) or {}).get('swap')}
            r['діагноз'] = e.get('діагноз_руки')
            rows.append(r)
with open(OUT, 'w') as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(len(rows), 'рядків')
