"""Зіставляє промпти старих записів без знання формату продукту."""
import difflib
import json
import sys


def схожість(а, б):
    """Порівнює початок і кінець промптів тим самим способом для обох replay."""
    def краї(текст):
        return текст[:600] + "\n…\n" + текст[-2500:]

    зіставлення = difflib.SequenceMatcher(None, краї(а), краї(б), autojunk=False)
    if abs(len(а) - len(б)) > 0.5 * max(len(а), len(б), 1):
        return зіставлення.quick_ratio()
    return зіставлення.ratio()


if __name__ == "__main__":
    дані = json.load(sys.stdin)
    оцінки = [схожість(дані["промпт"], текст) for текст in дані["кандидати"]]
    print(json.dumps(оцінки))
