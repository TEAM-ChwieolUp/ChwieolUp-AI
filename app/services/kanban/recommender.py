from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.llm_client import generate_json_with_llm
from app.schemas.kanban import KanbanMoveRecommendRequest, KanbanMoveRecommendResponse, KanbanStage


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "kanban_move_recommendation_prompt.txt"


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def _build_user_prompt(request: KanbanMoveRecommendRequest) -> str:
    payload = {
        "mail_subject": request.mail_subject,
        "mail_body": request.mail_body,
        "current_kanban_stage": request.current_kanban_stage.model_dump(),
        "user_kanban_stages": [stage.model_dump() for stage in request.user_kanban_stages],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _coerce_stage(raw_stage: Any) -> KanbanStage | None:
    if not isinstance(raw_stage, dict):
        return None

    try:
        return KanbanStage.model_validate(raw_stage)
    except Exception:
        return None


def recommend_kanban_move_with_llm(
    request: KanbanMoveRecommendRequest,
) -> KanbanMoveRecommendResponse:
    system_prompt = _load_system_prompt()
    user_prompt = _build_user_prompt(request)
    raw_response = generate_json_with_llm(system_prompt=system_prompt, user_prompt=user_prompt)

    return KanbanMoveRecommendResponse.model_construct(
        recommend_move=bool(raw_response.get("recommend_move", False)),
        from_stage=request.current_kanban_stage,
        to_stage=_coerce_stage(raw_response.get("to_stage")),
        confidence=raw_response.get("confidence", 0.0),
        reason=raw_response.get("reason", "메일 내용을 기반으로 칸반 이동 여부를 판단하기 어렵습니다."),
        evidence=raw_response.get("evidence", []),
        needs_user_confirmation=True,
    )
