"""Відтворює прогалини відновлення #2016 без мережі та правок реалізації.

Аргумент — тимчасове дерево точної голови PR. Це доказ для звіту, не гейт.
"""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from unittest.mock import patch


def main():
    """Друкує фактичне продовження пагінації та наслідки обірваних файлів."""
    sys.stdout.reconfigure(encoding="utf-8")
    помилки = []
    корінь = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(корінь / "джерела/проби"))
    from каталог_зависла_крамниця_json_проба import прогін, порція, РІЧ
    import обхід

    # Незавершена ініціалізація SQLite до створення таблиць; повтор із тим самим журналом.
    with tempfile.TemporaryDirectory() as журнал:
        база = Path(журнал) / "проходи/json.test/черга.sqlite3"
        база.parent.mkdir(parents=True)
        sqlite3.connect(база).close()
        for повтор in (1, 2):
            with patch.object(обхід, "запустити_крамниці", side_effect=lambda cmd, домени, *а: {д: (0, False) for д in домени}) as запуск:
                try:
                    обхід.main(["--журнал", журнал, "--магазини", "json.test,ok.test", "--циклів", "1"])
                    print("ВІДНОВЛЕННЯ:", обхід.прочитати_стан(журнал), "запусків=", запуск.call_count)
                except Exception as помилка:
                    помилки.append(type(помилка).__name__)
                    print(f"ОБРИВ/SQLite/повтор{повтор}: {type(помилка).__name__}: {помилка}; "
                          f"запусків={запуск.call_count}; стан_записано={(Path(журнал) / 'обхід_стан.tsv').exists()}")

    # Той самий API в обох запусках: 121 непорожня сторінка, потім порожня.
    for сімейство in ("woo", "shopify"):
        with tempfile.TemporaryDirectory() as журнал:
            запити = []

            def відповідь(контекст, адреса, **параметри):
                """Повертає незмінний каталог відповідно до номера запитаної сторінки."""
                сторінка = int(адреса.rsplit("=", 1)[1])
                запити.append(сторінка)
                річ = dict(РІЧ, id=сторінка, handle=f"p{сторінка}",
                           permalink=f"https://json.test/p{сторінка}")
                return порція(сімейство, [річ] if сторінка <= 121 else [])

            до, _ = прогін(журнал, сімейство, відповідь)
            після, _ = прогін(журнал, сімейство, відповідь)
            помилки.extend([] if 121 in запити and після["готово"] == "121" else ["пагінація"])
            print(f"МЕЖА/{сімейство}: запитів={len(запити)}, найбільша_сторінка={max(запити)}, "
                  f"готово={до['готово']}->{після['готово']}, лишилось={після['лишилось']}, "
                  f"причина={після['причина_код']}, товар121={121 in запити}")

    # Валідна картка та префікс наступного запису до першого байта «Я» включно.
    with tempfile.TemporaryDirectory() as журнал:
        файл = Path(журнал) / "сирі/json.test.jsonl"
        файл.parent.mkdir()
        цілий = json.dumps(dict(url="https://json.test/p1", стан="картка"), ensure_ascii=False)
        обірваний = json.dumps(dict(url="https://json.test/p2", назва="Я"), ensure_ascii=False).encode("utf-8")
        файл.write_bytes((цілий + "\n").encode("utf-8") + обірваний[:-3])
        with patch.object(обхід, "запустити_крамниці", side_effect=lambda cmd, домени, *а: {д: (0, False) for д in домени}) as запуск:
            try:
                обхід.main(["--журнал", журнал, "--магазини", "json.test,ok.test", "--циклів", "1"])
                print("ВІДНОВЛЕННЯ:", обхід.прочитати_стан(журнал), "запусків=", запуск.call_count)
            except Exception as помилка:
                помилки.append(type(помилка).__name__)
                print(f"ОБРИВ/JSONL: {type(помилка).__name__}; запусків={запуск.call_count}; "
                      f"стан_записано={(Path(журнал) / 'обхід_стан.tsv').exists()}")

    # Префікс штатного TSV: шапка та незавершений перший рядок.
    with tempfile.TemporaryDirectory() as журнал:
        файл = Path(журнал) / "обхід_стан.tsv"
        файл.write_text("\t".join(обхід.ШАПКА) + "\njson.test\tCATA", encoding="utf-8")
        with patch.object(обхід, "запустити_крамниці", side_effect=lambda cmd, домени, *а: {д: (0, False) for д in домени}) as запуск:
            try:
                обхід.main(["--журнал", журнал, "--магазини", "json.test,ok.test", "--циклів", "1"])
                print("ВІДНОВЛЕННЯ:", обхід.прочитати_стан(журнал), "запусків=", запуск.call_count)
            except Exception as помилка:
                помилки.append(type(помилка).__name__)
                print(f"ОБРИВ/TSV: {type(помилка).__name__}: {помилка}; запусків={запуск.call_count}")


    assert not помилки, помилки

if __name__ == "__main__":
    main()
