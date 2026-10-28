# -*- coding: utf-8 -*-
"""Друкує прогрес json-сімейства: однаковий розмір порцій не означає зупинку курсора."""
import csv, json, sys, tempfile
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
import обхід

def main():
    """Порівнює накопичені результати адрес із розміром одного проходу без sqlite-черги."""
    помилки = []
    for стан in ("CATALOG", "WAIT"):
        with tempfile.TemporaryDirectory(prefix="обхід-json-") as ж:
            файл = Path(ж) / "сирі" / "test.com.jsonl"
            файл.parent.mkdir()
            записи = [dict(url="/p0", стан="картка" if стан == "CATALOG" else "нижче_порогу")]
            файл.write_text(json.dumps(записи[0]) + "\n", encoding="utf-8")
            обхід.записати(ж, {"test.com": dict(домен="test.com", стан_код=стан, причина_код="",
                             адрес=1, готово=1, лишилось=1, цикл=1, підстава="стеля 1")})
            номер = [0]
            def завершити(timeout):
                """Доповнює журнал однією новою адресою за цикл."""
                номер[0] += 1
                записи.append(dict(записи[0], url=f"/p{номер[0]}"))
                файл.write_text("".join(json.dumps(з) + "\n" for з in записи), encoding="utf-8")
                return 0
            ряд = dict(нотатка="стеля 1", карток="0", адрес_знайдено="1", відкрито="1")
            with patch.object(обхід, "останні_рядки", return_value=({"test.com": ряд}, 1)), patch.object(
                обхід.subprocess, "Popen", return_value=Mock(wait=завершити)):
                (Path(ж) / "зведення_жнив.tsv").write_text("домен\n", encoding="utf-8")
                обхід.main(["--журнал", ж, "--магазини", "test.com", "--циклів", "3"])
            with open(Path(ж) / "обхід_стан.tsv", encoding="utf-8") as ф:
                с = next(csv.DictReader(ф, delimiter="\t"))
            print(f"json/{стан}: циклів={номер[0]}, готово={с['готово']}, причина={с['причина_код']}")
            помилки.append(номер[0] != 3 or с["готово"] != "4" or с["причина_код"] == "NO_PROGRESS")
    return int(any(помилки))

if __name__ == "__main__":
    sys.exit(main())
