"""Міряє всі місця обриву старого TSV та атомарну заміну нового стану."""
import csv, json, tempfile
from pathlib import Path
from unittest.mock import patch
from каталог_зависла_крамниця_json_проба import обхід
from json_прохід import позначити


def main():
    """Відбудовує кожен префікс TSV з журналу; незавершена заміна лишає попередній файл цілим."""
    збоїв = 0
    with tempfile.TemporaryDirectory(prefix="обрив-стан-") as ж:
        (Path(ж) / "сирі").mkdir()
        (Path(ж) / "сирі/json.test.jsonl").write_text(json.dumps(
            dict(url="https://json.test/p1", стан="картка"), ensure_ascii=False) + "\n", encoding="utf-8")
        позначити(ж, "json.test", True)
        с = dict(домен="json.test", стан_код="CATALOG", причина_код="", адрес=1,
                 готово=1, лишилось=0, цикл=1, підстава="кінець пагінації")
        обхід.записати(ж, {"json.test": с}); файл = Path(ж) / "обхід_стан.tsv"
        цілий = файл.read_bytes()
        for межа in range(len(цілий) + 1):
            файл.write_bytes(цілий[:межа])
            try:
                обхід.main(["--журнал", ж, "--магазини", "json.test", "--циклів", "0"])
                with файл.open(encoding="utf-8") as ф:
                    ряд = next(csv.DictReader(ф, delimiter="\t"))
                збоїв += ряд["готово"] != "1" or ряд["лишилось"] != "0"
            except (TypeError, ValueError, KeyError, StopIteration):
                збоїв += 1
        обхід.записати(ж, {"json.test": с}); попередній = файл.read_bytes()
        with patch.object(обхід.os, "replace", side_effect=OSError("обрив перед заміною")):
            try: обхід.записати(ж, {})
            except OSError: pass
        атомарно = файл.read_bytes() == попередній
        print(f"Б: відновлення префіксів — помилок {збоїв}/{len(цілий)+1}; атомарно={атомарно}")
    return int(bool(збоїв) or not атомарно)


if __name__ == "__main__":
    raise SystemExit(main())
