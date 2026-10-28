"""Незалежний замір кінцевих кольорів справжнього моста PR 2051."""
import importlib.util, itertools, json, pathlib, subprocess, sys
ROOT=pathlib.Path(sys.argv[1]); OUT=pathlib.Path(sys.argv[2])
sys.path.insert(0,str(ROOT/'джерела'))
import bridge as M, міст_основи as MO, brief as B, palettes as P, colorspace as CS
import колір_річ as KR, колір_відношення as KV
packets=[]; original=MO.пакет
def save(*a,**kw):
    p=original(*a,**kw); packets.append(p); return p
MO.пакет=save
profiles=[('#f1d0b5','#3b2417','#16110e'),('#bb8561','#56816b','#70503b'),('#5a3a2a','#5c8499','#d4b887')]
records=[]
for skin,eyes,hair in profiles:
    for saturation in (None,'приглушені','насичені'):
        inp=dict(шкіра=[skin],очі=eyes,волосся=[hair],обхвати={},зріст=168,вибір_кольору=dict(насиченість=saturation))
        screen=json.loads(M.палітри(inp)); packet=packets[-1]
        brief=B.бриф(packet,гілка=None)['текст']
        for branch in screen['гілки']:
            sp=next(g['спец'] for g in packet['палітри']['розвилка'] if g['схема']==branch['схема'])
            scheme=(sp.get('мисматч') or {}).get('базова',branch['схема'])
            method={'нейтрали+акцент':'нейтраль_плюс_акцент','тональна':'тон_у_тон'}.get(scheme,scheme)
            combo=next(c for c in sp['палітра_практична']['поєднання'] if c['прийом']==method)
            colors=[dict(lab=CS.hx(c['hex']),**dict(zip(('L','C','h'),CS.lch(CS.hx(c['hex']))))) for c in combo['кольори']]
            ok,why=P.набір_законний(colors)
            chrom=[c for c,raw in zip(colors,combo['кольори']) if raw['роль']=='колір']
            repeated=[KR.та_сама_сім_я(a,b) for a,b in itertools.combinations(chrom,2)]
            relationship={'аналогова':'analogous','приглушена_комплементарна':'complementary','тріада':'triadic'}.get(scheme)
            strengths=[KV.сила(KR.запис_кольору(a),KR.запис_кольору(b),relationship)[0] for a,b in itertools.combinations(chrom,2)] if relationship else []
            records.append(dict(профіль=[skin,eyes,hair],гама=saturation,схема=branch['схема'],чип=branch['зразки'],джерело=[c['hex'] for c in combo['кольори']],зразки_слотів={r['слот']:r['зразок'] for r in branch['ролі']},слоти_в_брифі=all(r['зразок'] in brief for r in branch['ролі'] if r['слот'] in ('верх','низ','взуття','сумка')),LC=[[round(c['L'],2),round(c['C'],2)] for c in colors],законне=ok,причина=why,сім_ї_попарно=repeated,сили_відношення=strengths))
MO.пакет=original
(OUT/'кінцеві-кольори.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
summary={}
for saturation in (None,'приглушені','насичені'):
    rs=[r for r in records if r['гама']==saturation]
    summary[str(saturation)]=dict(гілок=len(rs),чип_дорівнює_джерелу=sum(r['чип']==r['джерело'] for r in rs),слоти_в_брифі=sum(r['слоти_в_брифі'] for r in rs),незаконних=sum(not r['законне'] for r in rs),повторів=sum('так' in r['сім_ї_попарно'] for r in rs if r['схема']=='аналогова'),слабких_відношень=sum(any(s<.5 for s in r['сили_відношення']) for r in rs))
print(json.dumps(summary,ensure_ascii=False,indent=2))
print('НЕЗАКОННІ:')
for r in records:
    if not r['законне']:
        print(json.dumps({k:r[k] for k in ('профіль','гама','схема','чип','LC','причина')},ensure_ascii=False))