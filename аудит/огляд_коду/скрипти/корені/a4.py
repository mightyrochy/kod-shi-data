import re,glob,ast,collections as C,sys,json
SP=sys.argv[1]
REF=re.compile(r'рядок \d{3,4}|рядки \d|рядка \d|рядку \d|#\d{3,4}|row \d{3,4}')
SPEC=re.compile(r'тимчасово|поки\b|латк|обхід|окремо для|виняток|особлив|лише для|only for|workaround|hack',re.I)
HIST=re.compile(r'раніше|до правки|було\b|колись|тепер\b|відтепер|\b\d{1,2}\.(09|10)\b|#\d{3,4}|рядок \d{3,4}|рядки \d|рядка \d|рядку \d')
files=sorted(glob.glob('джерела/*.py')+glob.glob('джерела/*.js')+['джерела/показ.html'])
per=C.Counter(); func=C.Counter(); tot=0; nearlogic=0; spec_near=0; rows=[]; comlines=0; histlines=0; codelines=0
def pyfuncs(src):
    try: t=ast.parse(src)
    except Exception: return []
    out=[]
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): out.append((n.lineno,n.end_lineno,n.name))
    return out
JSF=re.compile(r'^\s*(?:async\s+)?function\*?\s+([^\s(]+)|^\s*(?:const|let|var)\s+([^\s=]+)\s*=\s*(?:async\s*)?(?:function|\([^)]*\)\s*=>)')
for f in files:
    src=open(f,encoding='utf-8',errors='replace').read(); L=src.split('\n')
    if f.endswith('.py'):
        fs=pyfuncs(src)
        def owner(i):
            best=None
            for a,b,nm in fs:
                if a<=i<=b and (best is None or a>best[0]): best=(a,nm)
            return best[1] if best else '<модуль>'
    else:
        starts=[(i+1,(m.group(1) or m.group(2))) for i,l in enumerate(L) for m in [JSF.match(l)] if m]
        def owner(i):
            prev=[s for s in starts if s[0]<=i]
            return prev[-1][1] if prev else '<модуль>'
    for i,l in enumerate(L,1):
        s=l.strip()
        iscom = s.startswith('#') if f.endswith('.py') else (s.startswith('//') or s.startswith('/*') or s.startswith('*'))
        # inline comment part
        if f.endswith('.py'):
            m=re.search(r'(?<![\'"\w])#(?!\d)',l) ; comment = l if iscom else (l[m.start():] if m and not iscom else '')
        else:
            m=l.find('//'); comment = l if iscom else (l[m:] if m>=0 and 'http' not in l[max(0,m-6):m] else '')
        if s: codelines+=1
        if iscom: comlines+=1
        if iscom and HIST.search(l): histlines+=1
        txt = comment if comment else ''
        if not REF.search(txt): continue
        for _ in REF.findall(txt):
            tot+=1; per[f]+=1
        ow=owner(i); func[(f,ow)]+=len(REF.findall(txt))
        win=' '.join(L[max(0,i-3):i+3])
        logic=bool(re.search(r'\bif\b|\belif\b|\bin \(|in \{|in \[|==|!=|\?\s|case\s|else\b',' '.join(L[i-1:i+3]) ))
        spec=bool(SPEC.search(win)) or bool(re.search(r"==\s*['\"][^'\"]+['\"]|in\s*[\(\{\[]\s*['\"]",' '.join(L[i-1:i+3])))
        nearlogic+=logic; spec_near+=spec
        rows.append((f,i,ow,logic,spec,s[:160]))
print('files',len(files),'nonblank lines',codelines,'comment lines',comlines,'history-ish comment lines',histlines)
print('refs total',tot,'lines with refs',len(rows),'near logic',nearlogic,'special-case pattern',spec_near)
print('PER FILE');[print(c,f) for f,c in per.most_common(15)]
print('TOP15 FUNCS');[print(c,f.split('/')[-1]+':'+fn) for (f,fn),c in func.most_common(15)]
json.dump(rows,open(SP+'/refs_rows.json','w'),ensure_ascii=False)
