#!/bin/bash
# (в) і (ґ) ще раз — знімки чотирьох карток зі «Сліпого перегляду» (стенд гортає пейджером у режимі blind)
export STOR=/tmp/n3/stor
зроблено() { grep -q '^rc=' /tmp/n3/out/$1/час.txt 2>/dev/null; }
зроблено в3_с4 || /tmp/n3/сцена.sh /tmp/n3/out/в3_с4 с4
зроблено в3_с5 || /tmp/n3/сцена.sh /tmp/n3/out/в3_с5 с5
зроблено ґ3_с5 || MOVCHYT=4 /tmp/n3/сцена.sh /tmp/n3/out/ґ3_с5 с5
echo ГОТОВО > /tmp/n3/out/батарея_3.done
