import asyncio
import json
import websockets
from collector.parser import parse_tick
from storage.supabase_db import insert_ticks_batch, upsert_candle_1m, insert_anomaly
from config import WS_URL
from collector.anomaly import check_anomaly

# 1분봉 집계 버퍼
_candle_buf = {}

# 틱 배치 버퍼
_tick_buf = []
BATCH_SIZE = 100


def _update_candle(tick: dict):
    code  = tick["code"]
    ts    = tick["timestamp"]
    ts_min = ts.replace(second=0, microsecond=0)

    if code not in _candle_buf:
        _candle_buf[code] = {
            "ts_min": ts_min,
            "o": tick["price"], "h": tick["price"],
            "l": tick["price"], "c": tick["price"],
            "v": tick["volume"],
        }
        return

    buf = _candle_buf[code]

    if ts_min > buf["ts_min"]:
        upsert_candle_1m(
            code, buf["ts_min"],
            buf["o"], buf["h"], buf["l"], buf["c"], buf["v"]
        )
        _candle_buf[code] = {
            "ts_min": ts_min,
            "o": tick["price"], "h": tick["price"],
            "l": tick["price"], "c": tick["price"],
            "v": tick["volume"],
        }
    else:
        buf["h"] = max(buf["h"], tick["price"])
        buf["l"] = min(buf["l"], tick["price"])
        buf["c"] = tick["price"]
        buf["v"] += tick["volume"]


def _subscribe_msg(approval_key: str, code: str) -> str:
    return json.dumps({
        "header": {
            "approval_key": approval_key,
            "custtype": "P",
            "tr_type": "1",
            "content-type": "utf-8",
        },
        "body": {
            "input": {
                "tr_id": "H0STCNT0",
                "tr_key": code,
            }
        },
    })


async def collect(approval_key: str, codes: list):
    global _tick_buf

    print(f"[WS] 연결 중: {WS_URL}")
    async with websockets.connect(WS_URL, ping_interval=20) as ws:
        print(f"[WS] 연결 완료, {len(codes)}종목 구독 시작")

        for code in codes:
            await ws.send(_subscribe_msg(approval_key, code))
            await asyncio.sleep(0.1)

        print(f"[WS] 구독 완료: {codes}")

        async for message in ws:
            raw = message if isinstance(message, str) else message.decode()

            if raw == "PINGPONG":
                await ws.send("PINGPONG")
                continue
            if raw.startswith("{"):
                try:
                    msg = json.loads(raw)
                    if msg.get("header", {}).get("tr_id") == "PINGPONG":
                        await ws.send(json.dumps({"header": {"tr_id": "PINGPONG"}}))
                except Exception:
                    pass
                continue

            parts = raw.split("|")
            if len(parts) < 4:
                continue
            tr_id = parts[1]
            if tr_id == "PINGPONG":
                await ws.send("PINGPONG")
                continue

            if tr_id == "H0STCNT0":
                fields = parts[3].split("^")
                tick = parse_tick(fields)
                if tick:
                    print(f"[틱] {tick['code']} {tick['price']:,}원 vol:{tick['volume']}")

                    for a in check_anomaly(tick):
                        if a["type"] == "price":
                            print(f"[이상치] {a['code']} 가격 급변동 z={a['z']} (현재가 {a['value']:,}원)")
                        else:
                            print(f"[이상치] {a['code']} 거래량 급증 z={a['z']} (체결량 {a['value']:,})")
                        insert_anomaly(a)
                        
                    _tick_buf.append(tick)
                    _update_candle(tick)

                    if len(_tick_buf) >= BATCH_SIZE:
                        insert_ticks_batch(_tick_buf)
                        print(f"[Supabase] {len(_tick_buf)}건 저장")
                        _tick_buf = []


async def flush_remaining():
    if _tick_buf:
        insert_ticks_batch(_tick_buf)
        print(f"[Supabase] 종료 flush: {len(_tick_buf)}건 저장")

    for code, buf in _candle_buf.items():
        upsert_candle_1m(
            code, buf["ts_min"],
            buf["o"], buf["h"], buf["l"], buf["c"], buf["v"]
        )
    print("[Supabase] 분봉 버퍼 flush 완료")
