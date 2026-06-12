# storage/db.py
import sqlite3
import os
from datetime import datetime
from config import DB_PATH

_conn = None


def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _init_schema()
    return _conn


def _init_schema():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        sql = f.read()
    _conn.executescript(sql)
    _conn.commit()
    print(f"[DB] 초기화 완료: {DB_PATH}")


def insert_tick(tick: dict):
    """틱 1건 저장"""
    conn = get_conn()
    conn.execute(
        """INSERT INTO ticks (code, timestamp, price, open, high, low, volume, change_pct, prev_close)
           VALUES (:code, :timestamp, :price, :open, :high, :low, :volume, :change_pct, :prev_close)""",
        {**tick, "timestamp": tick["timestamp"].isoformat()},
    )
    conn.commit()


def insert_ticks_batch(ticks: list):
    """틱 여러 건 한번에 저장"""
    if not ticks:
        return
    conn = get_conn()
    conn.executemany(
        """INSERT INTO ticks (code, timestamp, price, open, high, low, volume, change_pct, prev_close)
           VALUES (:code, :timestamp, :price, :open, :high, :low, :volume, :change_pct, :prev_close)""",
        [{**t, "timestamp": t["timestamp"].isoformat()} for t in ticks],
    )
    conn.commit()


def upsert_candle_1m(code: str, ts: datetime, o: int, h: int, l: int, c: int, v: int):
    """1분봉 upsert (있으면 업데이트, 없으면 삽입)"""
    conn = get_conn()
    conn.execute(
        """INSERT INTO candles_1m (code, ts, open, high, low, close, volume)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(code, ts) DO UPDATE SET
               high   = MAX(high,  excluded.high),
               low    = MIN(low,   excluded.low),
               close  = excluded.close,
               volume = volume + excluded.volume""",
        (code, ts.isoformat(), o, h, l, c, v),
    )
    conn.commit()


def get_candles(code: str, limit: int = 390) -> list:
    """최근 N개 1분봉 조회"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM candles_1m WHERE code = ? ORDER BY ts DESC LIMIT ?",
        (code, limit),
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def get_tick_count(code: str = None) -> int:
    """저장된 틱 수 확인"""
    conn = get_conn()
    if code:
        row = conn.execute("SELECT COUNT(*) FROM ticks WHERE code = ?", (code,)).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) FROM ticks").fetchone()
    return row[0]
