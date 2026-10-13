# -*- coding: utf-8 -*-
"""Проба РВ-5 · гомогліфи після С-56, за буквою СТАНДАРТ_КОДУ §2 п.4: латинська
літера з набору `a c e o p x y i k b` ПОРУЧ із кириличною в одному ідентифікаторі.
.py — токени NAME (рядки й коментарі не рахуються); .js/.html — слова поза лапками.
Окремо — лічба ЗМІШАНИХ імен (будь-яка латиниця поруч із кирилицею, п.3), які
С-56 свідомо не чіпала.

Прогін:  cd джерела && python3 ../аудит/проби/рв5_гомогліфи.py
"""
import collections, io, os, re, tokenize
ДЖ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "джерела"))
os.chdir(ДЖ)
КИР = "а-яіїєґА-ЯІЇЄҐ"
ГОМ = re.compile(r"[%s][acepxyikb]|[acepxyikb][%s]" % (КИР, КИР))
ЗМІШ = re.compile(r"[%s][A-Za-z]|[A-Za-z][%s]" % (КИР, КИР))
ІДЕН = re.compile(r"[A-Za-z_%s][A-Za-z0-9_%s]*" % (КИР, КИР))

def імена(шлях):
    if шлях.endswith(".py"):
        for tok in tokenize.generate_tokens(io.StringIO(open(шлях, encoding="utf-8").read()).readline):
            if tok.type == tokenize.NAME:
                yield tok.string, tok.start[0]
    else:
        for n, рядок in enumerate(open(шлях, encoding="utf-8"), 1):
            for m in ІДЕН.finditer(re.sub(r'"[^"]*"|\'[^\']*\'|`[^`]*`', "", рядок)):
                yield m.group(), n

гом, зміш = collections.defaultdict(set), collections.defaultdict(set)
for кор, теки, файли in os.walk("."):
    if "аудит" in кор or "node_modules" in кор:
        continue
    for ф in файли:
        if not ф.endswith((".py", ".js", ".html")):
            continue
        ш = os.path.join(кор, ф)
        for ім, n in імена(ш):
            if ЗМІШ.search(ім):
                зміш[ім].add(ш)
            if ГОМ.search(ім):
                гом[ім].add("%s:%d" % (ш, n))

print("гомогліфи за п.4 (набір a c e o p x y i k b): %d імен" % len(гом))
for k in sorted(гом):
    print("   %-12s %s" % (k, ", ".join(sorted(гом[k])[:3])))
ядро = {k for k, v in зміш.items() if any(not ш.startswith(("./прилади", "./проби", "./лабораторія")) for ш in v)}
print("змішаних імен (п.3) усього: %d · поза прилади/проби/лабораторія: %d" % (len(зміш), len(ядро)))
print("   " + ", ".join(sorted(ядро)))
