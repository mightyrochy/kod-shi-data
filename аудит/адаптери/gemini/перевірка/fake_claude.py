#!/usr/bin/env python3
import json, os, sys
msg = sys.stdin.read()
with open(os.environ['FAKE_CLAUDE_LOG'], 'a') as f:
    f.write(json.dumps({'argv': sys.argv[1:], 'stdin': msg}, ensure_ascii=False) + '\n')
print(json.dumps({'ok': os.environ.get('FAKE_CLAUDE_FAIL') != '1', 'session_id': sys.argv[sys.argv.index('--cloud') + 1]}))
