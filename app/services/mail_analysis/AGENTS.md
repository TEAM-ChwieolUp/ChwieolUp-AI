# Mail Analysis AGENTS.md

## 1. 기능 개요

이 모듈은 채용 관련 메일 본문을 분석하여, 사용자가 미리 정의한 전형 카테고리 중 해당 메일이 어떤 카테고리에 가장 가까운지 분류한다.

예를 들어 사용자가 다음과 같은 카테고리를 정의해두었다고 가정한다.

```json
[
  {
    "id": 1,
    "name": "서류 전형",
    "description": "지원서 제출, 서류 검토, 서류 합격 또는 불합격 관련 단계"
  },
  {
    "id": 2,
    "name": "코딩테스트",
    "description": "온라인 코딩테스트, 과제 테스트, 사전 테스트 관련 단계"
  },
  {
    "id": 3,
    "name": "1차 면접",
    "description": "기술면접, 실무진 면접, 1차 인터뷰 관련 단계"
  }
]
```

메일 본문이 “1차 기술 인터뷰 일정 안내”라면, 이 모듈은 `1차 면접` 카테고리를 추천해야 한다.

---

## 2. 핵심 목표

이 기능은 단순 문자열 매칭이 아니라, 메일 본문의 의미를 바탕으로 사용자가 정의한 전형 카테고리 중 가장 적절한 카테고리를 추론해야 한다.

출력에는 반드시 다음 정보가 포함되어야 한다.

- 예측된 카테고리
- 신뢰도 점수
- 그렇게 분류한 이유
- 근거가 된 메일 문구
- 사용자 확인 필요 여부

이 기능은 실제 칸반 이동을 수행하지 않는다.  
오직 “이 메일은 어떤 전형 단계와 관련 있어 보이는지”만 추천한다.

---

## 3. 입력 데이터

Endpoint:

```http
POST /ai/mail/stage-classify
```

Request 예시:

```json
{
  "mail_body": "안녕하세요. 카카오 채용팀입니다. 백엔드 개발자 포지션 1차 기술 인터뷰 일정을 안내드립니다. 인터뷰는 2026년 5월 7일 오후 2시에 진행될 예정입니다.",
  "user_stage_categories": [
    {
      "id": 1,
      "name": "서류 전형",
      "description": "지원서 제출, 서류 검토, 서류 합격 또는 불합격 관련 단계",
      "order": 1
    },
    {
      "id": 2,
      "name": "코딩테스트",
      "description": "온라인 코딩테스트, 과제 테스트, 사전 테스트 관련 단계",
      "order": 2
    },
    {
      "id": 3,
      "name": "1차 면접",
      "description": "기술면접, 실무진 면접, 1차 인터뷰 관련 단계",
      "order": 3
    }
  ]
}
```

---

## 4. 입력 Schema 요구사항

`app/schemas/mail_stage.py`에 Pydantic 모델을 정의한다.

권장 모델 구조:

```python
from typing import List, Optional
from pydantic import BaseModel, Field


class UserStageCategory(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    order: Optional[int] = None


class MailStageClassifyRequest(BaseModel):
    mail_body: str = Field(..., min_length=1)
    user_stage_categories: List[UserStageCategory] = Field(..., min_length=1)


class PredictedStage(BaseModel):
    id: int
    name: str
    order: Optional[int] = None


class MailStageClassifyResponse(BaseModel):
    predicted_stage: Optional[PredictedStage]
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str
    evidence: List[str]
    needs_user_confirmation: bool
```

---

## 5. 출력 데이터

Response 예시:

```json
{
  "predicted_stage": {
    "id": 3,
    "name": "1차 면접",
    "order": 3
  },
  "confidence": 0.91,
  "reason": "메일 본문에 '1차 기술 인터뷰 일정'이라는 표현이 포함되어 있으며, 이는 사용자가 정의한 '1차 면접' 카테고리 설명인 기술면접 또는 실무진 면접과 가장 잘 일치합니다.",
  "evidence": [
    "1차 기술 인터뷰 일정을 안내드립니다",
    "인터뷰는 2026년 5월 7일 오후 2시에 진행될 예정입니다"
  ],
  "needs_user_confirmation": true
}
```

---

## 6. 분류 규칙

### 6.1 제공된 카테고리만 사용

모델은 반드시 `user_stage_categories`에 포함된 카테고리 중 하나만 선택해야 한다.

금지:

```json
{
  "predicted_stage": {
    "id": 99,
    "name": "AI가 새로 만든 전형"
  }
}
```

LLM은 새로운 카테고리나 새로운 ID를 임의로 생성하면 안 된다.

---

### 6.2 모호한 경우

메일이 특정 전형 단계를 명확히 나타내지 않는 경우, `predicted_stage`는 `null`로 반환한다.

예시 메일:

```text
안녕하세요. 지원해주셔서 감사합니다. 추후 전형 일정은 다시 안내드리겠습니다.
```

권장 응답:

```json
{
  "predicted_stage": null,
  "confidence": 0.25,
  "reason": "메일 본문에 특정 전형 단계나 평가 방식이 명확히 언급되어 있지 않아 사용자가 정의한 카테고리 중 하나로 확정하기 어렵습니다.",
  "evidence": [
    "추후 전형 일정은 다시 안내드리겠습니다"
  ],
  "needs_user_confirmation": true
}
```

---

### 6.3 confidence 기준

`confidence`는 0.0부터 1.0 사이의 실수로 반환한다.

권장 기준:

| 점수 범위 | 의미 |
|---|---|
| 0.85 ~ 1.00 | 매우 명확함 |
| 0.65 ~ 0.84 | 어느 정도 명확함 |
| 0.40 ~ 0.64 | 애매함 |
| 0.00 ~ 0.39 | 분류 어려움 |

---

### 6.4 needs_user_confirmation

MVP에서는 항상 `true`로 반환한다.

이 기능은 사용자의 칸반 상태나 지원 상태를 자동 변경하지 않는다.  
따라서 AI가 높은 confidence를 반환하더라도 사용자의 확인이 필요하다.

---

### 6.5 evidence 규칙

`evidence`에는 메일 본문에서 실제로 존재하는 짧은 문구만 넣는다.

좋은 예:

```json
[
  "1차 기술 인터뷰 일정을 안내드립니다",
  "온라인 코딩테스트 응시 안내"
]
```

나쁜 예:

```json
[
  "면접과 관련 있어 보입니다",
  "코딩테스트 단계라고 판단됩니다"
]
```

`evidence`는 모델의 해석이 아니라, 메일 본문에서 가져온 근거 문구여야 한다.

---

## 7. LLM 사용 방식

이 기능은 서버 컴퓨터에 설치된 Ollama 기반 Gemma 모델을 사용한다.

OpenAI API를 사용하지 않는다.

LLM 호출은 반드시 다음 공통 함수만 사용한다.

```python
generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict
```

위 함수는 다음 파일에 구현되어 있어야 한다.

```text
app/core/llm_client.py
```

`mail_analysis` 모듈 내부에서 Ollama HTTP API를 직접 호출하면 안 된다.

---

## 8. Prompt 작성 규칙

프롬프트는 다음 파일에 작성한다.

```text
app/prompts/mail_stage_classification_prompt.txt
```

프롬프트에는 반드시 다음 규칙이 포함되어야 한다.

```text
너는 채용 메일을 사용자가 정의한 전형 카테고리 중 하나로 분류하는 AI다.

규칙:
1. 반드시 제공된 user_stage_categories 중에서만 선택한다.
2. 새로운 카테고리나 새로운 ID를 만들지 않는다.
3. 메일 내용만 근거로 판단한다.
4. 특정 전형 단계가 명확하지 않으면 predicted_stage를 null로 반환한다.
5. confidence는 0.0 이상 1.0 이하로 반환한다.
6. evidence에는 메일 본문에 실제로 존재하는 짧은 문구만 넣는다.
7. needs_user_confirmation은 항상 true로 반환한다.
8. 출력은 반드시 JSON 객체로만 작성한다.
```

---

## 9. LLM 출력 JSON 형식

LLM은 반드시 아래 JSON 형식으로만 응답해야 한다.

```json
{
  "predicted_stage": {
    "id": 3,
    "name": "1차 면접",
    "order": 3
  },
  "confidence": 0.91,
  "reason": "분류 이유",
  "evidence": ["근거 문구 1", "근거 문구 2"],
  "needs_user_confirmation": true
}
```

분류가 어려운 경우:

```json
{
  "predicted_stage": null,
  "confidence": 0.25,
  "reason": "분류가 어려운 이유",
  "evidence": ["근거 문구"],
  "needs_user_confirmation": true
}
```

---

## 10. 서비스 구조

이 기능은 아래 파일들을 중심으로 구현한다.

```text
app/routers/mail_stage.py
app/schemas/mail_stage.py
app/services/mail_analysis/service.py
app/services/mail_analysis/classifier.py
app/prompts/mail_stage_classification_prompt.txt
```

역할:

```text
app/routers/mail_stage.py
- FastAPI Router 정의
- POST /ai/mail/stage-classify 엔드포인트 제공
- request를 service 계층으로 전달
- response_model을 사용해 응답 검증

app/schemas/mail_stage.py
- Request/Response Pydantic 모델 정의

app/services/mail_analysis/service.py
- 전체 메일 카테고리 추측 흐름 관리
- 입력 검증
- classifier 호출
- 최종 응답 검증

app/services/mail_analysis/classifier.py
- LLM 프롬프트 생성
- generate_json_with_llm 호출
- LLM 결과를 Pydantic Response 모델로 변환

app/prompts/mail_stage_classification_prompt.txt
- LLM 시스템 프롬프트 관리
```

---

## 11. Router 구현 요구사항

`app/routers/mail_stage.py`에는 다음 엔드포인트를 구현한다.

```python
from fastapi import APIRouter
from app.schemas.mail_stage import (
    MailStageClassifyRequest,
    MailStageClassifyResponse,
)
from app.services.mail_analysis.service import classify_mail_stage


router = APIRouter()


@router.post(
    "/stage-classify",
    response_model=MailStageClassifyResponse,
)
def classify_stage(request: MailStageClassifyRequest):
    return classify_mail_stage(request)
```

`app/main.py`에서는 다음과 같이 등록한다.

```python
from app.routers.mail_stage import router as mail_stage_router

app.include_router(
    mail_stage_router,
    prefix="/ai/mail",
    tags=["mail-stage"],
)
```

---

## 12. Service 구현 요구사항

`app/services/mail_analysis/service.py`는 전체 흐름을 담당한다.

필수 함수:

```python
from app.schemas.mail_stage import (
    MailStageClassifyRequest,
    MailStageClassifyResponse,
)
from app.services.mail_analysis.classifier import classify_with_llm


def classify_mail_stage(
    request: MailStageClassifyRequest,
) -> MailStageClassifyResponse:
    # TODO:
    # 1. mail_body가 비어 있지 않은지 확인
    # 2. user_stage_categories가 비어 있지 않은지 확인
    # 3. classify_with_llm 호출
    # 4. 응답이 제공된 카테고리 중 하나인지 검증
    # 5. 유효하지 않은 stage id가 반환되면 predicted_stage를 null로 처리
    # 6. 최종 MailStageClassifyResponse 반환
    pass
```

---

## 13. Classifier 구현 요구사항

`app/services/mail_analysis/classifier.py`는 LLM 호출을 담당한다.

필수 함수:

```python
from app.schemas.mail_stage import (
    MailStageClassifyRequest,
    MailStageClassifyResponse,
)


def classify_with_llm(
    request: MailStageClassifyRequest,
) -> MailStageClassifyResponse:
    # TODO:
    # 1. prompt 파일 로드
    # 2. user_stage_categories와 mail_body를 JSON 문자열로 구성
    # 3. generate_json_with_llm(system_prompt, user_prompt) 호출
    # 4. 결과 dict를 MailStageClassifyResponse로 변환
    # 5. 변환 실패 시 예외 발생
    pass
```

---

## 14. 후처리 검증 규칙

LLM 응답은 그대로 반환하지 않는다.

반드시 후처리 검증을 수행한다.

### 14.1 stage id 검증

LLM이 반환한 `predicted_stage.id`가 입력된 `user_stage_categories` 안에 존재하는지 확인한다.

존재하지 않으면 다음처럼 처리한다.

```json
{
  "predicted_stage": null,
  "confidence": 0.0,
  "reason": "LLM이 제공된 카테고리 목록에 없는 전형 단계를 반환했으므로 분류 결과를 무효 처리했습니다.",
  "evidence": [],
  "needs_user_confirmation": true
}
```

---

### 14.2 confidence 보정

`confidence`가 0.0보다 작으면 0.0으로 보정한다.  
`confidence`가 1.0보다 크면 1.0으로 보정한다.

---

### 14.3 evidence 개수 제한

`evidence`는 최대 3개까지만 반환한다.

각 evidence는 너무 길지 않게 유지한다.

권장:

```text
최대 100자
```

---

### 14.4 needs_user_confirmation 보정

MVP에서는 LLM 응답과 관계없이 항상 `true`로 설정한다.

---

## 15. 에러 처리

다음 상황을 처리한다.

| 상황 | 처리 |
|---|---|
| mail_body가 비어 있음 | 422 또는 400 |
| user_stage_categories가 비어 있음 | 422 또는 400 |
| LLM 호출 실패 | 502 |
| LLM JSON 파싱 실패 | 502 |
| LLM 응답 schema 검증 실패 | 502 |
| 유효하지 않은 stage id 반환 | predicted_stage null 처리 |

FastAPI 라우터에서 직접 복잡한 에러 처리를 하지 않는다.  
서비스 계층에서 의미 있는 예외를 발생시키고, 필요하면 공통 예외 처리로 변환한다.

---

## 16. 테스트 요구사항

`tests/test_mail_stage.py`에 테스트를 작성한다.

필수 테스트:

1. 면접 일정 메일을 `1차 면접`으로 분류한다.
2. 코딩테스트 안내 메일을 `코딩테스트`로 분류한다.
3. 서류 결과 안내 메일을 `서류 전형`으로 분류한다.
4. 모호한 메일은 `predicted_stage: null` 또는 낮은 confidence를 반환한다.
5. LLM이 제공되지 않은 stage id를 반환하면 무효 처리한다.
6. `needs_user_confirmation`은 항상 true다.
7. evidence는 최대 3개까지만 반환된다.
8. confidence는 0.0 이상 1.0 이하로 보정된다.

테스트에서는 실제 Ollama 호출을 하지 않는다.  
`generate_json_with_llm`을 mock 처리한다.

---

## 17. 구현 범위

이번 MVP에서 구현할 것:

- POST /ai/mail/stage-classify
- Pydantic request/response schema
- LLM 기반 동적 카테고리 분류
- 제공된 카테고리 안에서만 선택하는 검증 로직
- confidence, reason, evidence 반환
- needs_user_confirmation true 고정
- 테스트 코드

이번 MVP에서 구현하지 않을 것:

- 메일 원문 저장
- DB 저장
- 칸반 이동 실행
- 캘린더 일정 생성
- 사용자별 모델 학습
- Vector DB
- Fine-tuning
- 관리자 페이지

---

## 18. Codex 작업 지시 예시

Codex에게 이 기능만 구현시킬 때는 다음과 같이 지시한다.

```text
app/services/mail_analysis/AGENTS.md의 지침을 참고해서 메일 전형 카테고리 추측 API만 구현해줘.

구현 범위:
- POST /ai/mail/stage-classify
- app/schemas/mail_stage.py의 Pydantic 모델
- app/routers/mail_stage.py의 라우터
- app/services/mail_analysis/service.py
- app/services/mail_analysis/classifier.py
- app/prompts/mail_stage_classification_prompt.txt
- tests/test_mail_stage.py

주의사항:
- 사용자가 제공한 user_stage_categories 중 하나만 선택해야 해.
- 새로운 stage id나 stage name을 만들면 안 돼.
- 모호하면 predicted_stage를 null로 반환해야 해.
- confidence, reason, evidence, needs_user_confirmation을 반드시 포함해야 해.
- needs_user_confirmation은 MVP에서는 항상 true야.
- LLM 호출은 app/core/llm_client.py의 generate_json_with_llm 함수만 사용해야 해.
- 실제 Ollama 호출 테스트는 하지 말고, 테스트에서는 generate_json_with_llm을 mock 처리해줘.
- 다른 기능인 회고 질문 생성, 칸반 이동 추천 코드는 수정하지 마.
```

---

## 19. 완료 기준

이 기능은 다음 조건을 만족하면 완료된 것으로 본다.

- `/ai/mail/stage-classify` 엔드포인트가 동작한다.
- 요청으로 메일 본문과 사용자 정의 카테고리 목록을 받는다.
- 응답으로 predicted_stage, confidence, reason, evidence, needs_user_confirmation을 반환한다.
- LLM이 잘못된 stage id를 반환해도 안전하게 처리한다.
- 테스트에서 실제 Ollama를 호출하지 않는다.
- 모든 응답은 Pydantic schema를 통과한다.
