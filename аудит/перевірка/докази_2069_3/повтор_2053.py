"""Повтор входів А–В відтворення #2053 на голові злиття; код 1 за збережених вад.

Ті самі обірвані байти й операції; очікування перевернуто з наявності вади на її усунення.
"""
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

корінь = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(корінь / "джерела/проби"))
from каталог_зависла_крамниця_json_проба import обхід, прогін, порція, РІЧ
from каталог_зависла_крамниця_sqlite_проба import прогін as прогін_html
from журнал_проходу import ЖурналПроходу, відбиток_рецепта

вади = []
for джерело in ("jsonl", "зведення"):
    with tempfile.TemporaryDirectory(prefix="review-2053-utf8-") as журнал:
        if джерело == "jsonl":
            файл = Path(журнал) / "сирі/json.test.jsonl"
            файл.parent.mkdir()
            текст = '{"url":"https://json.test/p1","назва":"Сукня'
        else:
            файл = Path(журнал) / "зведення_жнив.tsv"
            текст = "\t".join(обхід.ШАПКА_ЗВЕДЕННЯ) + "\n2026-10-28\tjson.test\tСукня"
        файл.write_bytes(текст.encode("utf-8")[:-1])
        for спроба in (1, 2):
            with patch.object(обхід, "запустити_крамниці", return_value={
                    "json.test": (0, False), "ok.com": (0, False)}) as запуск:
                try:
                    обхід.main(["--журнал", журнал, "--магазини", "json.test,ok.com", "--циклів", "1"])
                except UnicodeDecodeError as e:
                    вади.append(f"А/{джерело}/{спроба}")
                    print(f"А/{джерело}/{спроба}: {e!r}; запусків={запуск.call_count}; ВАДА")
                else:
                    assert запуск.call_count == 1
                    print(f"А/{джерело}/{спроба}: без винятку; запусків={запуск.call_count}; усунено")

for сімейство in ("woo", "shopify"):
    with tempfile.TemporaryDirectory(prefix="review-2053-line-") as журнал:
        файл = Path(журнал) / "сирі/json.test.jsonl"
        файл.parent.mkdir()
        файл.write_bytes(b'{"url":')
        стан, запитів = прогін(журнал, сімейство, [порція(сімейство, [РІЧ]), порція(сімейство, [])])
        підсумок = dict(обхід.результати(журнал, "json.test"))
        добре = запитів == 2 and стан["готово"] == "1" and підсумок == {"картка": 1}
        print(f"Б/{сімейство}: {підсумок=}, {запитів=}, стан={стан}; усунено={добре}")
        Path(журнал, "обхід_стан.tsv").unlink()
        стан, запитів = прогін(журнал, сімейство, [])
        добре &= (стан["стан_код"], стан["готово"], стан["лишилось"], запитів) == ("CATALOG", "1", "0", 0)
        print(f"Б/{сімейство}/без TSV: {стан=}, {запитів=}; усунено={добре}")
        if not добре:
            вади.append(f"Б/{сімейство}")

for втрата in ("обірваний", "відсутній"):
    with tempfile.TemporaryDirectory(prefix="review-2053-card-") as журнал:
        прогін_html(журнал)
        файл = Path(журнал) / "сирі/hang.com.jsonl"
        if втрата == "обірваний":
            файл.write_bytes(b'{"url":')
        else:
            файл.unlink()
        до = обхід.черга(журнал, "hang.com")
        стани, запуски = прогін_html(журнал)
        добре = до == (1, 0) and запуски == ["hang.com"] and стани["hang.com"]["лишилось"] == "0"
        рецепт = dict(домен="hang.com", сімейство="horoshop", транспорт="http", старт="https://hang.com")
        прохід = ЖурналПроходу(Path(журнал) / "проходи", "hang.com", відбиток_рецепта(рецепт), картки=файл)
        try:
            звіт = прохід.звіт()
            добре &= звіт["done"] == 1 and звіт["pending"] == 0
        finally:
            прохід.закрити()
        print(f"В/{втрата}: черга до={до}, {запуски=}, {звіт=}; усунено={добре}")
        if not добре:
            вади.append(f"В/{втрата}")
print(json.dumps(dict(збережені_вади=вади), ensure_ascii=False))
raise SystemExit(int(bool(вади)))
