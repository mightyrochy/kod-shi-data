# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '2C44BD77A2180F47054212220BCD473DEC088B7EACE2646B3B40047752C8785'
    'wrapper_health.ps1' = '3241ABE6F0C6AFB8DF67F50194C8777636B5BCD57983E4CACBBDC1DD20D67C76'
    'gemini_run.ps1'     = 'F445057CE3C80E76C97BF0009FCBA2844CD26A102CB79EA7BD9185C50953EF45'
    'gemini_publish.ps1' = '8058AE4919C1681192F2E45623CF6BC041F75D24DDBAB384978120E6E8213C50'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '638030C3FD09FE9E11DE2D3B024FD5354ACA681D1307D3993A77A50139467AD7'
    'claude_run.ps1'     = 'BFCB4079BEC682C12ABDB89EB75B8536B9102C263EE7274CE5C5F6E36A6CBA24'
}
