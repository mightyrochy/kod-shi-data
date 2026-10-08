import re,sys,os,collections
d=sys.argv[1]
for s in sorted(os.listdir(d)):
    p=os.path.join(d,s)
    if not os.path.isdir(p) or s.startswith('перша'): continue
    v=open(p+'/вердикти.txt',encoding='utf-8').read() if os.path.exists(p+'/вердикти.txt') else ''
    k=open(p+'/знімки/картки.txt',encoding='utf-8').read() if os.path.exists(p+'/знімки/картки.txt') else ''
    print('==',s)
    cards=re.split(r'═══ картка ',k)[1:]
    print('картки:',[c.split('═══')[0].strip() for c in cards])
    print('числа шкали у тексті:',re.findall(r'(?i)[^.\n]{0,50}(?:за шкалою|ошатність\w*\s*\d|\b\d+\s*(?:з|із|/)\s*10\b|\b\d–\d\b|рівн\w+ ошатності \d|\bбал\w* \d)[^.\n]{0,40}',k)[:6])
    rules=collections.Counter(re.findall(r'"правило":"([A-Z]-[A-Z]+-\d+)"',v)); print('правила:',dict(rules.most_common(14)))
    for pat in ['no_rain_layer_on_rainy_day','light_item_near_deep_skin','K-WEA-01','suede|замш','accent_role_lost','loud_elements_over_budget']:
        print(' ',pat,len(re.findall(pat,v)),'/ у картках',len(re.findall(pat,k)))
