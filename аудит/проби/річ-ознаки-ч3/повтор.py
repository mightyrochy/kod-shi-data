"""Повторює записи викликів мосту на зрізі ДО або поточному коді без моделей."""
import asyncio, gzip, json, pathlib, sys, tempfile


def main():
    """Відокремлює лише кеш кольорів і зберігає всі повернення та винятки."""
    К = pathlib.Path(__file__).resolve().parents[3]
    Д = pathlib.Path(__file__).resolve().parent
    режим = sys.argv[1]
    код = pathlib.Path(tempfile.gettempdir()) / "ознаки-ч3-до" if режим == "до" else К
    sys.path.insert(0, str(код / "джерела/прилади"))
    import знімок_мосту as З
    З.підготувати(str(код / "джерела"))
    import feed
    feed.каталог_на_диску("каталог_brief.xml")
    кеш = pathlib.Path(tempfile.gettempdir()) / ("повтор-ч3-" + режим + ".json")
    кеш.write_text("{}", "utf8")
    вих = []
    for сцена in ("палітра_її", "плитка_робота"):
        запис = З.прочитати(str(К / "аудит/проби/знімок_входи" / (сцена + ".jsonl.gz")))
        рядки = [json.loads(р) for р in запис.splitlines() if р.strip()]
        for рядок in рядки:
            вхід = json.loads(рядок["вхід"])
            if "кеш_кольорів" in вхід:
                вхід["кеш_кольорів"] = str(кеш)
            рядок["вхід"] = json.dumps(вхід, ensure_ascii=False)
        знімок, час = asyncio.run(З.прогнати("\n".join(json.dumps(р, ensure_ascii=False) for р in рядки)))
        записи = [json.loads(р) for р in знімок.splitlines()][1:]
        помилки = [dict(н=з["н"], ім=з["ім"], помилка=з["помилка"]) for з in записи if "помилка" in з]
        (Д / (сцена + "-" + режим + ".jsonl.gz")).write_bytes(gzip.compress(знімок.encode("utf8"), mtime=0))
        вих.append(dict(сцена=сцена, викликів=len(записи), помилки=помилки, секунд=час))
        print(сцена, "викликів", len(записи), "винятків", len(помилки), flush=True)
    (Д / ("повтор-" + режим + ".json")).write_text(json.dumps(вих, ensure_ascii=False, indent=2), "utf8")
    return int(any(x["помилки"] for x in вих))


if __name__ == "__main__":
    sys.exit(main())
