# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '2C44BD77A2180F47054212220BCD473DEC088B7EACE2646B3B40047752C8785'
    'wrapper_health.ps1' = 'BC7CDCBD744E360446B3D3721D0F70676A98D86B5770A3E3CB3713F9E770CEAB'
    'gemini_run.ps1'     = 'A70699CDD03F8F7C8DD68CE4233131D6D38B7B4B9D91AD881AB52F09E6CE96A4'
    'gemini_publish.ps1' = '651718F8227770B4D9BADF001719DDCA60604DEE8BFEB3C8D19B6FC3D2D32DF8'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = 'BA0B8D3E6A68B2E6D15A01C180792FC99CB32F5E19517EE90130A091E4D652E1'
    'claude_run.ps1'     = 'BF16025FE21FE81B5D0BD547C73D82A6A5F0C55ED66BF95FCB4F1727E18996B8'
}
