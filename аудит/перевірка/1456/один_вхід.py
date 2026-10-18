import gzip,json,os,sys
sys.path.insert(0,'/workspace/work/qa-1456/джерела'); os.chdir('/workspace/work/qa-1456/джерела')
import bridge
входи=[json.loads(р) for р in gzip.open('/workspace/work/qa1456-evidence/входи.jsonl.gz','rt')]
запит=next(в for в in входи if в['ім']=='запити')
вхід=json.loads(запит['вхід'])
р=json.loads(bridge.виклик(запит['ім'],вхід))
print(json.dumps({'ім':запит['ім'],'каталог':вхід.get('каталог'),'існує':os.path.exists(вхід['каталог']),'результат':р},ensure_ascii=False))
