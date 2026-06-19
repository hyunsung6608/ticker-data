from collections import deque
from statistics import mean, pstdev
import math

WINDOW = 30
DELTA_Z_THRESHOLD = 3.5       # 틱간 가격 변화량 기준
VOLUME_LOG_Z_THRESHOLD = 3.0  # 거래량 이상치 기준 (로그 변환 후 표준편차 배수)
MIN_VOLUME = 50               # 이 거래량 미만이면 거래량 이상치 무시

_delta_buf = {}    # code -> deque (틱간 가격 변화량)
_volume_buf = {}   # code -> deque
_last_price = {}   # code -> 직전 체결가


def check_anomaly(tick: dict) -> list:
    """틱 1건을 보고 이상치 목록 반환 (없으면 빈 리스트)"""
    code = tick["code"]

    if code not in _delta_buf:
        _delta_buf[code] = deque(maxlen=WINDOW)
        _volume_buf[code] = deque(maxlen=WINDOW)
        _last_price[code] = tick["price"]
        return []

    anomalies = []
    delta = tick["price"] - _last_price[code]
    d_buf = _delta_buf[code]
    v_buf = _volume_buf[code]

    if len(d_buf) >= WINDOW:
        sd = pstdev(d_buf)
        if sd > 0:
            z = (delta - mean(d_buf)) / sd
            if abs(z) >= DELTA_Z_THRESHOLD:
                anomalies.append({"code": code, "type": "price", "value": tick["price"], "z": round(z, 2)})

    if len(v_buf) >= WINDOW and tick["volume"] >= MIN_VOLUME:
        sd_v = pstdev(v_buf)
        if sd_v > 0:
            log_v = math.log(tick["volume"])
            z_v = (log_v - mean(v_buf)) / sd_v
            if z_v >= VOLUME_LOG_Z_THRESHOLD:
                anomalies.append({"code": code, "type": "volume", "value": tick["volume"], "z": round(z_v, 2)})

    d_buf.append(delta)
    v_buf.append(math.log(tick["volume"]))
    _last_price[code] = tick["price"]

    return anomalies