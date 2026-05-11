from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class KanbanStage(BaseModel):
    id: int
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    order: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank.")
        return stripped


class KanbanMoveRecommendRequest(BaseModel):
    mail_subject: str = ""
    mail_body: str = Field(..., min_length=1)
    current_kanban_stage: KanbanStage
    user_kanban_stages: list[KanbanStage] = Field(..., min_length=1)

    @field_validator("mail_subject", "mail_body")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class KanbanMoveRecommendResponse(BaseModel):
    recommend_move: bool
    from_stage: KanbanStage
    to_stage: Optional[KanbanStage] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., min_length=1)
    evidence: list[str] = Field(default_factory=list)
    needs_user_confirmation: bool
