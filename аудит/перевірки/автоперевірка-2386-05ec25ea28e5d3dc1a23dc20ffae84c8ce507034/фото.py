import collections, gzip, json, re, subprocess, sys, urllib.request, urllib.error
from pathlib import Path
sys.stdout.reconfigure(encoding='utf8')
def load(ref): return [json.loads(x) for x in gzip.decompress(subprocess.check_output(['git','show',ref+':каталог_записи_v1.jsonl.gz'])).splitlines()][1:]
old=load('560fa388e75fe10abe27145644d12d1be2266ab5'); new=load('05ec25ea28e5d3dc1a23dc20ffae84c8ce507034')
def bad(rows): return [r for r in rows if r['адреса'].startswith('https://25union.com.ua/') and any('/katalog/' in u and '/image/cache/' in u for u in r['кадри'])]
print('25union з /katalog/…/image/cache у URL фото: ДО',len(bad(old)),'ПІСЛЯ',len(bad(new)))
r=bad(new)[0]; photo=next(u for u in r['кадри'] if '/katalog/' in u and '/image/cache/' in u)
correct='https://25union.com.ua/image/cache/'+photo.split('/image/cache/',1)[1]
for url in [r['адреса'],photo,correct]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as f:
            body=f.read(); print('GET',url,'→',f.status,f.headers.get('Content-Type'),'байт',len(body))
            if url==r['адреса']:
                html=body.decode('utf8','replace'); print('base:',re.findall(r'<base[^>]+>',html,re.I)[:2])
    except Exception as e: print('GET',url,'→',type(e).__name__,str(e))
