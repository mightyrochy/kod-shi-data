"""Послідовний ДО → ПІСЛЯ та повна батарея; жодної моделі чи мережевого запиту."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile


def main():
    """Зберегти команди, коди, підсумки та журнали кожного завершеного виміру."""
    тека = pathlib.Path(__file__).resolve().parent
    корінь = тека.parents[2]
    джерела = корінь / "джерела"
    до = pathlib.Path("C:/Users/gemini/gemini-runs/tmp/dorobka-2093-do/джерела")
    середовище = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_PATH=str(джерела / "node_modules"))
    журнали = pathlib.Path(tempfile.mkdtemp(prefix="доробка-2093-механізм-"))
    оригінал = subprocess.check_output(["git", "show", "b75fd3fe:аудит/перевірки/автоперевірка-2082-45695e24c0c7de5858eddff3bdd86d5554b86092/крайові.py"], cwd=корінь)
    прилад = журнали / "крайові_2082.py"
    прилад.write_bytes(оригінал)
    результати = []

    def виконати(назва, команда, місце, джерело, очікуваний=0):
        р = subprocess.run(команда, cwd=місце, env=dict(середовище, E2_SOURCES=str(джерело)),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf8", errors="replace")
        файл = журнали / (str(len(результати) + 1) + ".log")
        файл.write_text(р.stdout, encoding="utf8")
        запис = dict(назва=назва, команда=команда, тека=str(місце), джерела=str(джерело),
                     код=р.returncode, очікуваний=очікуваний, журнал=str(файл),
                     вивід=р.stdout if len(р.stdout) < 15000 else "\n".join(р.stdout.splitlines()[-14:]))
        результати.append(запис)
        print(json.dumps(dict(назва=назва, код=р.returncode, очікуваний=очікуваний), ensure_ascii=False), flush=True)
        (тека / "механізм-вимір.json").write_text(json.dumps(dict(
            голова=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=корінь, text=True).strip(),
            результати=результати), ensure_ascii=False, indent=2) + "\n", encoding="utf8")

    for назва, дерево in (("ДО", до), ("ПІСЛЯ", джерела)):
        виконати(назва + " — три випадки #2082", [sys.executable, "-X", "utf8", str(прилад), str(дерево)], корінь, дерево)
        виконати(назва + " — спільний механізм", [sys.executable, "-X", "utf8", str(тека / "механізм.py")], корінь, дерево, 1 if назва == "ДО" else 0)
        виконати(назва + " — 17 варіантів повтору", [sys.executable, "-X", "utf8", str(джерела / "проби/шлях_шар_повтор.py")], корінь, дерево, 1 if назва == "ДО" else 0)
        if назва == "ДО":
            for файл in ("шлях_шар_договір.py", "шлях_шар_репліка.js", "шлях_шар_межі.js"):
                виконати(назва + " — " + файл, ([sys.executable, "-X", "utf8"] if файл.endswith(".py") else ["node"])
                         + [str(джерела / "проби" / файл)], корінь, дерево)
    for файл in ("стенд_знімок.py", "тест_живого_шляху.py", "тест_протоколу.py", "прилади/розділи_гейтів.py", "audit_contracts.py"):
        виконати(файл, [sys.executable, "-X", "utf8", файл] + (["--дим"] if файл == "стенд_знімок.py" else []), джерела, джерела)
    виконати("тест_показу.js", ["node", "тест_показу.js"], джерела, джерела)
    for файл in sorted((джерела / "проби").glob("шлях_шар_*.py")):
        виконати(файл.name, [sys.executable, "-X", "utf8", str(файл)], джерела, джерела)
    for файл in ("шлях_шар_репліка.js", "шлях_шар_межі.js"):
        виконати(файл, ["node", str(джерела / "проби" / файл)], джерела, джерела)
    виконати("показ: справжній ендпойнт", ["node", str(тека / "показ_повтор.js")], корінь, джерела)
    виконати("паспорт_повтор_8115.py", [sys.executable, "-X", "utf8", "проби/паспорт_повтор_8115.py"], джерела, джерела)
    виконати("дошка", [sys.executable, "-X", "utf8", "джерела/прилади/згорнути_дошку.py", "--лише-перевірити"], корінь, джерела)
    червоних = sum(р["код"] != р["очікуваний"] for р in результати)
    print("Команд: %d; неочікуваних кодів: %d; журнали: %s" % (len(результати), червоних, журнали))
    return 1 if червоних else 0


if __name__ == "__main__":
    sys.exit(main())
