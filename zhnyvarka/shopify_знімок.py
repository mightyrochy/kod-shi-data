# -*- coding: utf-8 -*-
"""ЗНІМОК SHOPIFY (рядок 5653): `products.json` чотирьох крамниць каталогу → `<тека>/<домен>.json.gz`.

Мережевий крок конвеєра, окремо від чистої збірки (`shopify_варіанти.перебрати`): знімок можна перечитати без мережі.
Шлях знімка бере рецепт крамниці (локаль: для nyni — `/uk/products.json`, українська версія, п.16). Беруться лише
товари, чий `handle` є серед записів каталогу. Темп — як у жниварки (пауза на домен).

ЗАПУСК (з кореня репозиторію)
  python3 zhnyvarka/shopify_знімок.py <тека> [домен …]"""
import gzip, json, os, sys
from urllib.parse import urljoin

ТУТ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ТУТ)
import жниварка as ж                                               # noqa: E402
import складальник as с                                            # noqa: E402
import shopify_варіанти as шв                                      # noqa: E402
import woo_варіанти as ва                                          # noqa: E402

СТОРІНОК = 40                                                      # як у `жниварка.shopify_products_json`


def знімок_крамниці(домен, записи, рецепт, пауза=1.0, лог=print):
    транспорт = ж.Транспорт(пауза=пауза, ігнорувати_robots=True)
    база = "https://" + домен
    товари = []
    for сторінка in range(1, СТОРІНОК + 1):
        r = транспорт.get(urljoin(база, "%s?limit=250&page=%d" % (рецепт["шлях_знімка"], сторінка)))
        if r["код"] != 200 or not (r["тіло"] or "").lstrip().startswith("{"):
            break
        частина = json.loads(r["тіло"]).get("products") or []
        if not частина:
            break
        товари.extend(частина)
    наші = {шв.ручка(з["адреса"]) for з in записи if ва.магазин(з) == домен}
    вибір = [т for т in товари if (т.get("handle") or "").lower() in наші]
    лог("%s: у каталозі %d адрес, у знімку %d товарів (з %d)" % (домен, len(наші), len(вибір), len(товари)))
    return вибір


def main(argv=None):
    а = argv if argv is not None else sys.argv[1:]
    if not а:
        print(__doc__)
        return 2
    рецепти = шв.читати_рецепти()
    тека, домени = а[0], (а[1:] or sorted(рецепти))
    os.makedirs(тека, exist_ok=True)
    _, записи = с.читати_записи()
    for д in домени:
        вибір = знімок_крамниці(д, записи, рецепти[д], лог=lambda *x: print(*x, flush=True))
        with gzip.open(os.path.join(тека, д + ".json.gz"), "wt", encoding="utf-8") as f:
            json.dump(вибір, f, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
