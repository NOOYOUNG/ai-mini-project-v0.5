"""
노드 실행 추적
- @traced("노드이름") 을 붙인 노드는 시작/종료 시점에 node_start / node_end 이벤트를 자동으로 내보냅니다.
- node_end 에는 노드 소요 시간(ms)이 들어갑니다.
"""
from __future__ import annotations

import time
from functools import wraps

from app.events import NodeEnd, NodeStart, emit


def traced(node_name: str):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(state):
            emit(NodeStart(node=node_name))
            started = time.perf_counter()
            try:
                return await fn(state)
            finally:
                elapsed = int((time.perf_counter() - started) * 1000)
                emit(NodeEnd(node=node_name, duration_ms=elapsed))
        return wrapper
    return decorator
