from __future__ import annotations

import re

from app.schemas.retrospective import (
    RetrospectiveQuestionItem,
    RetrospectiveQuestionRequest,
    RetrospectiveQuestionResponse,
    RetrospectiveQuestionTemplate,
)


def _priority_label(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"


def _normalize_question_text(value: str) -> str:
    return re.sub(r"[\W_]+", "", value).lower()


def _default_question_set_title(request: RetrospectiveQuestionRequest) -> str:
    return f"{request.process_stage} 회고 질문"


def _template_index(
    templates: list[RetrospectiveQuestionTemplate],
) -> dict[str, RetrospectiveQuestionTemplate]:
    return {template.id: template for template in templates}


def _normalize_source_template_ids(
    source_template_ids: list[str],
    valid_template_ids: set[str],
) -> list[str]:
    normalized: list[str] = []
    for template_id in source_template_ids:
        stripped = template_id.strip()
        if not stripped or stripped not in valid_template_ids or stripped in normalized:
            continue
        normalized.append(stripped)
    return normalized


def _deduplicate_questions(
    questions: list[RetrospectiveQuestionItem],
    valid_template_ids: set[str],
) -> list[RetrospectiveQuestionItem]:
    deduplicated: list[RetrospectiveQuestionItem] = []
    seen_questions: set[str] = set()

    for question in questions:
        normalized_question = _normalize_question_text(question.question)
        if not normalized_question or normalized_question in seen_questions:
            continue

        normalized_source_ids = _normalize_source_template_ids(
            question.source_template_ids,
            valid_template_ids,
        )
        if not normalized_source_ids:
            continue

        deduplicated.append(
            RetrospectiveQuestionItem(
                category=question.category,
                question=question.question,
                reason=question.reason,
                priority=question.priority,
                source_template_ids=normalized_source_ids,
            )
        )
        seen_questions.add(normalized_question)

    return deduplicated


def _build_fallback_question(template: RetrospectiveQuestionTemplate) -> RetrospectiveQuestionItem:
    return RetrospectiveQuestionItem(
        category=template.category,
        question=template.question,
        reason=template.intent,
        priority=_priority_label(template.priority),
        source_template_ids=[template.id],
    )


def validate_retrospective_response(
    request: RetrospectiveQuestionRequest,
    llm_response: RetrospectiveQuestionResponse,
    selected_templates: list[RetrospectiveQuestionTemplate],
) -> RetrospectiveQuestionResponse:
    if not selected_templates:
        raise ValueError("No retrospective question templates matched the request.")

    template_index = _template_index(selected_templates)
    valid_template_ids = set(template_index)
    questions = _deduplicate_questions(llm_response.questions, valid_template_ids)

    used_template_ids = {
        template_id
        for question in questions
        for template_id in question.source_template_ids
    }
    for template in selected_templates:
        if len(questions) >= request.question_count:
            break
        if template.id in used_template_ids:
            continue

        fallback_question = _build_fallback_question(template)
        normalized_question = _normalize_question_text(fallback_question.question)
        if any(_normalize_question_text(item.question) == normalized_question for item in questions):
            continue
        questions.append(fallback_question)
        used_template_ids.add(template.id)

    if not questions:
        raise ValueError("Failed to generate retrospective questions.")

    final_response = RetrospectiveQuestionResponse(
        question_set_title=(
            llm_response.question_set_title.strip()
            if isinstance(llm_response.question_set_title, str) and llm_response.question_set_title.strip()
            else _default_question_set_title(request)
        ),
        job_role=request.job_role,
        process_stage=request.process_stage,
        questions=questions[: request.question_count],
    )
    return final_response
