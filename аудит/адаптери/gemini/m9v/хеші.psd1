# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '68F8F34F6BBE4D47D222B77E6692D3F9ED1E9C64BB6DF64DF0F7FC567908130F'
    'wrapper_health.ps1' = '427A93D376A27296EC4601F0AD5D4E89215566B0911EF7F4F7297370ADC48D72'
    'gemini_run.ps1'     = '79F7294D836CB481404A9D9B1B3106C33DD8773705B5FF4097FE876EC9054EF4'
    'gemini_publish.ps1' = '4798D589C7369471DCBEDD005E9E692FA4FCB6D5F335254852249C90CA982CA4'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '77FE75B2BC5AC2BF20B5ECE88892B52C1A2F660BEA0DD1038C73C088D6121C9A'
    'queue_lanes.ps1'    = '35A7B51BEB2C0845784CC5C35F4CE729FCE3D3A3A3600C9CE4B5FEE9395907E2'
    'claude_run.ps1'     = 'A7D54BFFC5FD21700317FE3F2EC32FE2D1B1B844E727972F4C07045678734C3A'
}
