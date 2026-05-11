from fastapi import FastAPI

from app.routers.kanban import router as kanban_router
from app.routers.mail_stage import router as mail_stage_router
from app.routers.retrospective import router as retrospective_router


app = FastAPI(title="ChwieolUp AI Server")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(mail_stage_router)
app.include_router(retrospective_router)
app.include_router(kanban_router)
