"""Відтворює контрольні шість вставок і 14 точок золота на історичному коді та даних."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
ІСТОРІЯ = "c68cfea3"

ПРОГРАМА = '''
import json,sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "джерела"))
import palettes as П, фід_каталог as ФК, фід_збагачення as З
зб = З.читати_збагачення()
кат = ФК.прочитати_каталог(ФК.каталог_на_диску("каталог_повний.xml"), 0)["каталог"]
хроматичні, золото = [], []
ювелірних = 0
for р in кат:
    if not П.слот_металу(р.get("слот"), р.get("тип")):
        continue
    ювелірних += 1
    if not р.get("метал"):
        continue
    if П.хроматична_вставка(р):
        хроматичні.append(р["id"])
    з = зб.get(р["id"]) or {}
    if not З.збагачення_придатне(з) or (з.get("версія") or 1) < 2:
        continue
    слово, lab, _ = З.колір_збагачення(з)
    точки = [(слово, lab)] if lab is not None else []
    д = З.другий_колір(з.get("колір_другий"))
    if д and д[1] is not None:
        точки.append((д[0], д[1]))
    for слово, lab in точки:
        if П.метал_речі(tuple(lab), р.get("слот")) == "золото":
            золото.append({"id": р["id"], "слово": слово, "lab": lab})
дані = {"історія": "c68cfea3", "товарів": len(кат), "ювелірних": ювелірних,
        "хроматичні": хроматичні, "точки_золота": золото}
Path(sys.argv[1]).write_text(json.dumps(дані, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(дані, ensure_ascii=False, indent=1), flush=True)
assert len(хроматичні) == 6 and len(золото) == 14, "історичні числа не відтворились"
'''


def main():
    """Ізолює потрібний історичний код у tmp, не перемикаючи робочу гілку."""
    дерево = КОРІНЬ.parent / "tmp/контроль_c68cfea3"
    дерево.mkdir(exist_ok=True)
    файли = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", ІСТОРІЯ, "--", "джерела"], cwd=КОРІНЬ).decode().splitlines()
    файли = [ш for ш in файли if ш.count("/") == 1 and ш.endswith((".py", ".json", ".gz", ".md"))]
    файли.append("каталог_повний.xml.gz")
    маніфест = {}
    for ш in файли:
        байти = subprocess.check_output(["git", "show", ІСТОРІЯ + ":" + ш], cwd=КОРІНЬ)
        ціль = дерево / ш
        ціль.parent.mkdir(parents=True, exist_ok=True)
        ціль.write_bytes(байти)
        маніфест[ш] = hashlib.sha256(байти).hexdigest()
    (ТЕКА / "контроль_маніфест.json").write_text(json.dumps(маніфест, ensure_ascii=False, indent=1), encoding="utf-8")
    скрипт = дерево / "контроль.py"
    скрипт.write_text(ПРОГРАМА, encoding="utf-8")
    with (ТЕКА / "контроль_історія.txt").open("w", encoding="utf-8") as лог:
        р = subprocess.run([sys.executable, str(скрипт), str(ТЕКА / "контроль.json")], cwd=дерево,
                           stdout=лог, stderr=subprocess.STDOUT)
    print("Історичний контроль: код", р.returncode, flush=True)
    raise SystemExit(р.returncode)


if __name__ == "__main__":
    main()
