"""Годинник розбору: HTTP 400, повтор не-JSON і докат без нової успішної речі; мережа — заглушка."""
import contextlib, io, itertools, json, pathlib, sys, tempfile, urllib.error
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import каталог_розбір_прогін as П


def main():
    """Проганяє дві речі та друкує лічбу журналу, знаменник прогнозу й збережене тіло помилки."""
    офери = [dict(id="проба-%d" % і, назва="Сукня", категорія="", параметри={}) for і in range(2)]
    тіло = '{"error":"контекст замалий"}'
    помилка = lambda: urllib.error.HTTPError("http://проба", 400, "Bad Request", {}, io.BytesIO(тіло.encode()))
    відповідь = lambda текст: io.BytesIO(json.dumps({"choices": [{"message": {"content": текст}}]}).encode())
    with tempfile.TemporaryDirectory() as тека, contextlib.redirect_stdout(io.StringIO()), \
            patch.object(П.ФР, "читати_yml", return_value=(офери, {})), \
            patch.object(П.ФК, "каталог_на_диску", return_value="проба"), \
            patch.object(П, "вибірка", return_value=[("решта", о) for о in офери]), \
            patch.object(П.time, "time", side_effect=itertools.count(10)):
        with patch.object(П.urllib.request, "urlopen", side_effect=[помилка(), відповідь("не JSON"), відповідь("{}")]):
            П.прогін("проба", куди=тека, паралельно=1)
        читати = lambda ім: json.loads((pathlib.Path(тека) / ім).read_text())
        перший, годинник = читати("прогін.json"), читати("годинник.json")
        with patch.object(П.urllib.request, "urlopen", side_effect=помилка()) as мережа:
            П.прогін("проба", куди=тека, паралельно=1)
        докат, запитів = читати("годинник.json"), мережа.call_count
    дія = годинник["дія"]
    знаменник = годинник["прогноз"]["стадії"]["річ"]["зроблено"]
    тіло_є = тіло in (перший["речі"][0]["впало"] or "")
    спроби = годинник.get("спроби", [])
    print("викликів %s · спроб %s · впало %s · повторів %s · успішних у прогнозі %s" %
          (дія["викликів"], дія["спроб"], дія.get("впало"), дія["повторів"], знаменник))
    print("тіло HTTP 400 у прогін.json: %s · у спробах: %s" % (тіло_є, any(з.get("http_body") == тіло for з in спроби)))
    print("докат: нових запитів %s · прогноз %s" % (запитів, докат["прогноз"]["стадії"]))
    return (дія["викликів"] == 2 and дія["спроб"] == 3 and дія.get("впало") == 1 and
            дія["повторів"] == {"invalid_json": 1} and знаменник == 1 and тіло_є and
            any(з.get("http_status") == 400 and з.get("http_body") == тіло for з in спроби) and
            запитів == 1 and not докат["прогноз"]["стадії"])

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
