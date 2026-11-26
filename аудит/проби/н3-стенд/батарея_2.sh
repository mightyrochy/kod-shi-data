#!/bin/bash
# усе на 256406b1 (stor_2564), типовий режим вікна; прогін із «rc=» у час.txt пропускається (перезапуск після зупинки)
export STOR=/tmp/n3/stor_2564
зроблено() { grep -q '^rc=' /tmp/n3/out/$1/час.txt 2>/dev/null; }
зроблено г_турнір   || MODEL_VYBIR=turnir  /tmp/n3/сцена.sh /tmp/n3/out/г_турнір с5
зроблено г_оцінка   || MODEL_VYBIR=otsinka /tmp/n3/сцена.sh /tmp/n3/out/г_оцінка с5
зроблено г_короткий || ZAPYS=korotkyi      /tmp/n3/сцена.sh /tmp/n3/out/г_короткий с5
зроблено г_частин2  || CHASTYN=2           /tmp/n3/сцена.sh /tmp/n3/out/г_частин2 с5
зроблено г_частин3  || CHASTYN=3           /tmp/n3/сцена.sh /tmp/n3/out/г_частин3 с5
зроблено в2_с4      ||                     /tmp/n3/сцена.sh /tmp/n3/out/в2_с4 с4
зроблено в2_с5      ||                     /tmp/n3/сцена.sh /tmp/n3/out/в2_с5 с5
зроблено ґ2_с5      || MOVCHYT=4           /tmp/n3/сцена.sh /tmp/n3/out/ґ2_с5 с5
echo ГОТОВО > /tmp/n3/out/батарея_2.done
