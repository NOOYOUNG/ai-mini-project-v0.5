"""
근거 자료 검색
──────────────────────────────────────────────────────────────
두 가지 출처에서 근거를 찾습니다.
  1) 문서 검색 : 강사가 제공한 기본 자료 (scripts/ingest.py 로 미리 만든 벡터 인덱스)
  2) 웹 검색   : Tavily (TAVILY_API_KEY 가 없으면 건너뜀)

검색 결과는 모두 같은 형태(Evidence)로 맞춰서 돌려줍니다.
  {"kind": "doc" | "web", "source": 파일명 또는 URL, "title": 제목, "content": 본문 일부}
"""
from __future__ import annotations

import asyncio
from functools import lru_cache

from langchain_core.vectorstores import InMemoryVectorStore

from app.config import settings
from app.llm import get_embeddings

Evidence = dict


@lru_cache
def _load_index(item_id: str) -> InMemoryVectorStore | None:
    """아이템별 벡터 인덱스를 불러옵니다. 인덱스가 없으면 None."""
    path = settings.index_dir / f"{item_id}.json"
    if not path.exists():
        return None
    return InMemoryVectorStore.load(str(path), embedding=get_embeddings())


def index_exists(item_id: str) -> bool:
    return (settings.index_dir / f"{item_id}.json").exists()


async def search_docs(item_id: str, query: str, k: int = 4) -> list[Evidence]:
    """기본 자료에서 질문과 의미가 가까운 문단 k개를 찾습니다."""
    store = _load_index(item_id)
    if store is None:
        return []
    docs = await store.asimilarity_search(query, k=k)
    return [
        {
            "kind": "doc",
            "source": d.metadata.get("source", ""),
            "title": d.metadata.get("title", d.metadata.get("source", "")),
            "content": d.page_content,
        }
        for d in docs
    ]


def web_search_enabled() -> bool:
    return bool(settings.tavily_api_key)


async def search_web(query: str, max_results: int = 3) -> list[Evidence]:
    """웹에서 최신 정보를 찾습니다. (Tavily 클라이언트는 동기 방식이라 별도 스레드에서 실행)"""
    if not web_search_enabled():
        return []
    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.tavily_api_key)
    result = await asyncio.to_thread(client.search, query=query, max_results=max_results)
    return [
        {
            "kind": "web",
            "source": r.get("url", ""),
            "title": r.get("title", ""),
            "content": r.get("content", ""),
        }
        for r in result.get("results", [])
    ]
