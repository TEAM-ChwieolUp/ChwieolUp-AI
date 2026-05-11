from __future__ import annotations

import json
from pathlib import Path

from app.core.llm_client import generate_json_with_llm
from app.schemas.retrospective import (
    RetrospectiveQuestionItem,
    RetrospectiveQuestionRequest,
    RetrospectiveQuestionResponse,
    RetrospectiveQuestionTemplate,
)


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "retrospective_prompt.txt"


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def _priority_label(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"


def _build_user_prompt(
    request: RetrospectiveQuestionRequest,
    templates: list[RetrospectiveQuestionTemplate],
) -> str:
    payload = {
        "job_posting_title": request.job_posting_title,
        "company_name": request.company_name,
        "job_role": request.job_role,
        "process_stage": request.process_stage,
        "question_count": request.question_count,
        "selected_templates": [
            {
                "id": template.id,
                "question": template.question,
                "category": template.category,
                "intent": template.intent,
                "priority": _priority_label(template.priority),
                "tags": template.tags,
            }
            for template in templates
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def generate_retrospective_questions_with_llm(
    request: RetrospectiveQuestionRequest,
    templates: list[RetrospectiveQuestionTemplate],
) -> RetrospectiveQuestionResponse:
    system_prompt = _load_system_prompt()
    user_prompt = _build_user_prompt(request, templates)
    raw_response = generate_json_with_llm(system_prompt=system_prompt, user_prompt=user_prompt)

    raw_questions = raw_response.get("questions", [])
    questions: list[RetrospectiveQuestionItem] = []
    if isinstance(raw_questions, list):
        for item in raw_questions:
            if not isinstance(item, dict):
                continue
            try:
                questions.append(RetrospectiveQuestionItem.model_validate(item))
            except Exception:
                continue

    return RetrospectiveQuestionResponse.model_construct(
        question_set_title=raw_response.get("question_set_title", ""),
        job_role=raw_response.get("job_role", request.job_role),
        process_stage=raw_response.get("process_stage", request.process_stage),
        questions=questions,
    )
