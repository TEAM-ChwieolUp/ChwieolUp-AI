from __future__ import annotations

from app.schemas.mail_stage import (
    MailStageClassifyRequest,
    MailStageClassifyResponse,
    PredictedStage,
    UserStageCategory,
)
from app.services.mail_analysis.classifier import classify_mail_stage_with_llm


def _validate_request(request: MailStageClassifyRequest) -> None:
    if not request.mail_body.strip():
        raise ValueError("mail_body must not be blank.")
    if not request.user_stage_categories:
        raise ValueError("user_stage_categories must not be empty.")


def _build_stage_index(categories: list[UserStageCategory]) -> dict[int, UserStageCategory]:
    return {category.id: category for category in categories}


def _clamp_confidence(value: float) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        numeric_value = 0.0
    return max(0.0, min(1.0, numeric_value))


def _normalize_evidence(evidence: list[str]) -> list[str]:
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


def _normalize_predicted_stage(
    predicted_stage: PredictedStage | None,
    stage_index: dict[int, UserStageCategory],
) -> PredictedStage | None:
    if predicted_stage is None:
        return None

    matched_stage = stage_index.get(predicted_stage.id)
    if matched_stage is None:
        return None

    return PredictedStage(
        id=matched_stage.id,
        name=matched_stage.name,
        order=matched_stage.order,
    )


def classify_mail_stage(request: MailStageClassifyRequest) -> MailStageClassifyResponse:
    _validate_request(request)

    llm_response = classify_mail_stage_with_llm(request)
    stage_index = _build_stage_index(request.user_stage_categories)

    return MailStageClassifyResponse(
        predicted_stage=_normalize_predicted_stage(llm_response.predicted_stage, stage_index),
        confidence=_clamp_confidence(llm_response.confidence),
        reason=str(llm_response.reason).strip() or "메일 내용을 기반으로 전형 단계를 판단하기 어렵습니다.",
        evidence=_normalize_evidence(llm_response.evidence),
        needs_user_confirmation=True,
    )
