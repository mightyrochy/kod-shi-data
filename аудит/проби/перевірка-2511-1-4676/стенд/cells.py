import json,sys
for path in sys.argv[1:]:
    p=json.load(open(path))
    print('##',path.split('/')[-3:-1] if 'evidence' in path else path.split('/')[-2], 'passed=',p['check']['points'].get('passed'), '| failed=',p['check']['points'].get('failed'), '| keys=',list(p['check']['points'].keys()))
