"""Друкує шлях решти входів від цитованої відповіді до сценарію й чекліста."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import мовний_шар as М, паспорт_нагоди as П, суд_образу as С, формальність as Ф, дріт_моделі as Д, сценарій as День


if __name__ == "__main__":
    слова = "Виступаю влітку, відновлююсь. Супутник 8. Заявляю злам і колону, щільні колготи в тон взуття."
    поля = (("role", "роль", "speaker", "speaker"), ("season", "сезон", "summer", "літо"),
            ("life_transition", "життєвий_перехід", "recovery", "recovery"),
            ("companion_formality", "супутник_рівень", 8, 8),
            ("declared_break", "заявлений_злам", "yes", True),
            ("declared_column", "заявлена_колона", "yes", True),
            ("matching_opaque_tights", "тон_колготи", "yes", True))
    досі = {}
    for крок in ("unknown", "known", "omitted", "negative", "omitted", "unquoted"):
        слова = ("Виступаю влітку, відновлююсь. Супутник 8. Не заявляю злам чи колону, щільних колготок у тон не буде." if крок == "negative" else слова)
        u = {f: dict(value=("unknown" if крок == "unknown" else "no" if крок == "negative" and isinstance(v, bool) else c),
                     quote=("Вигадана цитата" if крок == "unquoted" else слова)) for f, _, c, v in поля}
        if крок == "omitted": u = {}
        r = М.прийняти_розмову(json.dumps(dict(update=u, text="Записала", need="none")))
        п = М.паспорт_з_шару(r["внутрішня"], {}, паспорт_досі=досі, слова_ходу=[слова])["паспорт"]
        с, _ = П.з_показу({}, п)
        ч = {p["вхід"]: p for p in С.чеклісти([], [], контекст=с)["надлишок"][-8:]}
        for f, k, c, v in поля:
            оч = None if крок == "unknown" else False if isinstance(v, bool) and крок in ("negative", "unquoted") else досі.get(k, v) if крок == "omitted" else v
            if крок == "unquoted": оч = досі.get(k)
            assert с.get(k) == оч, (крок, k, с.get(k), оч)
            assert ч[k]["стан"] == ("без входу" if оч is None else "пройдено"), ч[k]
            if оч is None: assert ч[k]["бракує"][0]["fields"] == [k]
            else:
                assert ч[k]["значення"] == оч and п["цитати_полів"][k] == слова
                assert f in М.паспорт_кодами(п), (f, М.паспорт_кодами(п))
                assert Д.випадок(с)["occasion_season" if f == "season" else f] == ("summer" if f == "season" else оч)
                assert День.день_кодами(с)["season"] == "summer"
        assert ч["гардероб"]["стан"] == "без входу"
        досі = п
        print(крок, "→", {k: с.get(k) for _, k, _, _ in поля})
    assert Ф.сценарій(роль="speaker")["діапазон"] != Ф.сценарій(роль="guest")["діапазон"]
    print("Сім входів, явне False, пропуск ходу й цитата: шлях пройдено")
