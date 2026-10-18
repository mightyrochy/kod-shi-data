# -*- coding: utf-8 -*-
"""7590: записана відповідь #1452 має 10 образів, незакрите day не губить решту.

Джерело: perevirka-1452-zhyvi@6054d890, ж7, VIDPOVIDI/seed3_09.
ДО: 1 образ; ПІСЛЯ: 10. Жодних моделей і мережі.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import протокол as П


def main():
    """Друкує прочитаний набір і перевіряє збереження речей та валідної прози."""
    сире = Path(__file__).with_name("дані_1452").joinpath("складання.json").read_text()
    об, чому, нот = П.розбір_за_схемою(сире, "ОБРАЗИ_V1")
    образи = (об or {}).get("образи", [])
    print("7590: образів", len(образи), "речей", [len(о["речі"]) for о in образи], нот)
    assert чому is None and len(образи) == 10
    assert all(len(о["речі"]) == 4 and len(о["свідомо"]) == 1 for о in образи)
    assert образи[0]["речі"] == ["#314·01", "#6·05", "#289·15", "#98·11"]
    assert образи[-1]["речі"] == ["#29·36", "#17·04", "#288·34", "#175·25"]
    for об in ({"text": 'walk, "day": a word', "next": []}, {"text": "walk, next day", "next": []}):
        сире = json.dumps(об)
        assert json.loads(П._закрити(сире)[0]) == об
    print("Валідні лапки й коми в прозі збережено")


if __name__ == "__main__":
    main()
