# Проба живого 1837 (3.2-Ж): з логів прогонів розмови друкує пору, годину в вимірах і на картці.
import re, sys, os
for т in sys.argv[1:]:
    t = open(т + '/лог.txt', encoding='utf-8').read()
    f = lambda р: (re.search(р, t) or [None, None])[1]
    print(os.path.basename(os.path.normpath(т)).ljust(24), 'пора=' + str(f(r'part_of_day="(\w+)"')), 'hour=' + str(f(r'\bhour=(\d+)')),
          'картка=' + str(f(r'"коли":"([^"]*)"')), 'година_моделі=' + str(f(r'"година_моделі":(\w+)')), 'не_взято=' + str(f(r'НЕ ВЗЯТО: (.*)'))[:90])
