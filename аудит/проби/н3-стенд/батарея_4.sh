#!/bin/bash
# чекає першого проходу батареї 3, відкладає його в out/перший і ганяє в3_с4, в3_с5, ґ3_с5 з кадрами карток
while [ ! -f /tmp/n3/out/батарея_3.done ]; do sleep 10; done
mkdir -p /tmp/n3/out/перший && mv /tmp/n3/out/в3_с4 /tmp/n3/out/в3_с5 /tmp/n3/out/ґ3_с5 /tmp/n3/out/батарея_3.done /tmp/n3/out/перший/
/tmp/n3/батарея_3.sh
for t in в3_с4 в3_с5 ґ3_с5; do python3 /home/user/kod-shi-data/аудит/проби/н3-стенд/склеїти.py /tmp/n3/out/$t/знімки > /tmp/n3/out/$t/склеєно.txt 2>&1; done
