from fastapi import APIRouter, HTTPException, status

from app.schemas.kanban import KanbanMoveRecommendRequest, KanbanMoveRecommendResponse
from app.services.kanban.service import recommend_kanban_move


router = APIRouter(prefix="/ai/kanban", tags=["kanban"])


@router.post(
    "/move-recommend",
    response_model=KanbanMoveRecommendResponse,
    status_code=status.HTTP_200_OK,
)
def recommend_kanban_move_endpoint(
    request: KanbanMoveRecommendRequest,
) -> KanbanMoveRecommendResponse:
    try:
        return recommend_kanban_move(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
