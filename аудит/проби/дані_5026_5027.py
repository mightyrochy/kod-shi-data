"""Разовий інвентар даних; без моделей, мережі й оцінювання фото."""
import collections, gzip, hashlib, json, pathlib, re, subprocess
корінь = pathlib.Path(__file__).resolve().parents[2]
голова = '8f22756364e060d4fc968671be11740d6aed8ceb'
медіа = '3a6b9a43023a63d9b837473b2f235b09c3ee5717'
шлях = 'аудит/перевірка/4920/незалежна_533e88ab/очні_оцінки.json'
def blob(ша, ім):
    return subprocess.check_output(['git', '-C', str(корінь), 'show', ша + ':' + ім])
import xml.etree.ElementTree as XML
імена = ['каталог_повний.xml.gz', 'джерела/каталог_збагачення.json.gz', 'джерела/каталог_кадри.json.gz']
байти = {ім: blob(голова, ім) for ім in імена}
фід = XML.fromstring(gzip.decompress(байти[імена[0]])).findall('.//offer')
збагачення = json.loads(gzip.decompress(байти[імена[1]]))
кадри = json.loads(gzip.decompress(байти[імена[2]]))['записи']
архів = blob(медіа, шлях); оцінки = json.loads(архів)
зміни = [р['id'] for р in оцінки if р['зміна']]; assert len(зміни) == 40
переліки = {}; поля = collections.Counter(); атрибути = collections.Counter(); url_поля = collections.Counter()
for р in фід:
    п = {х.get('name'): х.text or '' for х in р.findall('param')}
    ід = р.get('id') + '@' + п['магазин']
    списки = [set(а.strip().casefold() for а in re.split(r'[,;|]', п.get(к, '')) if а.strip()) for к in ['Колір', '~Колір']]
    атоми = max(списки, key=len)
    if len(атоми) >= 2: переліки[ід] = sorted(атоми)
    поля.update(п.keys()); атрибути.update(str(х.attrib) for х in р.findall('picture'))
    url_поля.update(к for к, в in п.items() if 'http' in в)
    assert all(not list(х) for х in р), 'Вкладені зв’язки потребують окремого читання'
схема = sorted(set(к for р in збагачення.values() for к in р))
вкладені_json = []
for р in фід:
    for х in р:
        try: в = json.loads(х.text or '')
        except ValueError: continue
        if isinstance(в, (dict, list)): вкладені_json.append(р.get('id'))
assert not вкладені_json, 'Вкладений JSON потребує перевірки зв’язків'
код_прозорості = {к: р for к, р in збагачення.items() if any(т in п.casefold() for п in р for т in ['прозор', 'opacity', 'transparen', 'transluc'])}
свотчі = [р for р in фід if any(х.get('name') == 'свотч_фото' for х in р.findall('param'))]
рез = {'main': голова, 'source_959': '2ec50075ccd00f7b45e34dbbcc2b34a2ebfff62d', 'media': медіа, 'sha256_gzip': {к: hashlib.sha256(в).hexdigest() for к, в in байти.items()}, 'sha256_frozen_archive': hashlib.sha256(архів).hexdigest(), 'denominator_definition': 'Усі сирі XML offer, включно з unavailable; ≥2 різні непорожні literal atoms в одному Колір або ~Колір, розділені комою/крапкою з комою/pipe. Slash і дефіс збережено. Це перелік атомів, а не доведені варіанти; не каталог11887 старої проби.', 'link_definition': 'Структурне явне присвоєння URL picture ідентифікатору або атому variant у фіді. Без filename heuristic, свотча як галереї, кольорового виміру або group як здогадки. Нуль обмежено збереженим XML, не сайтами.', 'transparency_definition': 'Окремий структурний код прозорості/напівпрозорості тканини; матеріал/вільний опис не код. Усі ключі збагачення та значення матеріалу наведено.', 'embedded_json_count': len(вкладені_json), 'offers': len(фід), 'enrichment_records': len(збагачення), 'multi_color_fields': len(переліки), 'multi_color_ids': sorted(переліки), 'picture_attribute_counts': dict(атрибути), 'feed_relation_candidate_fields': sorted(к for к in поля if any(т in к.casefold() for т in ['фото', 'свотч', 'варіант', 'variant', 'image', 'picture'])), 'swatch_records': len(свотчі), 'swatch_multi_color_records': sum(р.get('id') + '@' + next(х.text for х in р.findall('param') if х.get('name') == 'магазин') in переліки for р in свотчі), 'enrichment_fields': схема, 'material_values': sorted(set(str(р.get('матеріал')) for р in збагачення.values())), 'url_param_fields': dict(url_поля), 'explicit_gallery_variant_links': 0, 'transparency_code_records': len(код_прозорості), 'frozen40_with_transparency_code': sum(к in код_прозорості for к in зміни), 'frozen40_found_in_enrichment': sum(к in збагачення for к in зміни), 'frozen40_ids': зміни, '03995_measured_gallery_count': len(кадри.get('ж-03995@maxa.ua', [])), '01513_measured_gallery_count': len(кадри.get('ж-01513@wearme.ua', []))}
print(json.dumps(рез, ensure_ascii=False, indent=2))
