# Функційне покриття шляху образу: які функції модулів джерела/ виконались на тест_живого_шляху.py + тест_інваріанти.py.
# Потрібен Python 3.12+ (sys.monitoring). Запуск з кореня репозиторію (≈4 хв):
#   python3 аудит/звіти/ядро-образу-наново/скрипти/покриття.py джерела /tmp/покриття.json
import sys, os, runpy, json, unittest
ДЖ = os.path.realpath(sys.argv[1]); ВИХІД = os.path.realpath(sys.argv[2]); os.chdir(ДЖ); sys.path.insert(0, ДЖ)
М = sys.monitoring; ІД = 3
М.use_tool_id(ІД, "покриття")
виконано = set()
def старт(code, off):
    if code.co_filename.startswith(ДЖ): виконано.add((os.path.basename(code.co_filename), code.co_firstlineno, code.co_qualname))
    return М.DISABLE
М.register_callback(ІД, М.events.PY_START, старт)
М.set_events(ІД, М.events.PY_START)
sys.argv = ["тест_живого_шляху.py"]
try: runpy.run_path(os.path.join(ДЖ, "тест_живого_шляху.py"), run_name="__main__")
except SystemExit as e: print("тест_живого_шляху вихід", e.code, file=sys.stderr)
import тест_інваріанти
r = unittest.TextTestRunner(verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(тест_інваріанти))
print("інваріанти", r.testsRun, "помилок", len(r.errors), "провалів", len(r.failures), file=sys.stderr)
М.set_events(ІД, 0)
json.dump(sorted(виконано), open(ВИХІД, "w"), ensure_ascii=False)
print("функцій виконано", len(виконано), file=sys.stderr)
