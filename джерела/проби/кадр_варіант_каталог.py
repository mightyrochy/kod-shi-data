"""ДО → ПІСЛЯ за сирими variant_ids крамниці.
Запуск: python джерела/проби/кадр_варіант_каталог.py <тека знімків> <SHA ДО>."""
import collections, gzip, json, subprocess, sys, types
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / "zhnyvarka"))
import жниварка as ж
import shopify_варіанти as ш
def давній(ім, коміт):
    """Завантажує читача з базового коміту без іншої робочої копії."""
    шлях = "zhnyvarka/%s.py" % ім
    модуль = types.ModuleType("_до_" + ім)
    модуль.__file__ = str(КОРІНЬ / шлях)
    exec(compile(subprocess.check_output(["git", "show", коміт + ":" + шлях]), шлях, "exec"), модуль.__dict__)
    return модуль
def main():
    """Лічить записи, кадри та кадри без свого єдиного варіанта з сирих variant_ids."""
    старі = давній("жниварка", sys.argv[2]), давній("shopify_варіанти", sys.argv[2])
    for файл in sorted(Path(sys.argv[1]).glob("*.json.gz")):
        домен = файл.name[:-8]; база = "https://" + домен; рецепт = ш.читати_рецепти()[домен]
        товари = json.loads(gzip.decompress(файл.read_bytes())); лічба = collections.Counter(товарів=len(товари))
        assert товари, "Порожній знімок: " + str(файл)
        for т in товари:
            ключ = next(("option%d" % (о.get("position") or і + 1) for і, о in enumerate(т.get("options") or []) if (о.get("name") or "").strip() in рецепт["колір"]), None)
            кольори = {в["id"]: в.get(ключ) if ключ else None for в in т.get("variants") or []}
            if len(set(кольори.values())) < 2: continue
            лічба["товарів_з_кількома_кольорами"] += 1
            джерело = collections.defaultdict(set)
            for к in т.get("images") or []:
                if к.get("src"): джерело[ж.оригінал_фото(ж.канонічна(к["src"], база))].update(кольори.get(ід, "невідомо") for ід in к.get("variant_ids") or [])
            for стан, читачі in (("ДО", старі), ("ПІСЛЯ", (ж, ш))):
                for ім, записи in (("факти", читачі[0].факти_shopify(т, база)), ("адаптер", читачі[1].варіанти_shopify(т, рецепт) or [])):
                    for з in записи:
                        колір = кольори[з["ід_варіацій"][0]] if ім == "адаптер" else з["характеристики"].get("колір")
                        кадри = з["кадри"] if ім == "адаптер" else з["фото"]
                        лічба.update({стан+":"+ім+":записів": 1, стан+":"+ім+":без_кадрів": int(not кадри), стан+":"+ім+":кадрів": len(кадри), стан+":"+ім+":без_власника": sum(джерело[ж.оригінал_фото(ж.канонічна(к, база))] != {колір} for к in кадри)})
        print(домен, json.dumps(dict(sorted(лічба.items())), ensure_ascii=False))
        assert all(лічба["ПІСЛЯ:"+ім+":без_власника"] == 0 for ім in ("факти", "адаптер"))
if __name__ == "__main__": main()
