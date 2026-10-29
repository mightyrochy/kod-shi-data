"""Міряє повтор картки з пошкодженим записом JSONL у справжній SQLite-черзі."""
import tempfile
from pathlib import Path
from каталог_зависла_крамниця_sqlite_проба import обхід, прогін


def main():
    """Відновлює лише крамницю з утраченим підтвердженням DONE у журналі карток."""
    with tempfile.TemporaryDirectory() as ж:
        прогін(ж)
        файл = Path(ж) / "сирі/hang.com.jsonl"
        файл.write_bytes(b'{"url":"https://hang.com/p1","name":"\xd0')
        ч = обхід.черга(ж, "hang.com")
        стани, запуски = прогін(ж)
        с = стани["hang.com"]
        assert ч == (1, 0) and запуски == ["hang.com"]
        assert с["готово"] == "1" and с["лишилось"] == "0" and с["причина_код"] == "JOURNAL_CORRUPT"
        _, знову = прогін(ж)
        assert знову == []
        print(f"SQLite/JSONL: ДО={ч}, повтор={запуски}, готово={с['готово']}, зайвих={знову}")


if __name__ == "__main__":
    main()
