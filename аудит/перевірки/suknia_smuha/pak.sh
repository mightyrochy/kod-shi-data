#!/bin/bash
# $1 = W_N, $2 = тека прогонів (/tmp/rz/runs чи /tmp/rz/runs_do), $3 = ДО|ПІСЛЯ — кладе дані прогону сюди
S=$2/$1; D=$(dirname "$0")/$3/$1; mkdir -p $D
cp $S/знімки/картки.txt $S/знімки/текст_екранів.txt $D/
gzip -c $S/вердикти.txt > $D/вердикти.txt.gz; gzip -c $S/лог.txt > $D/лог.txt.gz
gzip -c $S/знімки/модель_виклики.json > $D/модель_виклики.json.gz
tar czf $D/відповіді.tar.gz -C $S VIDPOVIDI
cp $S/знімки/kartka_poz*_ruka1_* $S/знімки/kartka_poz*_ruka2_* $D/ 2>/dev/null
echo "$3/$1: $(du -sk $D | cut -f1) КБ"
