# Перебудова руки.md із записів (verdykty-*.json: позиція → рука; службове/<с>/руки.jsonl: діагноз руки 2).
# Запуск: python3 -I руки_з_вердиктів.py <тека результату>   (наприклад аудит/проби/Живий-через-міст)
import json, glob, os, sys
тека = sys.argv[1]
рядки = []
for вф in sorted(glob.glob(os.path.join(тека, 'с*_*', 'verdykty-*.json'))):
    с = os.path.basename(os.path.dirname(вф))
    д = json.load(open(вф, encoding='utf-8'))
    діаг = {}
    ф = os.path.join(тека, 'стенд', 'службове', с, 'руки.jsonl')
    if os.path.exists(ф):
        for л in open(ф, encoding='utf-8'):
            р = json.loads(л); діаг[р['прохід']] = р.get('поломка_руки_2')
    for н, пр in enumerate(д['прогони'], 1):
        for в in sorted(пр['вердикти'], key=lambda в: int(в['позиція'])):
            рядки.append(f"- {с} · {н} · {в['позиція']} → рука {в['рука']}; " + (json.dumps(діаг.get(н), ensure_ascii=False) if в['рука'] == '2' else ''))
open(os.path.join(тека, 'руки.md'), 'w', encoding='utf-8').write('\n\n'.join(рядки) + '\n')
print(len(рядки), 'рядків')
