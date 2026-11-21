"""Сторож будови ядра (`РЕЗУЛЬТАТ.md`, §4, «Ще в Н1»; мірило (ґ) наряду Н1): не лічильник місць, а заборона з нулем.

У `джерела/ядро/` (без `тести/`): нема `except: pass`; нема імпорту модулів, які ядро заміняє (`ОПИС.md`, розділ 3);
нема функцій над рядками її слів чи назв крамниць (п.12) — ні `re`, ні рядкових методів розбору тексту; кожне
поняття `поняття.py` складає лише його писач; кожну схему відповіді моделі читає один модуль.
"""
import ast
import os
import unittest

from ядро import поняття

ЯДРО = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ЗАМІННІ = set("""мовний_шар паспорт_нагоди паспорт_поля паспорт_основи міст_вхід картка_запиту її_входи conversation_tools
language_contract пакет_моделі міст_пакет міст_запити композитор_збирання композитор_слоти композитор_полюси
композитор_оцінка композитор_реєстр композитор_річ композитор_придатні семплер різноманітність_пулу уважний_вибір
порядок_запиту brief знання_дріт дріт_моделі збирач_промптів спільні_вимоги фрази_формату кеш_входу розбір_відповідей
протокол схема_відповіді схеми_розбору міст_відповіді руки_без_коду міст_рука2 знахідка людський_вихід суд_від_моделі
вердикт_моделі перевірка_образу суд_огляд суд_чеклісти суд_образу повнота_образу selection_policy міст_опис
пропозиція_заміни заміна_речі причини_речі bridge покроковик""".split())
РЯДКОВІ = {"lower", "upper", "casefold", "split", "rsplit", "splitlines", "startswith", "endswith", "replace", "find",
           "rfind", "index", "strip", "lstrip", "rstrip", "translate", "partition", "count", "title", "capitalize"}


def модулі():
    for ім in sorted(os.listdir(ЯДРО)):
        if ім.endswith(".py"):
            with open(os.path.join(ЯДРО, ім), encoding="utf-8") as ф:
                yield ім[:-3], ast.parse(ф.read(), ім)


class Будова(unittest.TestCase):
    def test_нема_except_pass(self):
        for ім, д in модулі():
            for в in ast.walk(д):
                if isinstance(в, ast.ExceptHandler):
                    with self.subTest(модуль=ім, рядок=в.lineno):
                        self.assertFalse(all(isinstance(т, ast.Pass) for т in в.body), "виняток ковтається мовчки")
                        self.assertIsNotNone(в.type, "голий except")

    def test_нема_імпорту_замінних(self):
        for ім, д in модулі():
            for в in ast.walk(д):
                імена = ([а.name for а in в.names] if isinstance(в, ast.Import)
                         else [в.module or ""] if isinstance(в, ast.ImportFrom) and not в.level else [])
                for і in імена:
                    with self.subTest(модуль=ім, імпорт=і):
                        self.assertNotIn(і.split(".")[0], ЗАМІННІ | {"re"})

    def test_нема_функцій_над_рядками_слів(self):
        for ім, д in модулі():
            for в in ast.walk(д):
                if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr in РЯДКОВІ:
                    with self.subTest(модуль=ім, рядок=в.lineno):
                        self.fail(f"рядковий метод .{в.func.attr}() — слова тлумачить лише мовна модель (п.12)")

    def test_один_писач_поняття(self):
        писачі = {ім: кл.ПИСАЧ for ім, кл in vars(поняття).items()
                  if isinstance(кл, type) and issubclass(кл, поняття._Поняття) and кл.ПИСАЧ}
        self.assertTrue({"Ситуація", "Пул", "Запит", "Образ", "Вирок", "Вибір", "Картка", "Річ"} <= set(писачі))
        for ім, д in модулі():
            for в in ast.walk(д):
                ф = в.func if isinstance(в, ast.Call) else None
                кл = (ф.id if isinstance(ф, ast.Name) else ф.value.id
                      if isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name) else None)
                if кл in писачі and ім != "поняття":
                    with self.subTest(модуль=ім, поняття=кл):
                        self.assertEqual(ім, писачі[кл], f"{кл} складає не його писач")

    def test_одна_схема_один_читач(self):
        читачі = {}
        for ім, д in модулі():
            for в in ast.walk(д):
                if isinstance(в, ast.Constant) and isinstance(в.value, str) and в.value.startswith("схема:"):
                    читачі.setdefault(в.value, set()).add(ім)
        for схема, мм in читачі.items():
            with self.subTest(схема=схема):
                self.assertEqual(len(мм), 1, f"{схема} читають {sorted(мм)}")


if __name__ == "__main__":
    unittest.main()
