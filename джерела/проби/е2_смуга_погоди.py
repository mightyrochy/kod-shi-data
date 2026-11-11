"""Перевіряє смугу на шві розмова → паспорт → сценарій → дріт без моделі."""
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import внутрішня_мова as В
import мовний_шар as М
import паспорт_нагоди as П
import сценарій as С, дріт_моделі as Д


def хід(код, цитата="мороз", досі=None):
    """Пропускає відповідь через розбір ходу, сторожа цитати й писаря паспорта."""
    відповідь = {"update": {"weather_band": {"quote": цитата, "value": код}} if код else {}, "need": "none"}
    р = М.прийняти_розмову(json.dumps(відповідь, ensure_ascii=False))
    return М.паспорт_з_шару(р["внутрішня"], {}, паспорт_досі=досі, слова_ходу=["надворі мороз"])["паспорт"]


if __name__ == "__main__":
    assert "temperature_c" not in В.СЦЕНАРІЙ and "weather_feel" not in В.СЦЕНАРІЙ
    assert "weather_feel" not in В.ТАБЛИЦЯ and not hasattr(С, "темп_для_правил")
    for код in В.ТАБЛИЦЯ["weather_band"]:
        п = хід(код, досі={"темп_c": 18, "картка_запиту": {"темп_c": {"значення": 18, "джерело": "hand"}}})
        н, незнайомі = П.з_показу({"темп_c": 18}, п)
        assert п["смуга_погоди"] == н["смуга_погоди"] == код and not незнайомі
        assert С.день_кодами(н)["weather_band"] == М.паспорт_кодами(п)["weather_band"] == Д.випадок(п)["weather_band"] == код
        assert п["виміри"]["weather_band"] == код and п["цитати_полів"]["смуга_погоди"] == "мороз"
        assert "темп_c" not in п["картка_запиту"]
        assert "темп_c" not in п and "темп_c" not in н and "temperature_c" not in С.день_кодами(н)
        assert хід(None, досі=п)["смуга_погоди"] == код
    п = хід("cold")
    п["картка_запиту"]["виміри"] = {"значення": {"temperature_c": 18}, "джерело": "default", "уривок": ""}
    assert хід("hot", досі=п)["смуга_погоди"] == "hot"
    assert "temperature_c" not in json.dumps(хід("hot", досі=п)["картка_запиту"])
    assert not хід("invented").get("смуга_погоди")
    assert хід("frost", "сніг")["картка_запиту"]["смуга_погоди"]["джерело"] == "reading"
    assert хід("invented", досі=п)["смуга_погоди"] == "cold"
    assert not П.з_показу({}, {"погода_відчуття": "frost"})[0].get("темп_c")
    assert П.значення_шапки(п, "смуга_погоди") == '"cold"'
    print("смуга погоди: 7/7; цитата, наступний хід, виправлення, чужий код і відсутність градусів — пройдено")
