# -*- coding: utf-8 -*-
"""ЗНІМОК WOO (рядок 5652): товари Store API шести крамниць каталогу + їхні варіації → `<тека>/<домен>.json.gz`.

Мережевий крок конвеєра, окремо від чистої збірки (`woo_варіанти.перебрати`): знімок можна перечитати без мережі.
Беруться лише товари, чия адреса є серед записів каталогу (решта крамниці — не наша вибірка); варіації —
`жниварка.woo_варіації` (кадр і `is_in_stock` кожної варіації). Темп — як у жниварки (пауза на домен).

ЗАПУСК (з кореня репозиторію)
  python3 zhnyvarka/woo_знімок.py <тека> [домен …]"""
import gzip, json, os, sys

ТУТ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ТУТ)
import жниварка as ж                                               # noqa: E402
import складальник as с                                            # noqa: E402
import woo_варіанти as ва                                          # noqa: E402

БАЗИ = {"sunwin-store.com": "https://www.sunwin-store.com", "feelyou.com.ua": "https://feelyou.com.ua",
        "likeangel.com.ua": "https://likeangel.com.ua", "attico.ua": "https://attico.ua",
        "morandi.ua": "https://morandi.ua", "maxa.ua": "https://maxa.ua"}


def знімок_крамниці(домен, записи, пауза=1.0, лог=print):
    транспорт = ж.Транспорт(пауза=пауза, ігнорувати_robots=True)
    рецепт = ж.woo_рецепт(домен)
    товари = [к["сирий"] for к in ж.woo_store_api(транспорт, БАЗИ[домен], лог, 100000)]
    наші = {ва.норм_адреса(з["адреса"]) for з in записи if ва.магазин(з) == домен}
    вибір = [т for т in товари if ва.норм_адреса(т.get("permalink")) in наші]
    ж.woo_варіації(транспорт, БАЗИ[домен], вибір, лог)
    лог("%s: у каталозі %d адрес, у знімку %d товарів (з %d), варіації є у %d" % (
        домен, len(наші), len(вибір), len(товари), sum("_варіації" in т for т in вибір)))
    return вибір


def main(argv=None):
    а = argv if argv is not None else sys.argv[1:]
    if not а:
        print(__doc__)
        return 2
    тека, домени = а[0], (а[1:] or sorted(БАЗИ))
    os.makedirs(тека, exist_ok=True)
    _, записи = с.читати_записи()
    for д in домени:
        вибір = знімок_крамниці(д, записи, лог=lambda *x: print(д, *x, flush=True))
        with gzip.open(os.path.join(тека, д + ".json.gz"), "wt", encoding="utf-8") as f:
            json.dump(вибір, f, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
