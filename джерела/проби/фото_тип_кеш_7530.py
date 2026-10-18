"""Жива база бачить появу optional overlay; лише синтетичний каталог."""
from фото_тип_синтетика import *
from unittest.mock import patch
import фід_каталог as К
import таблиця_каталогу as Т


def порожня_таблиця(*args):
    yield
    return None


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as td:
        feed = Path(td, "fixture.xml"); feed.write_text("synthetic")
        calls, legacy = [], {}
        def каталог(*args):
            calls.append(1)
            return len(calls)
        К._КЕШ_БАЗИ.clear()
        with patch.object(К, "читати_збагачення", lambda: legacy), patch.object(К, "ключ_фото_типу", lambda: З.ключ_фото_типу(td)), patch.object(К, "_прочитати_каталог", каталог), patch.object(Т, "база_кроками", порожня_таблиця):
            assert К._база_прогону(str(feed), кеш=None) == 1
            assert К._база_прогону(str(feed), кеш=None) == 1
            Path(td, Ф.ФАЙЛ).write_text("{}")
            assert К._база_прогону(str(feed), кеш=None) == 2
            Path(td, Ф.ПРИЙМАННЯ_ФАЙЛ).write_text("{}")
            assert К._база_прогону(str(feed), кеш=None) == 3
        К._КЕШ_БАЗИ.clear()
    print("SYNTHETIC_ONLY cache: reuse1, overlay→2, receipt→3; PASS")
