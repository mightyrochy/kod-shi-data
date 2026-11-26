import json,sys,os
for D in sys.argv[1:]:
  s=json.load(open(D+'/стан.json')); об=[json.loads(l) for l in open(D+'/обміни.jsonl')]
  print('==',D,'| успіх',s['успіх'],'| статус',s['статус'],'| карток_dom',s['карток_dom'],'| обмінів',len(об),'|',[o['тип'][:14] for o in об if not o['тип'].startswith('мовний')])
  for d in s['діагноз'] or []: print('  діагноз', d[:400])
  for р in (s.get('ядро') or {}).get('звіт',[]):
    if р.get('рука')==1 and 'заява' in р and р['заява'] in('pool_coverage',): print('  пул', р['взято'], р['знято'])
    elif р.get('рука')==1: print('  ', json.dumps(р,ensure_ascii=False)[:260])
