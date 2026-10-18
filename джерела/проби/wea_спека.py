# -*- coding: utf-8 -*-
"""Ф2/2.5: погодне послаблення третьої речі на кожній сукні/комплекті каталогу.
Виклик: python3 проби/wea_спека.py <джерела> <каталог.json>.
"""
import collections, hashlib, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(sys.argv[1]).resolve()))
import суд_від_моделі as С
кат = json.loads(pathlib.Path(sys.argv[2]).read_text())
торси = [р for р in кат if р.get("слот") in ("сукня", "комплект")]
решта = [dict(id="проба-взуття", слот="взуття", hex="#1c1c22"), dict(id="проба-сумка", слот="сумка", hex="#2e2e38")]
for т in (24.99, 25, 25.99, 26):
    лічба, рішення = collections.Counter(), []
    for р in торси:
        бл, мʼякі = С.структура_образу_заяви([р] + решта, None, dict(темп_c=т))
        коди = sorted(з["code"] for _, зз in бл for з in зз if з["code"] in ("needs_third_piece", "too_few_items"))
        причини = sorted((з.get("правило"), з.get("регістр"), з.get("гейт_знято_бо"), з.get("сила_нп")) for з in мʼякі)
        рішення.append([р["id"], коди, причини]); лічба.update(коди)
        лічба.update("репліка:" + str(з.get("гейт_знято_бо")) for з in мʼякі)
    print(json.dumps(dict(темп_c=т, межа=С._СПЕКА_C, торсів=len(торси), лічба=dict(лічба),
                         рішення_sha256=hashlib.sha256(json.dumps(рішення,ensure_ascii=False,sort_keys=True).encode()).hexdigest()), ensure_ascii=False, sort_keys=True))
