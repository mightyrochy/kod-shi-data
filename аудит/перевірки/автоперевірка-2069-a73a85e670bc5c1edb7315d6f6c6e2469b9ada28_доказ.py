"""Самостійне відтворення прогалин #2069; аргумент — дерево перевіреної голови.

Без мережі: справжній CLI для зведення; для JSON замінено лише HTTP та запуск процесу.
Це доказ огляду, не новий гейт. Код продукту не змінюється.
"""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def зведення(корінь):
    """Обрив штатного рядка зведення всередині UTF-8; два повтори тим самим CLI."""
    with tempfile.TemporaryDirectory(prefix="огляд-2069-зведення-") as ж:
        cmd = [sys.executable, str(корінь / "zhnyvarka/обхід.py"), "--журнал", ж,
               "--магазини", "ok.test", "--циклів", "1", "--секунд-на-магазин", "10",
               "--заглушка", "успіх"]
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        до = subprocess.run(cmd, capture_output=True, env=env, timeout=30)
        assert до.returncode == 0, до.stderr.decode("utf-8", "replace")
        файл = Path(ж) / "зведення_жнив.tsv"
        дані = файл.read_bytes()
        межа = дані.index(b"\n") + 1
        перший = next(i for i in range(межа, len(дані)) if дані[i] >= 128)
        файл.write_bytes(дані[:перший + 1])
        print(f"З1/ДО: штатний CLI код={до.returncode}; обрив рядка на байті UTF-8")
        for повтор in (1, 2):
            після = subprocess.run(cmd, capture_output=True, env=env, timeout=30)
            помилка = після.stderr.decode("utf-8", "replace").splitlines()[-1]
            print(f"З1/повтор{повтор}: код={після.returncode}; {помилка}")
            assert після.returncode != 0 and "UnicodeDecodeError" in помилка


def журнал_і_пагінація(корінь):
    """Той самий каталог із 121 сторінки: цілий журнал і обрив одного середнього запису."""
    sys.path.insert(0, str(корінь / "джерела/проби"))
    from каталог_зависла_крамниця_json_проба import прогін, порція, РІЧ
    from журнал_карток import прочитати

    for сім in ("woo", "shopify"):
        for пошкодити in (False, True):
            with tempfile.TemporaryDirectory(prefix="огляд-2069-json-") as ж:
                запити = []

                def відповідь(контекст, адреса, **параметри):
                    """Незмінні сторінки 1–121; 122-га порожня."""
                    n = int(адреса.rsplit("=", 1)[1])
                    запити.append(n)
                    річ = dict(РІЧ, id=n, handle=f"p{n}", permalink=f"https://json.test/p{n}")
                    return порція(сім, [річ] if n <= 121 else [])

                with contextlib.redirect_stdout(io.StringIO()):
                    до, _ = прогін(ж, сім, відповідь)
                assert до["готово"] == "120" and до["лишилось"] == "1"
                файл = Path(ж) / "сирі/json.test.jsonl"
                if пошкодити:
                    рядки = файл.read_bytes().splitlines(keepends=True)
                    рядки[59] = b"\xd0\n"
                    файл.write_bytes(b"".join(рядки))
                    assert len(прочитати(файл)[0]) == 119 and прочитати(файл)[1]
                запити.clear()
                for повтор in (1, 2, 3):
                    with contextlib.redirect_stdout(io.StringIO()):
                        після, _ = прогін(ж, сім, відповідь)
                    адреси = {з["url"] for з in прочитати(файл)[0]}
                    є121 = "https://json.test/p121" in адреси if сім == "woo" else "https://json.test/products/p121" in адреси
                    print(f"З2/{сім}/пошкоджено={пошкодити}/повтор{повтор}: "
                          f"готово={після['готово']}; лишилось={після['лишилось']}; "
                          f"причина={після['причина_код']}; HTTP={запити}; товар121={є121}")
                    if пошкодити:
                        assert після["готово"] == "120" and після["лишилось"] == "1"
                        assert після["причина_код"] == "JOURNAL_CORRUPT" and not є121 and not запити
                    else:
                        assert після["готово"] == "121" and після["лишилось"] == "0" and є121
                        assert запити == [121, 122]
                assert пошкодити == прочитати(файл)[1]


def зауваження_рецензента(корінь):
    """Окремо перевіряє два зауваження на голові від chatgpt-codex-connector[bot]."""
    import asyncio
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from каталог_зависла_крамниця_json_проба import прогін, порція, РІЧ, виконавець, обхід

    for сім in ("woo", "shopify"):
        with tempfile.TemporaryDirectory(prefix="огляд-2069-втрата-") as ж:
            with contextlib.redirect_stdout(io.StringIO()):
                до, _ = прогін(ж, сім, [порція(сім, [РІЧ]), порція(сім, [])])
                (Path(ж) / "сирі/json.test.jsonl").write_bytes(b"")
                після, запити = прогін(ж, сім, [])
            print(f"Р2/{сім}/порожній наявний JSONL: готово={до['готово']}->{після['готово']}; "
                  f"лишилось={після['лишилось']}; HTTP={запити}")
            assert до["готово"] == "1" and після["готово"] == "0" and після["лишилось"] == "0"

        with tempfile.TemporaryDirectory(prefix="огляд-2069-новий-") as ж:
            рецепт = dict(домен="json.test", сімейство=сім, транспорт="http", старт="https://json.test",
                          пошук="/products.json?page={n}" if сім == "shopify" else "/wp-json/wc/store/products?page={n}")
            а = SimpleNamespace(журнал=ж, стеля=300, секунд_на_магазин=30, без_огляду=True)
            карток = []
            for повтор in (1, 2):
                речі = [РІЧ] if повтор == 1 else [РІЧ, dict(РІЧ, id=2, handle="p2", permalink="https://json.test/p2")]
                збирач = виконавець.Виконавець(а)
                запити = AsyncMock(side_effect=[порція(сім, речі), порція(сім, [])])
                with contextlib.redirect_stdout(io.StringIO()), patch.object(збирач, "_get", запити):
                    asyncio.run(збирач._магазин(AsyncMock(), рецепт, asyncio.Semaphore(1)))
                карток.append(обхід.виконано_в_журналі(ж, "json.test"))
                if повтор == 2:
                    print(f"Р1/{сім}/нові жнива після кінця: карток={карток[0]}->{карток[1]}; "
                          f"HTTP={запити.await_count}; очікувано=2 картки")
                    assert карток == [1, 1] and запити.await_count == 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    корінь = Path(sys.argv[1]).resolve()
    зведення(корінь)
    журнал_і_пагінація(корінь)
    зауваження_рецензента(корінь)
    print("ПІДСУМОК: 2 нові вади та 2 зауваження рецензента підтверджено; контроль woo і shopify проходить")
