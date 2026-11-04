"""Невідомого власника не обходять колір жнив, старий кеш чи новий піксельний вимір."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import фід_каталог as ф, колір_річ as к

def main():
    """Проганяє справжній читач каталогу з невідомим варіантом та всіма запасними джерелами."""
    xml = '<yml_catalog><shop><categories><category id="1">Сукні</category></categories><offers><offer id="x" available="true"><name>Сукня червона</name><price>1000</price><currencyId>UAH</currencyId><categoryId>1</categoryId><url>https://shop.test/products/dress?variant=11</url><picture>https://shop.test/a.jpg</picture><param name="магазин">shop.test</param><param name="слот">сукня</param><param name="стать">жіноче</param><param name="Колір">червоний</param>{}</offer></offers></shop></yml_catalog>'
    зб = {"x@shop.test": dict(версія=2, фото="https://shop.test/a.jpg", впевненість=0.99,
                              колір_основний=dict(слово="червоний", hex="#bd1823", lab=[41, 61, 38], колір_тип="вимір"))}
    def пікселі(*_):
        """Виявляє недозволений вихід у вимір першого picture."""
        raise AssertionError("невідомий кадр пішов у піксельний вимір")
    ф.колір_з_фото = ф.палітра_принту = пікселі
    with tempfile.TemporaryDirectory() as тека:
        шлях, кеш = Path(тека) / "каталог.xml", Path(тека) / "кеш.json"
        кеш.write_text(json.dumps({"x@shop.test": dict(lab=[41, 61, 38], впевненість=0.99)}), encoding="utf-8")
        до = кеш.read_bytes()
        for збагачення in ({}, зб):
            шлях.write_text(xml.format('<param name="власник_кадру">"невідомо"</param>'), encoding="utf-8")
            результат = ф.прочитати_каталог(str(шлях), кеш=str(кеш), збагачення=збагачення)["каталог"]
            assert len(результат) == 1 and к.явний_тип_кольору(результат[0]) != "вимір", результат
        assert кеш.read_bytes() == до
        шлях.write_text(xml.format(""), encoding="utf-8")
        старий = ф.прочитати_каталог(str(шлях), ліміт_фото=0, кеш=str(кеш), збагачення={})["каталог"]
        assert len(старий) == 1 and к.явний_тип_кольору(старий[0]) == "вимір", старий
    print("Каталог: невідомий варіант — без виміру з жнив/кешу/picture; старий формат читається; кеш не змінено")

if __name__ == "__main__":
    main()
