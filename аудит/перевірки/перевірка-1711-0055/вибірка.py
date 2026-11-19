# Вибірка перевірки 17.11 00:55: 36 місць лічби «доля відкинутого», seed 1711, без 104 звірених (seed 16207, 1611, ймовірні 24 seed 2300) і названих.
# Запуск з кореня дерева голови: python3 -I аудит/перевірки/перевірка-1711-0055/вибірка.py .
import sys, os, random, importlib.util
os.chdir(sys.argv[1] if len(sys.argv) > 1 else '.')
сп = importlib.util.spec_from_file_location('л', 'аудит/проби/Лічба-Е2-втрата-слова-доля-відкинутого/лічба.py')
л = importlib.util.module_from_spec(сп); _а = sys.argv; sys.argv = ['x']; сп.loader.exec_module(л)
р = л.зібрати()
кл = lambda x: (x['файл'], x['рядок'], x['вираз'])
random.seed(16207); е40 = {кл(x) for x in random.sample(р, 40)}
названі = set(л.ВІДОМІ_МІСЦЯ.split())
м = lambda x: '%s:%d' % (os.path.basename(x['файл']), x['рядок'])
пул = [x for x in р if кл(x) not in е40 and м(x) not in названі]
random.seed(1611); н40 = {кл(x) for x in random.sample(пул, 40)}
# ймовірне відтворення 24 місць перевірки #4129 (seed 2300, без 40 виконавця)
пул2 = [x for x in р if кл(x) not in е40]; random.seed(2300); п24 = {м(x) for x in random.sample(пул2, 24)}
вже = е40 | н40
мій = [x for x in р if кл(x) not in вже and м(x) not in названі and м(x) not in п24
       and м(x) not in {м(y) for y in р if кл(y) in вже}]
print('пул', len(мій), file=sys.stderr)
random.seed(1711)
for i, x in enumerate(random.sample(мій, 36), 1):
    рядки = open(x['файл'], encoding='utf-8').read().split('\n')
    print('#%d %s:%d · %s · вид=%s · E=%s · ДОЛЯ=%s · %s' % (i, x['файл'], x['рядок'], x['вираз'][:100], x['вид'], x['E'][:40], x['доля'], x['пояснення'][:140]))
    for к in range(max(1, x['рядок'] - 3), min(len(рядки), x['рядок'] + 9)):
        print('    %d%s %s' % (к, '>' if к == x['рядок'] else ' ', рядки[к - 1][:180]))
