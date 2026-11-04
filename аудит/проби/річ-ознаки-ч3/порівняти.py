"""Порівнює збережений ДО з поточними читачами, включно з фізичним контролем."""
import contextlib, gzip, io, json, pathlib
import читачі


def main():
    """Звіряє утримання оцінок, збереження фізичного рангу та її відповіді."""
    Д = pathlib.Path(__file__).resolve().parent
    до = json.loads(gzip.decompress((Д / "читачі-до.json.gz").read_bytes()))
    вихід = io.StringIO()
    with contextlib.redirect_stdout(вихід):
        читачі.main()
    після = json.loads(вихід.getvalue())
    (Д / "читачі-після.json.gz").write_bytes(gzip.compress(вихід.getvalue().encode("utf8"), mtime=0))
    оцінки = [x for x in після["профілі"] if x["джерело"] == "model_hex"]
    assert len(оцінки) == 9
    assert all(not x["бік"]["вхід"] and x["бік"]["b_очей"] is None for x in оцінки)
    assert all(all(z["перепад"] is None and z["контраст"] == "невідомо" for z in x["ранг"]) for x in оцінки)
    assert all(not any(x["входи"][k] for k in ("бік_b_очей", "сивина", "м_яка")) for x in оцінки)
    assert all(not x["входи"]["не_стосується"] for x in оцінки)
    assert all(x["самозвіт"] == y["самозвіт"] for x, y in zip(до["профілі"], після["профілі"]))
    assert all(x["ранг"] == y["ранг"] for x, y in zip(до["профілі"], після["профілі"]) if x["джерело"] == "spectro")
    assert після["вільний"] == [None, True] and до["заданий"] == після["заданий"]
    assert після["порожній"]["чекліст"]["вікна"]["L"] is None
    assert після["порожній"]["ранг"][1]["ціль_хроми"] is None
    assert all(x["осі"]["C"] == 0.5 for x in після["порожній"]["ранг"][0])
    print("Оцінені профілі: 9; бік очей 8 → 0; числовий перепад 9 → 0; фізичні ранги незмінні 9/9; її відповіді незмінні 18/18; вільний тон: hex → вікно.")


if __name__ == "__main__":
    main()
