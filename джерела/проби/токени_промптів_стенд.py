# -*- coding: utf-8 -*-
"""П-6: бюджет промптів ДО/ПІСЛЯ за записами стенда (`рв6_стенд.js`, VIDPOVIDI=<тека>): кожен виклик
моделі — файл «── ПРОМПТ (N симв.) ──…── ВІДПОВІДЬ …». Друкує по типу виклику символи й токени
Gemma 3 (GEMMA_TOKENIZER — шлях до tokenizer.json; без нього лише символи) і різницю.
Запуск: GEMMA_TOKENIZER=… python3 проби/токени_промптів_стенд.py <тека ДО> <тека ПІСЛЯ> [<ДО2> <ПІСЛЯ2> …]"""
import os, re, sys, collections
Т = None
if os.environ.get("GEMMA_TOKENIZER"):
    from tokenizers import Tokenizer; Т = Tokenizer.from_file(os.environ["GEMMA_TOKENIZER"])
ток = lambda s: len(Т.encode(s, add_special_tokens=False).ids) if Т else 0


def лічба(тека):
    """{тип виклику: [викликів, символів, токенів]} за файлами однієї теки стенда."""
    г = collections.OrderedDict()
    for ім in sorted(os.listdir(тека)):
        т = open(os.path.join(тека, ім), encoding="utf-8").read()
        п = т.split("\n", 1)[1].split("\n\n── ВІДПОВІДЬ (")[0]
        к = г.setdefault(re.sub(r"^seed\d+_\d+_", "", ім)[:-4], [0, 0, 0])
        к[0] += 1; к[1] += len(п); к[2] += ток(п)
    return г


пари = list(zip(sys.argv[1::2], sys.argv[2::2]))
до, після = collections.Counter(), collections.Counter()
for а, б in пари:
    for тека, сума in ((а, до), (б, після)):
        for тип, (н, с, т_) in лічба(тека).items():
            сума[(тип, "н")] += н; сума[(тип, "с")] += с; сума[(тип, "т")] += т_
типи = sorted({т for т, _ in до} | {т for т, _ in після}, key=lambda т: -до[(т, "т")] - до[(т, "с")] / 1e6)
print("%-44s %9s %9s %7s" % ("виклик (сідів: %d)" % len(пари), "ток ДО", "ток ПІСЛЯ", "Δ %"))
for тип in типи:
    а, б = до[(тип, "т")] or до[(тип, "с")], після[(тип, "т")] or після[(тип, "с")]
    print("%-44s %9d %9d %+6.1f%%" % (тип[:44], а, б, 100.0 * (б - а) / а if а else 0.0))
а, б = sum(до[(т, "т")] or до[(т, "с")] for т in типи), sum(після[(т, "т")] or після[(т, "с")] for т in типи)
print("%-44s %9d %9d %+6.1f%%" % ("РАЗОМ" + ("" if Т else " (символи: токенізатора нема)"), а, б, 100.0 * (б - а) / а if а else 0.0))
