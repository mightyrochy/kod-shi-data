#!/bin/bash
# витягує теки прогонів з чотирьох гілок у /tmp/a6/runs/<W_N> (+ розпаковує відповіді)
cd /home/user/kod-shi-data
mkdir -p /tmp/a6/runs /tmp/a6/br
for b in rozbir-osnova rozbir-prohony-2 rozbir-prohony-3 rozbir-prohony-4; do
  rm -rf /tmp/a6/br/$b; mkdir -p /tmp/a6/br/$b
  git archive origin/claude/$b аудит/перевірки/rozbir_0210 | tar x -C /tmp/a6/br/$b
  for d in /tmp/a6/br/$b/аудит/перевірки/rozbir_0210/ж*_*/; do
    n=$(basename $d)
    [ -f $d/лог.txt.gz ] || continue
    if [ -d /tmp/a6/runs/$n ]; then
      cmp -s $d/лог.txt.gz /tmp/a6/runs/$n/лог.txt.gz || echo "РІЗНІ: $n у $b ($(cat /tmp/a6/runs/$n/.src))"
      continue
    fi
    cp -r $d /tmp/a6/runs/$n; echo $b > /tmp/a6/runs/$n/.src
    mkdir -p /tmp/a6/runs/$n/x && tar xzf /tmp/a6/runs/$n/відповіді.tar.gz -C /tmp/a6/runs/$n/x
  done
  cp /tmp/a6/br/$b/аудит/перевірки/rozbir_0210/прогони_*.txt /tmp/a6/runs/ 2>/dev/null
done
ls -d /tmp/a6/runs/ж*_* | wc -l
