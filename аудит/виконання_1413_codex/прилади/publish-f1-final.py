from pathlib import Path
import json,base64,re,zipfile,io,hashlib,statistics,collections,shutil
src=Path('/workspace/work/f1-results'); dest=Path('/workspace/work/current/аудит/виконання_1413_codex')
summary={}
for side in ['pre42','final']:
 root=src/side; out=dest/side;out.mkdir(exist_ok=True)
 html=(root/'index.html').read_bytes();m=re.search('const МОДУЛІ_ПОКАЗУ = "([A-Za-z0-9+/=]+)"'.encode(),html);assert m
 raw=base64.b64decode(m[1]);z=zipfile.ZipFile(io.BytesIO(raw));pycs=[i for i in z.infolist() if i.filename.endswith('.pyc')]
 http=json.loads((root/'http.json').read_text())
 for pair in http['пари']:
  for visit in pair:
   assert all(r['encodedBodySize']>0 and r['decodedBodySize']>0 for r in visit['ресурси'])
   if visit['стан']=='warm':assert all(r['transferSize']==0 for r in visit['ресурси']) and not visit['http_requests']
 vals=[];events=[]
 for n in [1,2,3]:
  d=json.loads((root/f'assembly-{n}.json').read_text()); vals.append((d['кінець']-d['т0'])/1000);events.append(dict(collections.Counter(x['к'] for x in d['події'])))
  for suffix in ['json','log','-system.json']:
   name=f'assembly-{n}{suffix}' if suffix.startswith('-') else f'assembly-{n}.{suffix}'
   shutil.copy2(root/name,out/name)
 for name in ['http.json','http.log']:shutil.copy2(root/name,out/name)
 summary[side]={'html_bytes':len(html),'html_sha256':hashlib.sha256(html).hexdigest(),'zip_bytes':len(raw),'zip_sha256':hashlib.sha256(raw).hexdigest(),'pyc_files':len(pycs),'pyc_compressed_bytes':sum(i.compress_size for i in pycs),'pyc_uncompressed_bytes':sum(i.file_size for i in pycs),'all_cards_seconds':vals,'median_seconds':statistics.median(vals),'events':events}
 assert events[0]==events[1]==events[2]
shutil.copy2(src/'http-compare.json',dest/'http-compare.json');shutil.copy2(src/'bytecode-probe.log',dest/'bytecode-probe.log')
shots=dest/'final'/'очі-390x844';shots.mkdir(exist_ok=True)
for p in (src/'final'/'shots-1').iterdir():
 if p.suffix in ['.png','.txt']:shutil.copy2(p,shots/p.name)
(dest/'assembly-and-bytes.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
