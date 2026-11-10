"""Порівняти пул і суд стенда на знімках Python-коду з Git та на робочому дереві."""
import importlib.machinery as ім, importlib.util as іу
import json, os, subprocess, sys, tempfile
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[3]
ДЖ = КОРІНЬ / 'джерела'
sys.path.insert(0, str(ДЖ))
os.chdir(КОРІНЬ)
версія = sys.argv[1]

def git(шлях):
    """Прочитати файл з названого коміту без зміни робочого дерева."""
    return subprocess.check_output(['git', 'show', f'{версія}:{шлях}'])

class Знімок:
    """Завантажувати локальні Python-модулі з одного знімка Git."""
    def find_spec(self, імʼя, path=None, target=None):
        """Зберегти шлях модуля, замінивши лише його Python-код."""
        опис = ім.PathFinder.find_spec(імʼя, path)
        if опис and опис.origin and Path(опис.origin).suffix == '.py' and Path(опис.origin).is_relative_to(ДЖ):
            class Читач(ім.SourceFileLoader):
                def get_code(self, fullname):
                    """Компілювати код з Git без кешу байткоду робочого дерева."""
                    return compile(git(Path(self.path).relative_to(КОРІНЬ).as_posix()), self.path, 'exec')
            return іу.spec_from_file_location(імʼя, опис.origin, loader=Читач(імʼя, опис.origin))

if версія != 'робоче':
    sys.meta_path.insert(0, Знімок())
import bridge as Б, feed as Ф
вхід = json.loads((ДЖ / 'стенд_вх.json').read_text(encoding='utf-8') if версія == 'робоче'
                 else git('джерела/стенд_вх.json'))
вхід.update(сід=3, каталог=Ф.каталог_на_диску(str(ДЖ / 'каталог_brief.xml')),
            кеш_кольорів=str(Path(tempfile.gettempdir()) / 'кеш_живого_шляху.json'))
виклик = lambda назва, дані: json.loads(Б.виклик(назва, json.dumps(дані, ensure_ascii=False)))
пул = виклик('запити', вхід)['пакети']['1']['пул']
образи = [dict(ід=f'о{і+1}', підпис='t', речі=[пул[с][і]['н'] for с in ('верх', 'низ', 'взуття', 'сумка', 'шарф', 'верхній_шар')]) for і in (0, 1)]
суд = виклик('від_моделі', dict(вхід, текст_моделі=json.dumps(dict(версія='1', образи=образи), ensure_ascii=False)))
вибір = виклик('від_моделі', dict(вхід, ітерація=2, відповідь='ВИБІР_V1', вибір_над=суд['вибір_над'], текст_моделі='{"версія":"1","обрано":"о1"}'))['вибір']
дані = dict(версія=версія, вхід=вхід, пул={с: [dict(н=р['н'], назва=р.get('назва'), тип=р.get('тип')) for р in п[:3]] for с, п in пул.items()},
             запропоновано=образи, прийнято=[{к: о.get(к) for к in ('ід', 'номер', 'речі_н', 'блокери')} for о in суд['образи']],
             верхній_суд=[р['id'] for р in суд['речі']], розбір=суд.get('розбір_блоків'), вибір=вибір)
Path(sys.argv[2]).write_text(json.dumps(дані, ensure_ascii=False, indent=2), encoding='utf-8')
print(версія, 'образів', len(суд['образи']), 'склад_збігається', суд['образи'][0]['ід'] == дані['верхній_суд'], 'вибрано_речей', len(вибір['ід']), 'відмова', вибір.get('чому_відмова'))
