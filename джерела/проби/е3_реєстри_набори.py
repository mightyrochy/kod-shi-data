"""Повний каталог і граничні входи шару реєстрів для порівняння ваги."""
import collections, gzip, json, os, pathlib


def набори(каталог):
    """Образи з каталогу: кожна річ сама, у парі й трійці; пари реєстрів; трійки одного реєстру."""
    import реєстри as Р
    к = sorted(каталог, key=lambda р: str(р['id']))
    n, імена, групи = len(к), sorted(Р.РЕЄСТРИ), collections.defaultdict(list)
    for р in к:
        в = Р.реєстр_речі(р)
        if в['розпізнано']:
            групи[max(sorted(в['бали']), key=в['бали'].get)].append(р)
    людина = [None] + [[x] for x in імена] + [[a, b] for a, b in zip(імена, імена[1:])]
    цілі = [None, (1, 3), (3, 5), (5, 7), (7, 9), (8, 10)]
    образи = []
    for i, р in enumerate(к):
        образи += [[р], [р, к[(i * 7919 + 1) % n]], [р, к[(i * 7919 + 1) % n], к[(i * 104729 + 3) % n]]]
    for a in імена:
        for b in імена:
            образи += [[x, y] for x, y in zip(групи[a][:20], групи[b][:20]) if a < b]
        образи += [групи[a][j:j + 3] for j in range(0, min(60, len(групи[a]) - 2), 3)]
    for i, образ in enumerate(образи):
        yield 'о%d' % i, образ, людина[i % len(людина)], цілі[i % len(цілі)]


def каталог():
    """Каталог без фото з кешу TMP (той самий вхід для обох дерев)."""
    кеш = pathlib.Path(os.environ['TMP']) / 'е3_каталог.json.gz'
    if not кеш.exists():
        import фід_каталог as Ф
        дані = Ф.база_прогону(Ф.каталог_на_диску('каталог_повний.xml'), ліміт_фото=0)['каталог']
        with gzip.open(кеш, 'wt', encoding='utf-8') as ф:
            json.dump(дані, ф, ensure_ascii=False)
    with gzip.open(кеш, 'rt', encoding='utf-8') as ф:
        return json.load(ф)
