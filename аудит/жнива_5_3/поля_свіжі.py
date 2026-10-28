"""Лічба полів 5.1 ДО/ПІСЛЯ на тих самих свіжих HTTP-тілах поточного журналу."""
import collections, importlib.util, json, sqlite3, subprocess, sys, tempfile
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / "zhnyvarka"))
import жниварка as після
from журнал_карток import прочитати


def main():
    """Не виконує HTTP; порівнює парсери до #1520 й поточний на збереженому матеріалі."""
    журнал = Path.home() / ".cache/liusterko/harvest-5.3-20261029"
    with tempfile.TemporaryDirectory() as тека:
        файл = Path(тека) / "до.py"
        файл.write_bytes(subprocess.check_output(["git", "show", "e48c1f1e0^:zhnyvarka/жниварка.py"], cwd=КОРІНЬ))
        сп = importlib.util.spec_from_file_location("до", файл); до = importlib.util.module_from_spec(сп); сп.loader.exec_module(до)
        лічби = {ім: collections.Counter() for ім in ("ДО", "ПІСЛЯ")}
        зразки = []
        for ряд in прочитати(журнал / "сирі/ricamare.com.ua.jsonl")[0]:
            if "відповідь" not in ряд:
                continue
            with sqlite3.connect(журнал / "проходи/ricamare.com.ua/черга.sqlite3") as база:
                код, хеш, ім = база.execute("SELECT код,sha256,файл FROM відповіді WHERE ід=?", (ряд["відповідь"],)).fetchone()
            if код != 200:
                continue
            html = (журнал / "проходи/ricamare.com.ua" / ім).read_text(encoding="utf8", errors="replace")
            зразки.append(dict(url=ряд["url"], sha256=хеш))
            for назва, модуль in (("ДО", до), ("ПІСЛЯ", після)):
                ф = модуль.факти_з_картки(html, ряд["url"], після.рецепт_селекторів("ricamare.com.ua")); ф["url"] = ряд["url"]
                з = модуль.канонічний_запис(ф, dict(домен="ricamare.com.ua"), "картка")
                л = лічби[назва]; л["сторінок"] += 1
                for поле in ("назва", "опис", "склад", "фото", "розміри"):
                    л[поле] += bool(з.get(поле))
                л["пар"] += len(з.get("характеристики_сирі", [])); л["свотчів"] += len(ф.get("свотчі", []))
                л["склад_з_опису"] += з.get("склад_джерело") == "опис"
        print(json.dumps(dict(база="e48c1f1e0^", лічби=лічби, зразки=зразки), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
