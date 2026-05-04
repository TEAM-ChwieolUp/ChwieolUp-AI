from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class UserStageCategory(BaseModel):
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


class MailStageClassifyRequest(BaseModel):
    mail_subject: str = ""
    mail_body: str = Field(..., min_length=1)
    user_stage_categories: list[UserStageCategory] = Field(..., min_length=1)

    @field_validator("mail_subject", "mail_body")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class PredictedStage(BaseModel):
    id: int
    name: str = Field(..., min_length=1)
    order: Optional[int] = None


class MailStageClassifyResponse(BaseModel):
    predicted_stage: Optional[PredictedStage] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., min_length=1)
    evidence: list[str] = Field(default_factory=list)
    needs_user_confirmation: bool
