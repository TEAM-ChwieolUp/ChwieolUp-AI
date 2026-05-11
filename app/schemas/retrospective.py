from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


QuestionPriority = Literal["high", "medium", "low"]


class RetrospectiveQuestionRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "job_posting_title": "카카오 백엔드 개발자 채용",
                "company_name": "카카오",
                "job_role": "백엔드 개발자",
                "process_stage": "1차 기술면접",
                "question_count": 4,
            }
        }
    )

    user_id: int | None = None
    job_posting_title: str = Field(
        ...,
        min_length=1,
        description="사용자가 지원한 채용공고명입니다.",
        examples=["카카오 백엔드 개발자 채용"],
    )
    company_name: str = Field(
        ...,
        min_length=1,
        description="지원 회사명입니다.",
        examples=["카카오"],
    )
    job_role: str = Field(
        ...,
        min_length=1,
        description="사용자가 실제로 인식하는 직무명입니다. 정규화 코드가 아니라 자유 텍스트입니다.",
        examples=["백엔드 개발자"],
    )
    process_stage: str = Field(
        ...,
        min_length=1,
        description="사용자가 실제로 쓰는 전형 단계명입니다. 템플릿 별칭과의 매칭에 사용됩니다.",
        examples=["1차 기술면접"],
    )
    question_count: int = Field(
        default=5,
        ge=1,
        le=10,
        description="생성할 회고 질문 개수입니다. 현재 1~10 범위만 허용합니다.",
    )

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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "technical_depth",
                "question": "카카오 백엔드 기술면접에서 가장 답변이 부족했던 기술 개념은 무엇이었나요?",
                "reason": "기술 보완 포인트를 찾기 위함입니다.",
                "priority": "high",
                "source_template_ids": ["q_backend_interview_001"],
            }
        }
    )

    category: str = Field(..., min_length=1, description="질문 카테고리입니다.")
    question: str = Field(..., min_length=1, description="사용자에게 보여줄 실제 회고 질문 문장입니다.")
    reason: str = Field(..., min_length=1, description="왜 이 질문이 포함되었는지에 대한 설명입니다.")
    priority: QuestionPriority = Field(..., description="질문의 우선순위입니다. high, medium, low 중 하나입니다.")
    source_template_ids: list[str] = Field(
        ...,
        min_length=1,
        description="이 질문이 어떤 템플릿에서 유래했는지 나타내는 템플릿 ID 목록입니다.",
    )

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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_set_title": "1차 기술면접 회고 질문",
                "job_role": "백엔드 개발자",
                "process_stage": "1차 기술면접",
                "questions": [
                    {
                        "category": "technical_depth",
                        "question": "카카오 백엔드 기술면접에서 가장 답변이 부족했던 기술 개념은 무엇이었나요?",
                        "reason": "기술 보완 포인트를 찾기 위함입니다.",
                        "priority": "high",
                        "source_template_ids": ["q_backend_interview_001"],
                    },
                    {
                        "category": "system_design",
                        "question": "시스템 설계 질문을 받았을 때 어떤 가정을 더 분명하게 설명했어야 했나요?",
                        "reason": "설계 사고 과정을 회고하기 위함입니다.",
                        "priority": "high",
                        "source_template_ids": ["q_backend_interview_002"],
                    },
                ],
            }
        }
    )

    question_set_title: str = Field(
        ...,
        min_length=1,
        description="회고 질문 세트의 제목입니다. 일반적으로 '{process_stage} 회고 질문' 형태로 생성됩니다.",
    )
    job_role: str = Field(..., min_length=1, description="요청에 들어온 직무명입니다.")
    process_stage: str = Field(..., min_length=1, description="요청에 들어온 전형 단계명입니다.")
    questions: list[RetrospectiveQuestionItem] = Field(
        ...,
        min_length=1,
        description="생성된 회고 질문 목록입니다.",
    )

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
