# AI Server

현재 디렉토리는 FastAPI 기반 AI 서버의 초기 골격만 생성된 상태입니다.

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

- `/health` 엔드포인트만 포함된 최소 FastAPI 앱이 준비되어 있습니다.
- LLM 호출은 이후 `app/core/llm_client.py`의 `generate_json_with_llm(system_prompt, user_prompt)`만 통해 수행하도록 유지합니다.
- 나머지 파일은 이후 구현을 위한 placeholder와 TODO 주석만 포함합니다.
