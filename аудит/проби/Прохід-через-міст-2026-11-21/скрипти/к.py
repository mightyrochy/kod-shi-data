"""Одна команда драйверу: python3 -I к.py <тека> '<json>' [скільки знаків тексту]. Чекає відповіді, друкує екран коротко."""
import json, os, sys, time
тека, к = sys.argv[1], json.loads(sys.argv[2]); межа = int(sys.argv[3]) if len(sys.argv) > 3 else 1500
черга = os.path.join(тека, 'черга'); n = 0
while os.path.exists(os.path.join(черга, f'{n:04d}.json')): n += 1
with open(os.path.join(черга, f'{n:04d}.json.tmp'), 'w') as ф: json.dump(к, ф, ensure_ascii=False)
os.rename(os.path.join(черга, f'{n:04d}.json.tmp'), os.path.join(черга, f'{n:04d}.json'))
відп = os.path.join(черга, f'{n:04d}.відп.json')
while not os.path.exists(відп):
    if os.path.exists(os.path.join(тека, 'збій.txt')): print('ЗБІЙ', open(os.path.join(тека, 'збій.txt')).read()[:500]); sys.exit(1)
    time.sleep(1)
time.sleep(0.3); в = json.load(open(відп))
print(f"#{n:04d} {к.get('дія')} помилка={в.get('помилка')} знайдено={в.get('знайдено')} чекав={в.get('чекав_с')} справжніх={в.get('справжніх')}")
print('ТЕКСТ:', (в.get('текст') or '').replace('\n', ' / ')[:межа])
print('ЕЛЕМ:', ' | '.join((в.get('елем') or [])[:60])[:межа])
