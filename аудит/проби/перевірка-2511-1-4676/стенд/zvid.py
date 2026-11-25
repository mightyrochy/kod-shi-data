import json,sys,os
W='/tmp/r3w'
CASES=[('незастосовне','outputs/candidate/незастосовне'),('бракує-вимірів','outputs/candidate/бракує-вимірів'),('один-вимір','evidence/один-вимір/candidate'),('граничний-розрив','evidence/граничний-розрив/candidate'),('перевірено','outputs/candidate/перевірено')]
def L(p): return json.load(open(p,encoding='utf-8'))
for c,p in CASES:
  print('\n########', c)
  for R,src in (('база','run-base'),('кандидат','run-cand')):
    o=f'{W}/out/{R}/{c}'; ет=L(o+'/етапи.json'); рез=L(o+'/результат.json'); ж=L(o+'/журнал_моделі.json')
    суд=dict(ет['суд']); суд.pop('мс',None)
    print(f'-- {R}: суд==CPython {суд==L(f"{W}/{src}/{p}/суд.json")}; кроки оцінки:',[x['крок'] for x in ет['виклики']],
          '; шар:',[ (z.get('де'),z.get('напрям'),z.get('причина')) for z in ет.get('мова_шару',[])])
    if ет.get('сторож_до_повтору'): print('   сторож до повтору:', json.dumps(ет['сторож_до_повтору'],ensure_ascii=False)[:600])
    for x in ет['виклики']:
      try: a=json.loads(x['відповідь_сира'])
      except Exception: a={'сире':x.get('відповідь_сира','')[:300]}
      print(f'   [{x["крок"]}] verdict={a.get("verdict")} answer={a.get("answer")!r}')
      for w in a.get('works',[]): print('      works', w.get('about'), w.get('items'), (w.get('text') or '')[:220])
      for w in a.get('change',[]): print('      change', w.get('id'), w.get('items'), (w.get('text') or '')[:220])
    к=рез['картка']; print('   картка: вердикт', к.get('вердикт'), '| змінити', len(к.get('змінити') or []), '| не_знаю', len(к.get('не_знаю') or []))
