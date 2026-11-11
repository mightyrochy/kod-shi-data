# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '68F8F34F6BBE4D47D222B77E6692D3F9ED1E9C64BB6DF64DF0F7FC567908130F'
    'wrapper_health.ps1' = '20C28285D5A90AA8E923A0DEA5E3311E4C14C62E13D2ED7FC9A8DE7B00DF6FC4'
    'gemini_run.ps1'     = '9713C70708D7FF0F0B7BE8AC7E4123869B0562451DCC8112D5E5CCBBDC20C56A'
    'gemini_publish.ps1' = 'DBCD6C5B954DB0F316B5F83361E2E5670D9B082734851049235296D04B9EA5D1'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '77FE75B2BC5AC2BF20B5ECE88892B52C1A2F660BEA0DD1038C73C088D6121C9A'
    'queue_lanes.ps1'    = '6760065E833415BEC9DD5785E75742E64C7B14E8E023E1F14962BA38EAC36025'
    'claude_run.ps1'     = '63FDF09489EB40EF2367F5710CE70EBC9C93A96A33B735DF0B91F96953BD9CB3'
}
