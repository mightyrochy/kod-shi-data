"""Т47 на старому шляху (Ядро-Н1-каркас; у `РЕЗУЛЬТАТ.md` — «старе: не виміряно»): той самий вхід — той самий вихід?

Старий шлях без моделі доходить лише до запитів рук: `bridge.виклик("запити")` дає пули й промпти (вирок і картка
старого шляху чекають відповіді моделі — тут не міряються). Записаного входу мосту для с5 нема (запис с5 — лише
обміни з моделлю), тож вхід — той самий, що в `тест_інваріанти.py`: `стенд_вх.json`, паспорт із записаної відповіді
мовної моделі, каталог brief. Міра: SHA-256 канонічного JSON виходу «запити» — двічі в одному процесі й раз у свіжому.
Запуск з кореня: python3 аудит/проби/ядро-н1/т47_старий_шлях.py
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ДЖЕРЕЛА = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "джерела")
os.chdir(ДЖЕРЕЛА)
sys.path.insert(0, os.getcwd())


def відбиток():
    import feed
    import bridge

    def виклик(ім, вхід):
        в = bridge.виклик(ім, вхід)
        return json.loads(в) if isinstance(в, str) else в
    from тест_інваріанти import ВІДПОВІДЬ_МОВНОЇ_МОДЕЛІ, КАТАЛОГ, ЇЇ_СЛОВА
    кеш = os.path.join(tempfile.mkdtemp(prefix="т47_"), "кеш_кольорів.json")
    with open(кеш, "w", encoding="utf-8") as ф:
        json.dump({}, ф)
    with open("стенд_вх.json", encoding="utf-8") as ф:
        вх = json.load(ф)
    вх.update(каталог=feed.каталог_на_диску(КАТАЛОГ), кеш_кольорів=кеш, сценарій={})
    вх["паспорт"] = виклик("паспорт", {"json_моделі": json.dumps(ВІДПОВІДЬ_МОВНОЇ_МОДЕЛІ, ensure_ascii=False),
                                         "сценарій": {}, "вимоги": ЇЇ_СЛОВА})["паспорт"]
    запити = виклик("запити", dict(вх, пакети=1))
    канон = json.dumps(запити, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(канон.encode("utf-8")).hexdigest(), len(канон)


if __name__ == "__main__":
    if sys.argv[1:] == ["--один"]:
        print(json.dumps(відбиток()))
        sys.exit(0)
    перший, другий = відбиток(), відбиток()
    свіжий = json.loads(subprocess.run([sys.executable, os.path.abspath(__file__), "--один"], capture_output=True,
                                       text=True, check=True).stdout.strip().splitlines()[-1])
    print(json.dumps({"перший": перший, "другий_у_тому_ж_процесі": другий, "свіжий_процес": свіжий,
                      "той_самий_процес_збіг": перший == другий, "свіжий_збіг": list(свіжий) == list(перший)},
                     ensure_ascii=False, indent=1))
