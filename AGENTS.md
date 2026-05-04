# AGENTS.md

## 프로젝트 개요

이 저장소는 취얼업(ChwieolUp) 취업 준비 플랫폼에서 사용하는 FastAPI 기반 AI 서버입니다.

Spring Boot 백엔드가 내부 HTTP API로 FastAPI AI 서버를 호출하며, AI 서버는 채용 메일 및 전형 정보를 바탕으로 다음 기능을 제공합니다.

1. 회고 질문 생성
2. 메일 기반 전형 카테고리 추측
3. 메일 기반 칸반 이동 추천

본 프로젝트의 MVP 목표는 Ollama 기반 LLM API, Pydantic, JSON 기반 템플릿 데이터를 이용해 안정적인 AI 응답 파이프라인을 구현하는 것입니다.

---

## 기술 스택

- Python 3.11 이상
- FastAPI
- Uvicorn
- Pydantic v2
- Ollama HTTP API 기반 LLM Client
- JSON 기반 질문 템플릿 저장소

향후 확장 후보:

- PostgreSQL
- Qdrant 또는 Chroma
- LangChain 또는 LlamaIndex
- 사용자별 회고 이력 기반 개인화
- RAG 기반 질문 검색
- LLM Judge 기반 응답 품질 평가

---

## 개발 원칙

- 각 AI 기능은 router, schema, service 계층으로 분리한다.
- FastAPI route handler에는 비즈니스 로직을 넣지 않는다.
- Route handler는 요청 검증 후 service 함수를 호출하는 역할만 담당한다.
- 모든 외부 요청/응답 형식은 Pydantic schema로 정의한다.
- LLM 응답은 반드시 JSON parsing과 schema validation을 거친 후 반환한다.
- 원본 LLM 응답을 그대로 클라이언트에 노출하지 않는다.
- AI 추천 결과에는 가능한 경우 `confidence`, `reason`, `evidence`, `needs_user_confirmation`을 포함한다.
- MVP 단계에서는 AI의 추천이 자동으로 실제 칸반 이동이나 일정 등록을 수행하지 않는다.
- 모든 추천은 사용자의 확인을 거쳐 적용되는 것을 전제로 한다.
- 추후 AI 모델이 추가될 수 있도록 모듈 경계를 명확히 유지한다.

---

## 권장 프로젝트 구조

```text
ai-server/
 ├── AGENTS.md
 ├── README.md
 ├── .env.example
 ├── requirements.txt
 ├── Dockerfile
 ├── docker-compose.yml
 ├── app/
 │   ├── main.py
 │   ├── core/
 │   │   ├── config.py
 │   │   ├── llm_client.py
 │   │   └── errors.py
 │   │
 │   ├── routers/
 │   │   ├── retrospective.py
 │   │   ├── mail_stage.py
 │   │   └── kanban.py
 │   │
 │   ├── schemas/
 │   │   ├── retrospective.py
 │   │   ├── mail_stage.py
 │   │   └── kanban.py
 │   │
 │   ├── services/
 │   │   ├── retrospective/
 │   │   │   ├── service.py
 │   │   │   ├── template_loader.py
 │   │   │   ├── retriever.py
 │   │   │   ├── generator.py
 │   │   │   └── validator.py
 │   │   │
 │   │   ├── mail_analysis/
 │   │   │   ├── service.py
 │   │   │   ├── extractor.py
 │   │   │   └── classifier.py
 │   │   │
 │   │   └── kanban/
 │   │       ├── service.py
 │   │       ├── recommender.py
 │   │       └── validator.py
 │   │
 │   ├── data/
 │   │   └── retrospective_questions.json
 │   │
 │   └── prompts/
 │       ├── retrospective_prompt.txt
 │       ├── mail_stage_classification_prompt.txt
 │       └── kanban_move_recommendation_prompt.txt
 │
 └── tests/
     ├── test_retrospective.py
     ├── test_mail_stage.py
     └── test_kanban.py
```

---

## 환경 변수

로컬 개발에서는 `.env` 파일을 사용한다.

필수 환경 변수:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e2b
APP_ENV=local
```

환경 변수 로딩은 다음 파일에서 처리한다.

```text
app/core/config.py
```

LLM 호출은 반드시 다음 파일을 통해서만 수행한다.

```text
app/core/llm_client.py
```

다른 service 계층에서 Ollama HTTP API를 직접 호출하지 않는다.
모든 기능은 `app/core/llm_client.py`의 `generate_json_with_llm(system_prompt, user_prompt)`를 통해서만 LLM을 호출한다.

---

# 기능 1. 회고 질문 생성 API

## Endpoint

```http
POST /ai/retrospective/questions
```

## 목적

채용공고명, 회사명, 직무, 전형 단계 정보를 바탕으로 사용자가 회고록을 작성할 때 도움이 되는 질문을 생성한다.

이 기능은 메일에서 직무나 전형을 추출하지 않는다. 직무와 전형 정보는 이미 Spring Boot 백엔드에서 추출 또는 정규화되어 전달된다고 가정한다.

---

## Request Schema

파일 위치:

```text
app/schemas/retrospective.py
```

예시 요청:

```json
{
  "user_id": 1,
  "job_posting_title": "카카오 백엔드 개발자 채용",
  "company_name": "카카오",
  "job_role": "백엔드 개발자",
  "role_category": "backend",
  "process_stage": "technical_interview",
  "process_stage_label": "1차 기술면접",
  "question_count": 6
}
```

필드 설명:

| 필드 | 설명 |
|---|---|
| `user_id` | 사용자 ID, 선택값 |
| `job_posting_title` | 채용공고명 |
| `company_name` | 회사명 |
| `job_role` | 직무명 |
| `role_category` | 정규화된 직무 카테고리 |
| `process_stage` | 정규화된 전형 단계 |
| `process_stage_label` | 사용자에게 보여지는 전형명 |
| `question_count` | 생성할 질문 개수 |

---

## Response Schema

```json
{
  "question_set_title": "백엔드 기술면접 회고 질문",
  "role_category": "backend",
  "process_stage": "technical_interview",
  "questions": [
    {
      "category": "technical_depth",
      "question": "이번 면접에서 답변이 부족했던 백엔드 기술 개념은 무엇이었나요?",
      "reason": "기술 이해도와 보완 학습 방향을 파악하기 위함입니다.",
      "priority": "high",
      "source_template_ids": ["q_backend_interview_001"]
    }
  ]
}
```

---

## 구현 요구사항

- 질문 템플릿은 다음 파일에서 로드한다.

```text
app/data/retrospective_questions.json
```

- 질문 템플릿은 `role_category`, `process_stage`를 기준으로 필터링한다.
- `all` 값을 wildcard로 지원한다.
- 필터링된 템플릿은 `priority`가 높은 순서로 정렬한다.
- 상위 템플릿을 LLM에 전달해 최종 질문을 생성한다.
- LLM은 템플릿을 그대로 복사하지 않고, 입력된 채용공고명/직무/전형에 맞게 자연스럽게 변형해야 한다.
- 최종 응답은 Pydantic schema로 검증한다.
- 중복 질문은 제거한다.
- 가능하면 요청받은 `question_count` 개수에 맞춰 질문을 반환한다.

---

## 질문 템플릿 형식

```json
[
  {
    "id": "q_backend_interview_001",
    "question": "이번 면접에서 답변이 부족했던 백엔드 기술 개념은 무엇이었나요?",
    "category": "technical_depth",
    "role_category": ["backend"],
    "process_stage": ["technical_interview"],
    "intent": "백엔드 기술 이해도와 보완 학습 포인트를 파악하기 위한 질문",
    "priority": 0.95,
    "tags": ["backend", "technical_interview", "api", "database", "server"]
  }
]
```

초기 MVP에서는 JSON 파일 기반으로 구현한다. 추후 PostgreSQL 또는 Vector DB로 이전할 수 있도록 service 계층을 분리한다.

---

# 기능 2. 메일 전형 카테고리 추측 API

## Endpoint

```http
POST /ai/mail/stage-classify
```

## 목적

메일 제목과 본문을 보고, 사용자가 정의한 전형 카테고리 중 해당 메일이 어떤 카테고리에 가장 가까운지 추측한다.

중요한 점은 전형 카테고리가 전역적으로 고정되어 있지 않다는 것이다. 사용자가 직접 만든 칸반 단계 또는 전형 단계 목록을 매 요청마다 백엔드가 전달한다.

AI는 반드시 제공된 `user_stage_categories` 중 하나만 선택해야 하며, 새로운 전형 단계를 임의로 만들면 안 된다.

---

## Request Schema

파일 위치:

```text
app/schemas/mail_stage.py
```

예시 요청:

```json
{
  "mail_subject": "[카카오] 1차 인터뷰 일정 안내",
  "mail_body": "안녕하세요. 카카오 채용팀입니다. 백엔드 개발자 포지션 1차 기술 인터뷰 일정을 안내드립니다.",
  "user_stage_categories": [
    {
      "id": 1,
      "name": "서류",
      "description": "지원서 제출 및 서류 심사 단계",
      "order": 1
    },
    {
      "id": 2,
      "name": "코딩테스트",
      "description": "온라인 코딩테스트 및 과제 테스트",
      "order": 2
    },
    {
      "id": 3,
      "name": "1차 면접",
      "description": "기술면접 또는 실무진 면접",
      "order": 3
    }
  ]
}
```

---

## Response Schema

```json
{
  "predicted_stage": {
    "id": 3,
    "name": "1차 면접",
    "order": 3
  },
  "confidence": 0.91,
  "reason": "메일 제목과 본문에 '1차 인터뷰', '기술 인터뷰 일정'이 포함되어 있어 1차 면접 단계로 판단했습니다.",
  "evidence": [
    "1차 인터뷰 일정 안내",
    "기술 인터뷰 일정을 안내드립니다"
  ],
  "needs_user_confirmation": true
}
```

카테고리를 판단하기 어려운 경우:

```json
{
  "predicted_stage": null,
  "confidence": 0.25,
  "reason": "메일 내용이 채용 전형의 진행 상태를 명확히 나타내지 않아 특정 전형 단계로 분류하기 어렵습니다.",
  "evidence": [],
  "needs_user_confirmation": true
}
```

---

## 구현 요구사항

- 반드시 요청으로 받은 `user_stage_categories` 중에서만 선택한다.
- 새로운 stage id, stage name을 생성하지 않는다.
- 적합한 카테고리가 없으면 `predicted_stage`는 `null`로 반환한다.
- 항상 다음 필드를 포함한다.
  - `confidence`
  - `reason`
  - `evidence`
  - `needs_user_confirmation`
- `needs_user_confirmation`은 MVP 단계에서는 항상 `true`로 둔다.
- `evidence`는 메일 제목 또는 본문에서 가져온 짧은 문구여야 한다.
- 원본 LLM 응답을 그대로 반환하지 않는다.

---

# 기능 3. 칸반 이동 추천 API

## Endpoint

```http
POST /ai/kanban/move-recommend
```

## 목적

메일 내용을 기반으로 현재 채용 카드가 칸반 보드에서 어느 단계로 이동해야 하는지 추천한다.

이 기능은 다음 정보를 함께 비교한다.

1. 메일 제목
2. 메일 본문
3. 현재 칸반 단계
4. 사용자가 정의한 전체 칸반 단계 목록

AI는 실제로 칸반을 이동시키지 않는다. 이동 여부와 이동 대상 단계만 추천한다.

---

## Request Schema

파일 위치:

```text
app/schemas/kanban.py
```

예시 요청:

```json
{
  "mail_subject": "[카카오] 최종 인터뷰 일정 안내",
  "mail_body": "최종 인터뷰 일정을 안내드립니다.",
  "current_kanban_stage": {
    "id": 2,
    "name": "코딩테스트",
    "description": "온라인 코딩테스트",
    "order": 2
  },
  "user_kanban_stages": [
    {
      "id": 1,
      "name": "서류",
      "description": "지원서 제출 및 서류 검토",
      "order": 1
    },
    {
      "id": 2,
      "name": "코딩테스트",
      "description": "온라인 코딩테스트",
      "order": 2
    },
    {
      "id": 3,
      "name": "1차 면접",
      "description": "실무진 면접",
      "order": 3
    },
    {
      "id": 4,
      "name": "최종 면접",
      "description": "임원 또는 최종 인터뷰",
      "order": 4
    }
  ]
}
```

---

## Response Schema

```json
{
  "recommend_move": true,
  "from_stage": {
    "id": 2,
    "name": "코딩테스트",
    "order": 2
  },
  "to_stage": {
    "id": 4,
    "name": "최종 면접",
    "order": 4
  },
  "confidence": 0.88,
  "reason": "메일 본문에서 최종 인터뷰 일정이 안내되었으므로 현재 코딩테스트 단계에서 최종 면접 단계로 이동하는 것이 적절합니다.",
  "evidence": [
    "최종 인터뷰 일정을 안내드립니다"
  ],
  "needs_user_confirmation": true
}
```

이동이 필요하지 않은 경우:

```json
{
  "recommend_move": false,
  "from_stage": {
    "id": 3,
    "name": "1차 면접",
    "order": 3
  },
  "to_stage": null,
  "confidence": 0.82,
  "reason": "메일 내용이 현재 단계인 1차 면접 일정 안내에 해당하므로 별도의 칸반 이동은 필요하지 않습니다.",
  "evidence": [
    "1차 면접 일정 안내"
  ],
  "needs_user_confirmation": true
}
```

---

## 구현 요구사항

- 이동 대상은 반드시 요청으로 받은 `user_kanban_stages` 중 하나여야 한다.
- 새로운 칸반 단계를 임의로 만들지 않는다.
- 예측된 단계가 현재 단계와 같다면 `recommend_move: false`를 반환한다.
- 메일이 단순 안내, 광고, 일반 공지 등 전형 진행과 무관하면 `recommend_move: false`를 반환한다.
- 확신이 낮은 경우에는 이동을 추천하지 않거나, 낮은 confidence와 함께 사용자 확인을 요구한다.
- MVP 단계에서는 `needs_user_confirmation`을 항상 `true`로 둔다.
- 인접 단계가 아니더라도 메일 내용이 명확하면 이동을 추천할 수 있다.
  - 예: 현재 단계가 `코딩테스트`이고 메일이 `최종 인터뷰 안내`라면 `최종 면접`으로 이동 추천 가능

---

# 공통 메일 분석 모듈

메일 전형 카테고리 추측 API와 칸반 이동 추천 API는 모두 메일 내용을 해석한다.

따라서 가능한 경우 다음 위치에 공통 메일 분석 로직을 둔다.

```text
app/services/mail_analysis/
```

공통 메일 분석 모듈은 추후 다음 정보를 추출할 수 있다.

```json
{
  "summary": "1차 기술면접 일정 안내 메일입니다.",
  "detected_event_type": "interview_schedule",
  "detected_stage_keywords": ["1차 인터뷰", "기술 인터뷰"],
  "date_candidates": ["2026-05-07T14:00:00+09:00"],
  "evidence": ["1차 인터뷰 일정 안내"]
}
```

MVP에서는 너무 복잡하게 만들지 않아도 된다. 다만 메일 분석 프롬프트나 evidence 추출 로직이 중복되지 않도록 구조만 분리해둔다.

---

# LLM 프롬프트 규칙

모든 LLM 프롬프트는 JSON 응답을 명시적으로 요구해야 한다.

LLM에게 반드시 지시해야 할 내용:

- 제공된 카테고리 또는 칸반 단계 중에서만 선택한다.
- 새로운 stage id를 만들지 않는다.
- 확실하지 않으면 낮은 confidence를 반환한다.
- evidence는 입력 메일에서 가져온 짧은 문구로 작성한다.
- 과도하게 확신하지 않는다.
- 실제 칸반 이동이나 일정 등록을 수행하지 않는다.
- 모든 액션성 추천은 사용자 확인이 필요하다고 판단한다.

---

# 에러 처리

다음 상황에 대한 에러 처리를 구현한다.

- 잘못된 요청 payload
- 비어 있는 메일 본문
- 비어 있는 stage category 목록
- 비어 있는 kanban stage 목록
- 현재 칸반 단계가 전체 칸반 단계 목록에 존재하지 않는 경우
- LLM API 호출 실패
- LLM 응답 parsing 실패
- LLM 응답 schema validation 실패

클라이언트에는 stack trace를 반환하지 않는다.

---

# 테스트 요구사항

## 회고 질문 생성 테스트

- 요청한 개수만큼 질문이 생성되는지 확인한다.
- `role_category`, `process_stage` 기준으로 템플릿이 필터링되는지 확인한다.
- `all` wildcard가 동작하는지 확인한다.
- 중복 질문이 제거되는지 확인한다.
- 응답 schema가 유효한지 확인한다.

## 메일 전형 카테고리 추측 테스트

- 면접 일정 안내 메일을 면접 단계로 분류하는지 확인한다.
- 코딩테스트 안내 메일을 코딩테스트 단계로 분류하는지 확인한다.
- 모호한 메일에 대해 낮은 confidence를 반환하는지 확인한다.
- 제공되지 않은 stage를 생성하지 않는지 확인한다.
- evidence가 포함되는지 확인한다.

## 칸반 이동 추천 테스트

- 메일이 다음 전형을 명확히 나타낼 때 이동을 추천하는지 확인한다.
- 예측 단계가 현재 단계와 같으면 이동을 추천하지 않는지 확인한다.
- 비인접 단계 이동도 허용되는지 확인한다.
- 제공되지 않은 칸반 단계를 생성하지 않는지 확인한다.
- reason과 evidence가 포함되는지 확인한다.

---

# API 명명 규칙

구현해야 하는 엔드포인트는 다음과 같다.

```http
GET  /health
POST /ai/retrospective/questions
POST /ai/mail/stage-classify
POST /ai/kanban/move-recommend
```

---

# 코딩 스타일

- 모든 함수에는 가능한 한 type hint를 작성한다.
- 외부 API request/response는 반드시 Pydantic model로 정의한다.
- 함수는 작고 테스트 가능하게 작성한다.
- 전역 mutable state는 피한다.
- 질문 템플릿처럼 자주 읽는 정적 데이터는 캐싱해도 된다.
- 프롬프트 템플릿은 가능한 한 `app/prompts/` 아래에 분리한다.
- API Key는 코드에 하드코딩하지 않는다.
- 설정값은 환경 변수로 관리한다.

---

# MVP 범위

이번 구현에서 포함할 것:

1. FastAPI 기본 서버
2. `/health` API
3. 회고 질문 생성 API
4. 메일 전형 카테고리 추측 API
5. 칸반 이동 추천 API
6. JSON 기반 회고 질문 템플릿
7. LLM Client Wrapper
8. Pydantic validation
9. 기본 테스트 코드
10. Dockerfile
11. docker-compose.yml
12. README.md

이번 구현에서 제외할 것:

- Vector DB
- RAG 기반 검색
- 사용자 과거 회고록 기반 개인화
- Calendar event 생성
- 실제 칸반 자동 이동
- DB persistence
- 인증/인가
- 관리자 대시보드
- Fine-tuning 모델 학습

---

# 예상 산출물

Codex는 다음 파일들을 구현해야 한다.

```text
1. FastAPI 프로젝트 기본 구조
2. app/main.py
3. app/core/config.py
4. app/core/llm_client.py
5. app/routers/retrospective.py
6. app/routers/mail_stage.py
7. app/routers/kanban.py
8. app/schemas/retrospective.py
9. app/schemas/mail_stage.py
10. app/schemas/kanban.py
11. app/services/retrospective/*
12. app/services/mail_analysis/*
13. app/services/kanban/*
14. app/data/retrospective_questions.json
15. app/prompts/*.txt
16. tests/*.py
17. requirements.txt
18. Dockerfile
19. docker-compose.yml
20. README.md
```

---

# 로컬 실행 방법

로컬 실행:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Docker 실행:

```bash
docker compose up -d --build
```

Health check:

```bash
curl http://localhost:8001/health
```

---

# Codex에게 줄 개발 명령 예시

```text
AGENTS.md의 지침을 따라 FastAPI 기반 AI 서버를 구현해줘.

우선 MVP 범위만 구현해줘.

구현할 기능은 다음 3가지야.

1. 회고 질문 생성 API
- POST /ai/retrospective/questions
- 질문 템플릿 JSON 기반 검색
- LLM을 사용해 최종 회고 질문 생성
- Pydantic 응답 검증

2. 메일 전형 카테고리 추측 API
- POST /ai/mail/stage-classify
- 메일 제목/본문과 사용자가 정의한 전형 카테고리 목록을 입력받음
- 해당 메일이 어떤 카테고리에 가장 가까운지 추측
- confidence, reason, evidence 포함

3. 칸반 이동 추천 API
- POST /ai/kanban/move-recommend
- 메일 제목/본문, 현재 칸반 단계, 사용자 칸반 단계 목록을 입력받음
- 이동이 필요한지와 이동 대상 단계를 추천
- confidence, reason, evidence, needs_user_confirmation 포함

주의사항:
- 모든 라우터는 얇게 유지하고, 실제 로직은 service 계층에 작성해줘.
- 모든 request/response는 Pydantic schema로 정의해줘.
- LLM 호출은 app/core/llm_client.py에서만 수행되도록 해줘.
- LLM 응답은 반드시 JSON parsing 및 schema validation을 거쳐 반환해줘.
- 테스트 코드도 함께 작성해줘.
- Dockerfile과 docker-compose.yml도 작성해줘.
- README.md에 실행 방법과 API 테스트 예시를 작성해줘.
```

---

# 향후 확장 방향

MVP 이후에는 다음 순서로 확장할 수 있다.

1. 회고 질문 템플릿을 DB로 이전
2. Qdrant 또는 Chroma 기반 RAG 적용
3. 사용자 과거 회고록 기반 개인화 질문 생성
4. 메일에서 일정 후보 추출 API 추가
5. 캘린더 등록 추천 API 추가
6. LLM Judge 기반 응답 품질 평가
7. 사용자 피드백 기반 질문 priority 조정
8. 일부 분류 작업에 대해 fine-tuning 모델 적용
