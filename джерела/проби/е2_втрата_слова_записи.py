"""Міряє розбір записаних складань і ремонтів; argv[1] — коміт ДО."""
import json, pathlib, subprocess, sys
корінь = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(корінь / "джерела"))


def основна():
    """Звіряє форму чотирьох записаних відповідей тим самим читачем протоколу."""
    import протокол as П
    if len(sys.argv) > 1:
        exec(compile(subprocess.check_output(["git", "show", sys.argv[1] + ":джерела/протокол.py"]),
                     П.__file__, "exec"), П.__dict__)
    тека = корінь / "аудит/проби/б1/ПІСЛЯ-Е3/06_б1_концерт_сміливо/VIDPOVIDI"
    for файл in sorted(тека.glob("*ОБРАЗИ_V1.txt")):
        текст = файл.read_text(encoding="utf8")
        відповідь = текст.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1]
        об, причина, нотатки = П.розбір_за_схемою(відповідь, "ОБРАЗИ_V1")
        print(json.dumps(dict(файл=файл.name, образів=len((об or {}).get("образи") or []),
            речей=[len(о.get("речі") or []) for о in (об or {}).get("образи") or []],
            причина=причина, нотатки=нотатки), ensure_ascii=False))


if __name__ == "__main__":
    основна()
