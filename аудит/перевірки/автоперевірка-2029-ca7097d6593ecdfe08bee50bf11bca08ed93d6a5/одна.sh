#!/bin/bash
# Одна проба: код виходу, секунди, останній рядок.
p=$1; R=C:/Users/Admin/claude-run/w/rev2029; n=$(basename $p .py); s=$(date +%s)
cd $R/head/джерела && timeout 1500 python -X utf8 $p > $R/dok/out/$n.txt 2>&1; c=$?
echo "$c $(( $(date +%s)-s ))s $n | $(tail -1 $R/dok/out/$n.txt | cut -c1-140)"
