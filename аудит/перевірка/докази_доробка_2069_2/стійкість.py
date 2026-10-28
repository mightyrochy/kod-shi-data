"""Вимір читачів жнив і дописування після обриву без зовнішньої мережі."""
from contextlib import redirect_stderr, redirect_stdout
import csv
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / "джерела/проби"))
from каталог_зависла_крамниця_json_проба import обхід, прогін, порція, РІЧ
from виконавець import Виконавець
from журнал_таблиці import дописати


def рядок(домен, **поля):
    """Формує рядок зведення з усіма числовими полями."""
    запис = dict.fromkeys(обхід.ШАПКА_ЗВЕДЕННЯ, "0")
    запис.update(домен=домен, нотатка="кінець", **поля)
    return "\t".join(запис[к] for к in обхід.ШАПКА_ЗВЕДЕННЯ)


def main():
    """Друкує факти збереження сусідів, фізичного курсора й відновлення справжніх жнив."""
    with tempfile.TemporaryDirectory(prefix="стійкість-2069-2-") as журнал:
        файл = Path(журнал) / "зведення_жнив.tsv"
        шапка = ("\t".join(обхід.ШАПКА_ЗВЕДЕННЯ) + "\n").encode()
        цілий = (рядок("old.test") + "\n").encode()
        діагностика = io.StringIO()
        with redirect_stderr(діагностика):
            for межа in range(1, len(цілий)):
                файл.write_bytes(шапка + цілий[:межа])
                ряди, курсор = обхід.останні_рядки(файл, 0)
                assert not ряди and курсор == 1, (межа, ряди, курсор)
                дописати(файл, рядок("ok.test"))
                ряди, курсор = обхід.останні_рядки(файл, курсор)
                assert set(ряди) == {"ok.test"} and курсор == 2, (межа, ряди, курсор)
            пошкоджені = [b"\xff\n", b"short\trow\n", (рядок("bad.test", карток="oops") + "\n").encode()]
            файл.write_bytes(шапка + цілий + b"".join(пошкоджені) + (рядок("last.test") + "\n").encode())
            ряди, курсор = обхід.останні_рядки(файл, 0)
            assert set(ряди) == {"old.test", "last.test"} and курсор == 5
            дописати(файл, рядок("new.test"))
            нові, курсор = обхід.останні_рядки(файл, курсор)
            assert set(нові) == {"new.test"} and курсор == 6
            assert обхід.останні_рядки(файл, курсор) == ({}, курсор)
            файл.write_bytes(b"\xff\n" + цілий)
            assert set(обхід.останні_рядки(файл, 0)[0]) == {"old.test"}
        print(f"Зведення: префіксів {len(цілий) - 1}; сусіди, пошкоджена шапка, курсор 5→6 і повтор без дублів — ОК")
        assert "JOURNAL_CORRUPT" in діагностика.getvalue()

        стан = Path(журнал) / "обхід_стан.tsv"
        добрий = dict(домен="ok.test", стан_код="CATALOG", причина_код="", адрес=1, готово=1,
                     лишилось=0, цикл=1, підстава='кінець "пошуку"')
        with стан.open("w", encoding="utf-8", newline="") as потік:
            писач = csv.DictWriter(потік, обхід.ШАПКА, delimiter="\t")
            писач.writeheader()
            писач.writerow(добрий)
        збережено = стан.read_bytes()
        for хвіст in (b"bad.test\tCATALOG\t\xff\n", b"bad.test\tCATALOG", b"\xff\n" + збережено.split(b"\n", 1)[1]):
            стан.write_bytes(збережено + хвіст)
            with redirect_stderr(діагностика):
                відновлено = обхід.прочитати_стан(журнал)
            assert відновлено == {"ok.test": добрий}, відновлено
        print("Стан TSV: цілий сусід і лапки збережені; пошкоджені рядки не підтверджують завершення — ОК")

        збирач = Виконавець(SimpleNamespace(журнал=журнал))
        позиція = Path(журнал) / "сирі/ok.test.стан.json"
        for дані in (b'{"sitemap":"\xd0', b'{"sitemap":', b'[]'):
            позиція.write_bytes(дані)
            with redirect_stdout(io.StringIO()) as лог:
                _, початок = збирач._стан("ok.test")
            assert початок == {"розділи": {}, "sitemap": [], "помилки": []}
            assert "JOURNAL_CORRUPT" in лог.getvalue()
        print("Курсор JSON: обірвані UTF-8/JSON і чужа форма діагностовані, пошук відновлено — ОК")

    for сімейство in ("woo", "shopify"):
        with tempfile.TemporaryDirectory(prefix="жнива-2069-2-") as журнал:
            файл = Path(журнал) / "зведення_жнив.tsv"
            файл.write_bytes(шапка + "2026-10-28\tbroken.test\tСукня".encode()[:-1])
            with redirect_stderr(io.StringIO()) as лог:
                стан, запитів = прогін(журнал, сімейство, [порція(сімейство, [РІЧ]), порція(сімейство, [])])
            assert стан["стан_код"] == "CATALOG" and стан["готово"] == "1" and стан["лишилось"] == "0"
            assert запитів == 2 and "JOURNAL_CORRUPT" in лог.getvalue()
            стан, повторів = прогін(журнал, сімейство, [])
            assert повторів == 0 and стан["стан_код"] == "CATALOG"
            print(f"Жнива {сімейство}: обірване зведення → картка 1, HTTP 2; повтор HTTP 0 — ОК")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
