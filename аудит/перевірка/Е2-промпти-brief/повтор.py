"""Повторює читання записаних прозових відповідей; модель і браузер не запускає."""
import json
from pathlib import Path
import subprocess
import sys
import types

if __name__ == "__main__":
    корінь = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(корінь / "джерела"))
    import розбір_відповідей as після

    sha = "6028f963a49c8a9d2c274385fb85699652b393e4"
    до = types.ModuleType("розбір_до")
    sys.modules[до.__name__] = до
    код = subprocess.check_output(["git", "show", sha + ":джерела/розбір_відповідей.py"], cwd=корінь).decode("utf-8")
    exec(compile(код, "розбір_до.py", "exec"), до.__dict__)
    результат = []
    for файл in sorted((корінь / "аудит/тести/власник_2026-09-25").glob("*.json")):
        for прогін in json.loads(файл.read_text(encoding="utf-8")).get("прогони", []):
            for вердикт in прогін.get("вердикти", []):
                for виклик in вердикт.get("етапи", {}).get("виклики", []):
                    промпт = виклик.get("запит", {}).get("текст", "")
                    if "Не називай у відповіді чисел світлоти" not in промпт:
                        continue
                    відповідь = виклик["відповідь_сира"]
                    а, б = до.речі_з_тексту(відповідь), після.речі_з_тексту(відповідь)
                    assert а == б and б
                    результат.append(dict(файл=файл.name, рука=вердикт.get("рука"), крок=виклик.get("крок"),
                                          символів_відповіді=len(відповідь), речей=len(б), збігається=а == б))
    assert len(результат) == 4
    print(json.dumps(результат, ensure_ascii=False, indent=2))
