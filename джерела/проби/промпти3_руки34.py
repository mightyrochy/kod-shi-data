# -*- coding: utf-8 -*-
"""Рядок 6213 (а), рішення менеджера (п.1): рядок заяв збирача тепер за ключами даних — промпт рук 3–4 (проза, перелік,
перепис) байт у байт той самий, що на коді ДО. Входи — дані 35 записаних промптів прози рук 3–4 живих прогонів
пачки 15 (`промпти3_база.записи`) і промпт переліку; друкує, скільки промптів збіглося байт у байт.
Запуск із `джерела`: python3 проби/промпти3_руки34.py"""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import промпти3_база as Б

if "--json" in sys.argv:
    sys.path.insert(1, os.getcwd())
    import руки_без_коду as Р, збирач_промптів as З
    вих = []
    for ш, п, _ in Б.записи(r"проза_рука_3_4\.txt$"):
        д = json.loads(п)
        дані = {к: v for к, v in д.items() if к != "task"}
        for перепис in (False, True):
            if перепис:
                дані.update(previous_answer=Р.ЗАГЛУШКА_ОПИСУ, remarks=Р.ЗАГЛУШКА_ЗАУВАЖЕНЬ)
            вих.append(json.dumps(З.зібрати(Р.ОБРАЗ, дані, мова_тексту=д["task"].get("language")), ensure_ascii=False))
    for мова in ("English", "Ukrainian"):
        вих += [Р.промпт_переліку(None, мова), Р.промпт_переліку([dict(id="с1", назва="x", слот="верх")], мова)]
    print(json.dumps([hashlib.sha1(т.encode()).hexdigest() for т in вих] + [sum(map(len, вих))]))
else:
    до, після = Б.до_після(__file__)
    print("промптів рук 3–4: %d · байт у байт ті самі: %d · символів ДО %d / ПІСЛЯ %d"
          % (len(до) - 1, sum(а == б for а, б in zip(до[:-1], після[:-1])), до[-1], після[-1]))
