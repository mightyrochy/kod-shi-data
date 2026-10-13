# -*- coding: utf-8 -*-
import sys, os, json, re, inspect, traceback, glob, collections, random
sys.path.insert(0, '.')
def sec(t): print("\n##", t)
def sig(f):
    try: return str(inspect.signature(f))
    except Exception as e: return '?'
def run(name, fn):
    try: fn()
    except Exception as e:
        print(f"  !! {name}: {type(e).__name__}: {str(e)[:220]}")
        tb = traceback.format_exc().splitlines()[-3:-1]; print("     ", ' | '.join(l.strip()[:120] for l in tb))

import colorspace as cs, bridge as B, fit as ПС, hypergraph as HG, silhouette as SL, outfit as O, pipeline as PL
import personal_palette as PP, palettes as PLS, palette as PAL, coordination as CO, accessory as AC, outer as OU, face_contrast as FC, bases as BS, areas as AR, feed as FD, composer as KM

sec("P08 H/X межа")
def p08():
    T = ПС.тіло(168, dict(плечі=96, груди=92, талія=76, стегна=98))
    z = ПС.зони(T) if 'зони' in dir(ПС) else None
    print("  fit.зони sig", sig(ПС.зони), "→", (z.get('ярлик') if isinstance(z, dict) else z) if z is not None else None)
    pr = HG.простір(T)
    print("  простір: живих", pr.get('живих'), "блокованих", pr.get('блокованих'), "крої", {k: len(v) for k, v in (pr.get('крої') or {}).items()}, "порожньо:", str(pr.get('порожньо'))[:160])
    print("  ЦІЛЬ_ЛІТЕРИ keys:", list(getattr(HG, 'ЦІЛЬ_ЛІТЕРИ', {}).keys()))
    T2 = ПС.тіло(168, dict(плечі=98, груди=92, талія=72, стегна=100)); z2 = ПС.зони(T2)
    print("  контроль (98/92/72/100):", (z2.get('ярлик') if isinstance(z2, dict) else z2), "живих", HG.простір(T2).get('живих'))
run("P08", p08)

sec("P12 _без_ід + читачі полів")
def p12():
    s = "вузол напруги — «сукня» (0.50, 1 ребро: K-WEA-01)"
    print("  _без_ід:", repr(B._без_ід(s)))
    print("  _без_ід_рядків:", repr(B._без_ід_рядків(s)))
run("P12", p12)

sec("P17 31 ID: форми емісії (запис vs _зн/dict)")
def p17():
    ids = "K-CHN-01 K-CLR-01 K-CLR-03 K-CLR-04 K-COL-03 K-COMP-02 K-CON-01 K-CRA-11 K-ECHO-01 K-EYE-02 K-IO-03 K-IO-04 K-IO-05 K-KOH-03 K-KOH-07 K-KOH-09 K-LNG-04 K-P0-01 K-PRC-01 K-SIL-07 K-SIZ-01 K-SYS-08 K-SYS-09 K-VAR-01 K-WEA-04 R-FEED-02 R-FEED-06 R-PC-03 R-PC-09 R-PRN-07 R-SSC-01".split()
    files = [f for f in glob.glob('*.py') if not f.startswith(('gate_','audit_','measure_','мутанти','гейти','відбиток','правила','зведення','звірка','проба','run_','pair_','стенд','траса','status','корпус','rule_genus','аудит_'))]
    src = {f: open(f, encoding='utf-8').read().splitlines() for f in files}
    for i in ids:
        zn = zap = dct = 0; where = set()
        for f, lines in src.items():
            for ln in lines:
                if i not in ln or ln.strip().startswith('#'): continue
                if '_зн(' in ln: zn += 1; where.add(f)
                elif 'запис(' in ln or 'слід' in ln or 'trace' in ln: zap += 1; where.add(f)
                elif 'правило' in ln and ('dict(' in ln or '"правило"' in ln or 'правило=' in ln): dct += 1; where.add(f)
        print(f"  {i:11s} _зн={zn} dict={dct} запис={zap}  {sorted(where)}")
run("P17", p17)

sec("P19 регулярки ID у приладах")
def p19():
    tests = ['K-COL-CONF', 'K-COL-JOIN', 'R-LNG-UA', 'K-COL-06-T', 'K-SYS-07a', 'P-PRT-01', 'K-KOH-05']
    for f in ['відбиток.py', 'правила.py', 'зведення.py', 'gate_reach.py', 'корпус.py', 'rule_genus.py', 'brief.py', 'outfit.py', 'language_gate.py']:
        for n, ln in enumerate(open(f, encoding='utf-8'), 1):
            m = re.search(r're\.compile\((r?["\'].*?["\'])', ln)
            if m and ('K' in m.group(1) or 'ID' in ln.upper() and '-' in m.group(1)):
                try:
                    pat = eval(m.group(1)); rx = re.compile(pat)
                    hits = [t for t in tests if rx.search(t)]
                    print(f"  {f}:{n} {pat[:60]!r} → ловить {hits}")
                except Exception as e: print(f"  {f}:{n} (не вдалося eval) {ln.strip()[:100]}")
run("P19", p19)

sec("P20 поза корпусом: outfit.ПОЗА_КОРПУСОМ проти корпусу")
def p20():
    corp = {}
    for f in glob.glob('тема-*.md') + glob.glob('topic-7*.md'):
        corp[f] = open(f, encoding='utf-8').read()
    pk = sorted(getattr(O, 'ПОЗА_КОРПУСОМ', []))
    print("  ПОЗА_КОРПУСОМ:", len(pk))
    for i in pk + ['K-CUT-00', 'K-SYS-08', 'K-SYS-09', 'K-COL-CONF', 'R-LNG-UA', 'K-HAIR-01', 'K-REG-07', 'P-PRT-01']:
        ment = {f[:12]: c.count(i) for f, c in corp.items() if i in c}
        defn = any(re.search(r'\*\*' + re.escape(i) + r'[.:\s\*]', c) for c in corp.values())
        tag = 'ПОЗА' if i in pk else 'не в списку'
        print(f"  {i:11s} {tag:12s} згадок={sum(ment.values()):3d} означення={'так' if defn else 'ні '} {ment}")
run("P20", p20)

sec("P22 ВИМКНЕНІ_СЛОВА")
def p22():
    print("  ВИМКНЕНІ_ПРАВИЛА:", getattr(PL, 'ВИМКНЕНІ_ПРАВИЛА', None))
    rx = getattr(PL, '_ВИМКНЕНІ_СЛОВА', None); print("  _ВИМКНЕНІ_СЛОВА:", getattr(rx, 'pattern', rx))
    fn = [n for n in dir(PL) if 'вимкн' in n.lower()]; print("  функції:", fn)
    words = ['припуск', 'прилягання', 'тісн', 'ковзанн']
    for f in ['silhouette.py', 'fit.py', 'outfit.py', 'outer.py', 'accessory.py']:
        hits = [(n, ln.strip()[:110]) for n, ln in enumerate(open(f, encoding='utf-8'), 1) if any(w in ln for w in words) and ('суть' in ln or '"' in ln) and not ln.strip().startswith('#')]
        print(f"  {f}: {len(hits)} рядків із цими словами у рядкових літералах; напр. {hits[:3]}")
run("P22", p22)

sec("P28 skin_pos")
def p28():
    print("  sig skin_pos", sig(cs.skin_pos))
    lab = cs.hx('#deb295')
    for prot in (None, 'uncontrolled'):
        try:
            random.seed(1)
            r = cs.skin_pos(lab, protocol=prot) if 'protocol' in sig(cs.skin_pos) else cs.skin_pos(lab)
            keys = {k: r[k] for k in r if 'ITA' in k or 'band' in k or 'смуга' in k}
            print(f"  protocol={prot}: {json.dumps(keys, ensure_ascii=False, default=str)[:300]}")
        except Exception as e: print("  ", prot, type(e).__name__, str(e)[:120])
run("P28", p28)

sec("P29 personal_palette серіалізація / hex / дуги")
def p29():
    F = cs.features(cs.hx('#deb295'), cs.hx('#f1dbaa'), cs.hx('#759087'))
    P = PP.палітра(F)
    try: json.dumps(P, ensure_ascii=False); print("  json.dumps(палітра): OK")
    except Exception as e: print("  json.dumps(палітра): ПАДАЄ:", type(e).__name__, str(e)[:100])
    print("  hex у рисах:", {k: (v.get('hex') if isinstance(v, dict) else None) for k, v in F.items() if isinstance(v, dict) and 'L' in v})
    S = getattr(PLS, 'СІМ_Ї', None) or getattr(PLS, "СІМ'Ї", None)
    if S:
        arcs = []
        for nm, v in S.items():
            for t in ('тепла', 'холодна'):
                a = v.get(t) if isinstance(v, dict) else None
                if a: arcs.append((nm, t, tuple(a)))
        ov = [(a, b) for a in arcs for b in arcs if a < b and a[2][0] < b[2][1] and b[2][0] < a[2][1]]
        print("  дуг", len(arcs), "перекриттів", len(ov), ov[:6])
run("P29", p29)

sec("P30 координація у вершині; відстань")
def p30():
    print("  sig координація", sig(CO.координація))
    src = open('coordination.py', encoding='utf-8').read()
    print("  d_ok у coordination:", src.count('d_ok('), "| cs.d_ok:", src.count('cs.d_ok'), "| власна:", 'def d_ok' in src or 'def _d_ok' in src)
    E = [dict(річ='a', слот='верх', lab=cs.hx('#3a5f8a')), dict(річ='b', слот='низ', lab=cs.hx('#8a6f3a')), dict(річ='c', слот='взуття', lab=cs.hx('#5a3a8a'))]
    my = CO.середня_близькість(E)
    m = my['d_ok'] if isinstance(my, dict) else my
    набір = [m - 0.05, m - 0.02, m + 0.02, m + 0.05]
    r = CO.координація(E, набір_кандидатів=набір)
    print("  моя", round(float(m), 4), "→ ранг", r.get('ранг'), "оцінка", r.get('оцінка'), "сила_нп", r.get('сила_нп'), "суть:", str(r.get('суть'))[:140])
run("P30", p30)

sec("P31 K-VAR-01 / K-COMP-02 / _портфель")
def p31():
    for f in ['composer.py', 'pipeline.py', 'bridge.py']:
        s = open(f, encoding='utf-8').read()
        print(f"  {f}: _портфель={s.count('_портфель')} K-VAR-01={s.count('K-VAR-01')} K-COMP-02={s.count('K-COMP-02')} ПОЛЮСИ_ОБРАЗУ={s.count('ПОЛЮСИ_ОБРАЗУ')}")
    c = ''.join(open(f, encoding='utf-8').read() for f in glob.glob('тема-4*.md'))
    print("  корпус тема-4 згадує composer._портфель:", '_портфель' in c, "| образ_коду:", 'образ_коду' in c)
run("P31", p31)

sec("P32 accessory відра + outer.СОЛЬОВРАЗЛИВІ")
def p32():
    T = ПС.тіло(168, dict(плечі=98, груди=92, талія=72, стегна=100), аксесуарні={'довжина_стопи_мм': 245, "зап'ястя_см": 16.0, 'голова_см': 56})
    речі = [dict(id='ш1', слот='взуття', тип='кеди', устілка_см=28.0, hex='#333333', lab=cs.hx('#333333')),
            dict(id='г1', слот='годинник', lug_мм=53, hex='#888888', lab=cs.hx('#888888'))]
    print("  sig перевірити", sig(AC.перевірити)[:120])
    r = AC.перевірити(T, речі, темп_c=18, опади='немає')
    def ids(k): return sorted({z.get('правило') for z in (r.get(k) or []) if isinstance(z, dict)})
    for k in ('ворота', 'преференції', 'питання', 'без_відповіді', 'без_входу'):
        print(f"  {k}: {ids(k) if k != 'без_входу' else (r.get(k) or [])[:12]}")
    print("  лишились:", [x.get('id') for x in (r.get('лишились') or [])])
    вр = AC.ворота_розміру(T, речі) if 'ворота_розміру' in dir(AC) else None
    if вр is not None:
        зн = вр[0] if isinstance(вр, tuple) else вр.get('знахідки') if isinstance(вр, dict) else вр
        print("  ворота_розміру прямо:", [(z.get('правило'), z.get('сила'), z.get('блокує')) for z in (зн or []) if isinstance(z, dict)][:6])
    print("  СОЛЬОВРАЗЛИВІ:", getattr(OU, 'СОЛЬОВРАЗЛИВІ', None))
    print("  sig догляд", sig(OU.догляд)[:120])
    for mat in ('замша', 'замш', 'замшеве пальто'):
        try:
            r2 = OU.догляд([dict(id='п', слот='верхній_шар', матеріал=mat, тип_верхнього='пальто')], реагенти=True)
            зн = r2 if isinstance(r2, list) else r2.get('знахідки', r2)
            print(f"   матеріал={mat!r}: {[z.get('правило') for z in зн if isinstance(z, dict)]}")
        except Exception as e: print(f"   матеріал={mat!r}: {type(e).__name__} {str(e)[:100]}")
run("P32", p32)

sec("P36 K-FIT-03 литка")
def p36():
    об = dict(плечі=98, груди=92, талія=72, стегна=100)
    for extra in (None, {'коліно': 35, 'литка': 36, 'щиколотка': 22}):
        T = ПС.тіло(168, об, рівні_см=None, аксесуарні=None) if extra is None else ПС.тіло(168, dict(об, **extra))
        prof = T['профіль']
        w = {nm: round(wd, 2) for nm, y, wd in prof if nm in ('стегна', 'коліно', 'литка')}
        r = ПС.край_проти_локального(prof, 33.6)
        print("  обхвати ноги" + (" НІ" if extra is None else " ТАК"), w, "→", {k: r.get(k) for k in ('на_максимумі', 'близькість', 'локальний') if isinstance(r, dict) and k in r} if isinstance(r, dict) else r)
    print("  екран показ.html поля мірок:", re.findall(r'id="мр-[^"]+"', open('показ.html', encoding='utf-8').read()))
run("P36", p36)

sec("P37 K-KOH-05 регістри / чеклісти")
def p37():
    F = cs.features(cs.hx('#deb295'), cs.hx('#f1dbaa'), cs.hx('#759087'))
    речі = [dict(id='ф', слот='верх', hex='#ffffff', тип='футболка', площа=0.3, джерело_площі='геометрія'),
            dict(id='д', слот='низ', hex='#2b3a67', тип='джинси', площа=0.5, джерело_площі='геометрія'),
            dict(id='к', слот='взуття', hex='#eeeeee', тип='кеди', площа=0.2, джерело_площі='геометрія')]
    print("  sig review має дрес_код:", 'дрес_код' in sig(O.review))
    for код in ('cocktail', 'business_casual', 'casual'):
        r = O.review(F, речі, дрес_код=код)
        rows = [(z.get('сила'), z.get('регістр'), z.get('блокує')) for st in r['стани'].values() for z in st['знахідки'] if z.get('правило') == 'K-KOH-05']
        print(f"   {код}: K-KOH-05 рядків {len(rows)} → {rows}")
    r = O.review(F, речі, дрес_код='business_casual')
    ch = O.чеклісти([z for st in r['стани'].values() for z in st['знахідки']], list(r['стани'].values())[0]['елементи'])
    def cnt(lst): return collections.Counter(p.get('стан') or p.get('статус') or str(p)[:10] for p in lst) if isinstance(lst, list) else str(lst)[:120]
    print("  чеклісти keys:", list(ch.keys()) if isinstance(ch, dict) else type(ch))
    for k, v in (ch.items() if isinstance(ch, dict) else []):
        if isinstance(v, (list, dict)): print("   ", k, cnt(v) if isinstance(v, list) else {kk: str(vv)[:60] for kk, vv in list(v.items())[:6]})
run("P37", p37)

sec("P38 важіль_макіяжу / bases._тепло")
def p38():
    print("  sig важіль_макіяжу", sig(FC.важіль_макіяжу))
    for hx in ('#d9a89a', '#5a1020'):
        try: print("  ", hx, FC.важіль_макіяжу(59.5, cs.hx(hx)))
        except Exception as e:
            try: print("  ", hx, FC.важіль_макіяжу(59.5, hx))
            except Exception as e2: print("  ", hx, type(e2).__name__, str(e2)[:100])
    print("  sig bases.ранг", sig(BS.ранг)[:160])
    F = cs.features(cs.hx('#c9b183'), cs.hx('#6b4b2e'), cs.hx('#759087'))
    print("  тепло_клас шкіри:", F.get('шкіра', {}).get('тепло_клас'), "вісь_знак_придатний:", F.get('шкіра', {}).get('вісь_знак_придатний'), "тепло_сила:", F.get('шкіра', {}).get('тепло_сила'))
    outs = {}
    for sz in (None, dict(метал='золото', білий='теплий', нейтралі='теплі'), dict(метал='срібло', білий='холодний', нейтралі='холодні')):
        try:
            r = BS.ранг(F, самозвіт=sz) if 'самозвіт' in sig(BS.ранг) else BS.ранг(F)
            top = [x.get('ключ') or x.get('назва') for x in (r if isinstance(r, list) else r.get('ранг') or r.get('основи') or [])][:8]
            outs[str(sz)[:30]] = top
        except Exception as e: outs[str(sz)[:30]] = f"{type(e).__name__}: {str(e)[:80]}"
    for k, v in outs.items(): print("   самозвіт", k, "→", v)
run("P38", p38)

sec("P39 волосся два пасма")
def p39():
    d = {'шкіра': '#deb295', 'волосся': ['#6b4b2e', '#b4b4b4'], 'очі': '#759087'}
    F = B._features(d)
    print("  риси:", [k for k in F if isinstance(F.get(k), dict) and 'L' in F[k]])
    v2 = F.get('волосся_2', {}); print("  волосся_2:", {k: v2.get(k) for k in ('C', 'h', 'warmth', 'тон_визначений')})
    r = PAL.розвилка_специфікацій(F, ['верх', 'низ', 'взуття', 'сумка'])
    print("  розвилка гілок:", len(r.get('розвилка') or []))
    print("  тест на два пасма у гейти_нові:", sum(1 for ln in open('гейти_нові.py', encoding='utf-8') if 'b4b4b4' in ln or 'пасм' in ln or 'сивин' in ln))
run("P39", p39)

sec("P40 жниварка")
def p40():
    import ast
    root = os.path.join('..', 'zhnyvarka') if os.path.isdir(os.path.join('..', 'zhnyvarka')) else '/home/user/kod-shi-src/zhnyvarka'
    files = sorted(glob.glob(os.path.join(root, '*.py')))
    alls = {f: open(f, encoding='utf-8').read() for f in files}
    for f, s in alls.items():
        t = ast.parse(s); defs = [n.name for n in ast.walk(t) if isinstance(n, ast.FunctionDef)]
        dead = [d for d in defs if sum(x.count(d) for x in alls.values()) <= 1]
        secrets = re.findall(r'(?i)(api[_-]?key|token|secret|password)\s*[=:]\s*["\'][^"\']{6,}', s)
        bare = len(re.findall(r'except\s*:', s)); broad = s.count('except Exception')
        print("  %s: def=%d без згадок=%d %s секрети=%d except-broad=%d bare=%d" % (os.path.basename(f), len(defs), len(dead), dead[:8], len(secrets), broad, bare))
    fs = open('feed.py', encoding='utf-8').read()
    shared = [n for n in ('слот', 'тип', 'колір', 'силует', 'довжина') if f'def {n}' in fs and any(f'def {n}' in s for s in alls.values())]
    print("  однойменні def у feed і жниварці:", shared)
run("P40", p40)
print("\n## DONE")
