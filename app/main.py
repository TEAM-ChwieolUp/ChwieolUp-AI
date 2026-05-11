from fastapi import FastAPI

from app.routers.kanban import router as kanban_router
from app.routers.mail_stage import router as mail_stage_router
from app.routers.retrospective import router as retrospective_router


app = FastAPI(
    title="ChwieolUp AI Server",
    summary="취얼업 AI 서버 OpenAPI 문서",
    description=(
        "취얼업(ChwieolUp) 취업 준비 플랫폼에서 사용하는 FastAPI 기반 AI 서버입니다.\n\n"
        "현재 제공 기능:\n"
        "- 메일 전형 카테고리 추측\n"
        "- 회고 질문 생성\n"
        "- 칸반 이동 추천\n\n"
        "공통 정책:\n"
        "- 모든 AI 응답은 JSON parsing 및 서버 후처리를 거칩니다.\n"
        "- 추천성 응답은 가능한 경우 confidence, reason, evidence를 포함합니다.\n"
        "- 자동 실행은 하지 않으며, 추천 결과는 사용자 확인 후 적용해야 합니다."
    ),
    version="0.1.0",
)


@app.get(
    "/health",
    summary="헬스 체크",
    description="서버 프로세스가 정상 기동 중인지 확인합니다.",
)
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(mail_stage_router)
app.include_router(retrospective_router)
app.include_router(kanban_router)
