"""Рядок 4280: глобали, що модуль визначає двічі на верхньому рівні — друге мовчки перекриває перше
(#866: `_КІНЕЦЬ_РЕЧЕННЯ` на рядках 191 і 3206). Друкує «модуль: ім'я — рядки» для кожного імені,
крім `__all__` та імен, які друге визначення будує з першого. Запуск: cd джерела && python3 проби/перекриті_глобали.py [файли]"""
import ast, glob, sys
for ф in sys.argv[1:] or sorted(glob.glob("*.py")):
    дерево, імена = ast.parse(open(ф, encoding="utf-8").read()), {}
    for в in дерево.body:
        цілі = [в.name] if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else \
            [ц.id for ц in (в.targets if isinstance(в, ast.Assign) else [getattr(в, "target", None)]) if isinstance(ц, ast.Name)]
        for і in цілі:
            читає = any(isinstance(н, ast.Name) and н.id == і and isinstance(н.ctx, ast.Load) for н in ast.walk(в)) if not isinstance(в, (ast.FunctionDef, ast.ClassDef)) else False
            імена.setdefault(і, []).append((в.lineno, читає))
    for і, р in імена.items():
        if len(р) > 1 and not any(ч for _, ч in р[1:]) and і != "__all__":
            print("%s: %s — рядки %s" % (ф, і, [л for л, _ in р]))
