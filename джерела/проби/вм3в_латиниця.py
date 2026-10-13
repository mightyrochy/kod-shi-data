# -*- coding: utf-8 -*-
"""ВМ-3в: латинські обривки в текстах карток стенда. Запуск: python вм3в_латиниця.py <картки.txt>…
Рахує слова, що жінка не мусить бачити: з літерами двох абеток («spідниця»), дефісні з латинською
частиною довшою за літеру («structured-форма») і чисті латинські від трьох літер. Законні: «V-подібний»,
«den», скорочення з великих до чотирьох, hex з шести знаків, а також слова рядків речей (назва, крамниця —
рядок із «₴» і рядок перед ним). Друкує факт: файл · слів латиницею · рядки з прикладами."""
import re
import sys
sys.stdout.reconfigure(encoding="utf-8")
ЛАТ = lambda л: "LATIN" in __import__("unicodedata").name(л, "")


def письмо(ч):
    л = [х for х in ч if х.isalpha()]
    лат = sum(ЛАТ(х) for х in л)
    return "" if not л else "лат" if лат == len(л) else "інше" if not лат else "змішане"


def чужі(рядок, свої):
    вих = []
    for с in re.findall(r"[^\W\d_][\w'’\-]*", рядок):
        if с.lower() in свої:
            continue
        ч = [(х, письмо(х)) for х in с.split("-") if х]
        if all(п == "лат" for _, п in ч):
            if any(len(х) >= 3 and х.lower() not in свої | {"den"} and not re.fullmatch(r"[0-9a-fA-F]{6}", х)
                   and not (х.isupper() and len(х) <= 4) for х, _ in ч):
                вих.append(с)
        elif any(п == "змішане" for _, п in ч) or any(п == "лат" and len(х) >= 2 for х, п in ч):
            вих.append(с)
    return вих


for файл in sys.argv[1:]:
    рядки = open(файл, encoding="utf-8").read().split("\n")
    свої = {с.lower() for і, р in enumerate(рядки) if "₴" in р
            for с in re.findall(r"[\w'’\-]+", р + " " + рядки[і - 1])}
    знахідки = [(і + 1, чужі(р, свої)) for і, р in enumerate(рядки) if чужі(р, свої)]
    print(f"{файл} · рядків {len(рядки)} · слів латиницею {sum(len(w) for _, w in знахідки)} · "
          + "; ".join(f"{і}: {','.join(w)}" for і, w in знахідки[:12]))
