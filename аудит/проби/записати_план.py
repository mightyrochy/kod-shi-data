"""Запускає сцени нічного чи автоживого JSON-плану з режимами питань PR."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from записати_сцену import режим_питання, сцена_реєстру, вхід_реєстру, змінні_режиму


def у_git(тека):
    """Тека всередині робочого дерева git (`.git` — тека клону чи файл worktree) — без виклику git."""
    тека = Path(тека).resolve()
    return any((к / ".git").exists() for к in (тека, *тека.parents))


def зберегти(вихід, план, повідомлення, гілка=None):
    """Коміт теки прогону й файла плану одразу після кроку, лише цих шляхів; з `гілка` — ще й пуш у неї.
    Обрив (світло, `NO_REPORT`, зупинка рушія) коштує щонайбільше поточної сцени: записане вже в гілці звіту, і
    наступний план бере його прогнаним (`Get-AutoRanPairs`). Збій git не зупиняє прогону — причина в stderr, а
    наступний коміт чи пуш забере й цей запис. Повертає True, коли коміт є."""
    if not у_git(вихід):
        return False
    шляхи = [str(Path(вихід).resolve())] + ([str(Path(план).resolve())] if план and у_git(Path(план).parent) else [])
    корінь = Path(вихід).resolve()
    def git(*аргументи):
        return subprocess.call(["git", *аргументи], cwd=str(корінь))
    if git("add", "-A", "--", *шляхи):
        print(f"КОМІТ: git add не вдався — {повідомлення}", file=sys.stderr, flush=True)
        return False
    if not git("diff", "--cached", "--quiet", "--", *шляхи):
        return False
    if git("commit", "-q", "-m", повідомлення, "--", *шляхи):
        print(f"КОМІТ: git commit не вдався — {повідомлення}", file=sys.stderr, flush=True)
        return False
    if гілка and git("push", "-q", "origin", "HEAD:refs/heads/" + гілка):
        print(f"ПУШ: git push у {гілка} не вдався — запис у коміті, його забере наступний пуш", file=sys.stderr, flush=True)
    return True


def відкласти_спробу(тека_сцени):
    """Теку сцени з попередньої спроби (обрив стенда, той самий план після обриву, нове питання до записаної сцени)
    переносить у `спроби/<сцена>-<N>` поруч: прилад пише лише в нову теку, а `нова_база.js` бере базами лише прямі
    теки сцен. Попередній запис лишається в історії гілки: план читає його за головою, яку переніс `reports`."""
    тека_сцени = Path(тека_сцени)
    if not тека_сцени.exists():
        return None
    спроби = тека_сцени.parent / "спроби"
    спроби.mkdir(exist_ok=True)
    номер = 1
    while (спроби / f"{тека_сцени.name}-{номер}").exists():
        номер += 1
    куди = спроби / f"{тека_сцени.name}-{номер}"
    тека_сцени.rename(куди)
    return куди


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


def придатні_питання(id_, питання):
    """Ділить питання сцени на ті, чий режим прилад виконує, і відмови (PR, причина): довільний текст у режимі злитого PR
    не виконується, але й не забирає запису сцени в її решти питань (нічний 05.11: 6 сцен без запису через 11 питань)."""
    вхід, придатні, відмови = вхід_реєстру(id_), [], []
    for пункт in питання:
        режим = режим_питання(пункт["question"])
        try:
            if режим is not None:
                змінні_режиму(id_, режим, вхід)
        except ValueError as причина:
            відмови.append((пункт["pr"], str(причина)))
            continue
        придатні.append(пункт)
    return придатні, відмови


def команди_плану(план, збірка, кеш, вихід, node="node"):
    """Готує команди сцен, причини відмов сцен і питань до створення тек або запуску першої сцени: одна сцена чи питання
    не зупиняє план. Сцену без жодного виконуваного питання записує режим реєстру — запис сцени плану є завжди."""
    команди, відмови, відмови_питань = [], {}, {}
    for id_, питання in план["scenes"].items():
        try:
            придатні, відмови_питань[id_] = придатні_питання(id_, питання)
            режим = режим_питань(id_, придатні)
            сцена_реєстру(id_, режим)
        except ValueError as причина:
            відмови[id_] = str(причина)
            continue
        команда = [sys.executable, str(Path(__file__).with_name("записати_сцену.py")),
                   str(збірка), str(кеш), str(вихід / id_), "--сцена", id_, "--node", node]
        if режим is not None:
            команда += ["--режим", режим]
        команди.append(команда)
    return команди, відмови, {id_: в for id_, в in відмови_питань.items() if в}


def виконати():
    """Послідовно записує сцени плану та зберігає команди й коди виходу; у робочому дереві git — коміт після кожної
    сцени (`зберегти`), тож обрив не губить записаного."""
    а = argparse.ArgumentParser(description=__doc__)
    а.add_argument("план", type=Path)
    а.add_argument("збірка", type=Path)
    а.add_argument("кеш", type=Path)
    а.add_argument("вихід", type=Path)
    а.add_argument("--лише-змінні", action="store_true")
    а.add_argument("--node", default="node")
    а.add_argument("--пуш", metavar="ГІЛКА", help="після кожного коміту пушити в цю гілку звіту (смуга Claude)")
    а.add_argument("--без-коміту", action="store_true", help="не комітити (тека поза git чи ручна проба)")
    п = а.parse_args()
    план = json.loads(п.план.read_text(encoding="utf-8-sig"))
    команди, відмови, відмови_питань = команди_плану(план, п.збірка, п.кеш, п.вихід, п.node)
    print(f"Сцен у плані: {len(команди) + len(відмови)} · з змінними: {len(команди)} · відмов сцени: {len(відмови)}"
          f" · відмов питання: {sum(map(len, відмови_питань.values()))}", file=sys.stderr, flush=True)
    for id_, причина in відмови.items():
        print(f"ВІДМОВА СЦЕНИ {id_}: {причина}", file=sys.stderr, flush=True)
    for id_, пари in відмови_питань.items():
        for pr, причина in пари:
            print(f"ВІДМОВА ПИТАННЯ {id_}: PR #{pr}: {причина}", file=sys.stderr, flush=True)
    if п.лише_змінні:
        for команда in команди:
            subprocess.run(команда + ["--лише-змінні"], check=True)
        return 0
    п.вихід.mkdir(parents=True, exist_ok=True)
    def коміт(повідомлення):
        if not п.без_коміту:
            зберегти(п.вихід, п.план, повідомлення, п.пуш)
    код = 0
    всього = len(команди)
    with (п.вихід / "done.txt").open("a", encoding="utf-8") as журнал:
        for id_, причина in відмови.items():
            журнал.write(json.dumps({"сцена": id_, "відмова": причина, "час": datetime.now(timezone.utc).isoformat()},
                                    ensure_ascii=False) + "\n")
        for id_, пари in відмови_питань.items():
            for pr, причина in пари:
                журнал.write(json.dumps({"сцена": id_, "pr": pr, "відмова_питання": причина,
                                         "час": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False) + "\n")
        журнал.flush()
        # План і відмови — у гілці звіту до першої сцени: обрив на ній лишає план, за яким наступний читає записане.
        коміт(f"{п.вихід.name}: план, сцен {всього}, відмов сцени {len(відмови)}")
        for номер, команда in enumerate(команди, 1):
            id_ = команда[команда.index("--сцена") + 1]
            відкладено = відкласти_спробу(п.вихід / id_)
            запис = {"початок": datetime.now(timezone.utc).isoformat(), "команда": команда}
            if відкладено:
                запис["попередня_спроба"] = відкладено.relative_to(п.вихід).as_posix()
            запис["rc"] = subprocess.run(команда).returncode
            запис["кінець"] = datetime.now(timezone.utc).isoformat()
            журнал.write(json.dumps(запис, ensure_ascii=False) + "\n")
            журнал.flush()
            код = max(код, запис["rc"])
            коміт(f"{п.вихід.name}: сцена {id_} rc {запис['rc']} ({номер} з {всього})")
    return код


if __name__ == "__main__":
    try:
        raise SystemExit(виконати())
    except ValueError as причина:
        raise SystemExit("ВІДМОВА: " + str(причина))
