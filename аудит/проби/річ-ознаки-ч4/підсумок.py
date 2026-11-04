"""Зводить повні журнали частини, зберігаючи окремо мірило кореня й пробу читачів."""
import collections
import hashlib
import json
import pathlib
import re

Т = pathlib.Path(__file__).resolve().parent
К = Т.parents[2]
СВОЇ = {"face_features.py", "вибір_палітри.py", "колір_простір_шкіра.py", "face_contrast.py",
        "колір_хрома.py", "міст_основи.py", "помада.py", "суд_блиск.py"}


def замір(ім):
    """Читає підсумок та всі місця з повного, успішно завершеного запуску."""
    текст = (Т / (ім + ".txt")).read_text("utf-8")
    останній = текст.strip().splitlines()[-1]
    assert re.fullmatch(r"місць: \d+", останній), останній
    місця = [р for р in текст.splitlines() if re.match(r"^джерела[/\\].*:\d+ ·", р)]
    лічба = collections.Counter(pathlib.PurePosixPath(р.split(":")[0].replace("\\", "/")).name for р in місця)
    assert len(місця) == int(останній.split(": ")[1])
    свої = {ім: лічба[ім] for ім in sorted(СВОЇ)}
    return dict(загалом=len(місця), свої=sum(свої.values()), решта=len(місця) - sum(свої.values()), файли=свої)


def повтори():
    """Порівнює винятки та відхилені відповіді записаних викликів ДО й ПІСЛЯ."""
    import gzip
    результат = {}
    for етап in ("до", "після"):
        записи = json.loads((Т / ("повтор-сцен-" + етап + ".json")).read_text("utf-8"))
        сцени = []
        for запис in записи:
            ім = запис["сцена"]
            рядки = [json.loads(р) for р in gzip.decompress((Т / (ім + "-" + етап + ".jsonl.gz")).read_bytes()).decode().splitlines()][1:]
            відхилені = [р["н"] for р in рядки if р["ім"] == "від_моделі"
                         and isinstance(р.get("результат"), dict)
                         and р["результат"].get("перевірено") is False]
            сцени.append(dict(сцена=ім, викликів=запис["викликів"], винятків=len(запис["помилки"]),
                              відхилені_відповіді=відхилені))
        результат[етап] = сцени
    return результат


def main():
    """Друкує та зберігає числа, за якими перевірка оцінює завершеність наряду."""
    до, після = замір("до"), замір("після")
    дані = dict(до=до, після=після, числова_умова_храповика=після["загалом"] <= до["загалом"],
                решта_не_росте=після["решта"] <= до["решта"], мірило_частини_пройдене=після["свої"] == 0,
                проба_читачів=json.loads((Т / "повтор.json").read_text("utf-8")),
                батарея=json.loads((Т / "батарея.json").read_text("utf-8")), повтор_сцен=повтори(),
                sha256_файлів={ім: hashlib.sha256((К / "джерела" / ім).read_bytes()).hexdigest() for ім in sorted(СВОЇ)})
    (Т / "вимір.json").write_text(json.dumps(дані, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(dict(до=до, після=після, перевірок=len(дані["батарея"]),
                         невдалих=sum(bool(з["код"]) for з in дані["батарея"])), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
