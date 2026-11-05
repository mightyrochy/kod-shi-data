import hashlib, json, os, re, sys, subprocess
from collections import Counter
from pathlib import Path

repo = Path.cwd()
src = repo/'джерела'
before = Path(os.environ['TEMP'])/'e2-ch1-before'
if sys.argv[1] == 'до':
    before.mkdir(exist_ok=True)
    for name in ('мовний_шар.py','внутрішня_мова.py','міст_вхід.py','фрази_формату.py'):
        data = subprocess.check_output(['git','show','b694ac2d2469b4191978e4e716ac2a912715dd58:джерела/'+name])
        (before/name).write_bytes(data)
sys.path.insert(0, str(src))
if sys.argv[1] == 'до':
    sys.path.insert(0, str(before))
import мовний_шар as M
import міст_вхід as B

records, prompts, counts = {}, {}, Counter()
for p in sorted((repo/'аудит/живі_12/А').rglob('*.txt')):
    text = p.read_text(encoding='utf-8')
    match = re.fullmatch(r'── ПРОМПТ \(\d+ симв\.\) ──\n(.*?)\n\n── ВІДПОВІДЬ \([^\n]*\) ──\n(.*)\n?', text, re.S)
    if not match:
        continue
    prompt, answer = match.groups()
    name = str(p.relative_to(repo))
    if 'мовний_шар_хід_розмови' in p.name:
        records[name] = M.прийняти_розмову(answer)
        obj = json.loads(prompt)
        data = {k: v for k, v in obj.items() if k not in ('task','now')}
        prompts[name] = len(json.dumps(M._ЗП_Р.зібрати(M.РОЗМОВА, data, мова_тексту='Ukrainian'), ensure_ascii=False))
        counts['розмова'] += 1
    elif 'мовний_шар_репліка' in p.name and 'РЕПЛІКА:\n' in prompt:
        data = json.loads(prompt.rsplit('РЕПЛІКА:\n', 1)[1])
        records[name] = M.прийняти_репліку(answer, data)
        prompts[name] = len(M.промпт_репліки(data))
        counts['репліка'] += 1
    elif p.name.endswith('_мовний_шар.txt') and 'ТЕКСТИ:\n' in prompt:
        data = json.loads(prompt.rsplit('ТЕКСТИ:\n', 1)[1])
        if isinstance(data, dict):
            rows = [dict(н=int(k), ключ=k, текст=v.get('текст','') if isinstance(v,dict) else v,
                         **({'виправ':v['виправ']} if isinstance(v,dict) and v.get('виправ') else {})) for k,v in data.items()]
        else:
            rows = [dict(r, ключ=str(r['н'])) for r in data]
        records[name] = M.прийняти(rows, answer)
        prompts[name] = len(M.промпт(rows))
        counts['тексти'] += 1

samples = {
    'плитки': len(M.промпт_розмови({'сценарій':{'нагода':'робота'}})),
    'портрет': len(B.промпт_кольору()),
    'порада': len(M.промпт_поради({'дозволені':['jewelry'], 'вада':next(iter(M.ВАДИ_ПОРАДИ_EN))})),
    **{f'вхід:{k}':len(M.промпт_входу(k, 'Її слова')) for k in ('question','review_items_fix','verdict_comment')},
}
wire = json.dumps(records, ensure_ascii=False, sort_keys=True, default=str)
result = dict(counts=counts, records=records, prompts=prompts, samples=samples,
              digest=hashlib.sha256(wire.encode()).hexdigest())
path = Path(os.environ['TEMP'])/f'e2-replay-{sys.argv[1]}.json'
path.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
print('Відповідей:',len(records),dict(counts),'відбиток:',result['digest'])
print('Промпти:', samples)
