# migrate.py
# SQLite ticker_data.db → Supabase 마이그레이션
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from storage.supabase_db import get_client
from config import SUPABASE_URL, SUPABASE_KEY

DB_PATH = "ticker_data.db"
BATCH_SIZE = 100


def migrate_ticks(conn):
    cursor = conn.execute("SELECT * FROM ticks ORDER BY id")
    rows = cursor.fetchall()
    total = len(rows)
    print(f"[틱] 총 {total:,}건 마이그레이션 시작")

    client = get_client()
    for i in range(0, total, BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        data = [
            {
                "code":       r["code"],
                "timestamp":  r["timestamp"],
                "price":      r["price"],
                "open":       r["open"],
                "high":       r["high"],
                "low":        r["low"],
                "volume":     r["volume"],
                "change_pct": r["change_pct"],
                "prev_close": r["prev_close"],
            }
            for r in batch
        ]
        client.table("ticks").insert(data).execute()
        print(f"[틱] {min(i + BATCH_SIZE, total):,}/{total:,}건 완료")

    print(f"[틱] 마이그레이션 완료")


def migrate_candles(conn):
    cursor = conn.execute("SELECT * FROM candles_1m ORDER BY id")
    rows = cursor.fetchall()
    total = len(rows)
    print(f"\n[분봉] 총 {total:,}건 마이그레이션 시작")

    client = get_client()
    for i in range(0, total, BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        data = [
            {
                "code":   r["code"],
                "ts":     r["ts"],
                "open":   r["open"],
                "high":   r["high"],
                "low":    r["low"],
                "close":  r["close"],
                "volume": r["volume"],
            }
            for r in batch
        ]
        client.table("candles_1m").upsert(data, on_conflict="code,ts").execute()
        print(f"[분봉] {min(i + BATCH_SIZE, total):,}/{total:,}건 완료")

    print(f"[분봉] 마이그레이션 완료")


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"[오류] {DB_PATH} 파일을 찾을 수 없어요.")
        print("ticker_data.db를 이 스크립트와 같은 폴더에 넣어주세요.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("=" * 50)
    print("  SQLite → Supabase 마이그레이션")
    print("=" * 50)

    migrate_ticks(conn)
    migrate_candles(conn)
    conn.close()

    print("\n[완료] 마이그레이션 성공!")