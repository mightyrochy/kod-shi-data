#!/usr/bin/env bash
set -euo pipefail
source /workspace/liusterko-tools/activate.sh
cd /workspace/review-batch-976/джерела
python3 --version
node --version
python3 -c "import чистка_каталогу as ч, feed as Ф; print('фід:', ч.забезпечити_чистим('каталог_повний.xml')); print('фікстура:', Ф.каталог_на_диску('каталог_brief.xml'))"
python3 стенд_знімок.py --дим
python3 тест_живого_шляху.py
python3 тест_протоколу.py
python3 прилади/розділи_гейтів.py
python3 audit_contracts.py
node тест_показу.js
echo 'БАТАРЕЯ ЗАВЕРШЕНА rc0'
