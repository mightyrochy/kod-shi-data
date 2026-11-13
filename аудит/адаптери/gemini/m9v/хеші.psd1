# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '457BB1DD87DCBF82027C42BD872E8F4A2B238E37090142756AEB02F61976BD94'
    'wrapper_health.ps1' = '4C3CF324647C66517B9A4018EEF3B0256C81822197C3EF015230DED8CF12D9E6'
    'gemini_run.ps1'     = 'F68C2AE0D96763CE3EBD3F4F98F67F873A83E4780E34709136865E8413CE1F38'
    'gemini_publish.ps1' = 'DB8C1C2D57BC02674B30D9284E87174FF6F635924FE6E1AF9AB1256486C8FE1F'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '77FE75B2BC5AC2BF20B5ECE88892B52C1A2F660BEA0DD1038C73C088D6121C9A'
    'queue_lanes.ps1'    = '8B2D7E8BC66B6FDF3B69F847D479D0A6B725D689A1BEACE76A8DAFBB549C1CE6'
    'claude_run.ps1'     = '94FE9054A1D743EBB6132ADFE8F511A8F0C294852C091EA39EA80F2779294BCC'
}
