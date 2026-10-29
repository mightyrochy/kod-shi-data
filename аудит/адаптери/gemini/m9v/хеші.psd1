# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '08598E452CB796A4684413CA8A6EF30CD3DA277EEBF2E10D58A625D7E32E7214'
    'wrapper_health.ps1' = 'D03E371F34B3AC2881B70047563260905CD2DEB343DCD8608257495E531B90EA'
    'gemini_run.ps1'     = 'C334DCBB9049CC6A1EF23AE4B7EACA96EFE18CE5A8792268D6F83A6DB9FA12DE'
    'gemini_publish.ps1' = 'BE05093F58E1D872A6B9E511E374E1A76CB699775D35FD35DCDCA87CA100C95F'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '3DCC86B4B323292A6A2C52D335778BE23D59366699E73947DFE27BDA92EDA881'
    'claude_run.ps1'     = '6DC882061FACDD7DE3BA5BB987B36B0A018ECE5596E99500A9C6245695756DE0'
}
