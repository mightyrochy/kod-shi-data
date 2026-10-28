"""Зводить завершені журнали та факти приймання доробки без повтору батареї."""
import json
from pathlib import Path
import subprocess


def main():
    """Звіряє два каталожні мірила, аркуші, коди батареї та межі гілки."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    читати = lambda ім: json.loads((тека / ім).read_text("utf-8"))
    команди = читати("ПІСЛЯ-команди.json")
    assert команди[-1]["назва"] == "показ", "Батарея ще триває"
    батарея = {к["назва"]: к["код"] for к in команди if к["назва"] in
               ("дим", "живий-шлях", "протокол", "розділи", "контракти", "показ")}
    assert len(батарея) == 6 and not any(батарея.values()), батарея
    assert читати("ДО-каталог.txt") == читати("ПІСЛЯ-каталог.txt")
    assert читати("ДО-фото.txt") == читати("ПІСЛЯ-фото.txt")
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
    assert all(ф.startswith(("джерела/прилади/", "джерела/проби/")) for ф in файли), файли
    факт = dict(голова=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=корінь).decode().strip(),
                батарея=батарея, команд=len(команди),
                ненульові=[к for к in команди if к["код"]], каталог_тотожний=True, фото_тотожне=True,
                аркушів=len(аркуші), записів=len(дані), інтервалів=len(інтервали),
                вимірів=вимірів, заборонених_шляхів=0, власні_файли_коду=файли)
    (тека / "підсумок.json").write_text(json.dumps(факт, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(факт, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
