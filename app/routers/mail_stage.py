from fastapi import APIRouter, HTTPException, status

from app.schemas.mail_stage import MailStageClassifyRequest, MailStageClassifyResponse
from app.services.mail_analysis.service import classify_mail_stage

router = APIRouter(prefix="/ai/mail", tags=["mail-stage"])


@router.post(
    "/stage-classify",
    response_model=MailStageClassifyResponse,
    status_code=status.HTTP_200_OK,
)
def classify_mail_stage_endpoint(
    request: MailStageClassifyRequest,
) -> MailStageClassifyResponse:
    try:
        return classify_mail_stage(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
