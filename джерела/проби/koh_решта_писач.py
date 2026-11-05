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
        оновлення = {поле: dict(value=("unknown" if крок == "unknown" else "no" if крок == "negative" and isinstance(значення, bool) else код),
                     quote=("Вигадана цитата" if крок == "unquoted" else слова)) for поле, _, код, значення in поля}
        if крок == "omitted": оновлення = {}
        розбір = М.прийняти_розмову(json.dumps(dict(update=оновлення, text="Записала", need="none")))
        п = М.паспорт_з_шару(розбір["внутрішня"], {}, паспорт_досі=досі, слова_ходу=[слова])["паспорт"]
        с, _ = П.з_показу({}, п)
        ч = {пункт["вхід"]: пункт for пункт in С.чеклісти([], [], контекст=с)["надлишок"][-8:]}
        for поле, ключ, код, значення in поля:
            оч = None if крок == "unknown" else False if isinstance(значення, bool) and крок in ("negative", "unquoted") else досі.get(ключ, значення) if крок == "omitted" else значення
            if крок == "unquoted": оч = досі.get(ключ)
            assert с.get(ключ) == оч and (not isinstance(оч, bool) or isinstance(с.get(ключ), bool)), (крок, ключ, с.get(ключ), оч)
            assert ч[ключ]["стан"] == ("без входу" if оч is None else "пройдено"), ч[ключ]
            if оч is None: assert ч[ключ]["бракує"][0]["fields"] == [ключ]
            else:
                assert ч[ключ]["значення"] == оч and п["цитати_полів"][ключ] == слова
                assert поле in М.паспорт_кодами(п), (поле, М.паспорт_кодами(п))
                assert Д.випадок(с)["occasion_season" if поле == "season" else поле] == ("summer" if поле == "season" else оч)
                assert День.день_кодами(с)["season"] == "summer"
        assert ч["гардероб"]["стан"] == "без входу"
        досі = п
        print(крок, "→", {ключ: с.get(ключ) for _, ключ, _, _ in поля})
    assert Ф.сценарій(роль="speaker")["діапазон"] != Ф.сценарій(роль="guest")["діапазон"]
    print("Сім входів, явне False, пропуск ходу й цитата: шлях пройдено")
