import json,sys,os,re,glob
def split(fn):
    t=open(fn,encoding='utf8').read()
    m=re.match(r'── ПРОМПТ \((\d+) симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \(([^)]*)\) ──\n(.*)\n$',t,re.S)
    return m.group(2),m.group(3),m.group(4)
def sz(x): return len(json.dumps(x,ensure_ascii=False))
for fn in sorted(glob.glob(sys.argv[1]+'/*.txt')):
    p,meta,r=split(fn)
    name=os.path.basename(fn)
    try:
        o=json.loads(p)
        parts=' '.join(f"{k}:{sz(v)}" for k,v in o.items())
        if 'task' in o and isinstance(o['task'],dict):
            parts+=' | task.'+' '.join(f"{k}:{sz(v)}" for k,v in o['task'].items())
        if 'завдання' in o and isinstance(o['завдання'],dict):
            parts+=' | завдання.'+' '.join(f"{k}:{sz(v)}" for k,v in o['завдання'].items())
    except Exception as e:
        parts='NOT-JSON first80='+p[:80].replace('\n',' ')
    print(name[:45].ljust(45), len(p), '|', parts[:600])
