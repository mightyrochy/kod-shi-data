"""Відтворює три вади відновлення на точній голові PR #2053 без мережі.

Запуск: python <цей файл> <дерево PR>. Код 0 означає, що вади відтворено.
Це доказ перевірки, а не новий гейт продукту.
"""
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


def main():
    """Перевіряє голову дерева й друкує наслідки обривів журналів."""
    корінь = Path(sys.argv[1]).resolve()
    голова = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=корінь, text=True).strip()
    assert голова == "4d9184708f0d7c177f69bc2f22c496c23562b8e9", голова
    sys.path.insert(0, str(корінь / "джерела/проби"))
    from каталог_зависла_крамниця_json_проба import обхід, прогін, порція, РІЧ
    from каталог_зависла_крамниця_sqlite_проба import прогін as прогін_html
    from журнал_проходу import ЖурналПроходу, відбиток_рецепта

    print("Голова:", голова)
    for джерело in ("jsonl", "зведення"):
        with tempfile.TemporaryDirectory(prefix="перевірка-2053-utf8-") as журнал:
            if джерело == "jsonl":
                файл = Path(журнал) / "сирі/json.test.jsonl"
                файл.parent.mkdir()
                текст = '{"url":"https://json.test/p1","назва":"Сукня'
            else:
                файл = Path(журнал) / "зведення_жнив.tsv"
                текст = "\t".join(обхід.ШАПКА_ЗВЕДЕННЯ) + "\n2026-10-28\tjson.test\tСукня"
            файл.write_bytes(текст.encode("utf-8")[:-1])
            for спроба in (1, 2):
                with patch.object(обхід, "запустити_крамниці") as запуск:
                    try:
                        обхід.main(["--журнал", журнал, "--магазини", "json.test,ok.com", "--циклів", "1"])
                    except UnicodeDecodeError:
                        assert запуск.call_count == 0
                        print(f"А/{джерело}/{спроба}: UnicodeDecodeError; запусків крамниць=0")
                    else:
                        raise AssertionError("Очікуваного падіння немає")

    for сімейство in ("woo", "shopify"):
        with tempfile.TemporaryDirectory(prefix="перевірка-2053-рядок-") as журнал:
            файл = Path(журнал) / "сирі/json.test.jsonl"
            файл.parent.mkdir()
            файл.write_bytes(b'{"url":')
            стан, запитів = прогін(журнал, сімейство, [порція(сімейство, [РІЧ]), порція(сімейство, [])])
            підсумок = dict(обхід.результати(журнал, "json.test"))
            assert запитів == 2 and стан["готово"] == "1" and підсумок == {}
            print(f"Б/{сімейство}: готово={стан['готово']}, читабельних результатів={підсумок}, запитів={запитів}")
            Path(журнал, "обхід_стан.tsv").unlink()
            стан, запитів = прогін(журнал, сімейство, [])
            assert (стан["стан_код"], стан["готово"], стан["лишилось"], запитів) == ("WAIT", "0", "0", 0)
            print(f"Б/{сімейство}/без TSV: WAIT, готово=0, лишилось=0, запитів=0")

    for втрата in ("обірваний", "відсутній"):
        with tempfile.TemporaryDirectory(prefix="перевірка-2053-картки-") as журнал:
            прогін_html(журнал)
            файл = Path(журнал) / "сирі/hang.com.jsonl"
            if втрата == "обірваний":
                файл.write_bytes(b'{"url":')
            else:
                файл.unlink()
            стани, запуски = прогін_html(журнал)
            assert запуски == [] and стани["hang.com"]["лишилось"] == "0"
            assert обхід.черга(журнал, "hang.com") == (1, 1)
            рецепт = dict(домен="hang.com", сімейство="horoshop", транспорт="http", старт="https://hang.com")
            прохід = ЖурналПроходу(Path(журнал) / "проходи", "hang.com", відбиток_рецепта(рецепт), картки=файл)
            try:
                звіт = прохід.звіт()
                assert звіт["pending"] == 1 and звіт["done"] == 0
                print(f"В/{втрата}: обхід готово=1, лишилось=0, запусків=0; ЖурналПроходу done=0, pending=1")
            finally:
                прохід.закрити()


if __name__ == "__main__":
    main()
