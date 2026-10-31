"""Порівнює промпти речей із фото (розмова й оцінка) і їхніх читачів з базою на записах; без викликів моделей.

Запуск із кореня: python аудит/проби/е2_фото_порівняння.py [SHA бази]. Вхід функції відновлено з даних записаного
промпту (фото з розміром, її речі словами, причина повтору; «outfit» — запис оцінки), відповідь — записана.
"""
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ГІЛКА = "origin/claude/zhyvi-1016-1"
ЗАКІНЧЕННЯ = ("речі_з_фото_шар_.txt", "ОЦІНКА_речі_на_фото.txt")


def прочитати(дерево, записи):
    """Друкує JSON: для кожного запису довжину зібраного промпту, ключі скелета й те, що прочитав читач."""
    sys.path.insert(0, дерево)
    import річ_з_фото as Р
    import оцінка_образу as О
    вих = []
    for запис in json.load(open(записи, encoding="utf-8")):
        дані = json.JSONDecoder().raw_decode(запис["промпт"])[0]   # повтор оцінки дописує нагадування за JSON
        фото = [dict(ід=ф["id"], ширина=ф.get("width"), висота=ф.get("height")) for ф in дані["photos"]]
        if дані.get("outfit"):
            промпт = О.промпт_речей(фото)
            прочитано = О.речі_з_відповіді(запис["відповідь"], фото)
        else:
            власні = дані.get("her_items_in_words") or None
            промпт = Р.промпт_фото(фото, власні, дані.get("format_error"))
            прочитано = Р.речі_з_відповіді_фото(запис["відповідь"], фото, None, власні)
        вих.append(dict(файл=запис["файл"], оцінка=bool(дані.get("outfit")), довжина=len(промпт),
                        скелет=list(json.loads(промпт)["task"]["answer_schema"]["items"][0]),
                        прочитано=json.dumps(прочитано, sort_keys=True, ensure_ascii=False, default=str)))
    print(json.dumps(вих, ensure_ascii=False))


def головна():
    """Дістає записи й дерево бази, запускає обидва дерева окремими процесами й звіряє читачів."""
    корінь = Path(__file__).resolve().parents[2]
    база = sys.argv[1] if len(sys.argv) > 1 else "1749b8264fe9f7519ab06b318c2727e62a46c1a9"
    git = lambda *а: subprocess.run(["git", "-C", str(корінь), *а], capture_output=True, check=True).stdout
    файли = [ф for ф in git("ls-tree", "-r", "--name-only", ГІЛКА).decode().splitlines()
             if ф.endswith(ЗАКІНЧЕННЯ) or ф.endswith(tuple(з + ".gz" for з in ЗАКІНЧЕННЯ))]
    записи = []
    for ф in файли:
        сире = git("show", ГІЛКА + ":" + ф)
        текст = (gzip.decompress(сире) if ф.endswith(".gz") else сире).decode("utf-8")
        промпт, відповідь = текст.split("── ВІДПОВІДЬ", 1)
        промпт = промпт.split("\n", 1)[1].strip()
        if промпт.startswith("{") and '"photos"' in промпт:   # давні записи без збирача — інший текст
            записи.append(dict(файл=ф, промпт=промпт, відповідь=відповідь.split("\n", 1)[1]))
    assert записи, "Записів речей із фото немає"
    дані = [json.JSONDecoder().raw_decode(з["промпт"])[0] for з in записи]
    print("записів %d (пропущено давніх %d): з her_items_in_words %d, з format_error %d" % (
        len(записи), len(файли) - len(записи), sum(bool(д.get("her_items_in_words")) for д in дані),
        sum(bool(д.get("format_error")) for д in дані)))
    with tempfile.TemporaryDirectory(prefix="е2-фото-") as тека:
        Path(тека, "записи.json").write_text(json.dumps(записи, ensure_ascii=False), encoding="utf-8")
        архів = subprocess.run(["git", "-C", str(корінь), "archive", база, "джерела"], capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", тека], input=архів.stdout, check=True)
        запуск = lambda д: json.loads(subprocess.run([sys.executable, "-W", "ignore", __file__, "--дерево", д,
                                                     str(Path(тека, "записи.json"))], capture_output=True,
                                                    check=True, cwd=д).stdout)
        до, після = запуск(str(Path(тека, "джерела"))), запуск(str(корінь / "джерела"))
    for вид in (False, True):
        пари = [(а, б) for а, б in zip(до, після) if а["оцінка"] is вид]
        print("%s: %d записів, довжина %d → %d (сума), коротший %d із %d" % (
            "оцінка" if вид else "розмова", len(пари), sum(а["довжина"] for а, _ in пари),
            sum(б["довжина"] for _, б in пари), sum(б["довжина"] < а["довжина"] for а, б in пари), len(пари)))
        if пари:
            а, б = пари[0]
            print("  скелет без:", sorted(set(а["скелет"]) - set(б["скелет"])), "· новий:",
                  sorted(set(б["скелет"]) - set(а["скелет"])))
    однаково = sum(а["прочитано"] == б["прочитано"] for а, б in zip(до, після))
    print("Записані відповіді речей із фото: однаково прочитано", однаково, "із", len(до))
    assert однаково == len(до), "Читання записаних відповідей змінилось"
    assert all(б["довжина"] < а["довжина"] for а, б in zip(до, після)), "Промпт не коротший за базу"


if __name__ == "__main__":
    прочитати(sys.argv[2], sys.argv[3]) if sys.argv[1:2] == ["--дерево"] else головна()
