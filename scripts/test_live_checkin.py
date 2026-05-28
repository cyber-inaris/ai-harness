#!/usr/bin/env python3
import sys
from pathlib import Path

# Добавляем пути в sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
SUBMODULE_ROOT = REPO_ROOT / "packages" / "any-auto-register"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SUBMODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUBMODULE_ROOT))

# Инициализируем БД и реестр платформ
from core.db import init_db
from core.registry import load_all
init_db()
load_all()

from core.base_platform import Account, RegisterConfig
from core.registry import get as get_platform
from providers.sms.sspanel_harness import _read_env_file

def run():
    print("=== Запуск Live Smoke Check-In ===")
    
    # Читаем секреты
    env_file = REPO_ROOT / "secrets" / "sspanel.env"
    if not env_file.exists():
        print(f"[FAIL] Файл секретов {env_file} не найден!")
        return 1
        
    env_config = _read_env_file(env_file)
    
    # Создаем конфиг провайдера
    config = RegisterConfig(
        executor_type="headed",
        extra={
            "sspanel_base_url": env_config.get("SSPANEL_BASE_URL", "http://localhost:3000"),
            "sspanel_admin_token": env_config.get("SSPANEL_ADMIN_TOKEN", ""),
            "bindings_db": env_config.get("AI_HARNESS_BINDINGS_DB", "data/provider-bindings.sqlite"),
            "provider_bindings_script": str(REPO_ROOT / "scripts" / "provider-bindings"),
            "executor": "local-mac-smoke",
        }
    )
    
    # Получаем инстанс платформы freeaisub
    try:
        platform = get_platform("freeaisub")(config)
        print("[OK] Платформа freeaisub загружена.")
    except Exception as e:
        print(f"[FAIL] Ошибка загрузки платформы: {e}")
        return 1
        
    # Создаем тестовый аккаунт. 
    # Используем telegram_id админа: 6828548683 (он точно есть в базе)
    # или фиктивный 8137700718
    target_tg_id = "6828548683"
    account = Account(
        platform="freeaisub",
        email="smoke@example.com",
        password="",
        user_id=target_tg_id,
    )
    
    print(f"Вызов checkin для Telegram ID: {target_tg_id}...")
    try:
        result = platform.execute_action(
            "checkin",
            account,
            {"provider_account_ref": "daily_checkin_smoke"}
        )
        print(f"Результат выполнения: {result}")
        if result.get("ok"):
            print("[SUCCESS] Чек-ин успешно выполнен!")
        else:
            print(f"[WARNING] Чек-ин вернул ошибку: {result.get('error')}")
    except Exception as e:
        print(f"[FAIL] Исключение при выполнении чек-ина: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(run())
