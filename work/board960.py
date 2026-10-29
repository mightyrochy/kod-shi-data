from pathlib import Path
p=Path(__file__).resolve().parents[1]/'аудит/БЕКЛОГ.md'
notes={
 '2672':' Ноутбук #960: у всіх 4 завершених сценах `codex/znimky-960-pislia:аудит/живі_960` є код.txt з source SHA 7c90a0093b5d7dc8587a90c541eaf11e23b9a3be, id, ПІСЛЯ й обома моделями; історичні прогалини цим не закрито.',
 '2900':' Ноутбук #960 на 7c90a009: HTTP 599 у двох повних сценах новорічної/морозу — 0/0; raw API й логи збережені в codex/znimky-960-pislia:аудит/живі_960. Це виконавчий вимір, не незалежне закриття.',
 '3520':' Ноутбук #960, ж7_мороз_без_відкритого на 7c90a009: обидва raw JSON повні, finish_reason=stop; перший опис 155 токенів, лише version/text/how_to_wear, named/about_items відсутні; другий 1106 токенів і named/about_items є. Стелю або причину старого обриву не приписано; API id й фрагменти LM Studio — codex/znimky-960-pislia:аудит/живі_960/lm_studio_excerpt_3520.log.',
 '3781':' Ноутбук #960: розпакованого .json немає; gzip у зібраному HTML побайтово тотожний main 7c90a009 (fd084c89…). Справжній Chromium/Pyodide: 17 речей карток, усі 15 наявних hex = вимір жнив, 2 hex відсутні; 16 перших кадрів канонічно збігаються, для ж-10177@kasandra.ua WEBP проти PNG — окрема межа доказу. Дані payload_3781.json/page_enrichment_3781.json у codex/znimky-960-pislia:аудит/живі_960; глобального закриття нема.',
 '4622':' Ноутбук #960, ПІСЛЯ 7c90a009, ж2_спорт_коментар seed4: movement=sport і place=cafe, але occasion=sport — назване мірило нагоди не пройдено. DO=rozmova rc0 не є прийманням цього мірила; raw і знімки — codex/znimky-960-pislia:аудит/живі_960/03_ж2_спорт_коментар.',
 '5190':' Ноутбук #960 на виконуваній голові #991 81f446f10523d555aa44fa8e7d24134992b80783: 8 перевірок приладу пройшли; 81/frozen40, 97 рядків, 119 входжень, походження 119 не доведене — лише переклад. Mamay: 12/97 формально перевірених рядків, 4-й пакет відхилений; дозволений Lapa fallback: 4/97, 2-й пакет відхилений; обидва — кількість variants не відповідає relation. Без автоматичного повтору/ремонту, ≥38/40 не виміряно, runtime_applied=false. Сирі докази codex/znimky-960-pilot-5190:аудит/ноутбук_960_5190 (93bf9e7ef590e9004fe7a69cbf75615576f8528e); стан ВІДКРИТО.'}
lines=p.read_text(encoding='utf-8').splitlines(keepends=True)
found=set()
for i,line in enumerate(lines):
 key=line.split('|')[1].strip() if line.startswith('|') else ''
 if key in notes:
  lines[i]=line.rstrip('\r\n').rstrip().removesuffix('|').rstrip()+notes[key]+' |\n'; found.add(key)
assert found==set(notes)
p.write_text(''.join(lines),encoding='utf-8')
