# main.py
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from collector.kis_auth import get_access_token, get_approval_key
from collector.kis_ws import collect, flush_remaining
from storage.supabase_db import get_tick_count

WATCH_CODES = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "035420",  # NAVER
]

DEFAULT_DURATION = int(os.environ.get("COLLECT_DURATION", 21600))


async def main():
    print("=" * 50)
    print("  Ticker Data Collector")
    print("=" * 50)

    access_token = get_access_token()
    approval_key = get_approval_key(access_token)

    print(f"\n[수집 종목] {WATCH_CODES}")
    print(f"[수집 시간] {DEFAULT_DURATION // 3600}시간")
    print(f"[Supabase 현재 틱 수] {get_tick_count():,}건\n")

    try:
        await asyncio.wait_for(
            collect(approval_key, WATCH_CODES),
            timeout=DEFAULT_DURATION
        )
    except asyncio.TimeoutError:
        print(f"\n[완료] {DEFAULT_DURATION // 3600}시간 수집 종료")
    except KeyboardInterrupt:
        pass
    finally:
        await flush_remaining()
        print(f"[완료] 총 저장 틱: {get_tick_count():,}건")


if __name__ == "__main__":
    asyncio.run(main())
