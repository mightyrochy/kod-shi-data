"""Відтворює ДО/ПІСЛЯ режимів і повну звірку синтаксису збереженого плану за 05.11."""
import importlib.util
import json
from pathlib import Path
import subprocess
import types

КОРІНЬ = Path(__file__).resolve().parents[3]
ТУТ = Path(__file__).resolve().parent
БАЗА = "fedeab0f789b7189b1be6a0211d5dfcad6d66c9d"
ПЛАН = "439529075c6318f9737558bda659a143d628c36b:аудит/проби/Е1-нічний-живий-20261105/ПЛАН.json"


def виконати():
    """Порівнює всі сцени без параметра та два режими мірила; друкує кількість неканонічних полів плану."""
    шлях = КОРІНЬ / "аудит/проби/записати_сцену.py"
    до = types.ModuleType("до")
    до.__file__ = str(шлях)
    код = subprocess.check_output(["git", "show", БАЗА + ":аудит/проби/записати_сцену.py"], cwd=КОРІНЬ).decode("utf-8")
    exec(compile(код, str(шлях), "exec"), до.__dict__)
    опис = importlib.util.spec_from_file_location("після", шлях)
    після = importlib.util.module_from_spec(опис)
    опис.loader.exec_module(після)
    def сцена(модуль, id_):
        """Читає результат або точну причину відмови сцени."""
        try:
            return модуль.сцена_реєстру(id_)
        except ValueError as причина:
            return str(причина)
    ids = [р.split("|")[0] for р in шлях.with_name("живі_сцени.txt").read_text(encoding="utf-8").splitlines() if р and not р.startswith("#")]
    різні = [id_ for id_ in ids if сцена(до, id_) != сцена(після, id_)]
    мірило = []
    for id_, режим in (("ж4_робота", "повне +фото"), ("ж1_свято_тріада", "повне")):
        старі = до.сцена_реєстру(id_)["змінні"]
        нові = після.сцена_реєстру(id_, режим)["змінні"]
        мірило.append({"сцена": id_, "режим": режим, "до": {к: старі[к] for к in ("DO", "OTSINKA", "FOTO") if к in старі},
                       "після": {к: нові[к] for к in ("DO", "OTSINKA", "FOTO") if к in нові}})
        assert "DO" not in нові and нові["OTSINKA"] == "0" and нові["FOTO"] == ("1" if "+фото" in режим else "0")
    звіт = {"база": БАЗА, "сцен_без_зміни": len(ids) - len(різні), "розбіжностей_без_режиму": len(різні), "мірило": мірило}
    (ТУТ / "ДО-ПІСЛЯ.json").write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert not різні, різні
    план = json.loads(subprocess.check_output(["git", "show", ПЛАН], cwd=КОРІНЬ).decode("utf-8"))
    відмови, полів = [], 0
    for id_, питання in план["scenes"].items():
        for пункт in питання:
            поля = пункт["question"].split("→")
            if len(поля) < 2:
                continue
            полів += 1
            try:
                після.змінні_режиму(id_, поля[1].strip(), "")
            except ValueError as причина:
                відмови.append({"сцена": id_, "pr": пункт["pr"], "режим": поля[1].strip(), "причина": str(причина)})
    звіт = {"джерело": ПЛАН, "сцен": len(план["scenes"]), "полів_режиму": полів, "неканонічних": len(відмови), "відмови": відмови}
    (ТУТ / "синтаксис_плану_0511.json").write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Без параметра: {len(ids)} сцен, розбіжностей {len(різні)}; обидва мірильні режими пройшли")
    print(f"Старий план: {len(план['scenes'])} сцен, полів режиму {полів}, неканонічних {len(відмови)}")


if __name__ == "__main__":
    виконати()
