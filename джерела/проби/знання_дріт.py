"""7503: безвтратне інтернування всіх чотирьох станів і чесна ціна нового знання."""
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import знання_речі as З
import знання_дріт as К
import збирач_промптів as П
import пакет_моделі as М


def головна():
    """Повний договір → codebook → той самий договір, без типових припущень."""
    канон = lambda р: json.dumps(р, sort_keys=True, ensure_ascii=False)
    речі = []
    for н, (стан, значення) in enumerate(zip(З.СТАТУСИ, ((20, 1, 2), [10, 30, 0, 5, None], None, None))):
        знання = З.знання({"тип": "dress_generic"})
        знання["color"].update(З.факт(стан, значення, "explicit_fixture"))
        знання["metal"].update(З.факт("measured", "absent", "explicit_fixture"))
        речі.append(dict(n=str(н), name="fixture", **З.на_дріт(знання)))
    речі += [dict(речі[0]), dict(речі[1], n="0"), dict(n="old", hex="#abcdef")]
    дані = dict(task=dict(input=[]), pool=П.таблиця(речі), **{"a~/b": речі[0]})
    дріт = К.ущільнити(дані)
    назад = П.рядки_таблиці(К.відновити(дріт)["pool"])
    assert канон(назад) == канон(речі)
    assert канон(дані["pool"]) == канон(П.таблиця(речі))
    assert len(дріт["knowledge_legend"]["sections"]["/pool"]["rows"]) == 7
    assert канон(К.відновити(дріт)["a~/b"]) == канон(речі[0])
    assert all("knowledge" not in р for р in П.рядки_таблиці(дріт["pool"]))
    текст = json.dumps(дріт, ensure_ascii=False, separators=(",", ":"))
    ціна = М.токенів(json.dumps(дріт["pool"], ensure_ascii=False, separators=(",", ":")))
    assert М.вага_пулу(текст) > ціна and К.ОПИС in дріт["task"]["input"]
    старе = dict(task=dict(input=[]), pool=П.таблиця([dict(n="old", hex="#123456")]))
    assert К.ущільнити(старе) == старе
    print("4 стани, точна Lab, походження/applicability, повтор n та локальний конфлікт: roundtrip без втрат")
    print("pool + codebook + join оплачуються чинним бюджетом; старі дані незмінні")


if __name__ == "__main__":
    головна()
