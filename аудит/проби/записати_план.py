"""Запускає сцени нічного чи автоживого JSON-плану з режимами питань PR."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from записати_сцену import режим_питання, сцена_реєстру, вхід_реєстру, змінні_режиму


def режим_питань(id_, питання):
    """Обирає режим, що покриває всі явно названі режими сцени, або лишає вибір реєстру; питання, яке прилад не виконає, — ValueError."""
    режими, додаткові, вхід = [], {}, вхід_реєстру(id_)
    for пункт in питання:
        режим = режим_питання(пункт["question"])
        if режим is None:
            continue
        try:
            змінні = змінні_режиму(id_, режим, вхід)
        except ValueError as причина:
            raise ValueError(f"PR #{пункт['pr']}: {причина}") from причина
        режими.append(змінні)
        входові = {о.partition("=")[0] for о in вхід.split()}
        for ключ, значення in змінні.items():
            if ключ in ("OTSINKA", "FOTO", "DO") or ключ in входові:
                continue
            if додаткові.setdefault(ключ, значення) != значення:
                raise ValueError(f"PR #{пункт['pr']}: Сцена {id_}: питання PR суперечать у {ключ}: {додаткові[ключ]} і {значення}")
    if not режими:
        return None
    # Оцінка — окремий шлях; разом з іншими питаннями потребує повного прогону зі сценами 6/6б.
    шляхи = [р.get("DO") for р in режими]
    оцінка = "otsinka" in шляхи or any("DO" not in р and "OTSINKA" not in р for р in режими)
    if оцінка and шляхи != ["otsinka"] * len(шляхи):
        режим = "повне (стенд: сцени 6 і 6б)"
    else:
        порядок = {"rozmova": "розмова", "palitra": "палітра", "koment": "коментар", None: "повне"}
        режим = "оцінка" if оцінка else next(порядок[шлях] for шлях in reversed(порядок) if шлях in шляхи)
    if any(р["FOTO"] == "1" for р in режими):
        режим = режим.replace(" (", " +фото (") if " (" in режим else режим + " +фото"
    if додаткові:
        режим += ", " + " ".join(f"{к}={в}" for к, в in додаткові.items())
    return режим


def команди_плану(план, збірка, кеш, вихід, node="node"):
    """Готує команди придатних сцен і причини відмов решти до створення тек або запуску першої сцени: одна сцена не зупиняє план."""
    команди, відмови = [], {}
    for id_, питання in план["scenes"].items():
        try:
            режим = режим_питань(id_, питання)
            сцена_реєстру(id_, режим)
        except ValueError as причина:
            відмови[id_] = str(причина)
            continue
        команда = [sys.executable, str(Path(__file__).with_name("записати_сцену.py")),
                   str(збірка), str(кеш), str(вихід / id_), "--сцена", id_, "--node", node]
        if режим is not None:
            команда += ["--режим", режим]
        команди.append(команда)
    return команди, відмови


def виконати():
    """Послідовно записує сцени плану та зберігає команди й коди виходу."""
    а = argparse.ArgumentParser(description=__doc__)
    а.add_argument("план", type=Path)
    а.add_argument("збірка", type=Path)
    а.add_argument("кеш", type=Path)
    а.add_argument("вихід", type=Path)
    а.add_argument("--лише-змінні", action="store_true")
    а.add_argument("--node", default="node")
    п = а.parse_args()
    план = json.loads(п.план.read_text(encoding="utf-8-sig"))
    команди, відмови = команди_плану(план, п.збірка, п.кеш, п.вихід, п.node)
    print(f"Сцен у плані: {len(команди) + len(відмови)} · з змінними: {len(команди)} · відмов сцени: {len(відмови)}", file=sys.stderr, flush=True)
    for id_, причина in відмови.items():
        print(f"ВІДМОВА СЦЕНИ {id_}: {причина}", file=sys.stderr, flush=True)
    if п.лише_змінні:
        for команда in команди:
            subprocess.run(команда + ["--лише-змінні"], check=True)
        return 0
    п.вихід.mkdir(parents=True, exist_ok=True)
    код = 0
    with (п.вихід / "done.txt").open("a", encoding="utf-8") as журнал:
        for id_, причина in відмови.items():
            журнал.write(json.dumps({"сцена": id_, "відмова": причина, "час": datetime.now(timezone.utc).isoformat()},
                                    ensure_ascii=False) + "\n")
        for команда in команди:
            запис = {"початок": datetime.now(timezone.utc).isoformat(), "команда": команда}
            запис["rc"] = subprocess.run(команда).returncode
            запис["кінець"] = datetime.now(timezone.utc).isoformat()
            журнал.write(json.dumps(запис, ensure_ascii=False) + "\n")
            журнал.flush()
            код = max(код, запис["rc"])
    return код


if __name__ == "__main__":
    try:
        raise SystemExit(виконати())
    except ValueError as причина:
        raise SystemExit("ВІДМОВА: " + str(причина))
