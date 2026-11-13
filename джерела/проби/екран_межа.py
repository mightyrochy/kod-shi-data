# -*- coding: utf-8 -*-
"""Межа екрана й логіки (наряд Екран-наново): що екран (`показ/екран/`) кличе з логіки (`показ/*.js`) і скільки
рядків логіки ще торкаються DOM. Друкує перелік імен межі й дві лічби; запуск з `джерела/`: python3 проби/екран_межа.py"""
import glob, os, re
ТЕКА = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'показ')
ЧИТАТИ = lambda п: re.sub(r'/\*.*?\*/', '', open(п, encoding='utf-8').read(), flags=re.S)
ОГОЛОШЕННЯ = re.compile(r'^(?:async\s+)?function\s*\*?\s*([^\s(]+)|^(?:const|let|var)\s+([^\s=,;]+)', re.M)
DOM = re.compile(r'\bdocument\.|\$\(|\.innerHTML|\.textContent|\.classList|\.appendChild|querySelector|'
                 r'addEventListener|\.onclick|createElement|\.scrollIntoView|\.focus\(|window\.scrollTo')
логіка = {п: ЧИТАТИ(п) for п in sorted(glob.glob(os.path.join(ТЕКА, '*.js')))}
екран = {п: ЧИТАТИ(п) for п in sorted(glob.glob(os.path.join(ТЕКА, 'екран', '*.js')))}
імена = {(м.group(1) or м.group(2)): os.path.basename(п) for п, т in логіка.items() for м in ОГОЛОШЕННЯ.finditer(т)}
слова = set(re.findall(r'[\wʼ$]+', '\n'.join(екран.values())))
межа = sorted((ф, ім) for ім, ф in імена.items() if ім in слова)
for ф, ім in межа:
    print('межа: %s ← %s' % (ім, ф))
торкань = {os.path.basename(п): sum(1 for р in т.split('\n') if DOM.search(р)) for п, т in логіка.items()}
for ф, н in sorted(торкань.items(), key=lambda х: -х[1]):
    if н: print('DOM у логіці: %s — %d рядків' % (ф, н))
print('імен межі: %d; рядків логіки з DOM: %d у %d файлах' % (len(межа), sum(торкань.values()), sum(1 for н in торкань.values() if н)))
