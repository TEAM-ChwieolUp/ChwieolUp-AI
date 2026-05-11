from fastapi import APIRouter, HTTPException, status

from app.schemas.retrospective import RetrospectiveQuestionRequest, RetrospectiveQuestionResponse
from app.services.retrospective.service import generate_retrospective_questions


router = APIRouter(prefix="/ai/retrospective", tags=["retrospective"])


@router.post(
    "/questions",
    response_model=RetrospectiveQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="회고 질문 생성",
    description=(
        "채용공고명, 회사명, 직무명, 전형 단계명을 바탕으로 회고 작성에 도움이 되는 질문 세트를 생성합니다.\n\n"
        "동작 방식:\n"
        "- 서버가 먼저 템플릿 데이터에서 관련 질문 후보를 선별합니다.\n"
        "- LLM은 선별된 템플릿을 바탕으로 질문을 자연스럽게 재작성합니다.\n"
        "- 서버가 중복 질문 제거, 템플릿 출처 검증, 질문 개수 보정을 수행합니다.\n"
        "- `job_role`과 `process_stage`는 사용자가 실제로 쓰는 자유 텍스트 값을 그대로 받습니다."
    ),
    responses={
        200: {
            "description": "회고 질문 생성 결과",
        },
        400: {
            "description": "템플릿 매칭 실패 또는 서비스 검증 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No retrospective question templates matched the request."
                    }
                }
            },
        },
        422: {
            "description": "Pydantic 요청 스키마 검증 실패",
        },
    },
)
def generate_retrospective_questions_endpoint(
    request: RetrospectiveQuestionRequest,
) -> RetrospectiveQuestionResponse:
    try:
        return generate_retrospective_questions(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
