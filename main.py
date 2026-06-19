import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from collector.kis_auth import get_access_token, get_approval_key
from collector.kis_ws import collect, flush_remaining
from storage.supabase_db import get_tick_count


WATCH_CODES = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "035420",  # NAVER
    "005380",  # 현대차
    "066570",  # LG전자
    "034020",  # 두산에너빌리티
    "329180",  # 현대중공업
    "010140",  # 삼성중공업
]

KST = timezone(timedelta(hours=9))
MAX_SESSION_SECONDS = 330 * 60   # 5시간30분 — 호스팅 러너 6시간 하드캡 보호용 안전장치
COLLECT_END_TIME = os.environ.get("COLLECT_END_TIME", "15:35")  # 워크플로우별로 다르게 지정
SESSION_MODE = os.environ.get("SESSION_MODE", "krx")  # "krx" | "nxt"


def seconds_until(target_str: str) -> int:
    """지금부터 목표 시각(HH:MM, KST)까지 남은 초"""
    hour, minute = map(int, target_str.split(":"))
    now = datetime.now(KST)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now >= target:
        return 0
    return int((target - now).total_seconds())

async def main():
    print("=" * 50)
    print("  Ticker Data Collector")
    print("=" * 50)

    access_token = get_access_token()
    approval_key = get_approval_key(access_token)

    duration = min(seconds_until(COLLECT_END_TIME), MAX_SESSION_SECONDS)
    if duration <= 0:
        print(f"\n[알림] 이미 목표 시각({COLLECT_END_TIME})을 지났어요. 수집을 건너뜁니다.")
        return

    print(f"\n[수집 종목] {WATCH_CODES}")
    print(f"[수집 목표] {COLLECT_END_TIME}까지 (최대 {duration // 60}분, 모드: {SESSION_MODE})")
    print(f"[Supabase 현재 틱 수] {get_tick_count():,}건\n")

    try:
        await asyncio.wait_for(
            collect(approval_key, WATCH_CODES, session_mode=SESSION_MODE),
            timeout=duration
        )
    except asyncio.TimeoutError:
        print(f"\n[완료] 수집 종료 (목표 도달 또는 안전 한도)")
    except KeyboardInterrupt:
        pass
    finally:
        await flush_remaining()
        print(f"[완료] 총 저장 틱: {get_tick_count():,}건")


if __name__ == "__main__":
    asyncio.run(main())
