#!/usr/bin/env python3
"""Витяг рядків «не виміряно» з п'яти оцінок у JSON (читання, без правок оцінок). Запуск: python3 витяг.py > рядки.json"""
import re, json, sys
Ф = [
 ("О1113","перевірки/оцінка-Е1-нічний-живий-20261113.md"),
 ("Х1115","перевірки/оцінка-Хмара-тестовий-20261115.md"),
 ("Е1115","проби/оцінка-Е1-нічний-живий-20261115.md"),
 ("Х1811","перевірки/Оцінка-прогону-хмара-1811.md"),
 ("Х1811р","перевірки/Оцінка-прогону-хмара-1811-ранок.md"),
]
def клітини(л): return [x.strip() for x in л.strip().strip('|').split('|')]
def pr(s):
    m=re.search(r'#?(\d{4})',s); return m.group(1) if m else ''
out=[]; усі=[]; всього={}
for ід,ф in Ф:
    for н,л in enumerate(open(ф,encoding='utf-8'),1):
        if not л.startswith('|'): continue
        c=клітини(л)
        if ід=="О1113" and len(c)==6 and c[0].isdigit():
            в,ск,пq,пит,від,док=c[4],c[1],c[2],c[3],c[4],c[5]; ск=re.sub(r' \(н\)','',ск)
        elif ід=="Х1115" and len(c)==5 and c[0].startswith('`'):
            ск,пq,пит,від,док=c[0].strip('`'),c[1],c[2],c[3],c[4]; в=від
        elif ід=="Е1115" and len(c)>=7 and c[1].isdigit():
            ск,пит,пq,від,док=c[0],c[2],c[3],c[5]," | ".join(c[6:]); в=від
        elif ід in("Х1811","Х1811р") and len(c)==7 and c[0].isdigit():
            ск,пq,пит,від,док=c[3],c[2],c[1],c[5],c[6]; в=від
        else: continue
        v=re.sub(r'[*`]','',в).strip()
        всього.setdefault(ід,{}); k='нв' if v.startswith('не виміряно') else v[:3]
        всього[ід][k]=всього[ід].get(k,0)+1
        р=dict(оцінка=ід,файл=ф,рядок=н,pr=pr(пq),сцена=ск,питання=пит,відповідь=в,причина=док,к=k)
        усі.append(р)
        if k=='нв': out.append(р)
json.dump(dict(рядки=out,усі=усі,розподіл=всього),sys.stdout,ensure_ascii=False,indent=1)
