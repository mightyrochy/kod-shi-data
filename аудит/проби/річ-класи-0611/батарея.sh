# Батарея кроку «класи в рисі»: спільна + сім'я ознак + проби, що читають класи риси.
cd /home/user/kod-shi-data/джерела
: > /tmp/rz/батарея.txt
for k in "python3 стенд_знімок.py --дим" "python3 тест_живого_шляху.py" "python3 тест_протоколу.py" "python3 прилади/розділи_гейтів.py" "python3 audit_contracts.py" "env NODE_PATH=node_modules node тест_показу.js" $(ls проби/ознаки_*.py проби/помада*.py проби/bas_ochi_81.py проби/col_R-COL-16.py проби/rang_різним_людям.py проби/осн1_ранг_суддя.py проби/поділ_colorspace_ast.py проби/pal_K-PAL-0[1-4].py 2>/dev/null | sed 's/^/python3_/'); do
  k=${k/python3_/python3 }; s=$(date +%s); timeout 1500 $k > /tmp/rz/бат.log 2>&1; c=$?
  echo "$c $(( $(date +%s)-s ))с $k :: $(tail -1 /tmp/rz/бат.log | cut -c1-160)" >> /tmp/rz/батарея.txt
  [ $c -ne 0 ] && cp /tmp/rz/бат.log "/tmp/rz/впало-$(basename "${k##* }").log"
done
echo КІНЕЦЬ >> /tmp/rz/батарея.txt
