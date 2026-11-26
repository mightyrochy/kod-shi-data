#!/bin/bash
for s in с3 с5 с8; do STOR=/tmp/n5/stor2 bash /tmp/n5/сцена.sh /tmp/n5/прогін3/$s $s; done
echo ГОТОВО > /tmp/n5/прогін3/готово.txt
