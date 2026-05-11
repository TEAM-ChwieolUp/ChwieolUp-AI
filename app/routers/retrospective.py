from fastapi import APIRouter, HTTPException, status

from app.schemas.retrospective import RetrospectiveQuestionRequest, RetrospectiveQuestionResponse
from app.services.retrospective.service import generate_retrospective_questions


router = APIRouter(prefix="/ai/retrospective", tags=["retrospective"])


@router.post(
    "/questions",
    response_model=RetrospectiveQuestionResponse,
    status_code=status.HTTP_200_OK,
)
def generate_retrospective_questions_endpoint(
    request: RetrospectiveQuestionRequest,
) -> RetrospectiveQuestionResponse:
    try:
        return generate_retrospective_questions(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
