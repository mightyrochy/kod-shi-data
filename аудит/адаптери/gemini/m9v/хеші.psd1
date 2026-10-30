# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '0A254E6884FA61DF9B4FC709EBC3AD05AE8CCD1A25A1F09D87D97C1A43A57184'
    'wrapper_health.ps1' = 'B3E2C44C4F342A915B814854A7D7619EDE2E019B48DC4A50CF4C9DB304C2E531'
    'gemini_run.ps1'     = 'ED151D76BA6658EA230A0442252F0D7D05C2F6D723461C383D8E10016206E8FE'
    'gemini_publish.ps1' = '3C97912267FFEF59F72A96D44D63B40A52BDA32174FF36E8F1438B076FFC225B'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '02868BB9FFE5320952634BA7A3E3D7B2F34D0F4D11699844F7429DFFDC66B909'
    'claude_run.ps1'     = 'C2E5B91E13B5B2DAC132716FF02769B691D55635BE913A31FD8A4A5B1D5575FE'
}
