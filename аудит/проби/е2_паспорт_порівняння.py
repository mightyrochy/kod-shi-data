"""Порівнює промпт виклику 0 і читача паспорта з базою на записаних відповідях; без викликів моделей.

Запуск із кореня: python аудит/проби/е2_паспорт_порівняння.py [SHA бази]. Вхід функції відновлено з даних
записаного промпту (обрано, типове, рукою, паспорт досі, розмова, фото), відповідь — записана.
"""
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ГІЛКА = "origin/claude/zhyvi-1016-1"


def прочитати(дерево, записи):
    """Друкує JSON: для кожного запису довжину зібраного промпту й паспорт, який прочитав читач."""
    sys.path.insert(0, дерево)
    import паспорт_нагоди as П
    вих = []
    for запис in json.load(open(записи, encoding="utf-8")):
        дані = json.JSONDecoder().raw_decode(запис["промпт"])[0]   # повтор дописує нагадування за JSON
        сц = dict(дані.get("обрано") or {}, **(дані.get("типове_не_назване") or {}))
        сц["типові_поля"] = list(дані.get("типове_не_назване") or {})
        сц.update(дані.get("змінено_рукою") or {})
        сц["події_руки"] = [dict(поле=к, значення=в, джерело="hand") for к, в in (дані.get("змінено_рукою") or {}).items()]
        історія = [dict(хто="людина" if р.startswith("She: ") else "ші", текст=р.split(": ", 1)[-1])
                   for р in дані.get("розмова") or []]
        слова = дані.get("її_слова") or (історія[-1]["текст"] if історія else "")
        фото = [dict(ід=ід, ширина=1000, висота=1000) for ід in дані.get("фото_речей") or []] or None
        досі = дані.get("паспорт_досі")
        промпт = П.промпт_паспорта(сц, слова, історія=історія or None, паспорт=досі, фото=фото)
        п = П.паспорт_з_json(запис["відповідь"], сц, слова, паспорт_досі=досі, фото=фото)
        вих.append(dict(файл=запис["файл"], довжина=len(промпт), паспорт=json.dumps(п, sort_keys=True, default=str)))
    print(json.dumps(вих, ensure_ascii=False))


def головна():
    """Дістає записи й дерево бази, запускає обидва дерева окремими процесами й звіряє читача."""
    корінь = Path(__file__).resolve().parents[2]
    база = sys.argv[1] if len(sys.argv) > 1 else "1afa60595e1adbdcee8a54c983b3a42be2b91fd3"
    git = lambda *а: subprocess.run(["git", "-C", str(корінь), *а], capture_output=True, check=True).stdout
    файли = [ф for ф in git("ls-tree", "-r", "--name-only", ГІЛКА).decode().splitlines()
             if ф.endswith(("паспорт_виклик_0_.txt", "паспорт_виклик_0_.txt.gz"))]
    записи = []
    for ф in файли:
        сире = git("show", ГІЛКА + ":" + ф)
        текст = (gzip.decompress(сире) if ф.endswith(".gz") else сире).decode("utf-8")
        промпт, відповідь = текст.split("── ВІДПОВІДЬ", 1)
        промпт = промпт.split("\n", 1)[1].strip()
        if промпт.startswith("{"):     # старі записи 25.09 — український текстовий промпт до збирача
            записи.append(dict(файл=ф, промпт=промпт, відповідь=відповідь.split("\n", 1)[1]))
    assert записи, "Записів виклику 0 немає"
    with tempfile.TemporaryDirectory(prefix="е2-паспорт-") as тека:
        Path(тека, "записи.json").write_text(json.dumps(записи, ensure_ascii=False), encoding="utf-8")
        архів = subprocess.run(["git", "-C", str(корінь), "archive", база, "джерела"], capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", тека], input=архів.stdout, check=True)
        запуск = lambda д: json.loads(subprocess.run([sys.executable, "-W", "ignore", __file__, "--дерево", д,
                                                     str(Path(тека, "записи.json"))], capture_output=True,
                                                    check=True, cwd=д).stdout)
        до, після = запуск(str(Path(тека, "джерела"))), запуск(str(корінь / "джерела"))
    for а, б in zip(до, після):
        print("%s: довжина %d → %d" % (Path(а["файл"]).parent.parent.name, а["довжина"], б["довжина"]))
    однаково = sum(а["паспорт"] == б["паспорт"] for а, б in zip(до, після))
    print("Записані відповіді виклику 0: однаково прочитано", однаково, "із", len(до))
    assert однаково == len(до), "Читання записаних паспортів змінилось"


if __name__ == "__main__":
    прочитати(sys.argv[2], sys.argv[3]) if sys.argv[1:2] == ["--дерево"] else головна()
