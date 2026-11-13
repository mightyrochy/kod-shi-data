# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '457BB1DD87DCBF82027C42BD872E8F4A2B238E37090142756AEB02F61976BD94'
    'wrapper_health.ps1' = 'BC0090E6D5A8F7F5FE15B2A7F8A0D21247485302084C723FFC6692FE68C26E63'
    'gemini_run.ps1'     = '54BF8330990979745D048BB49FD8FEA001179DF4B7B3E9EEDE79A3DA9EA59432'
    'gemini_publish.ps1' = 'D79B012AE72BD2C66DA958CC963C8317D1CA30ADA6D6FA4DA4907BA7FF7B8959'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '77FE75B2BC5AC2BF20B5ECE88892B52C1A2F660BEA0DD1038C73C088D6121C9A'
    'queue_lanes.ps1'    = '34A12C55A7C548DD3122B28C7FCA7CD1D60D5D514BE5EFEAEE5FD3E1B4F0700E'
    'claude_run.ps1'     = '0B96CB6F866B9D6778845B3A2B9209668CD110220B44AE6328CCB1B1BBBBCEC4'
}
