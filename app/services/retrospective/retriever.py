from __future__ import annotations

import re

from app.schemas.retrospective import RetrospectiveQuestionRequest, RetrospectiveQuestionTemplate


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _tokenize(value: str) -> set[str]:
    normalized = _normalize_text(value)
    normalized = re.sub(r"[^\w\s가-힣]", " ", normalized)
    return {token for token in normalized.split() if token}


def _match_dimension(values: list[str], target: str) -> tuple[bool, int]:
    normalized_target = _normalize_text(target)
    target_tokens = _tokenize(target)

    best_score = 0
    for value in values:
        normalized_value = _normalize_text(value)
        if normalized_target == normalized_value:
            return True, 3
        if normalized_value == "all":
            best_score = max(best_score, 1)
            continue
        if normalized_value and (
            normalized_target in normalized_value or normalized_value in normalized_target
        ):
            best_score = max(best_score, 2)
            continue

        value_tokens = _tokenize(value)
        if target_tokens and value_tokens and target_tokens.intersection(value_tokens):
            best_score = max(best_score, 2)

    if best_score > 0:
        return True, best_score
    return False, 0


def _template_sort_key(
    template: RetrospectiveQuestionTemplate,
    request: RetrospectiveQuestionRequest,
) -> tuple[int, float, str]:
    _, role_score = _match_dimension(template.role_category, request.job_role)
    _, stage_score = _match_dimension(template.process_stage, request.process_stage)
    return (role_score + stage_score, template.priority, template.id)


def select_retrospective_templates(
    request: RetrospectiveQuestionRequest,
    templates: list[RetrospectiveQuestionTemplate],
) -> list[RetrospectiveQuestionTemplate]:
    matched_templates: list[RetrospectiveQuestionTemplate] = []
    for template in templates:
        role_matched, _ = _match_dimension(template.role_category, request.job_role)
        stage_matched, _ = _match_dimension(template.process_stage, request.process_stage)
        if role_matched and stage_matched:
            matched_templates.append(template)

    matched_templates.sort(
        key=lambda template: _template_sort_key(template, request),
        reverse=True,
    )

    candidate_count = min(max(request.question_count * 2, 8), 15)
    return matched_templates[:candidate_count]
