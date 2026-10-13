"""ВМ-1: межа шару зі слотом і ознакою («без підборів») — чи йде слот у вето типів. Друкує факт."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import мовний_шар as М
for запис in ({"quote": "без підборів", "slot": "shoes", "feature": "heels"},
              {"quote": "без сукні", "slot": "dress"},
              {"quote": "без чорного верху", "slot": "top", "color_name": "black"}):
    в, слоти = М._межі([запис])
    print("%-20s → типи %s · кольори %s · слоти кольору %s" % (запис["quote"], в["типи"], в["кольори"], слоти))
