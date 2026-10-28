"""Звірити K-PAL-16 у двох деревах на тих самих id замість першої речі різних пулів."""
import json
import os
from pathlib import Path
import sys


def головна():
    """Зафіксувати вхід ДО або повторити його на голові через справжній міст."""
    дерево = Path(sys.argv[1]).resolve()
    тека = Path(__file__).resolve().parent
    код = дерево / "джерела"
    os.chdir(код)
    sys.path[:0] = [str(код), str(код / "проби")]
    import pal_вердикт as В
    import palettes as П
    import реєстр_правил as Р
    вхід, пакет, каталог, _ = В.стенд(гілка=0, самозвіт={"метал": "срібло"})
    if sys.argv[2] == "ДО":
        межова = next(x for слот in ("верх", "сукня", "низ")
                       for x in пакет["кандидати"].get(слот, [])
                       if (x.get("частка_вікна") or 1) < П.МЕЖОВА_ЧАСТКА)
        теплі = [В.з_каталогу(каталог, слот, lambda L, C, h, з: з["lab"][2] > Р.C["b_нейтралі"][0] + 8)
                 for слот in ("взуття", "сумка", "низ")]
        холодні = [В.з_каталогу(каталог, слот, lambda L, C, h, з: з["lab"][2] < Р.C["b_нейтралі"][1] - 8)
                   for слот in ("взуття", "сумка", "низ")]
        набори = {ім: [межова["id"]] + [x["id"] for x in комп if x]
                  for ім, комп in (("теплі", теплі), ("холодні", холодні))}
        (тека / "pal16-id.json").write_text(json.dumps(набори, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        набори = json.loads((тека / "pal16-id.json").read_text(encoding="utf-8"))
    результат = {}
    for ім, ід in набори.items():
        assert all(x in каталог for x in ід)
        зн, _ = В.знахідки(вхід, ід)
        результат[ім] = dict(id=ід, знахідка=В.рядок(зн, "K-PAL-16"),
            записи=[{к: каталог[x].get(к) for к in ("id", "назва", "слот", "lab", "колір_тип", "_частка_вікна")}
                    for x in ід])
    текст = json.dumps(результат, ensure_ascii=False, indent=2)
    (тека / ("pal16-фіксовані-" + sys.argv[2] + ".json")).write_text(текст, encoding="utf-8")
    print(текст)


if __name__ == "__main__":
    головна()
