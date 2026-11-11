# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '83BD346D207CDA9D053A33F6FDD2844A2AA0CDB9B2EC0C877995FE5B9B7600F4'
    'wrapper_health.ps1' = 'BC0090E6D5A8F7F5FE15B2A7F8A0D21247485302084C723FFC6692FE68C26E63'
    'gemini_run.ps1'     = '1469E1838FF2296583ECDD4B8FB60DC08CEBEF4618603EBFD78FCE771C29D780'
    'gemini_publish.ps1' = 'DBCD6C5B954DB0F316B5F83361E2E5670D9B082734851049235296D04B9EA5D1'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '77FE75B2BC5AC2BF20B5ECE88892B52C1A2F660BEA0DD1038C73C088D6121C9A'
    'queue_lanes.ps1'    = 'D56E9AFEEF1E682B46C32636550B8DB2CC613C65269DD17BE823DF1BB7A9E47D'
    'claude_run.ps1'     = '63FDF09489EB40EF2367F5710CE70EBC9C93A96A33B735DF0B91F96953BD9CB3'
}
