#!/bin/bash
# (в) ще раз — знімки «Сліпого перегляду» (усі чотири картки), після батареї 2
export STOR=/tmp/n3/stor_2564
зроблено() { grep -q '^rc=' /tmp/n3/out/$1/час.txt 2>/dev/null; }
зроблено в3_с4 || /tmp/n3/сцена.sh /tmp/n3/out/в3_с4 с4
зроблено в3_с5 || /tmp/n3/сцена.sh /tmp/n3/out/в3_с5 с5
зроблено ґ3_с5 || MOVCHYT=4 /tmp/n3/сцена.sh /tmp/n3/out/ґ3_с5 с5
echo ГОТОВО > /tmp/n3/out/батарея_3.done
