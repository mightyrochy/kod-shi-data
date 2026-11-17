# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '9FD96D439E62E7899D3C4891ECC3534A85F88AEB87D0D535B78795E53AF3596A'
    'wrapper_health.ps1' = '29AC20272066B82B3712B48D179067D60869AB6C6D604433B9422387222871B3'
    'gemini_run.ps1'     = '5730BB1031D2FE054C9C3937ABCD01E73BE8EDF74C0E178D564A87A8E9720A9C'
    'gemini_publish.ps1' = 'C30497DACC388BC5FA692CC30B13EF20E4E2EE5858A7E00ABEE986F59BA56D59'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '77FE75B2BC5AC2BF20B5ECE88892B52C1A2F660BEA0DD1038C73C088D6121C9A'
    'queue_lanes.ps1'    = '0C029F9F7CFAC3B0F92CE544C399036B7B2F72496EDA042C6D8D0B563E0E2C9F'
    'claude_run.ps1'     = 'AAB60046A6DC08140FC438960C5BA07218737142E119AB01D4D61D5265B914D1'
}
