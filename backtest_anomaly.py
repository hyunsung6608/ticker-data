# Supabase에 쌓인 과거 틱으로 이상치 감지 로직만 검증 (실시간 WS 없이)
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from storage.supabase_db import get_ticks
from collector.anomaly import check_anomaly

WATCH_CODES = [
    "005930", "000660", "035420", "005380",
    "066570", "034020", "329180", "010140",
]

LIMIT_PER_CODE = 1000


def run():
    total_anomalies = 0

    for code in WATCH_CODES:
        rows = get_ticks(code=code, limit=LIMIT_PER_CODE)
        print(f"\n[{code}] {len(rows)}건 검증 시작")

        for r in rows:
            tick = {
                "code": r["code"],
                "price": r["price"],
                "volume": r["volume"],
            }
            for a in check_anomaly(tick):
                total_anomalies += 1
                if a["type"] == "price":
                    print(f"  [이상치] {a['code']} 가격 급변동 z={a['z']} (현재가 {a['value']:,}원)")
                else:
                    print(f"  [이상치] {a['code']} 거래량 급증 {a['z']}배 (체결량 {a['value']:,})")

    print(f"\n총 {total_anomalies}건 이상치 감지됨")


if __name__ == "__main__":
    run()