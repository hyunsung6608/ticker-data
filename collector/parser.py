# collector/parser.py
from datetime import datetime


def parse_tick(fields: list) -> dict | None:
    """
    H0STCNT0 파이프 구분 데이터 파싱
    fields = parts[3].split("^")
    """
    if not fields or len(fields) < 13:
        return None
    try:
        code       = fields[0]
        time_str   = fields[1]   # HHMMSS
        price      = int(fields[2])
        sign       = fields[3]   # 1:상한 2:상승 3:보합 4:하락 5:하한
        change_amt = int(fields[4])
        change_pct = float(fields[5])
        open_p     = int(fields[7])
        high_p     = int(fields[8])
        low_p      = int(fields[9])
        volume     = int(fields[12])  # 체결거래량

        if not code or not price:
            return None

        neg = sign in ("4", "5")
        dp  = -abs(change_pct) if neg else abs(change_pct)
        prev_close = price - (-change_amt if neg else change_amt)

        # 체결 시각 — 오늘 날짜 + HHMMSS
        today = datetime.now().strftime("%Y%m%d")
        ts = datetime.strptime(f"{today}{time_str}", "%Y%m%d%H%M%S")

        return {
            "code":       code,
            "timestamp":  ts,
            "price":      price,
            "open":       open_p,
            "high":       high_p,
            "low":        low_p,
            "volume":     volume,
            "change_pct": dp,
            "prev_close": prev_close,
        }
    except (ValueError, IndexError) as e:
        return None
