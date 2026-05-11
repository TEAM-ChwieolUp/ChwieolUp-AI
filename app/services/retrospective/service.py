from __future__ import annotations

from app.schemas.retrospective import RetrospectiveQuestionRequest, RetrospectiveQuestionResponse
from app.services.retrospective.generator import generate_retrospective_questions_with_llm
from app.services.retrospective.retriever import select_retrospective_templates
from app.services.retrospective.template_loader import load_retrospective_templates
from app.services.retrospective.validator import validate_retrospective_response


def generate_retrospective_questions(
    request: RetrospectiveQuestionRequest,
) -> RetrospectiveQuestionResponse:
    templates = load_retrospective_templates()
    selected_templates = select_retrospective_templates(request, templates)
    if not selected_templates:
        raise ValueError("No retrospective question templates matched the request.")
    llm_response = generate_retrospective_questions_with_llm(request, selected_templates)
    return validate_retrospective_response(request, llm_response, selected_templates)
