"""Зворотний переклад наосліп: пари «вихідний опис — опис, відновлений із запису» для судді й лічба вердиктів.

    python аудит/звіти/опис-речі-кодом/суд.py в2 записи <тека_поза_репозиторієм>  → в2/записи_для_зворотного.json (без описів)
    python аудит/звіти/опис-речі-кодом/суд.py в2 пари <тека_поза_репозиторієм>    → в2/пари_суду.tsv; ключ — у теку поза
        репозиторієм, щоб суддя його не бачив (після суду — копія `ключ_суду.json` у в2/)
    python аудит/звіти/опис-речі-кодом/суд.py в2 звести                           → в2/лічба_суду.tsv, в2/підсумок_суду.json

Відновлювач бачить лише `запит_перекладу.md` (значення осей) і записи прогону 1; суддя — лише пари. Серед пар —
підставні (відновлений опис ІНШОЇ речі): скільки з них суддя відкинув — міра самого судді.
"""
import csv
import json
import random
import sys
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent
ЗЕРНО = 20261117
ПІДСТАВНИХ = 24
ПРОГІН = ТЕКА / (sys.argv[1] if len(sys.argv) > 1 else "в2")


def описи():
    with open(ТЕКА / "описи.tsv", encoding="utf-8") as ф:
        return {р["ключ"]: р["опис"] for р in csv.DictReader(ф, delimiter="\t")}


def записи(куди):
    sys.path.insert(0, str(ТЕКА))
    import запис as З
    З.ОСІ = json.loads((ПРОГІН / "осі.json").read_text(encoding="utf-8"))
    сирі = json.loads((ПРОГІН / "переклад_1.json").read_text(encoding="utf-8"))
    ключі = list(сирі)
    random.Random(ЗЕРНО).shuffle(ключі)
    таємні = {f"р{i + 1:03d}": к for i, к in enumerate(ключі)}
    (ПРОГІН / "записи_для_зворотного.json").write_text(json.dumps(
        {т: З.рядком(З.перевірити(сирі[к]["запис"])) for т, к in таємні.items()}, ensure_ascii=False, indent=0) + "\n",
        encoding="utf-8")
    (куди / "ключ_записів.json").write_text(json.dumps(таємні, ensure_ascii=False), encoding="utf-8")
    print(len(таємні), "записів")


def пари(куди):
    таємні = json.loads((куди / "ключ_записів.json").read_text(encoding="utf-8"))
    відновлені = json.loads((ПРОГІН / "зворотний_переклад.json").read_text(encoding="utf-8"))
    вихідні = описи()
    зерно = random.Random(ЗЕРНО)
    рядки = [(к, к) for к in таємні.values()]
    ключі = sorted(таємні.values())
    for к in зерно.sample(ключі, ПІДСТАВНИХ):
        інший = зерно.choice([x for x in ключі if x != к and x.split("/")[0] == к.split("/")[0]])
        рядки.append((к, інший))
    зерно.shuffle(рядки)
    за_ключем = {к: відновлені[т] for т, к in таємні.items()}
    ключ = {}
    with open(ПРОГІН / "пари_суду.tsv", "w", encoding="utf-8", newline="") as ф:
        п = csv.writer(ф, delimiter="\t", lineterminator="\n")
        п.writerow(["пара", "А", "Б"])
        for i, (а, б) in enumerate(рядки):
            п.writerow([f"п{i + 1:03d}", вихідні[а], за_ключем[б]])
            ключ[f"п{i + 1:03d}"] = {"А": а, "Б": б}
    (куди / "ключ_суду.json").write_text(json.dumps(ключ, ensure_ascii=False, indent=0), encoding="utf-8")
    print(len(рядки), "пар, з них підставних", ПІДСТАВНИХ)


def звести():
    ключ = json.loads((ПРОГІН / "ключ_суду.json").read_text(encoding="utf-8"))
    вердикти = json.loads((ПРОГІН / "вердикти_суду.json").read_text(encoding="utf-8"))
    with open(ПРОГІН / "пари_суду.tsv", encoding="utf-8") as ф:
        тексти = {р["пара"]: р for р in csv.DictReader(ф, delimiter="\t")}
    підсумок = {}
    with open(ПРОГІН / "лічба_суду.tsv", "w", encoding="utf-8", newline="") as ф:
        п = csv.writer(ф, delimiter="\t", lineterminator="\n")
        п.writerow(["пара", "річ", "підставна_з", "вердикт", "що_не_так", "А", "Б"])
        for пара, к in ключ.items():
            в = вердикти[пара]
            підставна = к["А"] != к["Б"]
            група = "підставні" if підставна else "90 описів" if к["А"].startswith("sproba") else к["А"].split("/")[0]
            г = підсумок.setdefault(група, {"усього": 0, "те саме": 0, "загублено": 0, "додано": 0, "інше": 0, "не те": {}})
            г["усього"] += 1
            г[в["вердикт"]] += 1
            if в["вердикт"] != "те саме" and not підставна:
                г["не те"][к["А"]] = f"{в['вердикт']}: {в.get('що', '')}"
            п.writerow([пара, к["А"], к["Б"] if підставна else "", в["вердикт"], в.get("що", ""), тексти[пара]["А"],
                        тексти[пара]["Б"]])
    (ПРОГІН / "підсумок_суду.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({г: {к: v for к, v in д.items() if к != "не те"} for г, д in підсумок.items()}, ensure_ascii=False))


if __name__ == "__main__":
    if sys.argv[2] == "звести":
        звести()
    else:
        {"записи": записи, "пари": пари}[sys.argv[2]](Path(sys.argv[3]))
