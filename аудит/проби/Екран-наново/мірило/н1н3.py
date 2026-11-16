"""н1н3.py — мірило Н1 і Н3 на записах другого живого прогону: що дія коментаря вердикту поклала в паспорт і «не ця».
Запуск із теки аудит/проби/живий-як-людина-2: python3 н1н3.py"""
import json, glob, sys
def ходити(о, шлях=''):
    if isinstance(о, dict):
        for к, в in о.items(): yield from ходити(в, шлях + '/' + str(к))
    elif isinstance(о, list):
        for і, в in enumerate(о): yield from ходити(в, шлях + '/' + str(і))
    else: yield шлях, о
разом = {'вердиктів': 0, 'зі_словами': 0, 'без_вдягнеш': 0, 'дія_є': 0, 'дія_не_ця': 0, 'дія_додано': 0, 'без_вдягнеш_і_дія': 0}
for f in sorted(glob.glob('с*_*/verdykty*.json')):
    d = json.load(open(f, encoding='utf8'))
    сц = f.split('/')[0][:2]
    for п in d['прогони']:
        for з in (п.get('вердикти') or п.get('записи') or []):
            if з.get('рука_впала') or з.get('запис_автоматичний'): continue
            разом['вердиктів'] += 1
            if not (з.get('коментар') or '').strip(): continue
            разом['зі_словами'] += 1
            безв = not з.get('вердикт_людини'); разом['без_вдягнеш'] += безв
            кд = з.get('коментар_дія')
            if кд:
                разом['дія_є'] += 1; разом['дія_не_ця'] += bool(кд.get('не_ця')); разом['дія_додано'] += bool(кд.get('додано'))
                if безв and (кд.get('не_ця') or кд.get('додано')): разом['без_вдягнеш_і_дія'] += 1
            if 'верхній_шар' in json.dumps(кд or {}, ensure_ascii=False) or '-v' in sys.argv:
                print(сц, 'рука', з.get('рука'), '| вдягнеш:', repr(з.get('вердикт_людини')), '| слова:', (з.get('коментар') or '')[:90].replace('\n', ' '),
                      '\n    дія:', json.dumps(кд, ensure_ascii=False)[:500])
    for шл, в in ходити(d):
        if isinstance(в, str) and в == 'верхній_шар' and ('вето' in шл or 'межі' in шл or 'додано' in шл): print('  ключ у даних:', сц, шл[-110:])
print(json.dumps(разом, ensure_ascii=False))
