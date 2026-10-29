"""Контроль пари бачить поля пакета за однакового брифа та ігнорує порядок пулу."""
import copy, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import поломки as П
перший = dict(текст='той самий бриф', пакет=dict(правила=[], coat_required=True,
               завдання=['third_piece'], пул=[dict(id='а'), dict(id='б')]))
другий = copy.deepcopy(перший)
другий['пакет']['пул'].reverse()
assert П.різниця_промптів(перший, другий) is False
for поле, значення in (('coat_required', False), ('завдання', ['no_third_piece']),
                      ('правила', [dict(код='K-CRA-01', заява='no_third_piece')])):
    другий = copy.deepcopy(перший)
    другий['пакет'][поле] = значення
    assert П.різниця_промптів(перший, другий) is True, поле
assert П.різниця_промптів(перший, None) is None
print('Е3: контроль пари — 3/3 зміни полів за незмінного брифа; переставлення пулу — без хибної різниці')
