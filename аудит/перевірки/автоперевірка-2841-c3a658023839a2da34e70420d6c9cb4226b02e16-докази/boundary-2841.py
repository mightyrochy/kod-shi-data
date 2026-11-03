from decimal import Decimal as D
import sys, os, json, pathlib
sys.path.insert(0,os.path.join(os.environ['TEMP'],'pr-2841','джерела'))
from body_shape import визначення
bad=[]
for waist in range(500,1401):
    w=D(waist)/10
    hh=w*D('1.193')
    b=w+D('15.24'); h=w+D('25.4')
    x=визначення(b,w,h,hh)
    if x['категорія'] != 'Spoon': bad.append((str(b),str(w),str(h),str(hh),x))
print('Межа high hip/waist = 1.193: перевірено',901,'розходжень',len(bad))
print(*bad[:8],sep='\n')
bad2=[]
for waist in range(500,1401):
    w=D(waist)/10
    b=w+D('22.86'); h=b
    x=визначення(b,w,h)
    if x['категорія'] != 'Hourglass': bad2.append((str(b),str(w),str(h),x))
print('Межа bust-waist = 9 дюймів: перевірено',901,'розходжень',len(bad2))
print(*bad2[:8],sep='\n')
(pathlib.Path(os.environ['TEMP'])/'boundary-2841.json').write_text(json.dumps({'high_hip':bad,'bust_waist':bad2},ensure_ascii=False,indent=2),encoding='utf8')
