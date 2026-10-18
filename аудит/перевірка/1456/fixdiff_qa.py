import asyncio, importlib.util, json, pathlib, subprocess
R = pathlib.Path('/workspace/work/qa-1456')
S = R/'джерела/проби/кеш_входу_11б.py'
сп = importlib.util.spec_from_file_location('проба_11б', S); П = importlib.util.module_from_spec(сп); сп.loader.exec_module(П)
async def перевірити_помилку(результат):
    виклики = []
    стара = П.ЗМ.прогнати
    async def міст(текст):
        виклики.append(json.loads(текст))
        return json.dumps({'формат':1})+'\n'+json.dumps(результат)+'\n', {}
    П.ЗМ.прогнати = міст
    текст = '\n'.join(json.dumps({'ім':'запити','вхід':json.dumps({'каталог':'старий.xml'})}) for _ in range(2))
    try:
        await П.відтворити(текст, '/явний/каталог.xml')
        raise AssertionError('помилка відтворення прийнята')
    except RuntimeError:
        assert len(виклики)==1, 'виконано наступний запис після помилки'
        assert json.loads(виклики[0]['вхід'])['каталог']=='/явний/каталог.xml'
    finally:
        П.ЗМ.прогнати=стара
for результат in ({'помилка':'FileNotFoundError'}, {'результат':{'помилка':'помилка каталогу'}}):
    asyncio.run(перевірити_помилку(результат))
print('PASS: обидві форми помилок зупиняють запис до наступного; явний каталог передано')
try:
    П.звірити()
    raise AssertionError('порожнє покриття прийняте')
except RuntimeError as e:
    assert 'бракує' in str(e)
print('PASS: порожнє покриття відхилене')
for args in ([], ['--каталог','/неіснуючий/каталог.xml']):
    п=subprocess.run(['python3', str(S), *args],capture_output=True,text=True)
    assert п.returncode!=0
    print('PASS: CLI', repr(args), 'rc',п.returncode)
база=subprocess.check_output(['git','show','7082932c3e9589b130fe5e70ff5367c4428a3af6:аудит/БЕКЛОГ.md'],cwd=R)
assert база == (R/'аудит/БЕКЛОГ.md').read_bytes()
фрагмент=(R/'аудит/дошка/krok-1.1-b.md').read_text()
assert 'стан 8320: **ЗАКРИТО #1456**' in фрагмент
assert all('| %d |'%n in фрагмент for n in (8390,8391,7600,7601))
print('PASS: спільна дошка тотожна ownbase, 8320/8390/8391/7600/7601 у фрагменті')
