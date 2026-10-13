# -*- coding: utf-8 -*-
"""Рядок 3530 · replay записаних відповідей OUTFITS_V1 (ЖИВІ-11/12/13, пачка 2 — гілки `claude/zhyvi-13`, `-14`):
вихід у токенах проти стелі 4000, скільки обірвано, скільки образів розібрано, яку частку символів їдять елементи
`items` довші за 20 симв. (рядок пулу, обʼєкт {n, …}), і скільки токенів та сама відповідь важила б, коли кожна
річ — лише «n» (те, що тепер просить промпт). TOKENIZER=<tokenizer.json Qwen3.5-9B> — точна лічба; без нього —
3,29 симв./т. (середнє цього ж корпусу тим токенізатором). Запуск: cd джерела && python3 проби/складання_стеля_3530.py"""
import hashlib, json, os, re, subprocess, sys
sys.path.insert(0, "."); import протокол as П
Т = os.environ.get("TOKENIZER") and __import__("tokenizers").Tokenizer.from_file(os.environ["TOKENIZER"])
ток = (lambda т: len(Т.encode(т).ids)) if Т else (lambda т: round(len(т) / 3.29))
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
ОБ, РЯД = re.compile(r'\{\s*"n"\s*:\s*"(#\d+·\d\d[^"]*)"[^{}]*\}'), re.compile(r'"(#\d+·\d\d(?:/(?:top|bottom))?)[^"]{12,}"')
бачено, з = set(), {}
for г in ("origin/claude/zhyvi-13", "origin/claude/zhyvi-14"):
    for ф in git("ls-tree", "-r", "--name-only", г, "--", "../аудит/").split("\n"):
        пр, _, в = git("show", "%s:%s" % (г, ф)).partition("\n── ВІДПОВІДЬ") if re.search(
            r"/VIDPOVIDI/.*(ОБРАЗИ_V1|повтор_формату)", ф) else ("", "", "")
        в = в.partition("\n")[2].strip()
        if "OUTFITS_V1" not in пр or not в or hashlib.md5(в.encode()).digest() in бачено:
            continue
        бачено.add(hashlib.md5(в.encode()).digest())
        м = re.search(r'"outfits_wanted"\s*:\s*(\d+)', пр)
        кл = {"10": "складання (10 образів)", "5": "ремонт (5 образів)"}.get(м and м.group(1), "ремонт повноти")
        об = П.розбір_за_схемою(в, "ОБРАЗИ_V1")[0] or {}
        ел = [x for о in об.get("образи") or [] if isinstance(о, dict) for x in о.get("речі") or []]
        довгі = [x for x in ел if not isinstance(x, str) or len(x) > 20]
        т, к = ток(в), ток(РЯД.sub(r'"\1"', ОБ.sub(r'"\1"', в)))
        с = з.setdefault(кл, dict(відп=0, т=0, к=0, обрив=0, обр=0, ел=0, довгі=0, симв=0, симв_д=0, понад=[], цілі=[]))
        for ключ, v in (("відп", 1), ("т", т), ("к", к), ("обрив", т >= 3900), ("обр", len(об.get("образи") or [])),
                        ("ел", len(ел)), ("довгі", len(довгі)), ("симв", len(в)),
                        ("симв_д", sum(len(json.dumps(x, ensure_ascii=False)) for x in довгі))):
            с[ключ] += v
        (с["понад"] if т >= 3900 else с["цілі"]).append(к)
for кл, с in з.items():
    ц = sorted(с["цілі"]) or [0]
    print("%-24s відповідей %3d · обірвано на стелі %2d · образів розібрано %3d · елементів items %4d, довгих %4d "
          "(%2d%% симв. відповідей)" % (кл, с["відп"], с["обрив"], с["обр"], с["ел"], с["довгі"], 100 * с["симв_д"] // с["симв"]))
    print("%-24s токенів виходу %6d → лише «n» %6d (−%d%%) · цілі лише «n»: медіана %d, p90 %d, макс %d т. · обірвані "
          "лише «n»: %s" % ("", с["т"], с["к"], 100 - 100 * с["к"] // с["т"], ц[len(ц) // 2], ц[int(.9 * (len(ц) - 1))], ц[-1],
                            sorted(с["понад"])))
