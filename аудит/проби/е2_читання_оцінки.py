"""Друкує факти змістового читання оцінки; моделі й каталог не викликає.

Запуск із кореня: python аудит/проби/е2_читання_оцінки.py.
"""
import json
import sys
from pathlib import Path


def головна():
    """Зіставляє справжні промпти й сторожа на штучному вході з дописаною річчю."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "джерела"))
    import оцінка_образу as О
    речі = О.виправити_речі([], [{"op": "add", "slot": "top", "color": "black"}])["речі"]
    образ, _, _ = О.скласти(речі)
    суд = dict(речі=речі, образ=образ, суд={"node": "верх"})
    оцінка = json.loads(О.промпт_оцінки(суд))
    допит = json.loads(О.промпт_допиту(суд, "What if I change the shoes?", {}))
    правила, межі = допит["task"]["rules"], допит["task"]["limits"]
    print("допит: схема=%s; правила оцінки збережено=%s" %
          (list(допит["answer_schema"]), правила == оцінка["task"]["rules"]))
    print("поля картки в правилах допиту=%s; хвіст забороняє їх=%s" %
          ([к for к in ("verdict", "works", "change") if any('"%s"' % к in р for р in правила)],
           'only "answer", without "verdict", "works" or "change"' in допит["now"]["rule"]))
    print("дописана річ: source=%s; фото=%s; в образі=%s; правило лише фото=%s" %
          (оцінка["items"][0]["source"], речі[0]["фото"], bool(образ),
           any("Judge only the items on her photos" in р for р in правила)))
    print("заборона ідів: у правилі=%s; у спільній межі=%s" %
          (any("Ids live only" in р for р in правила), any("without item numbers, ids" in м for м in межі)))
    відповідь = dict(answer="Try another colour.", verdict="wear_with_change",
                     change=[dict(id="c999", items=["h1"], text="Try another colour.")])
    прийнято = О.сторож_оцінки_об(відповідь, суд)
    print("сторож: вердикт=%s; причини=%s" %
          (прийнято["картка"]["вердикт"], [з["чому"] for з in прийнято["сторож"]]))
    print("читач допиту: причина=%s" % О.прийняти_допит('{"answer":"Try another colour."}')["причина"])


if __name__ == "__main__":
    головна()
