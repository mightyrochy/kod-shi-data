# Проба живого 1837: з теки прогону друкує факти запитів і відповідей моделі (поле потреби, політика, дози, полюс, свідомий хід).
import re, sys, glob, os, json
def розбір(ф):
    t = open(ф, encoding='utf-8').read(); i = t.find('── ВІДПОВІДЬ'); return t[:i if i > 0 else len(t)], t[i:] if i > 0 else ''
for тека in sys.argv[1:]:
    print('##', os.path.basename(os.path.normpath(тека)))
    for ф in sorted(glob.glob(тека + '/VIDPOVIDI/*ПАКЕТ*') + glob.glob(тека + '/VIDPOVIDI/*ВЕРДИКТ*')):
        п, в = розбір(ф); н = os.path.basename(ф)[5:-4]
        вим = re.search(r'"occasion_requirements":\{"profile":"(\w+)".*?"mourning":(\w+).*?"loudness_max":([\w.]+),"loudness_source":"(\w+)","near_white_veto":(\w+)', п)
        доз = {k: len(re.findall(r'"selection_doses":\{[^}]*"%s"' % k, п)) for k in ('edge', 'below_band', 'shine')}
        нам = re.search(r'"intent":"(\w+)".{0,40}?"goal"', п); дж = re.search(r'"intent_source":"(\w+)"', п)
        пул = len(re.findall(r'\["#\d+·\d+"', п))
        обр = re.findall(r'"pole":\s*"(\w+)"', в); дел = re.findall(r'"deliberate":\s*\[(.*?)\]\s*[,}\n]', в, re.S)
        з_ід = len(re.findall(r'"finding":\s*"[^"]+"', в)); з_пр = len(re.findall(r'"why":', в))
        print(f'{н[:34]:34} політика={"selection_policy" in п} потреба={вим.groups() if вим else None} дози={доз} пул={пул} намір={нам.group(1) if нам else None}/{дж.group(1) if дж else None} полюси={обр} deliberate_з_ід={з_ід} why={з_пр}')
    к = open(тека + '/знімки/картки.txt', encoding='utf-8').read() if os.path.exists(тека + '/знімки/картки.txt') else ''
    print('білих/молочних слів у картках:', len(re.findall(r'біл|молочн|айворі|кремов|кремов', к, re.I)), '· карток:', к.count('═══ картка'))
