"""Проби `джерела/проби/`, що кличуть змінені функції з іменованими аргументами, яких нова сигнатура не має."""
import ast, glob, inspect, os, sys, collections
sys.path.insert(0, os.getcwd())
import warnings; warnings.filterwarnings("ignore")
import суд_огляд, перевірка_образу, суд_чеклісти, суд_погода, суд_інтерес, формальність
Ф = {"review": суд_огляд.review, "підготувати": перевірка_образу.підготувати, "перевірити_образ": перевірка_образу.перевірити_образ,
     "чеклісти": суд_чеклісти.чеклісти, "погода": суд_погода.погода, "крок_редагування": суд_інтерес.крок_редагування,
     "нагода_палітра": формальність.нагода_палітра, "сценарій": формальність.сценарій}
П = {к: set(inspect.signature(ф).parameters) for к, ф in Ф.items()}
файли = collections.Counter()
for ф in sorted(glob.glob("проби/**/*.py", recursive=True)):
    try: д = ast.parse(open(ф, encoding="utf8").read())
    except SyntaxError: continue
    for в in ast.walk(д):
        if isinstance(в, ast.Call):
            ім = в.func.attr if isinstance(в.func, ast.Attribute) else getattr(в.func, "id", None)
            if ім in П and any(k.arg and k.arg not in П[ім] for k in в.keywords):
                файли[ф] += 1
print("файлів", len(файли), "викликів", sum(файли.values()))
for ф, н in файли.most_common(8): print(" ", ф, н)
