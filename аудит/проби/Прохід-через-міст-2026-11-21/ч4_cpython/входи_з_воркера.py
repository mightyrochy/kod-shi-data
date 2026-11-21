"""Воркер-журнал повтору (`відтворення.js` → воркер.jsonl) → входи `знімок_мосту.py` (ім, async, вхід) і знімок
Pyodide сторінки в форматі `знімок_мосту.py` (н, ім, результат | помилка) для `--діф`.
  python3 -I входи_з_воркера.py <воркер.jsonl> <входи.jsonl> <pyodide_сторінки.jsonl>"""
import hashlib, json, sys

воркер, входи_ш, знімок_ш = sys.argv[1:4]
рядки = [json.loads(р) for р in open(воркер, encoding='utf-8') if р.strip()]
туди = [р for р in рядки if р['б'] == 'туди' and р['тип'] == 'виклик']
звідти = {р['н']: р for р in рядки if р['б'] == 'звідти' and р['тип'] == 'відповідь'}
входи = [json.dumps({'ім': р['ім'], 'async': bool(р.get('асинх')), 'вхід': р['вхід'], 'рання': bool(р.get('рання'))},
                    ensure_ascii=False) for р in туди]
текст = '\n'.join(входи) + '\n'
open(входи_ш, 'w', encoding='utf-8').write(текст)


def канон(о):
    return json.dumps(о, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


знімок = [канон({'формат': 1, 'входи_sha256': hashlib.sha256(текст.encode('utf-8')).hexdigest(), 'викликів': len(туди)})]
for н, р in enumerate(туди):
    в = звідти.get(р['н'])
    запис = {'н': н, 'ім': р['ім']}
    if в is None:
        запис['помилка'] = 'нема відповіді воркера'
    elif в.get('помилка') is not None:
        запис['помилка'] = ([x for x in str(в['помилка']).splitlines() if x.strip()] or [''])[-1][:300]
    else:
        вих = в['вих']
        try:
            вих = json.loads(вих)
        except (TypeError, ValueError):
            pass
        if isinstance(вих, dict) and isinstance(вих.get('мс'), (int, float)):
            вих.pop('мс')
        запис['результат'] = вих
    знімок.append(канон(запис))
open(знімок_ш, 'w', encoding='utf-8').write('\n'.join(знімок) + '\n')
print(json.dumps({'викликів': len(туди), 'з_відповіддю': sum(1 for р in туди if р['н'] in звідти),
                  'асинх': sum(1 for р in туди if р.get('асинх')), 'рання': sum(1 for р in туди if р.get('рання'))},
                 ensure_ascii=False))
