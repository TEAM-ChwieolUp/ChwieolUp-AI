from fastapi import APIRouter, HTTPException, status

from app.schemas.mail_stage import MailStageClassifyRequest, MailStageClassifyResponse
from app.services.mail_analysis.service import classify_mail_stage

router = APIRouter(prefix="/ai/mail", tags=["mail-stage"])


@router.post(
    "/stage-classify",
    response_model=MailStageClassifyResponse,
    status_code=status.HTTP_200_OK,
    summary="메일 전형 카테고리 추측",
    description=(
        "메일 제목과 본문을 바탕으로, 사용자가 정의한 전형 단계 목록 중 어떤 단계에 가장 가까운지 추측합니다.\n\n"
        "동작 방식:\n"
        "- 입력으로 들어온 `user_stage_categories` 안에서만 선택합니다.\n"
        "- 새 stage를 생성하지 않습니다.\n"
        "- 메일이 모호하면 `predicted_stage`는 `null`이 될 수 있습니다.\n"
        "- `evidence`에는 메일 원문에서 발췌한 짧은 근거 문구가 들어갑니다.\n"
        "- `needs_user_confirmation`은 MVP 정책상 항상 `true`입니다."
    ),
    responses={
        200: {
            "description": "메일 전형 분류 결과",
        },
        400: {
            "description": "잘못된 입력 또는 서비스 검증 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "user_stage_categories must not be empty."
                    }
                }
            },
        },
        422: {
            "description": "Pydantic 요청 스키마 검증 실패",
        },
    },
)
def classify_mail_stage_endpoint(
    request: MailStageClassifyRequest,
) -> MailStageClassifyResponse:
    try:
        return classify_mail_stage(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
