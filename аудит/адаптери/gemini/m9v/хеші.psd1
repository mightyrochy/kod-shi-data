# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '83BD346D207CDA9D053A33F6FDD2844A2AA0CDB9B2EC0C877995FE5B9B7600F4'
    'wrapper_health.ps1' = 'BC0090E6D5A8F7F5FE15B2A7F8A0D21247485302084C723FFC6692FE68C26E63'
    'gemini_run.ps1'     = 'BBDB7461AE5309FD5141E20821C109D4203E724A14666F93497044E8BBCCF93D'
    'gemini_publish.ps1' = '47C38347D3C94227E2DF141E6EB18DFB403D12D64BC43E3325952FA6C51BE801'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '77FE75B2BC5AC2BF20B5ECE88892B52C1A2F660BEA0DD1038C73C088D6121C9A'
    'queue_lanes.ps1'    = 'B3AAB73B83F2387DFC363FA5BD9991D887F57AB475D0DA9E4F9893AC6AEF16BC'
    'claude_run.ps1'     = 'AFDC7ABE2B1F1F5BF3818AFFBF5D59B0BE79704AF00AEA85E5DFE4BBC560C50F'
}
