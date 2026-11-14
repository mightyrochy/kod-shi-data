"""Крок «один колір речі» (14.11.2026): код з виміру кадрів сукупності `зберегли_код.tsv` за трьома кодами.

Код судять за записом кадру (Lab і U головного сегмента, візерунок) — так само, як `surface.виміряти`
(«запис сам відтворює свій код»). Множників каналів поправки тла в записі нема, лише середній (`звірка.поправка`):
беремо (k, k, k). Перевірка цього наближення — колонка `код_прогону`: код прогону #3315 (f2e3e3b0; дерево
8c8d6adb несе той самий `surface.py`) на цьому ж наближенні має збігтися з записаним кодом.

Дерева: `прогін` — 8c8d6adb (гілка `claude/Річ-колір-вимір-розкид`), `main` — база кроку 8dafc111, `крок` — тека
`джерела` робочого дерева. Дані — гілка `claude/Річ-колір-вимір` на c7b37862 (лише два файли, без фото).

    git fetch --depth 1 origin claude/Річ-колір-вимір claude/Річ-колір-вимір-розкид
    python3 -I аудит/проби/річ_колір_один_колір_1411/відтворити.py <тимчасова_тека>
"""
import collections, csv, gzip, json, os, subprocess, sys
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[3]
ТУТ = Path(__file__).resolve().parent
ДАНІ = "c7b37862c5195f823e0ef211cd8ecd718b498f95"
ПРОГІН = "8c8d6adb06eb2927773dc0cdb2a35d0310887ed3"
БАЗА = "8dafc111"
ОГЛЯД = КОРІНЬ / "аудит/проби/річ_колір_розкид_очима_1411"
НЕЙТРАЛІ = {"чорний", "білий", "сірий", "графіт", "срібний"}

ОДИН = r'''
import gzip, json, sys
sys.path.insert(0, sys.argv[1])
import surface as S
d = json.load(gzip.open(sys.argv[2])); вих = {}
for к in json.load(open(sys.argv[3])):
    ід, файл = к.split("|", 1)
    в = next(x for x in d["записи"][ід] if x["файл"] == файл); з = d["звірка"][к]; k = з["поправка"]
    код, _, чому = S.код_розкиду(tuple(в["lab"]), з["хрома"][1], [k] * 3 if k else None)
    if код and sys.argv[4] == "так" and в["вимір"]["візерунок"] != "однотонний":
        код, чому = None, "код невідомо: вимір бачить кілька кольорів речі (%s)" % в["вимір"]["візерунок"]
    вих[к] = [код, чому]
json.dump(вих, sys.stdout, ensure_ascii=False)
'''


def git(*а, **кв):
    return subprocess.run(["git", "-C", str(КОРІНЬ), *а], check=True, capture_output=True, **кв).stdout


def дерево(sha, тека):
    тека.mkdir(parents=True, exist_ok=True)
    subprocess.run(["tar", "-x", "-C", str(тека)], input=git("archive", sha, "джерела"), check=True)
    return тека / "джерела"


def main():
    тмп = Path(sys.argv[1]); тмп.mkdir(parents=True, exist_ok=True)
    шлях = "аудит/проби/річ_колір_розкид_0811/"
    (тмп / "перевимір.json.gz").write_bytes(git("show", ДАНІ + ":" + шлях + "перевимір.json.gz"))
    (тмп / "зберегли_код.tsv").write_bytes(git("show", ДАНІ + ":" + шлях + "зберегли_код.tsv"))
    рядки = list(csv.DictReader(open(тмп / "зберегли_код.tsv", encoding="utf-8"), delimiter="\t"))
    ключі = [р["id"] + "|" + р["файл"] for р in рядки]
    json.dump(ключі, open(тмп / "ключі.json", "w"))
    коди = {}
    for ім, тека, однотонний in (("прогін", дерево(ПРОГІН, тмп / "прогін"), "ні"),
                                 ("main", дерево(БАЗА, тмп / "main"), "ні"),
                                 ("крок", КОРІНЬ / "джерела", "так")):
        вивід = subprocess.run([sys.executable, "-I", "-W", "ignore", "-c", ОДИН, str(тека), str(тмп / "перевимір.json.gz"),
                                str(тмп / "ключі.json"), однотонний], check=True, capture_output=True, cwd=str(тека)).stdout
        коди[ім] = json.loads(вивід)
    d = json.load(gzip.open(тмп / "перевимір.json.gz"))
    поля = ["id", "файл", "hex", "C", "U", "візерунок", "код_запису", "код_прогону", "код_main", "код_крок", "чому_крок"]
    with open(ТУТ / "сукупність.tsv", "w", encoding="utf-8", newline="") as ф:
        п = csv.writer(ф, delimiter="\t", lineterminator="\n"); п.writerow(поля)
        for р, к in zip(рядки, ключі):
            в = next(x for x in d["записи"][р["id"]] if x["файл"] == р["файл"]); з = d["звірка"][к]
            п.writerow([р["id"], р["файл"], р["hex"], з["хрома"][0], з["хрома"][1], в["вимір"]["візерунок"], р["код"],
                        коди["прогін"][к][0] or "невідомо", коди["main"][к][0] or "невідомо",
                        коди["крок"][к][0] or "невідомо", коди["крок"][к][1] or ""])
    оцінки = {р["номер"]: р for р in csv.DictReader(open(ОГЛЯД / "оцінки.tsv", encoding="utf-8"), delimiter="\t")}
    вибірка = list(csv.DictReader(open(ОГЛЯД / "вибірка.tsv", encoding="utf-8"), delimiter="\t"))
    with open(ТУТ / "вибірка_40.tsv", "w", encoding="utf-8", newline="") as ф:
        п = csv.writer(ф, delimiter="\t", lineterminator="\n")
        п.writerow(["номер", "кадр", "id", "hex", "вердикт_огляду", "причина_огляду", "код_запису", "код_main", "код_крок"])
        for р in вибірка:
            к = р["id"] + "|" + р["файл"]; о = оцінки[р["номер"]]
            п.writerow([р["номер"], р["кадр"], р["id"], р["hex"], о["вердикт"], о.get("причина", ""), р["код"],
                        коди["main"][к][0] or "невідомо", коди["крок"][к][0] or "невідомо"])
    # підсумки
    def лік(ім):
        речі = collections.defaultdict(list)
        for р, к in zip(рядки, ключі):
            речі[р["id"]].append(коди[ім][к][0] is not None)
        return (sum(коди[ім][к][0] is not None for к in ключі), sum(any(v) for v in речі.values()),
                sum(all(v) for v in речі.values()), len(речі))
    print("кадрів %d, речей %d" % (len(рядки), len({р["id"] for р in рядки})))
    print("наближення множників: код прогону = записаний — %d з %d" % (
        sum(коди["прогін"][к][0] == р["код"] for р, к in zip(рядки, ключі)), len(рядки)))
    for ім in ("прогін", "main", "крок"):
        print("%-6s код зберегли: кадрів %d, речей (хоч один кадр) %d, речей (усі кадри) %d з %d" % ((ім,) + лік(ім)))
    нейт = collections.Counter()
    for р, к in zip(рядки, ключі):
        if р["код"] in НЕЙТРАЛІ:
            з = d["звірка"][к]
            нейт[("тон невідомо" if з["хрома"][0] <= з["хрома"][1] else "тон відомий",
                  "main з кодом" if коди["main"][к][0] else "main невідомо",
                  "крок з кодом" if коди["крок"][к][0] else "крок невідомо")] += 1
    print("нейтральний код запису: %d кадрів" % sum(нейт.values()))
    for ключ, n in sorted(нейт.items()):
        print("  %s · %s · %s: %d" % (ключ + (n,)))
    зміни = collections.Counter((коди["main"][к][0], коди["крок"][к][1].split(":")[0] if коди["крок"][к][1] else "")
                                for к in ключі if коди["main"][к][0] != коди["крок"][к][0])
    print("main → крок, зняті коди:", ", ".join("%s %d" % (к[0], n) for к, n in зміни.most_common()))
    за_номером = collections.defaultdict(list)
    for р in вибірка:
        к = р["id"] + "|" + р["файл"]
        за_номером[р["номер"]].append((р["код"], коди["main"][к][0], коди["крок"][к][0]))
    ціль = [н for н, о in оцінки.items() if о.get("причина") in ("нейтральний код за невідомого тону", "візерунок")]
    for стовп, ім in ((0, "запис"), (1, "main"), (2, "крок")):
        print("40 речей, %-5s: цільових хибних з кодом %d з %d; правильних з кодом %d з 21 (усі кадри %d)" % (
            ім, sum(any(x[стовп] for x in за_номером[н]) for н in ціль), len(ціль),
            sum(any(x[стовп] for x in за_номером[н]) for н, о in оцінки.items() if о["вердикт"] == "правильна"),
            sum(all(x[стовп] for x in за_номером[н]) for н, о in оцінки.items() if о["вердикт"] == "правильна")))


if __name__ == "__main__":
    main()
