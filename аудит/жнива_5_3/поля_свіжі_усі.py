"""Лічба полів 5.1 ДО/ПІСЛЯ на свіжих HTTP-тілах журналу смуги Claude, усі крамниці (до 8 карток на крамницю).
Без HTTP: парсер до #1520 (e48c1f1e0^) проти поточного на тих самих збережених тілах."""
import collections, importlib.util, json, sqlite3, subprocess, sys, tempfile
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / "zhnyvarka"))
import жниварка as після
from журнал_карток import прочитати

ПОЛЯ = ("назва", "опис", "склад", "фото", "розміри", "колір", "тканина")
НА_КРАМНИЦЮ = 8


def main():
    журнал = Path.home() / ".cache/liusterko/harvest-5.3-claude"
    with tempfile.TemporaryDirectory() as тека:
        файл = Path(тека) / "до.py"
        файл.write_bytes(subprocess.check_output(["git", "show", "e48c1f1e0^:zhnyvarka/жниварка.py"], cwd=КОРІНЬ))
        сп = importlib.util.spec_from_file_location("до", файл); до = importlib.util.module_from_spec(сп); сп.loader.exec_module(до)
        разом = {ім: collections.Counter() for ім in ("ДО", "ПІСЛЯ")}
        по_крамницях = {}
        for сирий in sorted((журнал / "сирі").glob("*.jsonl")):
            дом = сирий.name[:-len(".jsonl")]
            бд = журнал / "проходи" / дом / "черга.sqlite3"
            if not бд.is_file():
                continue
            взято = 0
            лічби = {ім: collections.Counter() for ім in ("ДО", "ПІСЛЯ")}
            with sqlite3.connect(бд) as база:
                for ряд in прочитати(сирий)[0]:
                    if взято >= НА_КРАМНИЦЮ:
                        break
                    if "відповідь" not in ряд or "/ru/" in ряд["url"] or "/en/" in ряд["url"]:
                        continue
                    р = база.execute("SELECT код,файл FROM відповіді WHERE ід=?", (ряд["відповідь"],)).fetchone()
                    if not р or р[0] != 200 or not (журнал / "проходи" / дом / р[1]).is_file():
                        continue
                    html = (журнал / "проходи" / дом / р[1]).read_text(encoding="utf8", errors="replace")
                    try:
                        рец = після.рецепт_селекторів(дом)
                        вихід = []
                        for модуль in (до, після):
                            ф = модуль.факти_з_картки(html, ряд["url"], рец); ф["url"] = ряд["url"]
                            вихід.append((ф, модуль.канонічний_запис(ф, dict(домен=дом), "картка")))
                    except Exception:
                        continue
                    взято += 1
                    for назва, (ф, з) in zip(("ДО", "ПІСЛЯ"), вихід):
                        л = лічби[назва]; л["сторінок"] += 1
                        for поле in ПОЛЯ:
                            л[поле] += bool(з.get(поле))
                        л["пар"] += len(з.get("характеристики_сирі", [])); л["свотчів"] += len(ф.get("свотчі", []))
                        л["склад_з_опису"] += з.get("склад_джерело") == "опис"
            if взято:
                по_крамницях[дом] = {к: dict(в) for к, в in лічби.items()}
                for к in разом:
                    разом[к].update(лічби[к])
        print(json.dumps(dict(база="e48c1f1e0^", разом={к: dict(в) for к, в in разом.items()}, крамниці=по_крамницях), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
