"""Звужує виняток сортування розділу 71 до двох речей базового каталогу."""
import json, sys, xml.etree.ElementTree as ET
from pathlib import Path
дерево = Path(sys.argv[1]).resolve(); тека = Path(sys.argv[2]).resolve()
sys.path.insert(0,str(дерево/'джерела'))
import feed as ф
sys.stdout = open(sys.argv[3],'w',encoding='utf-8',buffering=1)
база = тека/'база-чистка.xml'
офери, _ = ф.читати_yml(str(база))
взяті = {}
for о in офери:
    з = ф.побудувати_запис_речі(о)
    о['запис_речі'] = з
    if ф.набір_цілий(о) is not True and ф.слот(о) != 'комплект':
        continue
    ключ = з['тип'] is None
    взяті.setdefault(ключ,о)
    if len(взяті)==2:
        break
print('Базовий каталог 560fa388; зразки до PR:',json.dumps([dict(id=о['id'],назва=о['назва'],тип=ф.побудувати_запис_речі(о)['тип']) for о in взяті.values()],ensure_ascii=False))
ід = {о['id'].split('@')[0] for о in взяті.values()}
к = ET.parse(база)
контейнер = к.find('.//offers')
for о in list(контейнер):
    if о.get('id') not in ід:
        контейнер.remove(о)
файл = тека/'два-комплекти.xml'; к.write(файл,encoding='utf-8',xml_declaration=True)
каталог = ф.прогін(str(файл),[],кеш=str(тека/'типи-кеш.json'),ліміт_фото=0)['каталог']
типи = {о.get('тип') for о in каталог if о['слот']=='комплект'}
print('Після штатного feed.прогін:',json.dumps([dict(id=о['id'],слот=о['слот'],тип=о.get('тип')) for о in каталог],ensure_ascii=False))
try:
    print('sorted:',sorted(типи))
except TypeError as п:
    print('Відтворено на двох речах бази:',type(п).__name__,str(п))
