"""Повторити наявні записи відповіді через чинні читачі без викликів моделей."""
import collections, gzip, json, re, sys
from pathlib import Path

корінь = Path(__file__).resolve().parents[4]
sys.path[:0] = [sys.argv[1], str(корінь / 'джерела')]
import мовний_шар as м

вих, числа = {}, collections.Counter()
for файл in sorted((корінь / 'аудит').glob('**/VIDPOVIDI/*.txt')):
    текст = файл.read_text(encoding='utf-8', errors='replace')
    частини = re.split(r'── ВІДПОВІДЬ \(([^\n]*)\) ──\n', текст, maxsplit=1)
    if len(частини) != 3 or 'HTTP 200' not in частини[1]:
        continue
    промпт, _, сира = частини
    нотатки = []
    об, причина = м._обʼєкт(сира, нотатки)
    запис = dict(прочитано=об is not None, причина=причина, нотатки=нотатки)
    числа['відповідей'] += 1
    числа['прочитано'] += об is not None
    if '\nТЕКСТИ:\n' in промпт:
        try:
            дані, _ = json.JSONDecoder().raw_decode(промпт.rsplit('\nТЕКСТИ:\n', 1)[1].lstrip())
        except ValueError:
            дані = None
        if isinstance(дані, dict):
            розмітка = [dict(н=н, ключ=str(н), текст=т.get('текст', '') if isinstance(т, dict) else т)
                        for н, т in дані.items()]
        else:
            розмітка = [dict(р, ключ=str(р['н'])) for р in (дані or []) if isinstance(р, dict) and 'н' in р]
        if розмітка:
            результат = м.прийняти(розмітка, сира)
            запис['переклад'] = результат
            числа['перекладів'] += 1
            числа['текстів'] += len(розмітка)
            числа['прийнятих_текстів'] += len(розмітка) - len(результат['без_відповіді'])
    вих[str(файл.relative_to(корінь))] = запис
Path(sys.argv[2]).write_bytes(gzip.compress(json.dumps(dict(числа=числа, записи=вих), ensure_ascii=False).encode('utf-8'), mtime=0))
print(json.dumps(числа, ensure_ascii=False))
