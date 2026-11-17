# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = 'E79271470D119CCFBE785119A19D51786C1303E6F82C9D1E0E0B5AEA56EAE6EF'
    'wrapper_health.ps1' = '97D335D46EDD60AE03859B7CD121CD0888D0D221AA6EA03FE368C2A33761B0D2'
    'gemini_run.ps1'     = 'F5CC8D2E36DECA48403E8A519F1094BA39441D27834957E97BE44C6A74A03705'
    'gemini_publish.ps1' = 'CCEFFB1417C1D54B6BF176F73F3B90E067986E20E76E7C85EE5E1174CD652A82'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '77FE75B2BC5AC2BF20B5ECE88892B52C1A2F660BEA0DD1038C73C088D6121C9A'
    'queue_lanes.ps1'    = '0C029F9F7CFAC3B0F92CE544C399036B7B2F72496EDA042C6D8D0B563E0E2C9F'
    'claude_run.ps1'     = 'E8A1FE8FABCA2CA05131CE92F86863AEAB5078E2C64CD1CD8468FF186B633B86'
}
