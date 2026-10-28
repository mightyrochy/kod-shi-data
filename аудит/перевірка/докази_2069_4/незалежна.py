"""Власні проби перевірки 2069-4; заміщено лише межу процесу та HTTP.

Запуск: python незалежна.py <дерево коду>. Приладів виконавця не імпортує.
"""
import asyncio
import contextlib
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "zhnyvarka"))
import виконавець as в
import обхід as о
from журнал_карток import прочитати


def річ(домен, n):
    return dict(id=n, handle=f"p{n}", permalink=f"https://{домен}/p{n}",
                name="Чорна сукня", title="Чорна сукня", images=[dict(src=f"https://{домен}/p.jpg")],
                variants=[dict(option1="M", available=True)],
                attributes=[dict(name="Розмір", terms=[dict(name="M")])])


def обхід(дім, сім, домени):
    HTTP, запуски = [], []
    а = SimpleNamespace(журнал=str(дім), стеля=300, секунд_на_магазин=10, без_огляду=True)
    збирач = в.Виконавець(а)

    async def get(контекст, url, **kwargs):
        домен = urlparse(url).netloc
        n = int(parse_qs(urlparse(url).query)["page"][0])
        HTTP.append((домен, n))
        речі = [річ(домен, 1), річ(домен, 2)] if n == 1 else []
        return 200, json.dumps({"products": речі} if сім == "shopify" else речі)

    def запуск(cmd, магазини, *args):
        for домен in магазини:
            запуски.append(домен)
            рецепт = dict(домен=домен, сімейство=сім, транспорт="http", старт=f"https://{домен}",
                         пошук="/products.json?page={n}" if сім == "shopify" else "/wp-json/wc/store/products?page={n}")
            with patch.object(збирач, "_get", get):
                asyncio.run(збирач._магазин(AsyncMock(), рецепт, asyncio.Semaphore(1)))
        return {д: (0, False) for д in магазини}

    with patch.object(о, "запустити_крамниці", запуск):
        о.main(["--журнал", str(дім), "--магазини", ",".join(домени), "--циклів", "1"])
    return HTTP, запуски


def матриця(сім, джерело, обрив):
    with tempfile.TemporaryDirectory(prefix="review-2069-4-") as tmp:
        дім = Path(tmp)
        обхід(дім, сім, ["old.com"])
        шляхи = {"зведення": дім / "зведення_жнив.tsv", "стан": дім / "обхід_стан.tsv",
                 "JSONL": дім / "сирі/old.com.jsonl"}
        файл = шляхи[джерело]
        цілі = файл.read_bytes().splitlines(keepends=True)
        if обрив == "межа":
            # Справжня втрата останнього цілого запису, збережено попередній рядок.
            файл.write_bytes(b"".join(цілі[:-1]))
        elif обрив == "без LF":
            файл.write_bytes(b"".join(цілі).rstrip(b"\r\n"))
        else:
            if джерело == "JSONL":
                # Друга картка відома кешу; першу мусить зберегти читач.
                хвіст = '{"url":"https://old.com/p2","назва":"Сукня'.encode()
                файл.write_bytes(цілі[0] + (хвіст[:-1] if обрив == "UTF-8" else хвіст[:24]))
            else:
                хвіст = ('2026-10-28\tbad.com\tСукня' if джерело == "зведення" else 'bad.com\tWAIT\tСукня').encode()
                файл.write_bytes(b"".join(цілі) + (хвіст[:-1] if обрив == "UTF-8" else хвіст[:14]))
        HTTP, запуски = обхід(дім, сім, ["old.com", "ok.com"])
        повтор, повторні = обхід(дім, сім, ["old.com", "ok.com"])
        записи, битий = прочитати(дім / "сирі/old.com.jsonl")
        стани = о.прочитати_стан(дім)
        підсумки, _ = о.останні_рядки(дім / "зведення_жнив.tsv", 0)
        return dict(сімейство=сім, файл=джерело, обрив=обрив, HTTP=HTTP, запуск=запуски,
                    повтор_HTTP=повтор, повтор_запуск=повторні, битий_JSONL=битий,
                    діагностика_стану=any(с["причина_код"] == "JOURNAL_CORRUPT" for с in стани.values()),
                    пройдено=("ok.com" in запуски and HTTP == [("ok.com", 1), ("ok.com", 2)]
                              and not повтор and not повторні and цілі[0] in файл.read_bytes()
                              and {з["url"] for з in записи} == {f"https://old.com/{'products/' if сім == 'shopify' else ''}p{n}" for n in (1, 2)}
                              and all(стани[д]["лишилось"] == 0 for д in ("old.com", "ok.com"))
                              and "ok.com" in підсумки
                              and (джерело == "зведення" and обрив == "межа" or "old.com" in підсумки)))


def дописування(джерело):
    with tempfile.TemporaryDirectory(prefix="review-2069-4-append-") as tmp:
        дім = Path(tmp)
        збирач = в.Виконавець(SimpleNamespace(журнал=tmp))
        if джерело == "JSONL":
            файл = дім / "сирі/a.com.jsonl"
            файл.write_bytes(b'{"url":"https://a.com/p0"}\n' + '{"url":"Сукня'.encode()[:-1])
            збирач._пиши(str(файл), dict(url="https://a.com/p1", стан="картка"))
            записи, битий = прочитати(файл)
            добре = битий and [з["url"] for з in записи] == ["https://a.com/p0", "https://a.com/p1"]
        elif джерело == "зведення":
            файл = дім / "зведення_жнив.tsv"
            with файл.open("ab") as ф:
                ф.write('2026-10-28\ta.com\tСукня'.encode()[:-1])
            обхід(дім, "woo", ["ok.com"])
            добре = "ok.com" in о.останні_рядки(файл, 0)[0]
        else:
            файл = дім / "обхід_стан.tsv"
            файл.write_bytes(("\t".join(о.ШАПКА) + "\na.com\tWAIT\tСукня").encode()[:-1])
            о.записати(tmp, {"ok.com": dict(домен="ok.com", стан_код="WAIT", причина_код="UNKNOWN",
                         адрес=1, готово=0, лишилось=1, цикл=1, підстава="нова")})
            добре = о.прочитати_стан(tmp)["ok.com"]["адрес"] == 1
        return dict(дописування=джерело, пройдено=bool(добре))


def курсор_JSON():
    with tempfile.TemporaryDirectory(prefix="review-2069-4-json-") as tmp:
        збирач = в.Виконавець(SimpleNamespace(журнал=tmp))
        файл = Path(tmp) / "сирі/a.com.стан.json"
        файл.write_bytes('{"розділи":{"Сукня'.encode()[:-1])
        _, стан = збирач._стан("a.com")
        return dict(курсор_JSON=True, пройдено=стан == {"розділи": {}, "sitemap": [], "помилки": []})


def фізичний_курсор():
    from журнал_таблиці import дописати
    with tempfile.TemporaryDirectory(prefix="review-2069-4-cursor-") as tmp:
        файл = Path(tmp) / "зведення_жнив.tsv"
        def ряд(домен):
            поля = {к: "0" for к in в.ШАПКА_ЗВЕДЕННЯ}
            поля["домен"] = домен
            return "\t".join(поля[к] for к in в.ШАПКА_ЗВЕДЕННЯ)
        файл.write_bytes(("\t".join(в.ШАПКА_ЗВЕДЕННЯ) + "\n" + ряд("a.com") + "\n").encode()
                         + 'Сукня'.encode()[:-1] + b"\n" + (ряд("b.com") + "\n").encode())
        перші, позиція = о.останні_рядки(файл, 0)
        дописати(файл, ряд("c.com"))
        другі, наступна = о.останні_рядки(файл, позиція)
        треті, кінець = о.останні_рядки(файл, наступна)
        return dict(фізичний_курсор=[позиція, наступна, кінець],
                    пройдено=set(перші) == {"a.com", "b.com"} and set(другі) == {"c.com"}
                    and not треті and [позиція, наступна, кінець] == [3, 4, 4])


def main():
    результати = []
    for сім in ("woo", "shopify"):
        for джерело in ("зведення", "стан", "JSONL"):
            for обрив in ("UTF-8", "середина", "межа", "без LF"):
                лог = io.StringIO()
                try:
                    with contextlib.redirect_stdout(лог), contextlib.redirect_stderr(лог):
                        факт = матриця(сім, джерело, обрив)
                    діагноз = "JOURNAL_CORRUPT" in лог.getvalue() or факт["діагностика_стану"]
                    потребує = обрив in ("UTF-8", "середина") or (обрив == "без LF" and джерело != "JSONL")
                    факт.update(діагностика=діагноз)
                    факт["пройдено"] &= not потребує or діагноз
                except Exception as e:
                    факт = dict(сімейство=сім, файл=джерело, обрив=обрив, пройдено=False,
                                виняток=f"{type(e).__name__}: {e}")
                результати.append(факт)
                print(json.dumps(факт, ensure_ascii=False), flush=True)
    for джерело in ("зведення", "стан", "JSONL", "курсор_JSON", "фізичний_курсор"):
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                факт = (курсор_JSON() if джерело == "курсор_JSON" else фізичний_курсор()
                        if джерело == "фізичний_курсор" else дописування(джерело))
        except Exception as e:
            факт = dict(дописування=джерело, пройдено=False, виняток=f"{type(e).__name__}: {e}")
        результати.append(факт)
        print(json.dumps(факт, ensure_ascii=False), flush=True)
    провали = sum(not ф["пройдено"] for ф in результати)
    print(json.dumps(dict(випадків=len(результати), пройдено=len(результати)-провали, провалів=провали), ensure_ascii=False))
    return int(bool(провали))


if __name__ == "__main__":
    raise SystemExit(main())
