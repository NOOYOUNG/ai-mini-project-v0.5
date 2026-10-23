"""
Supervisor
──────────────────────────────────────────────────────────────
작업자(worker) 노드 중 다음에 무엇을 실행할지 결정합니다.

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

# 보고서를 만들기 위한 기본 작업 순서
DEFAULT_PLAN = ["researcher", "competitor_analyst", "writer"]


@traced("supervisor")
async def supervisor(state: AgentState) -> dict:
    plan = state.get("plan") or list(DEFAULT_PLAN)
    index = state.get("plan_index", 0)

    next_worker = plan[index] if index < len(plan) else "writer"

    emit(Route(
        source="supervisor",
        target=next_worker,
        reason=f"작업 계획 {index + 1}/{len(plan)} 단계",
    ))
    return {"plan": plan, "plan_index": index + 1, "next": next_worker}


def route_from_supervisor(state: AgentState) -> str:
    """조건부 엣지: Supervisor가 정한 다음 노드 이름을 돌려줍니다."""
    return state["next"]
