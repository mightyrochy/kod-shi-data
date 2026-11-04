"""Зводить уже завершені повні виводи приладу, не змінюючи його класу."""
from collections import Counter
import importlib.util, json, pathlib, re, subprocess


def main():
    """Звіряє пару на Python 3.11, захищені файли й незростання чужих місць."""
    К = pathlib.Path(__file__).resolve().parents[3]
    Д = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("храповик", К / "джерела/прилади/храповик_кореня.py")
    Х = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(Х)
    свої = {"brief.py", "колір_річ.py", "міст_вхід.py", "bases.py", "палітра_схеми.py",
            "суд_чеклісти.py", "колір_нейтралі.py", "палітра_нейтраль.py"}
    пари = []
    for режим in ("до-311", "після-311"):
        мета = json.loads((Д / (режим + "-мірило.json")).read_text("utf8"))
        рядки = (Д / (режим + ".txt")).read_text("utf8").splitlines()
        assert мета["код"] == 0 and мета["python"].startswith("3.11.9 ")
        загалом = int(Х.МІСЦЬ.fullmatch(next(x for x in reversed(рядки) if x.strip())).group(1))
        місця = Counter(m[1] for x in рядки if (m := re.match(r"^джерела/([^:]+):\d+ ·", x)))
        assert sum(місця.values()) == загалом
        власних = sum(n for f, n in місця.items() if f in свої)
        пари.append(dict(режим=режим, загалом=загалом, своїх=власних, решта=загалом-власних,
                         по_файлах=dict(місця), секунд=мета["секунд"], голова=мета["голова"]))
    до, після = пари
    assert після["загалом"] <= до["загалом"] and після["решта"] <= до["решта"]
    паспорт = (К / "аудит/корені/Річ-ознаки-обличчя.md").read_text("utf8")
    прилад, _, бази, помилки = Х.розібрати_паспорт(паспорт)
    assert not помилки
    захищені = [прилад, *бази, *Х.ХРАПОВИК]
    diff = subprocess.check_output(["git", "diff", "--name-only", "abdaea370a9ab713ded7521859e34c131c1789ed",
                                    "--", *захищені, ".github", "аудит/адаптери/gemini"], cwd=К).decode("utf8")
    assert not diff.strip(), diff
    вих = dict(пара=пари, клас_незмінений=True, захищені=захищені,
                умова_незростання=True, повний_CI_храповик_запускався=False)
    (Д / "повне-мірило.json").write_text(json.dumps(вих, ensure_ascii=False, indent=2), "utf8")
    print(json.dumps(вих, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
