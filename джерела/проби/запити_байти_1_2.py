# -*- coding: utf-8 -*-
"""Мірило кроку 1.2: розмір JSON виходу `запити` для показу (без 1,48 МБ кандидатів)."""
import json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import bridge as B

вх = json.load(open("стенд_вх.json", encoding="utf-8"))
вх.pop("пакети", None)
if len(sys.argv) > 1:
    вх["каталог"] = sys.argv[1]

вих = B.виклик("запити", json.dumps(вх, ensure_ascii=False))
б = len(вих.encode("utf-8"))
д = json.loads(вих)
є_канд = "кандидати" in д or "кандидати_донора" in д

вх_к = dict(вх, кандидати=1)
вих_к = B.виклик("запити", json.dumps(вх_к, ensure_ascii=False))
б_к = len(вих_к.encode("utf-8"))
д_к = json.loads(вих_к)
є_канд_к = "кандидати" in д_к and "кандидати_донора" in д_к

print(f"каталог: {os.path.basename(вх.get('каталог', ''))}")
print(f"запити (показ): {б:,} байт ({б / 1024 / 1024:.2f} МБ), кандидати={є_канд}")
print(f"запити (явний запит): {б_к:,} байт ({б_к / 1024 / 1024:.2f} МБ), кандидати={є_канд_к}")
