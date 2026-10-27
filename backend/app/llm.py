"""
LLM / 임베딩 생성과 사용량 기록
- 모든 LLM 호출은 이 파일의 ainvoke_tracked / astream_tracked 를 거칩니다.
- 호출이 끝날 때마다 llm_usage 이벤트(토큰 수, 예상 비용)가 발생합니다.
"""
from __future__ import annotations

from contextvars import ContextVar
from functools import lru_cache

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import PRICING_PER_1M, settings
from app.events import LlmUsage, Token, emit

_run_cost_usd: ContextVar[float] = ContextVar("run_cost_usd", default=0.0)


@lru_cache
def get_llm() -> ChatOpenAI:
    # stream_usage=True : 스트리밍 응답에서도 토큰 사용량을 받기 위한 옵션
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=0,
        stream_usage=True,
        api_key=settings.openai_api_key,
    )


@lru_cache
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICING_PER_1M.get(model, (0.0, 0.0))
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


def reset_llm_cost_usage() -> None:
    """실행 1회 기준 LLM 누적 비용을 초기화합니다."""
    _run_cost_usd.set(0.0)


def _emit_usage(node: str, message) -> None:
    usage = getattr(message, "usage_metadata", None) or {}
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cost_usd = estimate_cost(settings.llm_model, input_tokens, output_tokens)
    total_cost_usd = _run_cost_usd.get() + cost_usd
    _run_cost_usd.set(total_cost_usd)

    emit(LlmUsage(
        node=node,
        model=settings.llm_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
    ))

    if total_cost_usd >= settings.llm_cost_limit_usd:
        raise RuntimeError(
            "LLM 비용 상한 도달: "
            f"${total_cost_usd:.6f} / ${settings.llm_cost_limit_usd:.6f}"
        )


async def ainvoke_tracked(messages: list[BaseMessage], node: str) -> str:
    """LLM을 한 번 호출하고 응답 텍스트를 돌려줍니다. (사용량 이벤트 자동 발생)"""
    response = await get_llm().ainvoke(messages)
    _emit_usage(node, response)
    return response.content


async def astream_tracked(messages: list[BaseMessage], node: str) -> str:
    """
    LLM 응답을 조각(token) 단위로 Frontend에 흘려보내면서 전체 텍스트를 돌려줍니다.
    조각들을 더해(+) 하나의 메시지로 합치면 마지막에 사용량 정보가 들어 있습니다.
    """
    full = None
    async for chunk in get_llm().astream(messages):
        if chunk.content:
            emit(Token(node=node, text=chunk.content))
        full = chunk if full is None else full + chunk
    if full is None:
        return ""
    _emit_usage(node, full)
    return full.content
