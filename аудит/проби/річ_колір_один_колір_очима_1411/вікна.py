"""Частина 2: яке вікно зняло код з виміру — код 73 кадрів вибірки на шести деревах між прогоном #3315 і main.

Дерева: прогін 8c8d6adb → до #3382 (його база 7e8f4bde) → голова #3382 c056cdad → до #3405 (його база 58277383) →
голова #3405 c23e8a7b → main 8dafc111 (база кроку; `джерела/` поточного main a6b373f4 з ним однакові). Код судять
за записом, як `відтворити.py` кроку (`../річ_колір_один_колір_1411/`): `surface.код_розкиду(lab, U, (k, k, k))`,
без правки кроку. Слово крамниці — параметр «Колір» і «колір_джерело» `каталог_записи_v1.jsonl.gz` поточного дерева.

    git fetch --depth 1 origin claude/Річ-колір-вимір
    git fetch --depth 1 origin 7e8f4bde21935798775ea6e94c5609d39051d639 c056cdad3bdf2d5f61280863e10eee85cae59a8b \
        582773833a4a20b5547921dfd5eb343f1e7fbb8e c23e8a7b4fe2fb30346c42c739cde46e821c5771 8c8d6adb06eb2927773dc0cdb2a35d0310887ed3
    python3 -I аудит/проби/річ_колір_один_колір_очима_1411/вікна.py <тимчасова_тека>
Пише `вікна.tsv` тут.
"""
import ast, csv, gzip, json, subprocess, sys
from pathlib import Path

ТУТ = Path(__file__).resolve().parent
КОРІНЬ = ТУТ.parents[2]
ДАНІ = "c7b37862c5195f823e0ef211cd8ecd718b498f95"
ДЕРЕВА = [("прогін", "8c8d6adb06eb2927773dc0cdb2a35d0310887ed3"),
          ("до_3382", "7e8f4bde21935798775ea6e94c5609d39051d639"),
          ("голова_3382", "c056cdad3bdf2d5f61280863e10eee85cae59a8b"),
          ("до_3405", "582773833a4a20b5547921dfd5eb343f1e7fbb8e"),
          ("голова_3405", "c23e8a7b4fe2fb30346c42c739cde46e821c5771"),
          ("main", "8dafc111")]
ОДИН = r'''
import gzip, json, sys
sys.path.insert(0, sys.argv[1])
import surface as S
d = json.load(gzip.open(sys.argv[2])); вих = {}
for к in json.load(open(sys.argv[3])):
    ід, файл = к.split("|", 1)
    в = next(x for x in d["записи"][ід] if x["файл"] == файл); з = d["звірка"][к]; k = з["поправка"]
    код, _, чому = S.код_розкиду(tuple(в["lab"]), з["хрома"][1], [k] * 3 if k else None)
    слово, у_вікні = S.слово_з_lab(tuple(в["lab"]))
    вих[к] = [код, чому, слово, у_вікні]
json.dump(вих, sys.stdout, ensure_ascii=False)
'''


def git(*а):
    return subprocess.run(["git", "-C", str(КОРІНЬ), *а], check=True, capture_output=True).stdout


def main():
    тмп = Path(sys.argv[1]); тмп.mkdir(parents=True, exist_ok=True)
    (тмп / "перевимір.json.gz").write_bytes(git("show", ДАНІ + ":аудит/проби/річ_колір_розкид_0811/перевимір.json.gz"))
    вибірка = list(csv.DictReader(git("show", "HEAD:аудит/проби/річ_колір_розкид_очима_1411/вибірка.tsv")
                                  .decode("utf-8").splitlines(), delimiter="\t"))
    ключі = [р["id"] + "|" + р["файл"] for р in вибірка]
    json.dump(ключі, open(тмп / "ключі40.json", "w"))
    коди = {}
    for ім, sha in ДЕРЕВА:
        т = тмп / ("д_" + ім); т.mkdir(exist_ok=True)
        if not (т / "джерела").exists():
            subprocess.run(["tar", "-x", "-C", str(т)], input=git("archive", sha, "джерела"), check=True)
        коди[ім] = json.loads(subprocess.run([sys.executable, "-I", "-W", "ignore", "-c", ОДИН, str(т / "джерела"),
                                              str(тмп / "перевимір.json.gz"), str(тмп / "ключі40.json")],
                                             check=True, capture_output=True, cwd=str(т / "джерела")).stdout)
    ід = {р["id"].split("@")[0] for р in вибірка}
    крамниця = {}
    for р in map(json.loads, gzip.open(КОРІНЬ / "каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8")):
        if р.get("ід") in ід:
            п = р["параметри"]; п = ast.literal_eval(п) if isinstance(п, str) else п
            п = {x[0]: x[1] for x in п}
            крамниця[р["ід"]] = (п.get("Колір", ""), п.get("колір_джерело", ""))
    with open(ТУТ / "вікна.tsv", "w", encoding="utf-8", newline="") as ф:
        п = csv.writer(ф, delimiter="\t", lineterminator="\n")
        п.writerow(["номер", "кадр", "id", "hex"] + [ім for ім, _ in ДЕРЕВА] +
                   ["зняв", "слово_точки_main", "точка_в_певному_вікні_main", "чому_main", "Колір_крамниці", "колір_джерело"])
        for р, к in zip(вибірка, ключі):
            ряд = [коди[ім][к][0] or "невідомо" for ім, _ in ДЕРЕВА]
            зняв = next((ДЕРЕВА[і + 1][0] for і in range(len(ряд) - 1) if ряд[і] != "невідомо" and ряд[і + 1] == "невідомо"), "")
            зняв = {"голова_3382": "#3382", "голова_3405": "#3405"}.get(зняв, зняв)
            м = коди["main"][к]
            п.writerow([р["номер"], р["кадр"], р["id"], р["hex"]] + ряд +
                       [зняв, м[2], "так" if м[3] else "ні", м[1] or ""] + list(крамниця.get(р["id"].split("@")[0], ("", ""))))
    print("кадрів", len(ключі))


if __name__ == "__main__":
    main()
