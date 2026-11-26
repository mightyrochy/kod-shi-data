#!/usr/bin/env python3
"""Стартове завантаження і число інструментів з init-події (доповнення п.1, 26.11).
Вхід: каталог з підкаталогами `<ключ>/NNN.txt` — сторінки list_events (kinds system+assistant), будь-який порядок.
Для кожної сесії: init-події (час, число інструментів у списку `tools`, з них MCP, статуси MCP-серверів) і перший
основний запит моделі (час, input/cache_read/cache_creation). Пише JSON і короткий вивід. Сирих сторінок у репозиторії нема.
Запуск: python3 схеми.py <каталог> <вихід_json>"""
import json,glob,os,sys
def pages(d):
    ev={}
    for f in sorted(glob.glob(f'{d}/*.txt')):
        t=open(f).read()
        try: j=json.loads(t[t.index('{"ccr"'):t.rindex('}')+1])['ccr'].get('data',[])
        except Exception as e: print('ПОГАНИЙ ФАЙЛ',f,e,file=sys.stderr); continue
        for e in j: ev[json.dumps(e,sort_keys=True)[:400]+e['created_at']]=e
    return sorted(ev.values(),key=lambda e:e['created_at'])
def one(d):
    inits=[]; first=None
    for e in pages(d):
        if 'system' in e:
            c=e['system'].get('internal_anthropic_catchall') or {}
            if c.get('subtype')=='init':
                t=c.get('tools') or []
                inits.append(dict(ts=e['created_at'],tools=len(t),mcp=sum(x.startswith('mcp__') for x in t),
                  servers={s['name'][:12]:s['status'] for s in c.get('mcp_servers',[])},skills=len(c.get('skills',[])),model=c.get('model')))
        elif 'assistant' in e and first is None:
            a=e['assistant']; m=(a.get('internal_anthropic_catchall') or {}).get('message') or a.get('message') or {}
            u=m.get('usage'); 
            if u and not a.get('parent_tool_use_id') and not (a.get('internal_anthropic_catchall') or {}).get('parent_tool_use_id'):
                first=dict(ts=e['created_at'],input=u.get('input_tokens',0),cache_read=u.get('cache_read_input_tokens',0),cache_creation=u.get('cache_creation_input_tokens',0))
    return dict(inits=inits,first=first,events_files=len(glob.glob(f'{d}/*.txt')))
if __name__=='__main__':
    root,out=sys.argv[1],sys.argv[2]; res={}
    for d in sorted(glob.glob(f'{root}/*/')):
        k=os.path.basename(d.rstrip('/')); r=one(d); res[k]=r
        f=r['first']; i=r['inits']
        print(k,'init:',[(x['ts'][11:19],x['tools'],x['mcp'],x['servers']) for x in i[:3]],'перший запит:',f)
    json.dump(res,open(out,'w'),ensure_ascii=False,indent=1)
