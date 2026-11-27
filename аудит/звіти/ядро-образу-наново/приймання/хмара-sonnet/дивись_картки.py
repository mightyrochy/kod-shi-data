import json,sys
p=sys.argv[1]
рядки=[json.loads(l) for l in open(p+'/руки.jsonl',encoding='utf8')]
з=рядки[-1]
print('кроки:',[r['що'][:40] for r in рядки])
print('статус:',з['статус'][:200])
print('паспорт:',json.dumps(з['паспорт'],ensure_ascii=False)[:700])
for м in з['чат']: print('ЧАТ',м['хто'],':',м['текст'][:350])
for i,к in enumerate(з['картки']):
    print(f'--картка {i+1} рука={к["рука"]} вирок={к["вирок"]} дія={str(к["дія"])[:90]} заміни={len(к["заміни"])}')
    print('  речі:',json.dumps(к['речі'],ensure_ascii=False)[:300])
    print('  опис:',str(к['опис'])[:500])
