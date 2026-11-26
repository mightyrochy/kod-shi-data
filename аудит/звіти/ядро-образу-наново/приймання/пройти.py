"""Бере хід Н6 і запускає на чинному стенді окремий прохід кожної сцени."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess


ТУТ = Path(__file__).resolve().parent
КОРІНЬ = ТУТ.parents[3]
ПРОБИ = КОРІНЬ / "аудит/проби"
ПЕРШІ_ВІСІМ = [f"с{н}" for н in range(1, 9)]


def сцени():
    """Звіряє імена ситуацій у ході з реєстром і читає їхні входи."""
    реєстр = {}
    for рядок in (ПРОБИ / "живі_сцени.txt").read_text(encoding="utf-8").splitlines():
        if рядок.strip() and not рядок.startswith("#"):
            ід, жінка, слова, вхід, *_ = рядок.split("|")
            реєстр[ід] = (жінка, слова, вхід)
    плани = {}
    for рядок in (ТУТ / "хід.md").read_text(encoding="utf-8").splitlines():
        стовпці = рядок.split("|")
        if len(стовпці) != 6 or not рядок.startswith("| "):
            continue
        _, номер, ід, до, після, _ = map(str.strip, стовпці)
        if номер == "Ситуація":
            continue
        жінка, слова, вхід = реєстр[ід]
        змінні = dict(пара.split("=", 1) for пара in re.split(r" (?=[A-Z][A-Z0-9_]*=)", вхід) if пара)
        # Хід приймання відтворює лише її дії й початкові дані, без підстановки готового паспорта.
        дії_до = [дія for дія in до.split(";") if дія]
        дії_після = [дія for дія in після.split(";") if дія]
        if "ROZMOVA" in змінні and not any(дія.startswith("репліка:") for дія in дії_до):
            листи = json.loads((КОРІНЬ / змінні["ROZMOVA"]).read_text(encoding="utf-8"))
            дії_до = [f"репліка:{лист['вона']}" for лист in листи if not лист.get("перший")] + дії_до
        використані = {к: в for к, в in змінні.items() if к in {"FOTO_RECHI", "ZBIJ", "ZRIST"}}
        плани[номер] = dict(ід=ід, номер=номер, слова=слова, до=дії_до, після=дії_після,
                           вхід=dict(використані, ZHINKA=str(ПРОБИ / f"жінки/{жінка}.json"),
                                     FOTO="1", SCENA=ід, CHAT_TEXT=слова))
    return плани


def main():
    """Вибирає ситуації, запускає браузер і зберігає код кінця кожної."""
    параметри = argparse.ArgumentParser(description=__doc__)
    параметри.add_argument("ситуація", help="всі, номер (с3, ж4, 17263) або список через кому")
    параметри.add_argument("вихід", type=Path)
    а = параметри.parse_args()
    шлях = os.environ["SHLIAKH"]
    плани = сцени()
    if а.ситуація == "всі":
        # с5 і 17264 мають ідентичний рядок реєстру. Той самий запис відповідає на обидва питання.
        вибір = ПЕРШІ_ВІСІМ if шлях == "старий" else [н for н in плани if н != "17264"]
    else:
        вибір = а.ситуація.split(",")
    if відсутні := [н for н in вибір if н not in плани]:
        параметри.error("немає в ході: " + ", ".join(відсутні))
    проходів = int(os.environ.get("PROHODY", "2"))
    if проходів not in (1, 2):
        параметри.error("PROHODY має дорівнювати 1 або 2")
    плани = [dict(плани[н], прохід=прохід, шлях=шлях) for прохід in range(1, проходів + 1) for н in вибір]
    if os.environ.get("REPLAY_PLAN"):
        print(json.dumps(плани, ensure_ascii=False, indent=2))
        return 0
    if not any(os.environ.get(к) for к in ("ZHYVA", "MODEL", "REPLAY_EXCHANGE")):
        параметри.error("потрібен MODEL для локального стенда, ZHYVA для підписки або записаний обмін")
    збірка = (Path(os.environ["STOR"]) / "голова.txt").read_text(encoding="utf-8").strip()
    джерело = dict(збірка=збірка, **{к: os.environ.get(к) for к in ("MODEL", "MODEL_MOVA", "ZHYVA", "REPLAY_EXCHANGE")})
    а.вихід.mkdir(parents=True, exist_ok=True)
    паспорт = а.вихід / "джерело.json"
    if паспорт.is_file() and json.loads(паспорт.read_text(encoding="utf-8")) != джерело:
        параметри.error("у цій теці вже є прогін з іншою збіркою чи моделями; виберіть нову теку")
    паспорт.write_text(json.dumps(джерело, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    невдалі = []
    for план in плани:
        вихід = (а.вихід / шлях / str(план["прохід"]) / план["номер"]).resolve()
        if (вихід / "готово").is_file():
            continue
        if вихід.exists():
            архів = вихід.with_name(вихід.name + ".обірвано")
            суфікс = 0
            while архів.exists():
                суфікс += 1
                архів = вихід.with_name(вихід.name + f".обірвано-{суфікс}")
            вихід.rename(архів)
        вихід.mkdir(parents=True)
        файл_плану = вихід / "план.json"
        файл_плану.write_text(json.dumps(план, ensure_ascii=False, indent=2), encoding="utf-8")
        env = dict(os.environ, **план["вхід"], N6_PLAN=str(файл_плану), ZNIMKY=str(вихід / "знімки"),
                   VIDPOVIDI=str(вихід / "відповіді"), OTSINKA="0", ODNOCHASNO="1")
        print(f"{шлях}, прохід {план['прохід']}, {план['номер']} ({план['ід']})", flush=True)
        with (вихід / "лог.txt").open("w", encoding="utf-8") as лог:
            вих = subprocess.run(
                ["node", str(ПРОБИ / "рв6_стенд.js"), "http://127.0.0.1:8765",
                 os.environ["STOR"], os.environ["PYODIDE"], "3"],
                cwd=КОРІНЬ, env=env, stdout=лог, stderr=subprocess.STDOUT, check=False,
            )
        if вих.returncode == 0:
            (вихід / "готово").touch()
        else:
            невдалі.append(f"{план['номер']}/{план['прохід']} ({вих.returncode}) — {вихід / 'лог.txt'}")
    if невдалі:
        print("Обірвані проходи:")
        print("\n".join(невдалі))
    return int(bool(невдалі))


if __name__ == "__main__":
    raise SystemExit(main())
