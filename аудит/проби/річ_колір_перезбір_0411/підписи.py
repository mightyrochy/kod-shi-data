"""Зберегти назву, слот і заявлений колір кожної речі вибірки з того самого каталогу."""
import json
from pathlib import Path
import sys

ТЕКА = Path(__file__).resolve().parent
sys.path.insert(0, str(ТЕКА.parents[2] / "джерела"))
import feed as Ф
from жнива_промпти import тип_речі


def головна():
    """Дати очному огляду предмет виміру, щоб не оцінити сусідню річ на моделі."""
    ід = {р["id"] for р in json.loads((ТЕКА / "вибірка.json").read_text(encoding="utf-8"))}
    офери = Ф.читати_yml(Ф.каталог_на_диску())[0]
    записи = {о["id"]: dict(назва=о.get("назва"), url=о.get("url"), тип=тип_речі(о),
              колір_сирий=о.get("колір_сирий"), колір_назва=о.get("колір_назва"))
              for о in офери if о.get("id") in ід}
    assert len(записи) == len(ід), (len(записи), len(ід))
    (ТЕКА / "підписи.json").write_text(json.dumps(записи, ensure_ascii=False, indent=2), encoding="utf-8")
    print("підписів:", len(записи))


if __name__ == "__main__":
    головна()
