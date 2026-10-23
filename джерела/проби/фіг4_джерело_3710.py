"""3710: факти frozen каталогу й входи повтору; фото та моделі не запускає."""
import collections, gzip, hashlib, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feed as Ф, фід_розбір as Р, outfit as О
import жнива_реєстр as Ж

def головна():
    """Друкує факти; за третім аргументом зберігає лише вхід пілоту поза продуктом."""
    сирий_xml = gzip.decompress(Path(sys.argv[1]).read_bytes())
    fd = os.memfd_create("3710_exact_raw"); os.write(fd, сирий_xml)
    фід = "/proc/self/fd/%d" % fd
    офери = Р.офери_фіду(фід); сирі = {р['id']: р for р in офери}
    кат = Ф.база_прогону(фід, ліміт_фото=0, кеш=str(Path(os.environ["TMPDIR"]) / "3710_кеш_не_створюється.json"), кешувати=False)['каталог']
    сукні = [р for р in кат if р.get('слот') == 'сукня' and р.get('тип') != 'комбінезон']
    пілот = [р for р in сукні if р.get('крій') in ('fitted', 'relaxed')]
    вхід = []
    for р in sorted(пілот, key=lambda р: р['id']):
        о = сирі[р['id']]; слот = Ф.слоти(о)['слот']; тип = Ф.тип_речі(о, слот)
        сукня = Ж.це_сукня(слот, тип)
        вхід.append(dict(id=р['id'], слот=слот, тип=тип, контракт_сукні=сукня,
                         крій_до=р.get('крій'), крої_до=О.крої_слота(р)[0], фото=о.get('фото'),
                         фото_опису_до=р.get('фото_опису'), джерело_до=р.get('крій_джерело')))
    print('RAW XML', len(сирий_xml), 'SHA256', hashlib.sha256(сирий_xml).hexdigest(), 'offers', len(офери))
    print('RUNTIME каталог', len(кат), 'сукні', len(сукні), 'крої', dict(collections.Counter(р.get('крій') for р in сукні)))
    print('RUNTIME SHA256', hashlib.sha256(json.dumps(кат, ensure_ascii=False, sort_keys=True).encode()).hexdigest(), 'raw_ids_поза_runtime', sorted(set(сирі) - {р['id'] for р in кат}))
    print('пілот', len(вхід), 'типи producer', dict(collections.Counter(р['тип'] for р in вхід)))
    print('контракт сукні', sum(р['контракт_сукні'] for р in вхід), 'без одного крою ДО', sum(len(р['крої_до']) != 1 for р in вхід))
    комб = [р for р in офери if Ф.тип_речі(р, Ф.слоти(р)['слот']) == 'комбінезон']
    print('комбінезонів', len(комб), 'dressenum', sum(Ж.це_сукня(Ф.слоти(р)['слот'], 'комбінезон') for р in комб), 'None', Ж.це_сукня('сукня', None))
    print('перелік ДО', Ж.КРОЇ, 'ПІСЛЯ', Ж.КРОЇ_СУКНІ, 'невідоме', None)
    print('пілот sha256', hashlib.sha256(json.dumps(вхід, ensure_ascii=False, sort_keys=True).encode()).hexdigest())
    os.close(fd)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(вхід, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    головна()
