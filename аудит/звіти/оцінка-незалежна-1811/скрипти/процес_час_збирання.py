#!/usr/bin/env python3
"""час_збирання.md: з обміни.jsonl.gz кожної ситуації. Прохід = від початку першого виклику збирання (прозова рука «Put together one
outfit», опис образу «You read the description», каталожні «{"version":"1"…» і «Photo 1»), до кінця останнього виклику, що почався
до першого перекладу вердикту жінки («You are a translator in a styling app»); виклики перекладу вердиктів не рахуються.
Запуск із теки стенд/: python3 час_збирання.py > ../час_збирання.md"""
import gzip, json, glob, os, datetime as D
def т(x): return D.datetime.fromisoformat(x.replace('Z', '+00:00')).timestamp()
print("# Час збирання образів (з запису звернень до моделі)\n")
print("Прохід = від початку першого виклику збирання (прозові руки, опис образу, каталожні руки, вибір фото) до кінця останнього виклику збирання, що почався до першого перекладу вердикту жінки; виклики перекладу вердиктів не рахуються. «Найдовший виклик збирання» — найдовший один виклик у проході; обрив «worker: мовчить» шукано в записі відповідей, консолі сторінки й логу стенда.\n")
print("| ситуація · прохід | виклики збирання | від початку до кінця, с | найдовший один виклик, с | «worker: мовчить» |\n|---|---|---|---|---|")
понад = 0; всього = 0
for ф in sorted(glob.glob('службове/*/обміни.jsonl.gz')):
    с = os.path.basename(os.path.dirname(ф)); кр = []
    for л in gzip.open(ф, 'rt'):
        о = json.loads(л); q = json.loads(о['запит']); m = q['messages'][0]['content']
        з = m if isinstance(m, str) else ' '.join(b.get('text', '') for b in m if isinstance(b, dict))
        п = т(о['час']); кр.append((п, п + float(о['с']), з, о))
    кр.sort(key=lambda x: x[0]); прох = []; тек = None
    мітки = ('{"version":"1"', 'Photo 1', )
    for п, к, з, о in кр:
        верд = 'You are a translator in a styling app' in з[:200]
        збир = з.startswith(мітки) or 'Put together one outfit' in з[:200] or 'You read the description of an outfit' in з[:200]
        if верд:
            тек = None
        elif збир and тек is None:
            тек = []; прох.append(тек); тек.append((п, к, о))
        elif тек is not None:
            тек.append((п, к, о))
    сл = open(os.path.join(os.path.dirname(ф), 'консоль.txt'), encoding='utf-8', errors='replace').read()
    обр = 'так' if ('мовчить' in сл or any('мовчить' in x[2]['відповідь'] for p in прох for x in p)) else 'ні'
    for н, p in enumerate(прох, 1):
        дов = max(x[1] - x[0] for x in p); всього += 1; понад += sum(1 for x in p if x[1] - x[0] > 300)
        print(f"| {с.split('_')[0]} · {н} | {len(p)} | {max(x[1] for x in p) - min(x[0] for x in p):.0f} | {дов:.0f} | {обр} |")
print(f"\nВикликів понад 300 с: {понад}; проходів: {всього}.")
