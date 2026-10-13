# -*- coding: utf-8 -*-
"""Знахідка автоогляду #726: питання без `values`, що стоїть лише там, де крій речі не названо
(`cut_not_declared_assumed_regular`, K-BOD-02), не «для всіх»: на картці, де воно доречне, воно має бути.
4 сценарії стенда × 14 випадкових образів (сід 7): скільки образів мають таке питання і скільки з них
несуть `для_всіх` (картка його не малює). Контроль: на скількох образах глобальні питання (`no_input_*`) лишились `для_всіх`.
Запуск із `джерела`: python3 проби/питання_крою_на_картці.py   (~1,5 хв)"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import feed; feed.каталог_на_диску("каталог_повний.xml")
import bridge as B, стенд_знімок as СЗ
вх0, R, образів, з_кроєм, сховані, глобальні = json.load(open("стенд_вх.json")), random.Random(7), 0, 0, 0, 0
for назва, сц in list(СЗ.СЦЕНАРІЇ.items())[:4]:
    вх = dict(вх0, сценарій=сц, випадок=назва)
    к = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False))).get("кандидати") or {}
    for _ in range(14):
        ід = [R.choice(к[с])["id"] for с in ("верх", "низ", "взуття", "сумка") if к.get(с)]
        п = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ід), ensure_ascii=False))).get("питання") or []
        образів += 1
        крій = [q for q in п if "cut_not_declared" in json.dumps(q.get("повідомлення"))]
        з_кроєм += bool(крій); сховані += any(q.get("для_всіх") for q in крій)
        глобальні += any(q.get("для_всіх") and "no_input_" in json.dumps(q.get("повідомлення")) for q in п)
print("образів %d · з питанням «крій не названо» %d · з них приховано від картки (для_всіх) %d · образів із глобальним no_input_* лише у звіті %d"
      % (образів, з_кроєм, сховані, глобальні))
