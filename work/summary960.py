from pathlib import Path
import json,re,hashlib,shutil
root=Path(__file__).resolve().parents[1]; out=root/'аудит/живі_960'
scenes=[]
for d in sorted(out.iterdir()):
    if not d.is_dir() or not (d/'лог.txt').exists(): continue
    log=(d/'лог.txt').read_text(encoding='utf-8')
    calls=[]
    for f in sorted((d/'transport_1').glob('*.json')):
        x=json.loads(f.read_text(encoding='utf-8')); c=x['result'].get('choices',[{}])[0]
        text=c.get('message',{}).get('content',''); parsed=None
        try: parsed=json.loads(text); error=None
        except Exception as e: error=str(e)
        calls.append(dict(file=f.name,id=x['result'].get('id'),model=x.get('model'),seconds=x['seconds'],
            status=x['status'],finish_reason=c.get('finish_reason'),usage=x['result'].get('usage'),
            strict_json=error is None,json_error=error,top_keys=list(parsed) if isinstance(parsed,dict) else None))
    scenes.append(dict(path=d.name,interrupted='environment_attempt' in d.name,
      code=(d/'код.txt').read_text(encoding='utf-8').strip(),http599=log.count('HTTP 599'),
      failures=[s.strip().split('  →')[0] for s in log.splitlines() if s.startswith('  ✗')],
      screenshot_count=len(list((d/'знімки').glob('*.png'))),calls=calls,
      image_loss_lines=[s.strip() for s in log.splitlines() if 'кадрів не дійшло до моделі:' in s]))
result=dict(source_sha='7c90a0093b5d7dc8587a90c541eaf11e23b9a3be',scenes=scenes,independent_acceptance=False,
  studio_log_note='Raw LM Studio API responses retain exact id/usage/finish_reason. Server-log excerpts below match description response ids.',
  remaining=['5201/4623 exact scene inputs/DO missing','ГГ1 selection and concrete paired assignment pending','Independent Astra visual review pending'])
(out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
studio=Path('C:/Users/Admin/.lmstudio/server-logs/2026-10/2026-10-13.1.log').read_text(encoding='utf-8',errors='replace').splitlines()
excerpts=[]
d=out/'04_ж7_мороз_без_відкритого/transport_1'
for number in ['025','026']:
    r=json.loads((d/(number+'.json')).read_text(encoding='utf-8'))
    rid=r['result'].get('id'); indices=[i for i,line in enumerate(studio) if rid and rid in line]
    excerpts.append(f'RAW DESCRIPTION {number}, response id={rid}, server-log matches={len(indices)}')
    for i in indices:
        end=next((j for j in range(i+1,min(i+80,len(studio))) if re.match(r'^\[2026-',studio[j])),min(i+35,len(studio)))
        excerpts.extend(studio[max(0,i-2):end])
(out/'lm_studio_excerpt_3520.log').write_text('\n'.join(excerpts)+'\n',encoding='utf-8')
for f in ['run960.py','transport960.js','check_page960.js','check_payload960.py','baselines960.py']:
    shutil.copy2(root/'work'/f,out/f)
print([(s['path'],s['http599'],len(s['failures']),len(s['calls'])) for s in scenes])
