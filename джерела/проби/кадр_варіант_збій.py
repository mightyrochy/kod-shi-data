"""Лічить приховані збої власника кадру в читачі, кольорі й записувачі фактів; SHA ДО — необов'язковий."""
import subprocess, sys, types
from pathlib import Path
from unittest.mock import patch
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "джерела"), str(КОРІНЬ / "джерела/прилади")]
import фід_власник_кадру as в, власник_кадру as ф

def main():
    """Відрізняє битий JSON і тип від штатної відсутності доказу на всіх трьох шляхах."""
    читач = в
    if len(sys.argv) > 1:
        читач = types.ModuleType("_до")
        exec(compile(subprocess.check_output(["git", "show", sys.argv[1] + ":джерела/фід_власник_кадру.py"]), в.__file__, "exec"), читач.__dict__)
    кадр = "https://shop.test/a.jpg"
    о = dict(id="x@shop.test", url="https://shop.test/products/a?variant=11", фото=[кадр])
    зб = {"фото": кадр}
    шляхи = [lambda: читач.запис(о, зб, факти={}),
             lambda: читач.чужий_кадр_кольору(о, зб, {}, lambda _: None, {}),
             lambda: ф.факти([о], {о["id"]: зб}, {})]
    приховано = 0
    with patch.object(ф, "ВК", читач):
        for значення in ('{', ["не рядок"]):
            о["параметри"] = {"власник_кадру": значення}
            for шлях in шляхи:
                try:
                    шлях()
                except ValueError as збій:
                    assert о["id"] in str(збій) and isinstance(збій.__cause__, (TypeError, ValueError))
                else:
                    приховано += 1
        for параметри in ({}, {"власник_кадру": '"невідомо"'}, {"власник_кадру": '{}'}):
            о["параметри"] = параметри
            assert шляхи[0]()["варіант"] == "невідомо" and bool(шляхи[1]()) == ("власник_кадру" in параметри)
            assert шляхи[2]()[о["id"]][6] == "невідомо"
    print("Прихованих збоїв: %d з 6; штатний невідомий власник: 9 з 9" % приховано)
    return bool(приховано)

if __name__ == "__main__":
    sys.exit(main())
