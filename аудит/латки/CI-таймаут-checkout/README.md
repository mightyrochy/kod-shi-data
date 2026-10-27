# Латка: збільшення timeout-minutes для завдань з actions/checkout

- **Базовий коміт (SHA бази):** `fec370a88ecbb3521e9cdbc49bfdd919338c3229`
- **Наряд:** `аудит/наряди/CI-таймаут-checkout.md`
- **Рядок дошки:** 10354

## Файли та рядки «було → стало»

1. `.github/workflows/zbirka.yml`
   - Завдання: `zminy` («що змінилось у push чи PR»)
   - Рядок 29:
     - було: `timeout-minutes: 3`
     - стало: `timeout-minutes: 10`

2. `.github/workflows/zhnyva.yml`
   - Завдання: `schedule-readiness`
   - Рядок 46:
     - було: `timeout-minutes: 2`
     - стало: `timeout-minutes: 10`

Файли обгортки з `аудит/адаптери/gemini/m9v/хеші.psd1` не змінювалися.

## Перевірка та застосування латки

Перевірка на базовому коміті:
```bash
git apply --check аудит/латки/CI-таймаут-checkout/01-timeout.patch
```

Застосування латки:
```bash
git apply --index аудит/латки/CI-таймаут-checkout/01-timeout.patch
```

## Результати перевірки
- `git apply --check аудит/латки/CI-таймаут-checkout/01-timeout.patch` — чисто (код 0).
- `python джерела/прилади/згорнути_дошку.py --лише-перевірити` — 0 помилок.
- Захищені файли `.github/` та `аудит/адаптери/gemini/` у гілці не змінювалися (захист М.9-Г).
