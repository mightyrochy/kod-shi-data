# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '9C83D2F6D3C215F78C0CA107B87D3533779B3D099D18A72078BBC890BBCFEE65'
    'wrapper_health.ps1' = '1427DF6C7CF1A6D5EDBC66072B58ED085A34C15D3DC7463750F93FB06F5FA810'
    'gemini_run.ps1'     = 'F5CC8D2E36DECA48403E8A519F1094BA39441D27834957E97BE44C6A74A03705'
    'gemini_publish.ps1' = 'E23261312EB38F37CE6B359F0AEC8E852777169CB375277C9FAC8DDB80B405E2'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '77FE75B2BC5AC2BF20B5ECE88892B52C1A2F660BEA0DD1038C73C088D6121C9A'
    'queue_lanes.ps1'    = '43886D9BA13D20EE542D23C4298253033A66DC7FC713637C70E141F2BE629769'
    'claude_run.ps1'     = '3A8593A32DE00A2B2CFCE5DBF1E8B58F7428BB989871793D56B6E737A5BC2B16'
}
