# config.py
import os

# .env 파일 자동 로드
def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

_load_env()

APP_KEY    = os.environ.get("KIS_APP_KEY", "")
APP_SECRET = os.environ.get("KIS_APP_SECRET", "")
ACCOUNT_NO = os.environ.get("KIS_ACCOUNT_NO", "")

# KIS API
BASE_URL = "https://openapi.koreainvestment.com:9443"
WS_URL   = "ws://ops.koreainvestment.com:21000"

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# SQLite
DB_PATH = "ticker_data.db"