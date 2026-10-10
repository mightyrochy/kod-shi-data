# -*- coding: utf-8 -*-
"""Рядок 3490: записана відповідь seed3_01 (живі 13 А/06) — «одягну своє взуття з фото» у `wants` зі `status: has`.
Друкує, де лишилась річ: `own_items` / `wants` / `незнайомі`. Без моделі. Запуск: python3 проби/мова_свою_річ_3490.py <файл>"""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import мовний_шар as М
т = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
р = М.прийняти_розмову(т[т.index("── ВІДПОВІДЬ"):].split("\n", 1)[1])
в = р["внутрішня"]
print("own_items=%s\nwants=%s\nнезнайомі=%s\nперенесено=%s" % (json.dumps(в.get("own_items"), ensure_ascii=False),
      json.dumps(в.get("wants"), ensure_ascii=False), р["незнайомі"], р["перенесено"]))
