# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_health.ps1' = 'FCE45448539D53A6B5718319842FC845DA870F39453A6B716C7AF8A2DB65B88E'
    'gemini_run.ps1'     = '48C66A30A0967CE9A8AA60B9ECF102479D6B6C2672B2978F1C0D8A1D6C8100AD'
    'gemini_publish.ps1' = '735FB7390DD948FBA97B5AA8DE16416C4ACBB99CB92C33A4A9B0AD1E62EF74B5'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '3550085176F339BA00B1D1C28391AC585B0959128335D193601734261D00085B'
    'queue_lanes.ps1'    = '12ADC3824C6F126EE91F953B5FA65A96C015FC3D99C39FF9914A167DA2F92DD9'
    'claude_run.ps1'     = 'A17354251B4CD11A6D3A77254615798486CE9BEDBA02B3960D0DE9577E19BE4C'
}
