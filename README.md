# AI Server

현재 디렉토리는 FastAPI 기반 AI 서버의 MVP 기능을 구현 중인 상태입니다.

현재 LLM 연동 대상은 서버 내부 Ollama HTTP API이며, 기본 모델은 `gemma4:e2b`입니다.

## 구조

- `app/`: 애플리케이션 소스 코드
- `app/core/`: 설정, Ollama LLM 클라이언트, 공통 에러 정의
- `app/routers/`: API 라우터 정의 위치
- `app/schemas/`: 요청/응답 Pydantic 스키마 정의 위치
- `app/services/`: 기능별 비즈니스 로직 계층 위치
- `app/data/`: 정적 데이터 파일 위치
- `app/prompts/`: LLM 프롬프트 템플릿 위치
- `tests/`: 테스트 코드 위치

## 현재 상태

- `GET /health`
- `POST /ai/mail/stage-classify`
- `POST /ai/retrospective/questions`
- LLM 호출은 `app/core/llm_client.py`의 `generate_json_with_llm(system_prompt, user_prompt)`만 사용합니다.

## Mail Stage Classify API

`POST /ai/mail/stage-classify`

메일 본문과 사용자가 정의한 전형 카테고리 목록을 받아, 가장 가까운 전형 단계를 추측합니다.

```bash
curl -X POST http://localhost:8001/ai/mail/stage-classify \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

예상 응답 형식:

```json
{
  "predicted_stage": {
    "id": 3,
    "name": "1차 면접",
    "order": 3
  },
  "confidence": 0.91,
  "reason": "메일 본문에 1차 기술 인터뷰 일정이 명시되어 있어 1차 면접 단계와 가장 가깝습니다.",
  "evidence": [
    "1차 기술 인터뷰 일정을 안내드립니다"
  ],
  "needs_user_confirmation": true
}
```

## Retrospective Questions API

`POST /ai/retrospective/questions`

채용공고명, 회사명, 직무, 전형 단계에 맞춰 회고 질문 세트를 생성합니다.

```bash
curl -X POST http://localhost:8001/ai/retrospective/questions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "job_posting_title": "카카오 백엔드 개발자 채용",
    "company_name": "카카오",
    "job_role": "백엔드 개발자",
    "process_stage": "1차 기술면접",
    "question_count": 4
  }'
```

예상 응답 형식:

```json
{
  "question_set_title": "1차 기술면접 회고 질문",
  "job_role": "백엔드 개발자",
  "process_stage": "1차 기술면접",
  "questions": [
    {
      "category": "technical_depth",
      "question": "카카오 백엔드 기술면접에서 가장 답변이 부족했던 기술 개념은 무엇이었나요?",
      "reason": "기술 보완 포인트를 찾기 위함입니다.",
      "priority": "high",
      "source_template_ids": ["q_backend_interview_001"]
    }
  ]
}
```
