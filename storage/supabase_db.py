# storage/supabase_db.py
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime

_client: Client = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[Supabase] 연결 완료")
    return _client


def insert_ticks_batch(ticks: list):
    """틱 여러 건 Supabase에 저장"""
    if not ticks:
        return
    rows = [
        {
            "code":       t["code"],
            "timestamp":  t["timestamp"].isoformat(),
            "price":      t["price"],
            "open":       t["open"],
            "high":       t["high"],
            "low":        t["low"],
            "volume":     t["volume"],
            "change_pct": t["change_pct"],
            "prev_close": t["prev_close"],
        }
        for t in ticks
    ]
    get_client().table("ticks").insert(rows).execute()


def upsert_candle_1m(code: str, ts: datetime, o: int, h: int, l: int, c: int, v: int):
    """1분봉 upsert"""
    get_client().table("candles_1m").upsert(
        {
            "code":   code,
            "ts":     ts.isoformat(),
            "open":   o,
            "high":   h,
            "low":    l,
            "close":  c,
            "volume": v,
        },
        on_conflict="code,ts"
    ).execute()


def get_tick_count(code: str = None) -> int:
    """저장된 틱 수 확인"""
    try:
        client = get_client()
        if code:
            res = client.table("ticks").select("id", count="estimated").eq("code", code).execute()
        else:
            res = client.table("ticks").select("id", count="estimated").execute()
        return res.count or 0
    except Exception as e:
        print(f"[Supabase] 틱 카운트 조회 실패 (무시하고 진행): {e}")
        return -1