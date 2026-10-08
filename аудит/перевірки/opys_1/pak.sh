#!/bin/bash
# $1 = W_N ; кладе дані прогону з /tmp/rz/runs у цю теку
S=/tmp/rz/runs/$1; D=$(dirname "$0")/ПІСЛЯ/$1; mkdir -p $D
cp $S/знімки/картки.txt $S/знімки/текст_екранів.txt $D/
gzip -c $S/вердикти.txt > $D/вердикти.txt.gz; gzip -c $S/лог.txt > $D/лог.txt.gz
gzip -c $S/знімки/модель_виклики.json > $D/модель_виклики.json.gz
tar czf $D/відповіді.tar.gz -C $S VIDPOVIDI
cp $S/знімки/kartka_poz*_ruka1_* $S/знімки/kartka_poz*_ruka2_* $S/знімки/ekran_scenariyi_seed3.png $S/знімки/ekran_palitra_seed3.png $D/ 2>/dev/null
cp $S/знімки/ekran_znaiomstvo_3_fihura_seed3.png $D/ 2>/dev/null
echo "$1: $(du -sk $D | cut -f1) КБ"
