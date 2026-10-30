"""Колір-інтервал на повному каталозі: добір металу, сім'ї та чистота суду.

Запуск: python мірило.py <дерево> <каталог.json> <вихід.json>.
Читає готовий знімок каталогу, не викликає моделей чи завантаження фото.
"""
import collections
import json
from pathlib import Path
import sys


def головна():
    """Порахувати кожну річ штатними API, зі збереженням id відмінностей."""
    дерево, каталог, вихід = map(Path, sys.argv[1:4])
    sys.path.insert(0, str(дерево / "джерела"))
    import колір_річ as К
    import palettes as П
    import feed as Ф
    import палітра_схеми as С
    from суд_від_моделі import бюджет_і_відлуння, _метал_точки
    речі = json.loads(каталог.read_text(encoding="utf-8"))["каталог"]
    індекс = {р["id"]: р for р in речі}
    типи = collections.Counter(К.тип_кольору(р) for р in речі)
    метали = [р for р in речі if р.get("метал") and К.межі_кольору(р) is not None
              and П.колір_металу(р)]
    рядок = dict(L_min=0, L_max=100, C_min=0, C_max=150, h_from=0, h_to=359)
    втрачені = [р["id"] for р in метали if not Ф.описує_річ(р, dict(рядок, метал=р["метал"]))]
    хибні, розбіжності = [], []
    for р in метали:
        if not _метал_точки((р, р["слот"], None, None, None)):
            розбіжності.append(р["id"])
        if any(з.get("правило") == "K-COL-05" for з in бюджет_і_відлуння([р])):
            хибні.append(р["id"])
    сім = dict(роль="акцент", дуга=(300, 60))
    пул = collections.defaultdict(list)
    for р in речі:
        пул[р.get("слот")].append(dict(id=р["id"]))
    у_пулі = С._великі_у_пулі(сім, пул, індекс)
    ж = індекс["ж-07553@brenda.ua"]
    факт = dict(записів=len(речі), типи=типи,
                невимір_з_lab=sum(bool(р.get("lab")) for р in речі if К.тип_кольору(р) != "вимір"),
                металів=len(метали), втрачено_у_металевому_рядку=len(втрачені), втрачені_id=втрачені,
                хибних_K_COL_05=len(хибні), розбіжностей_суду_металу=розбіжності,
                ж_07553_K_COL_05=[з for з in бюджет_і_відлуння([ж]) if з.get("правило") == "K-COL-05"],
                великих_червоних_у_каталозі=С._великі_у_каталозі(сім, індекс),
                великих_червоних_у_пулі=у_пулі, разом_у_пулі=sum(у_пулі.values()))
    вихід.write_text(json.dumps(факт, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({к: в for к, в in факт.items() if к != "втрачені_id"}, ensure_ascii=False))
    return int(bool(хибні or розбіжності))


if __name__ == "__main__":
    raise SystemExit(головна())
