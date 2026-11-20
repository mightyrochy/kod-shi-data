#!/bin/bash
cd /tmp/вимір
python3 скрипти/повтор.py дані/міст_до.jsonl claude-sonnet-5-5 low дані/sonnet_low.jsonl 6 > дані/sonnet.out 2>&1 &
python3 скрипти/повтор.py дані/міст_до.jsonl claude-haiku-5-5 low дані/haiku_low.jsonl 6 > дані/haiku.out 2>&1 &
wait
cat дані/sonnet.out дані/haiku.out
