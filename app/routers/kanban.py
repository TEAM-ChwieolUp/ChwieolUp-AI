from fastapi import APIRouter, HTTPException, status

from app.schemas.kanban import KanbanMoveRecommendRequest, KanbanMoveRecommendResponse
from app.services.kanban.service import recommend_kanban_move


router = APIRouter(prefix="/ai/kanban", tags=["kanban"])


@router.post(
    "/move-recommend",
    response_model=KanbanMoveRecommendResponse,
    status_code=status.HTTP_200_OK,
    summary="칸반 이동 추천",
    description=(
        "메일 제목과 본문, 현재 칸반 단계, 사용자의 전체 칸반 단계 목록을 바탕으로 채용 카드를 다른 단계로 이동해야 하는지 추천합니다.\n\n"
        "동작 방식:\n"
        "- LLM은 `user_kanban_stages` 안에서만 이동 대상 단계를 고를 수 있습니다.\n"
        "- stage `description`도 단계 의미를 이해하는 보조 문맥으로 사용됩니다.\n"
        "- 서버는 현재 단계와 동일한 단계, 없는 단계, 낮은 confidence, 빈 evidence를 보수적으로 거절합니다.\n"
        "- `recommend_move`가 `false`이면 `to_stage`는 `null`로 정규화됩니다.\n"
        "- `needs_user_confirmation`은 MVP 정책상 항상 `true`입니다."
    ),
    responses={
        200: {
            "description": "칸반 이동 추천 결과",
        },
        400: {
            "description": "잘못된 입력 또는 서비스 검증 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "current_kanban_stage must exist in user_kanban_stages."
                    }
                }
            },
        },
        422: {
            "description": "Pydantic 요청 스키마 검증 실패",
        },
    },
)
def recommend_kanban_move_endpoint(
    request: KanbanMoveRecommendRequest,
) -> KanbanMoveRecommendResponse:
    try:
        return recommend_kanban_move(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
