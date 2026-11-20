import sys
d=sys.argv[1]
s=open(d+'/аудит/проби/рв6_стенд.js',encoding='utf8').read()
a="    await знімок('ng4_rozmova', null);\n    await знімок('ng4_kartka', '#е-випадок');"
assert s.count(a)==1
w="    await стор.evaluate(async () => { await Promise.race([ХІД_ПЛИТОК_П.обіцянка || Promise.resolve(), new Promise(r => setTimeout(r, 3000))]); });\n"
open(d+'/аудит/проби/рв6_стенд_чекає.js','w',encoding='utf8').write(s.replace(a,w+a))
