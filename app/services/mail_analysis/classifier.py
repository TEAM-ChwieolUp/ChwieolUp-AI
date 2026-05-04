from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.llm_client import generate_json_with_llm
from app.schemas.mail_stage import MailStageClassifyRequest, MailStageClassifyResponse, PredictedStage


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "mail_stage_classification_prompt.txt"


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def _build_user_prompt(request: MailStageClassifyRequest) -> str:
    categories = [category.model_dump() for category in request.user_stage_categories]
    payload = {
        "mail_subject": request.mail_subject,
        "mail_body": request.mail_body,
        "user_stage_categories": categories,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _coerce_predicted_stage(raw_stage: Any) -> PredictedStage | None:
    if not isinstance(raw_stage, dict):
        return None

    try:
        return PredictedStage.model_validate(raw_stage)
    except Exception:
        return None


def classify_mail_stage_with_llm(request: MailStageClassifyRequest) -> MailStageClassifyResponse:
    system_prompt = _load_system_prompt()
    user_prompt = _build_user_prompt(request)
    raw_response = generate_json_with_llm(system_prompt=system_prompt, user_prompt=user_prompt)

    return MailStageClassifyResponse.model_construct(
        predicted_stage=_coerce_predicted_stage(raw_response.get("predicted_stage")),
        confidence=raw_response.get("confidence", 0.0),
        reason=raw_response.get("reason", "메일 내용을 기반으로 전형 단계를 판단하기 어렵습니다."),
        evidence=raw_response.get("evidence", []),
        needs_user_confirmation=True,
    )
