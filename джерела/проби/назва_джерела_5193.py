"""5193: лічить наявні джерела назв, не створює модельних відповідей або каталогу."""
import gzip, hashlib, json, xml.etree.ElementTree as E
from collections import Counter
from pathlib import Path

def main():
    """Друкує факти сирого фіду, збагачення й назв карток без запуску продукту."""
    корінь = Path(__file__).resolve().parents[2]
    тека = корінь / 'джерела'
    сирі = (корінь / 'каталог_повний.xml.gz').read_bytes()
    речі = E.fromstring(gzip.decompress(сирі)).findall('.//offer')
    збагачення = json.loads(gzip.decompress((тека / 'каталог_збагачення.json.gz').read_bytes()))
    картки = json.loads(gzip.decompress((тека / 'назви_карток.json.gz').read_bytes()))
    ключі = Counter()
    def порахувати(значення):
        """Лічить ключі також у вкладених записах, зокрема з_v1."""
        if isinstance(значення, dict):
            ключі.update(значення.keys())
            for дочірнє in значення.values():
                порахувати(дочірнє)
        elif isinstance(значення, list):
            for дочірнє in значення:
                порахувати(дочірнє)
    порахувати(збагачення)
    поля = ('name', 'name_ua', 'назва', 'назва_показу', 'title', 'display_name')
    параметри = Counter(п.get('name') for р in речі for п in р.findall('param'))
    назви = [р.findtext('name') or '' for р in речі]
    print(json.dumps(dict(raw=len(речі), id_різні=len({р.get('id') for р in речі}),
        url_непорожні=sum(bool(р.findtext('url')) for р in речі),
        name_непорожні=sum(bool(н.strip()) for н in назви), name_різні=len(set(назви)),
        name_ua=sum(р.find('name_ua') is not None for р in речі),
        vendor_model=sum(р.get('type') == 'vendor.model' for р in речі),
        назва_показу_param=параметри['назва_показу'],
        джерело_опис=sum(р.findtext("param[@name='назва_джерело']") == 'опис' for р in речі),
        бренд_у_name=sum('(Other Brand)' in н for н in назви),
        збагачення=len(збагачення), ключі_назви={к: ключі[к] for к in поля},
        картки=len(картки), картки_рядки=sum(isinstance(з, str) for з in картки.values()),
        raw_gzip_sha256=hashlib.sha256(сирі).hexdigest()), ensure_ascii=False, sort_keys=True))
if __name__ == '__main__':
    main()
