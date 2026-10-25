# AI Service Mini Project — 기술 전략 분석 에이전트

반도체 아이템 하나를 골라, 분석 대상 기업들의 기술 현황과 성숙도(TRL)를 분석하는 보고서를 만드는 에이전트의 Baseline 코드입니다. 실행하고 관찰하면서 문제를 진단하고, 단계별로 코드를 수정해 나갑니다.

## 사용법

### 사전 준비

- `git` 설치 확인 : `git --version`
- `uv` 설치 확인 : `uv --version`
- `Node.js` 18.17 이상 설치 확인 : `node --version`
- 프로젝트 루트 : `ai-mini-project-v0.5/`
- 루트에 `.env` 준비
  - 필수 : ANY_API_KEY

### 1. 코드 받기 (최초 1회)

```
git clone https://github.com/elizabeth-kj-bae/ai-mini-project-v0.5.git
cd ai-mini-project-v0.5
```


### 2. 환경 구성 (최초 1회)

```
# 프로젝트 루트에서 실행
uv sync --locked
```

### 3. 자료 → 벡터 인덱스

```
# 기본 자료를 backend/data/<item>/ 에 넣은 뒤 인덱스 생성
cd backend
uv run python scripts/ingest.py --item hbf      # 또는 --all
```

`backend/index/hbf.json`이 생성되면 정상입니다. 자료가 바뀌면 다시 실행해야 합니다.

### 4. Backend 실행 (Terminal #1)

```
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

브라우저에서 `http://localhost:8000/api/config`를 열어 아이템 목록(JSON)이 보이면 정상입니다.

> Backend 실행 시 `LangChainPendingDeprecationWarning` 경고가 보여도 동작에는 영향이 없습니다.

### 5. Frontend 실행 (Terminal #2)

```
cd frontend
npm install      # 최초 1회
npm run dev
```

브라우저에서 `http://localhost:3000` → 아이템 선택 → Q1 실행 → 답변이 스트리밍되면 정상입니다.

> `npm install` 후 vulnerabilities 경고가 보여도 `npm audit fix`는 실행하지 마세요.

## 프로젝트

### Directory

```
ai-mini-project-v0.5/
├── CHECKLIST.md             Day 1 진단 체크리스트
├── backend/                 FastAPI + LangGraph
│   ├── app/
│   │   ├── main.py          API 서버 (SSE 스트리밍)
│   │   ├── config.py        환경 변수, 아이템 설정, LLM 단가표
│   │   ├── events.py        이벤트 스키마 (Frontend와 공유하는 약속)
│   │   ├── llm.py           LLM 호출 + 사용량 기록
│   │   ├── retrieval.py     문서 검색(벡터) + 웹 검색
│   │   └── agent/
│   │       ├── graph.py       그래프 구성
│   │       ├── state.py       공유 상태
│   │       ├── supervisor.py  다음 작업 결정
│   │       ├── nodes.py       작업자 노드 + 평가 노드
│   │       ├── prompts.py     프롬프트
│   │       └── tracing.py     노드 시작/종료 이벤트
│   ├── config/items.yaml    아이템별 분석 대상 기업, 테스트 질문
│   ├── data/<item>/         강사 제공 기본 자료를 넣는 곳
│   ├── index/               벡터 인덱스 저장 위치 (ingest.py 가 생성)
│   └── scripts/ingest.py    기본 자료 → 벡터 인덱스
└── frontend/                Next.js (실행 관찰 화면)
    ├── app/
    │   ├── page.tsx         질문 입력 · 답변 스트리밍 · 관찰 패널
    │   ├── layout.tsx       공통 레이아웃
    │   └── globals.css      스타일
    └── lib/
        ├── sse.ts           Backend 요청 · SSE 수신
        └── events.ts        이벤트 type 정의 (backend events.py와 짝)
```

### 화면 구성

| 영역 | 내용 |
|---|---|
| 왼쪽 | 아이템 선택, 테스트 질문(Q1~Q3), 답변 스트리밍, 최종 보고서 |
| 오른쪽 | 실행 요약, 노드 실행 타임라인, 경쟁사별 분석 갈래, 라우팅, 단계별 평가, LLM 사용량, 진행 로그 |

오른쪽 패널의 모든 값은 Backend가 보내는 이벤트로 그려집니다. 이벤트 종류와 필드는 `backend/app/events.py` 상단 설명을 참고하세요.

### 점검용 테스트 모드

화면의 "실행 모드"에서 **테스트 모드**를 선택하고 실행하면, 보고서 작성 단계가 근거 없이 일반론만 담긴 "부실한 결과"를 만듭니다. 평가 단계가 이런 결과를 어떻게 처리하는지 확인할 때 사용합니다.

- Backend를 다시 시작할 필요 없이 실행할 때마다 모드를 고를 수 있습니다.
- 실행한 모드는 오른쪽 패널 맨 위 "실행 모드"에 표시됩니다. 캡쳐할 때 함께 담기도록 하세요.

## Licence

© 2025–2026 Keejoo Bae — SK AX / SKALA. All rights reserved.

Provided for educational use in this course. You may clone, run, and modify it for your own learning. **Commercial use and redistribution — of the original or modified versions — are not permitted.**

See [LICENSE](LICENSE).
