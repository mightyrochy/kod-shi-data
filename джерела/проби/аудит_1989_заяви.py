# -*- coding: utf-8 -*-
"""Рядок 1989: напрямок вузла приходить значенням, спалах не стверджується."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import внутрішня_мова as ВМ

тексти = [v for v in vars(ВМ).values() if isinstance(v, dict)]
вузол = next(d["knot_placement_buckle_as_detail"] for d in тексти if "knot_placement_buckle_as_detail" in d)
спалах = next(d["chroma_too_high_for_photo_event"] for d in тексти if "chroma_too_high_for_photo_event" in d)
print("вузол без напрямку:", "in front" not in вузол and "knot" in вузол)
print("спалах умовно:", "may blow out" in спалах)
