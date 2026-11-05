"""ДО → ПІСЛЯ на тих самих знімках Shopify через повний перезбір XML та фактів власності.
Аргументи: тека знімків, SHA ДО. Продуктові файли не змінюються; кольори не перемірюються."""
import collections, gzip, json, sys, tempfile
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "джерела"), str(КОРІНЬ / "zhnyvarka"), str(КОРІНЬ / "джерела/прилади")]
import feed, жниварка as ж, shopify_варіанти as ш, складальник as с, власник_кадру as ф, фід_власник_кадру as в
from кадр_варіант_каталог import давній

def main():
    """Лічить підтвердження кадру в каталозі та в наявних вимірах без штучних хешів."""
    шапка, записи = с.читати_записи()
    знімки = {п.name[:-8]: json.loads(gzip.decompress(п.read_bytes())) for п in Path(sys.argv[1]).glob("*.json.gz")}
    assert знімки and all(знімки.values())
    зб = json.loads(gzip.decompress((КОРІНЬ / "джерела/каталог_збагачення.json.gz").read_bytes()))
    км = json.loads(gzip.decompress((КОРІНЬ / "джерела/каталог_кадри.json.gz").read_bytes()))
    маніфест = json.loads(gzip.decompress((КОРІНЬ / "каталог_маніфест_кадрів.json.gz").read_bytes()))["кадри"]
    магазини = {м["домен"]: м for м in ж.читати_магазини(str(КОРІНЬ / "zhnyvarka/магазини.tsv"))}
    for стан, адаптер in (("ДО", давній("shopify_варіанти", sys.argv[2])), ("ПІСЛЯ", ш)):
        нові, _, збагачення, _, звіт, черга = адаптер.перебрати(записи, знімки, ш.читати_рецепти(), зб, км, "2026-11-04", ж=ж, магазини=магазини)
        with tempfile.TemporaryDirectory() as тека:
            шлях = Path(тека) / "каталог.xml"
            шлях.write_text(с.скласти(шапка, нові), encoding="utf-8")
            оф = feed.читати_yml(str(шлях))[0]
        факти, лічби = ф.факти(оф, збагачення, маніфест), collections.defaultdict(collections.Counter)
        for о in оф:
            if о.get("магазин") not in знімки: continue
            л = лічби[о["магазин"]]; л["записів"] += 1; л["кадрів"] += len(о["фото"])
            л["підтверджених_кадрів"] += sum(в.доказ_варіанта(о, к) is not None for к in о["фото"])
            власник = в.запис(о, збагачення.get(о["id"]), факти=факти)
            if not власник: continue
            л["наявних_вимірів"] += 1
            л["вимірів_з_власником"] += власник["варіант"] != "невідомо"
            л["своїх_вимірів_з_власником"] += власник["варіант"] != "невідомо" and власник["стан"] == "свій"
        assert len(нові) == len({з["ід"] for з in нові}) and {з["ід"] for з in записи} <= {з["ід"] for з in нові}
        print(стан, json.dumps(dict(усього_записів=len(нові), черга=len(черга), крамниці=лічби), ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
