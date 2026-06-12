# collector/kis_auth.py
import requests
import json
import os
from datetime import datetime, timedelta
from config import APP_KEY, APP_SECRET, BASE_URL

TOKEN_CACHE_FILE = ".token_cache.json"


def load_cached_token():
    """저장된 토큰 로드 (당일 유효한 경우만)"""
    if not os.path.exists(TOKEN_CACHE_FILE):
        return None
    try:
        with open(TOKEN_CACHE_FILE, "r") as f:
            cache = json.load(f)
        # 만료 시간 확인
        expires_at = datetime.fromisoformat(cache["expires_at"])
        if datetime.now() < expires_at - timedelta(minutes=10):
            print(f"[Auth] 캐시된 토큰 사용 (만료: {expires_at.strftime('%H:%M')})")
            return cache["access_token"]
    except Exception as e:
        print(f"[Auth] 캐시 로드 실패: {e}")
    return None


def save_token_cache(token, expires_in_seconds):
    """토큰 캐시 저장"""
    expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
    with open(TOKEN_CACHE_FILE, "w") as f:
        json.dump({"access_token": token, "expires_at": expires_at.isoformat()}, f)


def get_access_token():
    """액세스 토큰 발급 (캐시 우선)"""
    cached = load_cached_token()
    if cached:
        return cached

    print("[Auth] 새 토큰 발급 중...")
    url = f"{BASE_URL}/oauth2/tokenP"
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }
    resp = requests.post(url, json=body)
    resp.raise_for_status()
    data = resp.json()

    token = data["access_token"]
    expires_in = int(data.get("expires_in", 86400))
    save_token_cache(token, expires_in)
    print(f"[Auth] 토큰 발급 완료")
    return token


def get_approval_key(access_token):
    """WebSocket 접속키 발급"""
    print("[Auth] WebSocket 접속키 발급 중...")
    url = f"{BASE_URL}/oauth2/Approval"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET,
    }
    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()
    data = resp.json()
    approval_key = data.get("approval_key")
    print(f"[Auth] 접속키 발급 완료")
    return approval_key
