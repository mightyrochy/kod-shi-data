"""Звіряє AST змінених функцій із Python-вантажем повної HTML-збірки."""
import ast, base64, io, json, pathlib, re, sys, zipfile

ФУНКЦІЇ = {'selection_policy': ['ідентичність', 'порядок', 'ключ_образу'],
           'семплер': ['_перемішати', 'вибрати_зі_слота'],
           'композитор_реєстр': ['перемішати'], 'порядок_запиту': ['перемішати', 'перемішати_слоти', 'перемішати_дріт'],
           'пакет_моделі': ['номери_речей'], 'міст_пакет': ['додати_за_запитом'],
           'міст_відповіді': ['від_моделі'],
           'повнота_образу': ['_ключ_мети', 'дібрати_кодом', '_ремонт_гейтів',
                             'повнота_набору', 'вердикт_повноти', 'вибір_з_json']}


def функції(текст):
    """Повертає AST функцій без документальних рядків, які знімає збирач."""
    дерево = ast.parse(текст)
    for вузол in ast.walk(дерево):
        if isinstance(вузол, (ast.Module, ast.FunctionDef, ast.ClassDef)) and вузол.body:
            п = вузол.body[0]
            if isinstance(п, ast.Expr) and isinstance(п.value, ast.Constant) and isinstance(п.value.value, str):
                вузол.body.pop(0)
    return {n.name: ast.dump(n, include_attributes=False) for n in дерево.body if isinstance(n, ast.FunctionDef)}


def головна():
    """Знайти ZIP вантажу та перевірити функції на закомічених джерелах."""
    корінь = pathlib.Path(__file__).resolve().parents[3]
    текст = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
    for збіг in re.finditer(r'[A-Za-z0-9+/]{10000,}={0,2}', текст):
        try:
            архів = zipfile.ZipFile(io.BytesIO(base64.b64decode(збіг.group())))
        except zipfile.BadZipFile:
            continue
        вади, всього = [], 0
        for модуль, імена in ФУНКЦІЇ.items():
            дж = функції((корінь / 'джерела' / (модуль + '.py')).read_text(encoding='utf-8'))
            вантаж = функції(архів.read(модуль + '.py').decode('utf-8'))
            for ім in імена:
                всього += 1
                if дж[ім] != вантаж.get(ім): вади.append(модуль + '::' + ім)
        print(json.dumps(dict(функцій=всього, розбіжності=вади), ensure_ascii=False))
        return int(bool(вади))
    raise ValueError('У збірці не знайдено Python-вантажу')


if __name__ == '__main__':
    sys.exit(головна())
