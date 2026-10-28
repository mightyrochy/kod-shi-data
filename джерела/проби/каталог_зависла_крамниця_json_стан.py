"""Міряє відновлення старого хибного нуля й обірваного стану JSON-пагінації."""
import tempfile
from pathlib import Path
from каталог_зависла_крамниця_json_проба import обхід, прогін, порція, РІЧ
from json_прохід import позначити

def main():
    """Довіряє завершенню лише з цілим журналом; старий маркер без суми відбудовує прохід."""
    for сім in ("woo", "shopify"):
        for вміст in (None, "{", "{}", "null", '{"завершено":false}', '{"завершено":true}'):
            with tempfile.TemporaryDirectory(prefix="обхід-json-стан-") as ж:
                файл = Path(ж) / "проходи" / "json.test" / "json_стан.json"
                if вміст is not None:
                    файл.parent.mkdir(parents=True)
                    файл.write_text(вміст, encoding="utf-8")
                обхід.записати(ж, {"json.test": dict(домен="json.test", стан_код="WAIT", причина_код="UNKNOWN",
                                 адрес=0, готово=0, лишилось=0, цикл=1, підстава="стор. 1: HTML 502")})
                стан, запитів = прогін(ж, сім, [порція(сім, [РІЧ]), порція(сім, [])])
                оч = 2
                print(f"{сім}/стан={вміст}: запитів={запитів}/{оч}, залишок={стан['лишилось']}")
                assert запитів == оч and стан["лишилось"] == "0"
        with tempfile.TemporaryDirectory(prefix="обхід-json-скидання-") as ж:
            прогін(ж, сім, [порція(сім, [])])
            (Path(ж) / "обхід_стан.tsv").unlink()
            позначити(ж, "json.test", False)
            стан, _ = прогін(ж, сім, [(502, "<html>Bad Gateway</html>")] * 3)
            assert стан["лишилось"] == "1" and стан["причина_код"] == "EXCEPTION"
            print(f"{сім}/новий прохід після завершення: залишок=1, причина=EXCEPTION")
    print("JSON-стан: 14/14 сценаріїв пройдено")

if __name__ == "__main__":
    main()
