"""Порівняння справжніх емітентів із функціями бази та суд складів усіх стендових сцен.

Запуск із кореня: python аудит/проби/е3_сила_правила/стани_входу.py <SHA бази> <JSON звіту>.
Старі функції виконуються з поточними незміненими залежностями; це локальний повтор коду,
а не окремий запуск повного старого дерева чи незалежна перевірка.
"""
import ast
import copy
import importlib
import itertools
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = ROOT / "джерела"
sys.path.insert(0, str(SRC))
os.chdir(SRC)
import bridge as B
import colorspace as CS
import колір_річ as KR
import колір_нейтралі as KN
import колір_світлота as KL
import колір_хрома as KC
import coordination as CO
import аксесуари_структура as AC
import формальність as FM
import знахідка as Z
import стенд_знімок as SZ

MODULES = ("coordination", "аксесуари_структура", "колір_нейтралі", "колір_річ",
           "колір_світлота", "колір_хрома", "формальність", "реєстр_сила", "реєстр_тіри")
STATES = ("питання", "утримано", "ok")


def old_functions(sha):
    """Пари поточних і старих змінених функцій без запису другого дерева на диск."""
    pairs = {}
    targets = set()
    for name in MODULES:
        mod = importlib.import_module(name)
        path = SRC / (name + ".py")
        old = ast.parse(subprocess.check_output(["git", "show", sha + ":джерела/" + path.name]).decode("utf-8"))
        new = ast.parse(path.read_text(encoding="utf-8"))
        before = {n.name: n for n in old.body if isinstance(n, ast.FunctionDef)}
        for n in new.body:
            if not isinstance(n, ast.FunctionDef) or n.name not in before:
                continue
            if ast.dump(n) == ast.dump(before[n.name]):
                continue
            holder = {}
            exec(compile(ast.Module(body=[before[n.name]], type_ignores=[]), str(path), "exec"), mod.__dict__, holder)
            pairs[id(getattr(mod, n.name))] = holder[n.name]
            if name not in ("реєстр_сила", "реєстр_тіри"):
                for call in ast.walk(n):
                    if isinstance(call, ast.Call) and any(k.arg == "сила" and isinstance(k.value, ast.Constant)
                            and k.value.value in STATES for k in call.keywords):
                        strength = next(k for k in call.keywords if k.arg == "сила")
                        targets.add((str(path), strength.value.lineno))
    swaps = [(m.__dict__, k, value, pairs[id(value)]) for m in list(sys.modules.values()) if m
             for k, value in list(vars(m).items()) if id(value) in pairs]
    return swaps, targets


def element(item, slot, lab=(70, 0, 0), area=None):
    """Виміряний елемент без вигаданої площі; поля — входи справжніх судів."""
    L, chroma, hue = CS.lch(lab)
    return dict(річ=item, слот=slot, lab=lab, L=L, C=chroma, h=hue, площа=area,
                near=1.0, нейтраль=KR.нейтраль(lab), гучний=chroma >= 40, тип="сорочка",
                текстура=None, блиск=0, принт=None, сім_я=KR.сім_я(lab))


def main():
    """Зберігає ДО/ПІСЛЯ, охоплення емісій і різницю судів каталогу."""
    sha, output = sys.argv[1:3]
    sha = subprocess.check_output(["git", "rev-parse", sha], cwd=ROOT).decode().strip()
    output = (ROOT / output).resolve()
    swaps, targets = old_functions(sha)
    seen = set()
    paths = {p for p, _ in targets}
    def trace(frame, event, _arg):
        """Рахує виконані емісії у змінених модулях."""
        if frame.f_code.co_filename not in paths:
            return None
        if event == "line" and (frame.f_code.co_filename, frame.f_lineno) in targets:
            seen.add((frame.f_code.co_filename, frame.f_lineno))
        return trace
    def evaluate(fn, old=False, collect=True):
        """Виконує той самий виклик зі старими чи поточними емітентами."""
        for namespace, key, current, previous in swaps:
            namespace[key] = previous if old else current
        try:
            sys.settrace(trace if collect and not old else None)
            return copy.deepcopy(fn())
        finally:
            sys.settrace(None)
            for namespace, key, current, _previous in swaps:
                namespace[key] = current
    report = dict(base=sha, limitation=__doc__.strip(), cases=[], catalogue=[], uncovered=[])
    def save():
        """Зберігає вже отримані факти, включно з невдалим порівнянням."""
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    def compare(label, fn):
        """Порівнює фактичні виходи гілки й перевіряє вагу станів."""
        before, after = evaluate(fn, True), evaluate(fn)
        for z in Z.список(after):
            if z.get("сила") in STATES:
                assert z.get("сила_нп") == 0.0 and z.get("блокує") is False, z
                assert not ({"впевненість", "для_стиліста"} & z.keys()), z
        report["cases"].append(dict(case=label, before=before, after=after))
        save()
    red = element("червоний", "верх", (60, 65, 20))
    red2 = element("червона сумка", "сумка", (60, 65, 20))
    white = element("оптичний", "верх", (90, 0, 0))
    cream = element("вершковий", "сумка", (90, 0, 10))
    compare("координація: одна річ", lambda: CO.координація([red]))
    compare("координація: немає набору", lambda: CO.координація([red, red2]))
    distance = CO.середня_близькість([red, red2])
    compare("координація: немає розкиду", lambda: CO.координація([red, red2], [distance] * 3))
    compare("точний збіг шумніший за поріг", lambda: AC.надточний_збіг([red, red2]))
    for state in ("шум", "шум_L"):
        compare("нейтралі: " + state, lambda state=state: KN._зібрати_крос([(white, cream, (state, 2.0))]))
    compare("білі: відповідь відсутня", lambda: KN.білі([white]))
    compare("білі: відповідь без боку", lambda: KN.білі([white], драп={"білий": "не бачу різниці"}))
    compare("білі: немає площі", lambda: KN.білі([white, cream]))
    compare("кольору немає", lambda: KR.без_входу_кольору("K-COL-01", [(dict(red, lab=None),)],
                                                       перевірка="cannot_tell_lightness_structure"))
    compare("світлота: одна поверхня", lambda: KL.перевірка_value([dict(white, площа=0.7)]))
    compare("контраст: у межах", lambda: KL.біля_обличчя([dict(white, L=65, lab=(65, 0, 0))],
                dict(доступно=True, L_шкіри=70, value_gap=5)))
    features = CS.features(CS.hx("#cba58e"), CS.hx("#1735c7"), CS.hx("#597170"))
    features["оправа"] = dict(C=60.0, h=100.0)
    compare("хрома: площі волосся й оправи немає", lambda: KC.бюджет_хроми([red, red2], features))
    compare("відлуння: немає площі", lambda: KC.відлуння([red, red2]))
    compare("сукня: немає бала фото", lambda: FM.формальність_образу([dict(white, тип="сукня_без_уточнення", слот="сукня")]))
    # Варіанти класу слота мають різні поверхні за невідомої площі.
    for slot in ("сумка", "взуття", "шарф"):
        pair = [element("холодна річ", "верх", (70, 0, -4)), element("тепла річ", slot, (70, 4, 10))]
        compare("крос за слотом: " + slot, lambda pair=pair: KN.нейтралі_крос_за_слотом(pair))
        compare("світлота за слотом: " + slot, lambda pair=pair: KL.перевірка_value_за_слотом(pair))
    report["emissions"] = dict(total=len(targets), covered=len(targets & seen))
    report["uncovered"] = [dict(file=str(pathlib.Path(p).relative_to(ROOT)), line=n) for p, n in sorted(targets - seen)]
    report["catalogue_scope"] = "Фінальні знахідки вердикт.образи[0].знахідки; вкладені діагностичні представлення не лічаться як емісії."
    save()
    print("ФАКТ · гілок емісії %d/%d" % (len(targets & seen), len(targets)), flush=True)
    inp = json.loads((SRC / "стенд_вх.json").read_text(encoding="utf-8"))
    for scene, scenario in SZ.СЦЕНАРІЇ.items():
        request = dict(inp, сценарій=scenario, випадок=scene)
        packet = json.loads(B.виклик("запити", json.dumps(request, ensure_ascii=False)))
        candidates = packet.get("кандидати") or {}
        slots = [[c["id"] for c in candidates.get(s, [])[:2]] for s in ("верх", "низ", "взуття", "сумка")]
        for ids in itertools.product(*[s for s in slots if s]):
            fn = lambda ids=ids: json.loads(B.виклик("від_моделі", json.dumps(dict(request, ід=list(ids)), ensure_ascii=False)))
            before, after = evaluate(fn, True, False), evaluate(fn, False, False)
            def findings(result):
                """Повертає один канонічний перелік фінального суду образу."""
                assert not result.get("помилка"), result
                return result["вердикт"]["образи"][0].get("знахідки") or []
            old, new = findings(before), findings(after)
            key = lambda z: (z.get("правило"), z.get("суть"),
                             () if z.get("сила") == "ok" else tuple(z.get("речі") or []))
            if [key(z) for z in old] != [key(z) for z in new]:
                report["mismatch"] = dict(scene=scene, ids=ids, before=old, after=new)
                save()
                raise AssertionError("змінився склад знахідок")
            changes = []
            for a, b in zip(old, new):
                if a == b:
                    continue
                assert a.get("сила") in STATES and b.get("сила") == a.get("сила"), (a, b)
                assert b["сила_нп"] == 0.0 and not b["блокує"], b
                changes.append(dict(rule=b["правило"], state=b["сила"],
                    fields={k: [a.get(k), b.get(k)] for k in a.keys() | b.keys() if a.get(k) != b.get(k)}))
            report["catalogue"].append(dict(scene=scene, ids=ids, findings=len(new), changes=changes))
        print("ФАКТ · каталог: " + scene, flush=True)
    report["uncovered"] = [dict(file=str(pathlib.Path(p).relative_to(ROOT)), line=n) for p, n in sorted(targets - seen)]
    report["emissions"] = dict(total=len(targets), covered=len(targets & seen))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ФАКТ · емісій %d/%d · випадків %d · складів каталогу %d" %
          (len(targets & seen), len(targets), len(report["cases"]), len(report["catalogue"])))
    if targets - seen:
        print("Не охоплено:", report["uncovered"])


if __name__ == "__main__":
    main()
