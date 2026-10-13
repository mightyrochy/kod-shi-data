# -*- coding: utf-8 -*-
"""Рядок 1925: діагноз вдалого повтору опису без речей поза образом (node над фрагментом показу)."""
import pathlib, re, subprocess
h = (pathlib.Path(__file__).resolve().parent.parent / "показ.html").read_text()
i = h.index("if ((в4б.опис||{}).текст && !(")
блок = h[i:h.index("}catch(e){", i)]
js = "const ЗБ={діагноз:[]},рука=1;function t(в4б){" + блок + "} " \
     "t({опис:{текст:'є',названо_поза_образом:[]}});t({опис:{текст:'є',названо_поза_образом:['x']}});" \
     "t({опис:{помилки:[]}});console.log(JSON.stringify(ЗБ.діагноз));"
out = subprocess.run(["node", "-e", js], check=True, capture_output=True, text=True).stdout
д = __import__("json").loads(out)
print("ПІСЛЯ:", *д, sep="\n  ")
assert "retry_succeeded · card=retry_text" in д[0] and "named_not_in_outfit" in д[1] and "no_description" in д[2]
