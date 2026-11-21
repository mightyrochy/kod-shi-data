"""Виконує змінену перевірку замші з гейтів на її власному вході."""
import ast
import inspect
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import accessory
import outfit
import реєстр_правил
import суд_образу


def main():
    """Перевірити сам вираз гейта після зміни контракту сирої ваги."""
    шлях = pathlib.Path(__file__).resolve().parent.parent / 'прилади/розділи_гейтів.py'
    модуль = ast.parse(шлях.read_text(encoding='utf-8')).body
    тіло = next(n.body for n in модуль if isinstance(n, ast.FunctionDef) and n.name == 'main')
    # перехідний помічник гейтів `_сц` (#4550) — частина виразу гейта, поки він є в модулі
    помічники = [n for n in модуль if isinstance(n, ast.FunctionDef) and n.name == '_сц']
    імена = {'_пара121', '_речі121', '_п5', '_п1'}
    вибрані = [n for n in тіло if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id in імена for t in n.targets)]
    вибрані += [n for n in тіло if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                 and isinstance(n.value.func, ast.Name) and n.value.func.id == 'тест'
                 and n.value.args and isinstance(n.value.args[0], ast.Constant)
                 and str(n.value.args[0].value).startswith('замша в мокрий сніг:')]
    assert len(вибрані) == 5
    def перевірити(назва, умова, доказ):
        """Залишити оцінку й діагностику оригінального гейта."""
        print(назва, доказ)
        assert умова, доказ
    простір = dict(_A121=accessory, O=outfit, _СУД=суд_образу,
                   _РЕЄСТР=реєстр_правил, тест=перевірити, _inspect_сц=inspect)
    exec(compile(ast.Module(body=помічники + вибрані, type_ignores=[]), str(шлях), 'exec'), простір)


if __name__ == '__main__':
    main()
