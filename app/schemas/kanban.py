from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class KanbanStage(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 4,
                "name": "최종 면접",
                "description": "임원 또는 최종 인터뷰",
                "order": 4,
            }
        }
    )

    id: int
    name: str = Field(..., min_length=1, description="사용자가 정의한 칸반 단계명입니다.")
    description: Optional[str] = Field(
        default=None,
        description="단계에 대한 보조 설명입니다. LLM이 단계 의미를 이해하는 데 사용됩니다.",
    )
    order: Optional[int] = Field(default=None, description="칸반 단계 순서입니다.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank.")
        return stripped


class KanbanMoveRecommendRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mail_subject": "[카카오] 최종 인터뷰 일정 안내",
                "mail_body": "안녕하세요. 최종 인터뷰 일정을 안내드립니다.",
                "current_kanban_stage": {
                    "id": 2,
                    "name": "코딩테스트",
                    "description": "온라인 코딩테스트",
                    "order": 2,
                },
                "user_kanban_stages": [
                    {
                        "id": 1,
                        "name": "서류",
                        "description": "지원서 제출 및 서류 심사 단계",
                        "order": 1,
                    },
                    {
                        "id": 2,
                        "name": "코딩테스트",
                        "description": "온라인 코딩테스트",
                        "order": 2,
                    },
                    {
                        "id": 3,
                        "name": "1차 면접",
                        "description": "실무진 면접",
                        "order": 3,
                    },
                    {
                        "id": 4,
                        "name": "최종 면접",
                        "description": "임원 또는 최종 인터뷰",
                        "order": 4,
                    },
                ],
            }
        }
    )

    mail_subject: str = Field(
        default="",
        description="메일 제목입니다. 비어 있어도 되지만, 이동 추천 정확도 향상에 도움이 됩니다.",
        examples=["[카카오] 최종 인터뷰 일정 안내"],
    )
    mail_body: str = Field(
        ...,
        min_length=1,
        description="메일 본문입니다. 칸반 이동 추천 판단의 핵심 입력입니다.",
        examples=["안녕하세요. 최종 인터뷰 일정을 안내드립니다."],
    )
    current_kanban_stage: KanbanStage = Field(
        ...,
        description="현재 채용 카드가 위치한 칸반 단계입니다. 반드시 user_kanban_stages 안에 포함되어야 합니다.",
    )
    user_kanban_stages: list[KanbanStage] = Field(
        ...,
        min_length=1,
        description="사용자가 정의한 전체 칸반 단계 목록입니다. AI는 반드시 이 목록 안에서만 이동 대상을 선택해야 합니다.",
    )

    @field_validator("mail_subject", "mail_body")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class KanbanMoveRecommendResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "recommend_move": True,
                    "from_stage": {
                        "id": 2,
                        "name": "코딩테스트",
                        "description": "온라인 코딩테스트",
                        "order": 2,
                    },
                    "to_stage": {
                        "id": 4,
                        "name": "최종 면접",
                        "description": "임원 또는 최종 인터뷰",
                        "order": 4,
                    },
                    "confidence": 0.88,
                    "reason": "메일 본문에 최종 인터뷰 일정이 명시되어 있습니다.",
                    "evidence": ["최종 인터뷰 일정을 안내드립니다"],
                    "needs_user_confirmation": True,
                },
                {
                    "recommend_move": False,
                    "from_stage": {
                        "id": 3,
                        "name": "1차 면접",
                        "description": "실무진 면접",
                        "order": 3,
                    },
                    "to_stage": None,
                    "confidence": 0.42,
                    "reason": "메일 내용이 현재 단계와 동일하거나 이동 근거가 충분하지 않습니다.",
                    "evidence": ["추후 다시 안내드리겠습니다"],
                    "needs_user_confirmation": True,
                },
            ]
        }
    )

    recommend_move: bool = Field(
        ...,
        description="현재 칸반 단계를 다른 단계로 이동하라고 추천하는지 여부입니다.",
    )
    from_stage: KanbanStage = Field(..., description="현재 칸반 단계입니다.")
    to_stage: Optional[KanbanStage] = Field(
        default=None,
        description="이동 추천 대상 단계입니다. recommend_move가 false이면 null입니다.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="이동 추천 판단에 대한 신뢰도입니다. 0.0~1.0 사이 값으로 반환됩니다.",
    )
    reason: str = Field(..., min_length=1, description="왜 이동 추천 또는 비추천을 했는지에 대한 설명입니다.")
    evidence: list[str] = Field(
        default_factory=list,
        description="메일 제목 또는 본문에서 직접 발췌한 근거 문구 목록입니다. 최대 3개까지 반환됩니다.",
    )
    needs_user_confirmation: bool = Field(
        ...,
        description="MVP 정책상 항상 true입니다. 실제 칸반 이동 전 사용자 확인이 필요함을 의미합니다.",
    )
