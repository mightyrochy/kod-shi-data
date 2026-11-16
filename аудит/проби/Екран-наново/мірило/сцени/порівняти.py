import os,re
К='/tmp/м/сцени'
for м in ['розмова','палітра','функція','повне','повне_фото']:
    д,п=[[р.rstrip('\n') for р in open(f'{К}/{м}_{ч}/звірки.txt',encoding='utf8')] if os.path.exists(f'{К}/{м}_{ч}/звірки.txt') else None for ч in ('до','після')]
    if д is None or п is None: print(м,'нема'); continue
    без=lambda с:[re.sub(r'^[✔✗]\s*','',р) for р in с]
    лише_до=[р for р in без(д) if р not in без(п)]; лише_після=[р for р in без(п) if р not in без(д)]
    print(f"{м}: ДО {sum(р[0]=='✔' for р in д)}✔/{sum(р[0]=='✗' for р in д)}✗ ПІСЛЯ {sum(р[0]=='✔' for р in п)}✔/{sum(р[0]=='✗' for р in п)}✗ · назв лише ДО {len(лише_до)}, лише ПІСЛЯ {len(лише_після)}")
    for р in лише_до[:6]: print('   − ',р[:230])
    for р in лише_після[:6]: print('   + ',р[:230])
    for р in п:
        if р[0]=='✗': print('   ✗після ',р[:230])
    for р in д:
        if р[0]=='✗': print('   ✗до ',р[:230])
