-- storage/schema.sql

-- 원본 틱 데이터
CREATE TABLE IF NOT EXISTS ticks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT    NOT NULL,           -- 종목코드
    timestamp  TEXT    NOT NULL,           -- 체결시각 (ISO8601)
    price      INTEGER NOT NULL,           -- 체결가
    open       INTEGER,                    -- 시가
    high       INTEGER,                    -- 고가
    low        INTEGER,                    -- 저가
    volume     INTEGER,                    -- 체결거래량
    change_pct REAL,                       -- 등락률
    prev_close INTEGER                     -- 전일종가
);

-- 1분봉 OHLCV (집계)
CREATE TABLE IF NOT EXISTS candles_1m (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT    NOT NULL,
    ts         TEXT    NOT NULL,           -- 분봉 시작시각 (ISO8601)
    open       INTEGER NOT NULL,
    high       INTEGER NOT NULL,
    low        INTEGER NOT NULL,
    close      INTEGER NOT NULL,
    volume     INTEGER NOT NULL,
    UNIQUE(code, ts)                       -- 중복 방지
);

CREATE INDEX IF NOT EXISTS idx_ticks_code_ts    ON ticks(code, timestamp);
CREATE INDEX IF NOT EXISTS idx_candles_code_ts  ON candles_1m(code, ts);
