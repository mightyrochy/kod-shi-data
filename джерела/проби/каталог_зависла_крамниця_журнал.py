"""Міряє обрив UTF-8 у хвості й середині JSONL та ізоляцію крамниць."""
import asyncio, json, tempfile
from pathlib import Path
from unittest.mock import patch
from каталог_зависла_крамниця_json_проба import обхід, виконавець
from журнал_проходу import ЖурналПроходу


def main():
    """Перебирає кожен байт запису, зберігаючи цілі сусідні картки й повтор обходу."""
    запис = lambda n: json.dumps(dict(url=f"https://bad.test/p{n}", стан="картка", назва="Яї"), ensure_ascii=False).encode()
    помилок = 0
    for хвіст in (True, False):
        for межа in range(1, len(запис(2))):
            with tempfile.TemporaryDirectory() as ж:
                файл = Path(ж) / "сирі/bad.test.jsonl"; файл.parent.mkdir()
                файл.write_bytes(запис(1) + b"\n" + запис(2)[:межа] + (b"" if хвіст else b"\n" + запис(3) + b"\n"))
                try:
                    with patch.object(обхід, "запустити_крамниці", return_value={"bad.test": (0, False), "ok.test": (0, False)}) as запуск:
                        for _ in range(2):
                            обхід.main(["--журнал", ж, "--магазини", "bad.test,ok.test", "--циклів", "1"])
                        assert запуск.call_count == 2 and "ok.test" in запуск.call_args.args[1]
                    стани = обхід.прочитати_стан(ж)
                    assert стани["bad.test"]["причина_код"] == "JOURNAL_CORRUPT"
                    assert стани["bad.test"]["готово"] == (1 if хвіст else 2)
                    а = type("Аргументи", (), {"журнал": ж})()
                    збирач = виконавець.Виконавець(а)
                    assert len(збирач._журнал("bad.test")[1]) == (1 if хвіст else 2)
                    asyncio.run(збирач._огляд(None, "bad.test"))
                    п = ЖурналПроходу(Path(ж) / "проходи", "bad.test", "проба", картки=файл); п.закрити()
                    збирач._пиши(str(файл), dict(url="https://bad.test/new", стан="картка"))
                    assert "https://bad.test/new" in збирач._журнал("bad.test")[1]
                except Exception as п:
                    помилок += 1; print(f"хвіст={хвіст}, байт={межа}: {type(п).__name__}: {п}")
    print(f"Журнал: {2 * (len(запис(2)) - 1)} сценаріїв; помилок={помилок}")
    return int(bool(помилок))


if __name__ == "__main__":
    raise SystemExit(main())
