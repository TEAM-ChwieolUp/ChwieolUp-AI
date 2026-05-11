from __future__ import annotations

from app.schemas.kanban import KanbanMoveRecommendResponse, KanbanStage


def build_stage_index(stages: list[KanbanStage]) -> dict[int, KanbanStage]:
    return {stage.id: stage for stage in stages}


def clamp_confidence(value: float) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        numeric_value = 0.0
    return max(0.0, min(1.0, numeric_value))


def normalize_evidence(evidence: list[str]) -> list[str]:
    normalized: list[str] = []
    for item in evidence:
        if not isinstance(item, str):
            continue
        stripped = item.strip()
        if not stripped:
            continue
        normalized.append(stripped)
        if len(normalized) == 3:
            break
    return normalized


def normalize_stage(
    stage: KanbanStage | None,
    stage_index: dict[int, KanbanStage],
) -> KanbanStage | None:
    if stage is None:
        return None

    matched_stage = stage_index.get(stage.id)
    if matched_stage is None:
        return None

    return KanbanStage(
        id=matched_stage.id,
        name=matched_stage.name,
        description=matched_stage.description,
        order=matched_stage.order,
    )


def should_recommend_move(
    recommend_move: bool,
    to_stage: KanbanStage | None,
    current_stage: KanbanStage,
    confidence: float,
    evidence: list[str],
) -> bool:
    if not recommend_move:
        return False
    if to_stage is None:
        return False
    if to_stage.id == current_stage.id:
        return False
    if confidence < 0.7:
        return False
    if not evidence:
        return False
    return True


def normalize_reason(reason: str, recommend_move: bool) -> str:
    stripped = str(reason).strip()
    if stripped:
        return stripped
    if recommend_move:
        return "메일 내용을 기반으로 현재 단계에서 다른 칸반 단계로 이동하는 것이 적절하다고 판단했습니다."
    return "메일 내용을 기반으로 현재 단계에서 별도의 칸반 이동은 필요하지 않다고 판단했습니다."
