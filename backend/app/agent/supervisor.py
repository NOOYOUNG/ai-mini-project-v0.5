"""
Supervisor - 동적 라우팅
──────────────────────────────────────────────────────────────
현재 작업 상태와 결과를 확인하여 다음 worker를 결정합니다.

작업자 목록
  researcher          질문에 필요한 근거 자료 수집 (문서 + 웹)
  competitor_analyst  분석 대상 기업별 현황 분석
  writer              보고서 작성
"""
from __future__ import annotations

from app.agent.state import AgentState
from app.agent.tracing import traced
from app.events import Route, emit

WORKERS = ["researcher", "competitor_analyst", "writer"]


def has_result(state: AgentState, *keys: str) -> bool:
    """State에 지정한 결과가 존재하고 비어 있지 않은지 확인합니다."""
    for key in keys:
        value = state.get(key)
        if value is not None and value != "" and value != [] and value != {}:
            return True
    return False


@traced("supervisor")
async def supervisor(state: AgentState) -> dict:
    # 1. 최종 보고서가 이미 작성되었다면 종료합니다.
    if has_result(state, "draft"):
        next_worker = "FINISH"
        reason = "최종 보고서가 작성되어 작업 종료"

    # 2. 조사 결과가 없다면 researcher를 실행합니다.
    elif not has_result(state, "evidence"):
        next_worker = "researcher"
        reason = "조사 결과가 없어 근거 자료 수집 필요"

    # 3. 조사 결과는 있지만 기업 분석 결과가 없다면 분석합니다.
    elif not has_result(state, "competitor_findings"):
        next_worker = "competitor_analyst"
        reason = "조사 결과 확보 완료, 기업별 현황 분석 필요"

    # 4. 조사와 기업 분석 결과가 모두 있다면 보고서를 작성합니다.
    else:
        next_worker = "writer"
        reason = "조사 및 기업 분석 완료, 최종 보고서 작성 필요"

    # 5. 라우팅 이벤트를 기록합니다.
    emit(
        Route(
            source="supervisor",
            target=next_worker,
            reason=reason,
        )
    )

    return {
        "next": next_worker,
        "routing_reason": reason,
    }


def route_from_supervisor(state: AgentState) -> str:
    """조건부 엣지에서 Supervisor가 선택한 다음 노드를 반환합니다."""
    return state["next"]
