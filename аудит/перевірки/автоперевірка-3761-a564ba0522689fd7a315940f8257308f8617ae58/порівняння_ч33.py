"""Звіряє повні виводи стенда 60 образів × три тіла на спільному кеші каталогу."""
import difflib
import pathlib

тека = pathlib.Path(__file__).resolve().parent
виводи = []
for ім in ["base-ч33.txt", "head-ч33.txt"]:
    текст = (тека / ім).read_text(encoding="utf-8")
    assert "код виходу: 0" in текст, ім
    виводи.append([р for р in текст.splitlines() if р and not р.startswith(("команда:", "код:"))])
різниця = list(difflib.unified_diff(*виводи, fromfile="ДО", tofile="ПІСЛЯ", lineterm=""))
лічб = sum(р.startswith("  ") and " · " in р for р in виводи[0])
підсумок = "ДО = ПІСЛЯ: %s; рядків лічби: %d; образів 60 × тіл 3 = 180.\n" % (not різниця, лічб)
(тека / "порівняння-ч33.txt").write_text(підсумок + "\n".join(різниця), encoding="utf-8")
print(підсумок, end="")
assert not різниця, "Вердикти змінилися"
