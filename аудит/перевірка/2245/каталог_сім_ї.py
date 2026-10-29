"""Сім'я речі (`колір_річ.сім_я`) для кожної речі каталогу з lab; argv: тека джерел, файл виводу (json)."""
import sys, os, json; sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])
import фід_каталог as ФК, колір_річ as КР, colorspace as cs
к = ФК.прочитати_каталог(ФК.каталог_на_диску('каталог_повний.xml'), 0)['каталог']
out = {}
for x in к:
    lab = x.get('lab')
    if not lab: continue
    L, C, h = cs.lch(tuple(lab))
    фото = x.get('фото'); фото = фото[0] if isinstance(фото, (list, tuple)) and фото else фото
    out[x['id']] = dict(с=КР.сім_я(tuple(lab)), L=round(L, 1), C=round(C, 1), h=round(h, 1), слово=x.get('колір_назва'),
                        назва=x.get('назва'), фото=фото, тип=x.get('колір_тип'))
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False)
print(len(к), len(out))
