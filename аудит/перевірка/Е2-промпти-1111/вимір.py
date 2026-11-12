"""Фіксує прилад на актуальному main та повні довжини прозового вибору без моделі."""
import json
from pathlib import Path
import subprocess
import sys


if __name__ == "__main__":
    корінь = Path(__file__).resolve().parents[3]
    тека = Path(__file__).resolve().parent
    sha = "696dc1837d9f89a6c0d9a8bc82837c3feea68c9c"
    subprocess.run(["git", "diff", "--exit-code", sha, "--", "джерела", "zhnyvarka",
                    "аудит/корені/Е2-промпти-довжини.json"], cwd=корінь, check=True)
    команда = [sys.executable, "-X", "utf8", "джерела/прилади/корінь_е2_промпти.py",
               "--база", "аудит/корені/Е2-промпти-довжини.json", "--деталі",
               "--записати-базу", str(тека / "довжини.json"), "--sha", sha]
    with (тека / "прилад.txt").open("w", encoding="utf-8", newline="\n") as журнал:
        subprocess.run(команда, cwd=корінь, stdout=журнал, stderr=subprocess.STDOUT, check=True)
    журнал = (тека / "прилад.txt").read_text(encoding="utf-8")
    sys.path.insert(0, str(корінь / "джерела"))
    import brief
    import повнота_образу as вибір

    довжини = json.loads((тека / "довжини.json").read_text(encoding="utf-8"))["довжини"]
    образи = [dict(підпис="о1", речі=[], свідомі=[], блокує=[], знахідки=[])]
    результат = dict(main=sha, python=sys.version, продукт_тотожний_main=True,
                     місць=int(журнал.strip().splitlines()[-1].split(": ")[1]),
                     прилад_вибору={к: в for к, в in довжини.items() if "промпт_вибору:" in к},
                     формати={к: len(getattr(brief, к)) for к in ("ФОРМАТ", "ФОРМАТ_ЛИШЕ_ТЕКСТ")},
                     справжній_вибір={str(б): len(вибір.промпт_вибору(образи, "офіс", б))
                                      for б in (False, True)})
    (тека / "вимір.json").write_text(json.dumps(результат, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(результат, ensure_ascii=False, indent=2))
