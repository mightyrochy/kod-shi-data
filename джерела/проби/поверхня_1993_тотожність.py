# -*- coding: utf-8 -*-
"""Звіряє бітові маски, 8-зв'язність і частотні перцентилі з ядром перевірки."""
import random, subprocess, sys, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import surface as П


def main():
    """Перевіряє краї, вузькі кадри, діагоналі й повторювані значення."""
    до = types.ModuleType('поверхня_до')
    exec(subprocess.check_output(['git', 'show', '665dfb48:джерела/surface.py']).decode('utf-8'), до.__dict__)
    г, перетворень, плям, квантилів = random.Random(1993), 0, 0, 0
    for w, h in [(1, 1), (2, 7), (7, 2), (31, 29), (64, 48), (257, 3)]:
        for f in [0, .15, .6, .9, 1]:
            м = [г.random() < f for _ in range(w*h)]
            for r in [0, 1, 2, 4]:
                for e in [False, True]:
                    assert list(П._морфологія(м, w, h, r, e)) == до._морфологія(м, w, h, r, e)
                    перетворень += 1
            for n in [1, 4, 15]:
                assert П._плями(м, w, h, n) == до._плями(м, w, h, n)
                плям += 1
    for _ in range(100):
        ч = {г.random(): г.randint(1, 30) for _ in range(г.randint(1, 30))}
        ряд = [x for x, n in ч.items() for _ in range(n)]
        for q in [0, 25, 50, 75, 90, 100]:
            assert П._квантиль_частот(list(ч.items()), q) == до.перцентиль(ряд, q)
            квантилів += 1
    print(f'Тотожні: морфологія {перетворень}; плями {плям}; перцентилі {квантилів}')


if __name__ == '__main__':
    main()
