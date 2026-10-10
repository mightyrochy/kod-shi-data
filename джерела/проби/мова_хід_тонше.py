# -*- coding: utf-8 -*-
"""Рядок 3491 (МОВА-ХІД-ТОНШЕ): промпт ходу розмови К7р (перший хід, її лист живих 12) — знаки частинами, і що
кожен знятий дубль тепер сказано рівно раз. З текою записаних відповідей ходу (`*мовний_шар_хід_розмови.txt`,
напр. ЖИВІ-16/17) — ще поля й коди, які код бере з тих самих відповідей, і дайджест: до/після правки промпту він
мусить бути той самий (промпт не міняє того, як код читає відповідь).
Запуск: python3 проби/мова_хід_тонше.py [тека_записів]"""
import sys, json, pathlib, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import мовний_шар as М
лист = (pathlib.Path(__file__).resolve().parents[2] / "аудит/живі_12/А/02_ж7_мороз_без_відкритого/VIDPOVIDI/"
        "seed4_01_мовний_шар_хід_розмови.txt").read_text(encoding="utf-8")
нове = json.loads(лист.split("\n", 1)[1].split("── ВІДПОВІДЬ")[0])["her_new_message"]
п = json.loads(М.промпт_розмови({"розмова": {"нове": нове, "історія": []}}))
т = json.dumps(п, ensure_ascii=False)
print("промпт К7р, симв.: %d · rules %d (%d правил) · codes %d (%d рядків) · input %d"
      % (len(т), len(json.dumps(п["task"]["rules"], ensure_ascii=False)), len(п["task"]["rules"]),
         len(json.dumps(п["task"]["codes"], ensure_ascii=False)), len(п["task"]["codes"]),
         len(json.dumps(п["task"]["input"], ensure_ascii=False))))
# дубль → уривок, що лишився раз (0 — сказане зникло; 2+ — дубль повернувся)
for що, уривок in (("вечірня сцена умов поради", "hour 18 or later"),
                   ("«надворі» умов поради", "setting outdoor or mixed"),
                   ("part_of_day: місця вечора", "reads as evening by itself"),
                   ("цитата — її форми слів", "keeps her word forms"), ("приклади смуг — не коди", "for the band only"),
                   ("її межа відкритого — над нормою", "overrides the event's norm"),
                   ("own_items: лише її слова й фото", "the photo is looked at by another model"),
                   ("need none: певне без її речей", "know for sure without her items")):
    print("  %-34s %d" % (що, т.count(уривок)))
print("  крапка й «—» — код (`_бульбашка`): %r" % М._бульбашка(["Записала мороз - і сніг", "Розкажи про макіяж"]))
if len(sys.argv) > 1:
    рядки = []
    for ф in sorted(pathlib.Path(sys.argv[1]).rglob("*мовний_шар_хід_розмови.txt")):
        р = М.прийняти_розмову(ф.read_text(encoding="utf-8").split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1])
        рядки.append(json.dumps([р["внутрішня"], р["частини"], р["незнайомі"], р["невідомо"], р["причина"], р["текст"]],
                                ensure_ascii=False, sort_keys=True, default=str))
    print("записів %d · полів паспорта %d · дайджест %s" % (len(рядки), sum(len(json.loads(x)[0]) for x in рядки),
                                                           hashlib.sha1("\n".join(рядки).encode()).hexdigest()[:12]))
