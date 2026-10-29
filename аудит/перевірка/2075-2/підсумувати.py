"""Зводить завершені журнали та факти приймання доробки без повтору батареї."""
import json
from pathlib import Path
import subprocess
import sys


def main():
    """Звіряє два каталожні мірила, аркуші, коди батареї та межі гілки."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    читати = lambda ім: json.loads((тека / ім).read_text("utf-8"))
    етап = sys.argv[1] if len(sys.argv) > 1 else "ПІСЛЯ-фінал"
    первісні = читати(етап + "-команди.json")
    assert первісні[-1]["назва"] == "показ", "Батарея ще триває"
    повтор = читати("ГОЛОВА-команди.json")
    assert len(повтор) == 22 and all(к["код"] == к["очікуваний_код"] for к in повтор), повтор
    assert next(к for к in повтор if к["назва"] == "поділ_жнива_офлайн")["саме_10681"]
    нові = {к["назва"]: к for к in повтор}
    команди = [нові.get(к["назва"], к) for к in первісні]
    батарея = {к["назва"]: к["код"] for к in команди if к["назва"] in
               ("дим", "живий-шлях", "протокол", "розділи", "контракти", "показ")}
    assert len(батарея) == 6 and not any(батарея.values()), батарея
    assert читати("ДО-каталог.txt") == читати(етап + "-каталог.txt")
    assert читати("ДО-фото.txt") == читати(етап + "-фото.txt")
    ненульові = {к["назва"]: к["код"] for к in команди if к["код"]}
    assert ненульові == {"поділ_жнива_офлайн": 1}, ненульові
    інвентар = читати("межа-інвентар.json")["підсумки"]
    assert інвентар["ПІСЛЯ"]["обходів"] == 0, інвентар
    assert len(читати("AST-команди.json")) == 14
    assert all(к["код"] == 0 for к in читати("AST-команди.json"))
    дані = json.loads((корінь / "аудит/проби/поверхня_212/після.json").read_text("utf-8"))
    інтервали = [п["споживачеві"][1] for п in дані.values()
                 if п and isinstance(п["споживачеві"][1], dict)]
    вимірів = sum(bool(п) and isinstance(п["споживачеві"][1], str) for п in дані.values())
    assert all(к["колір_тип"] == "інтервал" and len(к["межі"]) == 5 and "hex" not in к for к in інтервали)
    аркуші = list((корінь / "аудит/проби/поверхня_212").glob("аркуш_*.jpg"))
    assert len(аркуші) == 5 and len(дані) == 51 and len(інтервали) == 24 and вимірів == 27
    заборонені = subprocess.check_output(["git", "log", "--format=", "--name-only", "origin/main..HEAD", "--",
                                         ".github", "аудит/адаптери/gemini"], cwd=корінь).decode("utf-8").strip()
    assert not заборонені, заборонені
    файли = subprocess.check_output(["git", "-c", "core.quotepath=false", "diff", "--name-only",
                                    "dd10cf82cd0dad262e39e87b30bc3e7c41f0dc39", "HEAD", "--", "джерела"],
                                   cwd=корінь).decode("utf-8").splitlines()
    assert not (корінь / "аудит/наряди/доробка-2075-2.md").exists()
    факт = dict(голова=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=корінь).decode().strip(),
                батарея=батарея, команд=len(команди),
                етап=етап, повторені_перевірки=повтор,
                первісні_відмови=[к for к in первісні if к["код"]],
                ненульові=[к for к in команди if к["код"]], каталог_тотожний=True, фото_тотожне=True,
                інвентар=інвентар, AST="14/14", наряд_видалено=True,
                аркушів=len(аркуші), записів=len(дані), інтервалів=len(інтервали),
                вимірів=вимірів, заборонених_шляхів=0, власні_файли_коду=файли)
    (тека / "підсумок-механізму.json").write_text(json.dumps(факт, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(факт, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
