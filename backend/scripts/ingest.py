"""
기본 자료 → 벡터 인덱스 만들기
──────────────────────────────────────────────────────────────
사용법 (backend 폴더에서 실행)
    uv run python scripts/ingest.py --item hbf
    uv run python scripts/ingest.py --all

처리 순서
  1) data/<item>/ 폴더의 PDF, .md, .txt 파일을 읽습니다.
  2) 문서를 일정 길이의 조각(chunk)으로 자릅니다.
  3) 각 조각을 임베딩(숫자 벡터)으로 바꿉니다.
  4) index/<item>.json 으로 저장합니다. → app/retrieval.py 가 이 파일을 읽습니다.

자료를 바꾸면 반드시 이 스크립트를 다시 실행해야 검색 결과에 반영됩니다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))   # backend/ 를 import 경로에 추가

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import load_items, settings
from app.llm import get_embeddings

# 조각 크기와 겹치는 길이 (글자 수 기준)
#  - 너무 작으면 문맥이 끊기고, 너무 크면 검색 정확도가 떨어집니다.
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def load_file(path: Path) -> list[Document]:
    """파일 하나를 읽어 Document 목록으로 돌려줍니다. (PDF는 페이지마다 1개)"""
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        docs = []
        for page_no, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                docs.append(Document(
                    page_content=text,
                    metadata={"source": path.name, "title": path.stem, "page": page_no},
                ))
        return docs
    if path.suffix.lower() in {".md", ".txt"}:
        if path.name == "README.md":          # 폴더 안내 파일은 제외
            return []
        text = path.read_text(encoding="utf-8")
        return [Document(page_content=text, metadata={"source": path.name, "title": path.stem})]
    return []


def build_index(item_id: str) -> None:
    folder = settings.data_dir / item_id
    files = sorted(p for p in folder.iterdir() if p.is_file())
    docs: list[Document] = []
    for f in files:
        loaded = load_file(f)
        print(f"  - {f.name}: {len(loaded)}개 문서(페이지)")
        docs.extend(loaded)

    if not docs:
        print(f"[{item_id}] 읽을 자료가 없습니다. data/{item_id}/ 폴더를 확인하세요.")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(docs)
    print(f"[{item_id}] 조각 {len(chunks)}개 → 임베딩 생성 중...")

    store = InMemoryVectorStore.from_documents(chunks, embedding=get_embeddings())
    settings.index_dir.mkdir(exist_ok=True)
    out = settings.index_dir / f"{item_id}.json"
    store.dump(str(out))
    print(f"[{item_id}] 저장 완료: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--item", help="아이템 ID (config/items.yaml 참고)")
    parser.add_argument("--all", action="store_true", help="모든 아이템 처리")
    args = parser.parse_args()

    targets = list(load_items()) if args.all else [args.item]
    if not targets or targets == [None]:
        parser.error("--item 또는 --all 을 지정하세요.")
    for item_id in targets:
        print(f"[{item_id}] 자료 읽는 중...")
        build_index(item_id)
