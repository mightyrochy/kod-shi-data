"""Назва точки на стику сімей (`palettes.назва`, #3882): світлі кремові клітинки ґратки основ. argv: корінь_джерел"""
import sys; sys.path.insert(0, sys.argv[1])
import palettes as П, colorspace as cs, колір_тон as КТ
for h in ('#dbd8be', '#dcd9b0'):
    lab = cs.hx(h)
    print(h, [round(x, 1) for x in lab], П.назва(lab), [(с, round(в, 2)) for с, в in КТ.сім_ї_кольору(tuple(lab))[:2]])
