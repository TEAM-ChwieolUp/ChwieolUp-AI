from __future__ import annotations

from app.schemas.kanban import KanbanMoveRecommendRequest, KanbanMoveRecommendResponse
from app.services.kanban.recommender import recommend_kanban_move_with_llm
from app.services.kanban.validator import (
    build_stage_index,
    clamp_confidence,
    normalize_evidence,
    normalize_reason,
    normalize_stage,
    should_recommend_move,
)


def _validate_request(request: KanbanMoveRecommendRequest) -> None:
    if not request.mail_body.strip():
        raise ValueError("mail_body must not be blank.")
    if not request.user_kanban_stages:
        raise ValueError("user_kanban_stages must not be empty.")

    stage_index = build_stage_index(request.user_kanban_stages)
    if request.current_kanban_stage.id not in stage_index:
        raise ValueError("current_kanban_stage must exist in user_kanban_stages.")


def recommend_kanban_move(request: KanbanMoveRecommendRequest) -> KanbanMoveRecommendResponse:
    _validate_request(request)

    llm_response = recommend_kanban_move_with_llm(request)
    stage_index = build_stage_index(request.user_kanban_stages)
    normalized_to_stage = normalize_stage(llm_response.to_stage, stage_index)
    confidence = clamp_confidence(llm_response.confidence)
    evidence = normalize_evidence(llm_response.evidence)
    recommend_move = should_recommend_move(
        llm_response.recommend_move,
        normalized_to_stage,
        request.current_kanban_stage,
        confidence,
        evidence,
    )

    return KanbanMoveRecommendResponse(
        recommend_move=recommend_move,
        from_stage=request.current_kanban_stage,
        to_stage=normalized_to_stage if recommend_move else None,
        confidence=confidence,
        reason=normalize_reason(llm_response.reason, recommend_move),
        evidence=evidence,
        needs_user_confirmation=True,
    )
