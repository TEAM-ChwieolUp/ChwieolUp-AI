from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


QuestionPriority = Literal["high", "medium", "low"]


class RetrospectiveQuestionRequest(BaseModel):
    user_id: int | None = None
    job_posting_title: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    job_role: str = Field(..., min_length=1)
    process_stage: str = Field(..., min_length=1)
    question_count: int = Field(default=5, ge=1, le=10)

    @field_validator(
        "job_posting_title",
        "company_name",
        "job_role",
        "process_stage",
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be blank.")
        return stripped


class RetrospectiveQuestionItem(BaseModel):
    category: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    priority: QuestionPriority
    source_template_ids: list[str] = Field(..., min_length=1)

    @field_validator("category", "question", "reason")
    @classmethod
    def strip_item_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be blank.")
        return stripped

    @field_validator("source_template_ids")
    @classmethod
    def validate_template_ids(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if not normalized:
            raise ValueError("source_template_ids must not be empty.")
        return normalized


class RetrospectiveQuestionResponse(BaseModel):
    question_set_title: str = Field(..., min_length=1)
    job_role: str = Field(..., min_length=1)
    process_stage: str = Field(..., min_length=1)
    questions: list[RetrospectiveQuestionItem] = Field(..., min_length=1)

    @field_validator("question_set_title", "job_role", "process_stage")
    @classmethod
    def strip_response_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be blank.")
        return stripped


class RetrospectiveQuestionTemplate(BaseModel):
    id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    role_category: list[str] = Field(..., min_length=1)
    process_stage: list[str] = Field(..., min_length=1)
    intent: str = Field(..., min_length=1)
    priority: float = Field(..., ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)

    @field_validator("id", "question", "category", "intent")
    @classmethod
    def strip_template_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be blank.")
        return stripped

    @field_validator("role_category", "process_stage", "tags")
    @classmethod
    def normalize_string_lists(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if value and not normalized:
            raise ValueError("string list must include at least one non-blank value.")
        return normalized
