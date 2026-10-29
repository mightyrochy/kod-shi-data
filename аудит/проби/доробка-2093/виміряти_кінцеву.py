"""Завершити ДО → ПІСЛЯ кінцевої відповіді, мірила збереження й батарею без моделей."""
import json
import os
import pathlib
import subprocess
import sys


def main():
    """Записати команди, повні журнали та коди кожного послідовного запуску."""
    тека = pathlib.Path(__file__).resolve().parent
    корінь = тека.parents[2]
    джерела = корінь / "джерела"
    до = pathlib.Path(os.environ.get("E2_BEFORE", "C:/Users/gemini/gemini-runs/tmp/e2-final-before"))
    журнали = тека / "кінцева-журнали"
    журнали.mkdir(exist_ok=True)
    середовище = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_PATH=str(джерела / "node_modules"))
    результати = []
    оригінал = subprocess.check_output(["git", "show", "b75fd3fe:аудит/перевірки/автоперевірка-2082-45695e24c0c7de5858eddff3bdd86d5554b86092/крайові.py"], cwd=корінь)
    прилад = журнали / "крайові_2082.py"
    прилад.write_bytes(оригінал)

    def виконати(назва, команда, місце, дерево, очікуваний=0):
        """Дочекатися команди й зберегти її код та весь текст журналу."""
        р = subprocess.run(команда, cwd=місце, env=dict(середовище, E2_SOURCES=str(дерево)),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf8", errors="replace")
        файл = журнали / (str(len(результати) + 1) + ".txt")
        файл.write_text("\n".join(рядок.rstrip() for рядок in р.stdout.splitlines()).rstrip() + "\n", encoding="utf8")
        результати.append(dict(назва=назва, команда=команда, тека=str(місце), джерела=str(дерево),
                              код=р.returncode, очікуваний=очікуваний, журнал=файл.relative_to(корінь).as_posix(),
                              підсумок="\n".join(р.stdout.splitlines()[-5:])))
        (тека / "кінцева-вимір.json").write_text(json.dumps(dict(
            до=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=до, text=True).strip(),
            після=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=корінь, text=True).strip(),
            результати=результати), ensure_ascii=False, indent=2) + "\n", encoding="utf8")
        print(json.dumps(dict(назва=назва, код=р.returncode, очікуваний=очікуваний), ensure_ascii=False), flush=True)

    for назва, дерево in (("ДО", до / "джерела"), ("ПІСЛЯ", джерела)):
        виконати(назва + " — оригінальний прилад #2116", ["node", str(тека / "відмова_повтору_2116.js"), str(дерево.parent)], корінь, дерево)
        виконати(назва + " — кінцевий показ і кеш", ["node", str(тека / "кінцева_відповідь.js")], корінь, дерево, 1 if назва == "ДО" else 0)
        виконати(назва + " — три втрати #2082", [sys.executable, "-X", "utf8", str(прилад), str(дерево)], корінь, дерево)
        виконати(назва + " — механізм 18", [sys.executable, "-X", "utf8", str(тека / "механізм.py")], корінь, дерево)
        виконати(назва + " — повтор 17", [sys.executable, "-X", "utf8", str(джерела / "проби/шлях_шар_повтор.py")], корінь, дерево)
    for файл in ("стенд_знімок.py", "тест_живого_шляху.py", "тест_протоколу.py", "прилади/розділи_гейтів.py", "audit_contracts.py"):
        виконати(файл, [sys.executable, "-X", "utf8", файл] + (["--дим"] if файл == "стенд_знімок.py" else []), джерела, джерела)
    виконати("тест_показу.js", ["node", "тест_показу.js"], джерела, джерела)
    for файл in sorted((джерела / "проби").glob("шлях_шар_*.py")):
        виконати(файл.name, [sys.executable, "-X", "utf8", str(файл)], джерела, джерела)
    for файл in ("шлях_шар_репліка.js", "шлях_шар_межі.js"):
        виконати(файл, ["node", str(джерела / "проби" / файл)], джерела, джерела)
    виконати("показ_повтор.js", ["node", str(тека / "показ_повтор.js")], корінь, джерела)
    виконати("паспорт_повтор_8115.py", [sys.executable, "-X", "utf8", "проби/паспорт_повтор_8115.py"], джерела, джерела)
    виконати("дошка", [sys.executable, "-X", "utf8", "джерела/прилади/згорнути_дошку.py", "--лише-перевірити"], корінь, джерела)
    помилок = sum(р["код"] != р["очікуваний"] for р in результати)
    print("Команд: %d; неочікуваних кодів: %d" % (len(результати), помилок))
    return 1 if помилок else 0


if __name__ == "__main__":
    sys.exit(main())
