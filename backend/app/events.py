"""
이벤트 스키마
──────────────────────────────────────────────────────────────
에이전트 실행 중에 일어나는 일을 Frontend로 실시간 전달하기 위한 약속(형식)입니다.
- 모든 이벤트에는 type(종류)과 ts(발생 시각, epoch 밀리초)가 들어갑니다.
- Frontend(lib/events.ts)도 같은 형식을 사용합니다. 한쪽을 바꾸면 다른 쪽도 함께 바꿔야 합니다.

이벤트 종류
  run_start    실행 시작 (아이템, 분석 대상 기업, 질문)
  node_start   노드 시작
  node_end     노드 종료 (소요 시간 포함)
  branch_start 경쟁사별 분석 한 갈래 시작
  branch_end   경쟁사별 분석 한 갈래 종료 (소요 시간 포함)
  route        Supervisor가 다음 작업을 결정
  progress     진행 상황 메시지
  llm_usage    LLM 호출 1회의 토큰 사용량과 예상 비용
  evaluation   단계별 평가 결과
  token        답변 스트리밍 조각
  report       최종 보고서 (Markdown)
  error        오류
  done         실행 종료 (전체 요약)
"""
from __future__ import annotations

import time
from typing import Literal, Optional

from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field


def now_ms() -> int:
    return int(time.time() * 1000)


class BaseEvent(BaseModel):
    type: str
    ts: int = Field(default_factory=now_ms)


class RunStart(BaseEvent):
    type: Literal["run_start"] = "run_start"
    run_id: str
    item_id: str
    item_name: str
    competitors: list[str]
    query: str
    test_mode: bool = False      # 점검용 테스트 모드 여부


class NodeStart(BaseEvent):
    type: Literal["node_start"] = "node_start"
    node: str


class NodeEnd(BaseEvent):
    type: Literal["node_end"] = "node_end"
    node: str
    duration_ms: int


class BranchStart(BaseEvent):
    type: Literal["branch_start"] = "branch_start"
    node: str
    branch: str          # 예: 경쟁사 이름


class BranchEnd(BaseEvent):
    type: Literal["branch_end"] = "branch_end"
    node: str
    branch: str
    duration_ms: int


class Route(BaseEvent):
    type: Literal["route"] = "route"
    source: str
    target: str
    reason: str = ""


class Progress(BaseEvent):
    type: Literal["progress"] = "progress"
    node: str
    message: str


class LlmUsage(BaseEvent):
    type: Literal["llm_usage"] = "llm_usage"
    node: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


class Evaluation(BaseEvent):
    type: Literal["evaluation"] = "evaluation"
    stage: str
    passed: bool
    reason: str
    attempt: int


class Token(BaseEvent):
    type: Literal["token"] = "token"
    node: str
    text: str


class Report(BaseEvent):
    type: Literal["report"] = "report"
    run_id: str
    markdown: str


class ErrorEvent(BaseEvent):
    type: Literal["error"] = "error"
    message: str


class Done(BaseEvent):
    type: Literal["done"] = "done"
    run_id: str
    total_duration_ms: int
    llm_calls: int
    input_tokens: int
    output_tokens: int
    total_cost_usd: float


def emit(event: BaseEvent) -> None:
    """
    그래프 노드 안에서 이벤트를 내보냅니다.
    LangGraph의 custom 스트림 모드(stream_mode="custom")로 전달되며,
    main.py 가 이를 받아 SSE로 Frontend에 보냅니다.
    그래프 밖(예: 단독 테스트)에서 호출되면 조용히 무시합니다.
    """
    try:
        writer = get_stream_writer()
    except Exception:
        return
    writer(event.model_dump())
