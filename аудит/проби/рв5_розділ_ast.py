# -*- coding: utf-8 -*-
"""Проба РВ-5 · «жодних змін поведінки» етапу 7 перевіряється по AST, не по слову.

(1) Н-02-01: кожна верхня сутність старого `outfit.py` (коміт ab5711b — після С-56,
до сесії 1) мусить знайтись рівно в одному з п'яти модулів із тим самим AST;
дозволена різниця — лише рядкові літерали (адреси «outfit.X» → «модуль.X», сесія 4).
Звіряється двічі: з кінцем сесії 4 (163d39d — рівно розділення) і з HEAD, куди вже
входять Н-02-05 (С-60) і Н-small-data-107 — розбіжності другої звірки їхні.
(2) Н-02-02 / Н-02-03: функції, перенесені в `лабораторія/`, мусять мати той самий
AST, що їхні тіла в модулях ядра на debab18 (після С-60, до переносу).

Прогін:  cd джерела && python3 ../аудит/проби/рв5_розділ_ast.py
"""
import ast, os, subprocess
ДЖ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "джерела"))
os.chdir(ДЖ)
МОДУЛІ = ("outfit", "реєстр_правил", "колір_образу", "формальність", "суд_образу")


def з_гіта(коміт, файл):
    return subprocess.run(["git", "show", "%s:джерела/%s" % (коміт, файл)],
                          capture_output=True, text=True, check=True).stdout


def сутності(текст):
    з = {}
    for n in ast.parse(текст).body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            з[n.name] = n
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    з[t.id] = n
    return з


def без_рядків(n):
    n2 = ast.parse(ast.unparse(n))
    for c in ast.walk(n2):
        if isinstance(c, ast.Constant) and isinstance(c.value, str):
            c.value = "S"
    return ast.dump(n2)


def стан(a, b):
    if a is None: return "НЕМА У СТАРОМУ"
    if b is None: return "НЕМА В НОВОМУ"
    if ast.dump(a) == ast.dump(b): return "ідентично"
    if без_рядків(a) == без_рядків(b): return "лише рядки"
    return "⚠ AST РІЗНИТЬСЯ"


def звірити_розділ(підпис, читач):
    старе = сутності(з_гіта("ab5711b", "outfit.py"))
    нові = {}
    for м in МОДУЛІ:
        for k, v in сутності(читач(м)).items():
            нові.setdefault(k, []).append((м, v))
    лічба = {}
    print("── 1. Розділення outfit.py: ab5711b → %s" % підпис)
    for k, n in старе.items():
        if k not in нові:
            лічба["зникли"] = лічба.get("зникли", 0) + 1
            print("   зникло: %s" % k); continue
        м, нн = нові[k][0]
        с = стан(n, нн)
        лічба[с] = лічба.get(с, 0) + 1
        if с != "ідентично":
            print("   %-16s %-24s → %s" % (с, k, м))
    дублі = [k for k in старе if k in нові and len(нові[k]) > 1]
    print("   сутностей %d · %s · дублі між модулями: %s"
          % (len(старе), " · ".join("%s %d" % (k, v) for k, v in лічба.items()), дублі or "0"))


звірити_розділ("163d39d (кінець сесії 4 — рівно розділення)", lambda м: з_гіта("163d39d", м + ".py"))
print()
звірити_розділ("HEAD (плюс Н-02-05 і Н-small-data-107: розбіжності тут — їхні)",
               lambda м: open(м + ".py", encoding="utf-8").read())

print("\n── 2. Переноси в лабораторія/ (debab18 → HEAD)")
ПЕРЕНЕСЕНО = {
 "без_викликача.py": [("areas", "near_face"), ("bases", "зона_світлоти"), ("colorspace", "from_image"),
                      ("colorspace", "ht_scale"), ("fit", "_максимум_у_вікні"), ("graph", "з_тілом"),
                      ("graph", "ключ_комбінації"), ("palettes", "для_сезону"), ("silhouette", "рід_речі"),
                      ("verify", "є_візерунок"), ("colorspace", "та_сама_шкіра"), ("graph", "рядок_вузла_словами")],
 "зони_з_масок.py": [("extract", "adaptive_k"), ("extract", "erode"), ("extract", "face_frame_band"),
                     ("extract", "cheek_zone"), ("extract", "illuminant_cast"), ("extract", "build_zones"),
                     ("extract", "MIN_SCLERA_PX"), ("colorspace", "ZONE_MAP"), ("colorspace", "infer_source"),
                     ("colorspace", "features_from_zones")],
 "правки_профілю.py": [("profile", "_зсув"), ("profile", "перефарбування"), ("profile", "засмага"),
                       ("profile", "макіяж"), ("profile", "вікна_біля_обличчя")],
 "передбачення_координації.py": [("coordination", "ПЕРЕДБАЧЕННЯ"), ("coordination", "розрізнювальна_здатність"),
                                 ("coordination", "розрізнювальна_інтенсивності"), ("coordination", "не_зроблено")],
}
старі, лічба = {}, {}
for файл, список in ПЕРЕНЕСЕНО.items():
    нов = сутності(open(os.path.join("лабораторія", файл), encoding="utf-8").read())
    for м, ім in список:
        if м not in старі:
            старі[м] = сутності(з_гіта("debab18", м + ".py"))
        с = стан(старі[м].get(ім), нов.get(ім))
        лічба[с] = лічба.get(с, 0) + 1
        if с != "ідентично":
            print("   %-28s %-24s %s" % (файл, ім, с))
    зайві = [k for k in нов if k not in {ім for _, ім in список} and not k.startswith("__")]
    if зайві:
        print("   %-28s інші верхні імена: %s" % (файл, зайві))
print("   перенесених сутностей %d · %s" % (sum(лічба.values()), " · ".join("%s %d" % (k, v) for k, v in лічба.items())))
