#!/usr/bin/env python3
"""ІН-1: збирає PDF інструкції з `інструкція.html`.

Три кроки, бо номери сторінок у змісті відомі лише ПІСЛЯ верстки:
  1) `нарізка.py` — знімки з проходів стенда у теку `знімки/`;
  2) перший рендер у Chromium;
  3) з готового PDF беруться сторінки, де стоїть мітка «РОЗДІЛ N», номери
     вписуються у зміст — і рендер повторюється. Вставка йде в наявний рядок
     змісту (<small> у кінці рядка), тож розкладка від неї не рухається.

Запуск:
  CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node22/lib/node_modules \
    python3 зібрати.py
"""
import os
import re
import subprocess
import sys

ТЕКА = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ТЕКА, 'інструкція.html')
PDF = os.path.normpath(os.path.join(ТЕКА, '..', 'інструкція_тестувальниць_2026-09.pdf'))


def рендер():
    subprocess.run(['node', os.path.join(ТЕКА, 'рендер.js'), HTML, PDF],
                   check=True, cwd=ТЕКА)


def сторінки_розділів():
    """{номер розділу: сторінка PDF} — за міткою «РОЗДІЛ N» на самій сторінці."""
    import pypdfium2 as pdfium
    д = pdfium.PdfDocument(PDF)
    де = {}
    for i in range(len(д)):
        # БЕЗ .upper(): мітка розділу намальована великими (text-transform), а
        # посилання в тексті — малими («розділ 12»). Інакше згадка в реченні
        # видавала б себе за початок розділу.
        плоский = re.sub(r'\s+', '', д[i].get_textpage().get_text_range())
        for n in re.findall(r'РОЗДІЛ(\d+)', плоский):
            де.setdefault(int(n), i + 1)
    return де


def вписати(де):
    s = open(HTML, encoding='utf-8').read()
    рядки = re.findall(r'<li><b>.*?</b>(?:<small>\d+</small>)?</li>', s)
    змін = 0
    for k, рядок in enumerate(рядки, start=1):
        if k not in де:
            continue
        без = re.sub(r'<small>\d+</small></li>$', '</li>', рядок)
        новий = без[:-len('</li>')] + '<small>%d</small></li>' % де[k]
        if новий != рядок:
            s = s.replace(рядок, новий, 1)
            змін += 1
    open(HTML, 'w', encoding='utf-8').write(s)
    return змін, len(рядки)


if __name__ == '__main__':
    subprocess.run([sys.executable, os.path.join(ТЕКА, 'нарізка.py')], check=True)
    рендер()
    де = сторінки_розділів()
    print('розділів у PDF:', sorted(де.items()))
    print('рядків змісту оновлено: %d з %d' % вписати(де))
    рендер()
    import pypdfium2 as pdfium
    print('✔ сторінок у PDF:', len(pdfium.PdfDocument(PDF)))
