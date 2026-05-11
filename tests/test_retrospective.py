from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.schemas.retrospective import (
    RetrospectiveQuestionRequest,
    RetrospectiveQuestionResponse,
    RetrospectiveQuestionTemplate,
)
from app.services.retrospective.retriever import select_retrospective_templates
from app.services.retrospective.service import generate_retrospective_questions


client = TestClient(app)


def build_request() -> dict:
    return {
        "user_id": 1,
        "job_posting_title": "카카오 백엔드 개발자 채용",
        "company_name": "카카오",
        "job_role": "백엔드 개발자",
        "process_stage": "1차 기술면접",
        "question_count": 4,
    }


def build_templates() -> list[RetrospectiveQuestionTemplate]:
    raw_templates = [
        {
            "id": "exact_high",
            "question": "백엔드 기술 개념 중 가장 취약했던 부분은 무엇이었나요?",
            "category": "technical_depth",
            "role_category": ["backend", "백엔드", "백엔드 개발자"],
            "process_stage": ["technical_interview", "기술면접", "1차 기술면접", "실무 면접"],
            "intent": "기술 보완 포인트를 찾기 위한 질문",
            "priority": 0.95,
            "tags": ["backend"],
        },
        {
            "id": "exact_medium",
            "question": "시스템 설계 질문에서 어려웠던 지점은 무엇이었나요?",
            "category": "system_design",
            "role_category": ["backend", "백엔드", "백엔드 개발자"],
            "process_stage": ["technical_interview", "기술면접", "1차 기술면접", "실무 면접"],
            "intent": "설계 사고 과정을 회고하기 위한 질문",
            "priority": 0.84,
            "tags": ["backend"],
        },
        {
            "id": "role_all",
            "question": "이번 전형 준비 과정에서 가장 효과적이었던 전략은 무엇이었나요?",
            "category": "preparation",
            "role_category": ["backend", "백엔드", "백엔드 개발자"],
            "process_stage": ["all"],
            "intent": "재사용 가능한 준비 전략을 정리하기 위한 질문",
            "priority": 0.8,
            "tags": ["backend"],
        },
        {
            "id": "all_stage",
            "question": "실제 질문과 예상 질문 사이의 차이는 무엇이었나요?",
            "category": "expectation_gap",
            "role_category": ["all"],
            "process_stage": ["technical_interview", "기술면접", "1차 기술면접", "실무 면접"],
            "intent": "예상과 실제의 차이를 돌아보기 위한 질문",
            "priority": 0.78,
            "tags": ["all"],
        },
        {
            "id": "all_all",
            "question": "다음 지원에서 바꾸고 싶은 점은 무엇인가요?",
            "category": "improvement",
            "role_category": ["all"],
            "process_stage": ["all"],
            "intent": "다음 액션을 정리하기 위한 질문",
            "priority": 0.7,
            "tags": ["all"],
        },
        {
            "id": "frontend_irrelevant",
            "question": "프론트엔드 구현에서 가장 어려웠던 점은 무엇이었나요?",
            "category": "technical_depth",
            "role_category": ["frontend"],
            "process_stage": ["technical_interview", "기술면접"],
            "intent": "다른 직무 템플릿",
            "priority": 0.99,
            "tags": ["frontend"],
        },
    ]
    return [RetrospectiveQuestionTemplate.model_validate(item) for item in raw_templates]


def test_template_selection_prefers_exact_matches_and_keeps_wildcards() -> None:
    request = RetrospectiveQuestionRequest.model_validate(build_request())

    selected = select_retrospective_templates(request, build_templates())

    assert [template.id for template in selected[:5]] == [
        "exact_high",
        "exact_medium",
        "role_all",
        "all_stage",
        "all_all",
    ]


def test_template_selection_matches_user_defined_stage_text() -> None:
    payload = build_request()
    payload["process_stage"] = "실무 면접"
    request = RetrospectiveQuestionRequest.model_validate(payload)

    selected = select_retrospective_templates(request, build_templates())

    assert selected[0].id == "exact_high"


def test_service_returns_requested_question_count_with_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        assert "selected_templates" in user_prompt
        return {
            "question_set_title": "백엔드 기술면접 회고 질문",
            "job_role": "백엔드 개발자",
            "process_stage": "1차 기술면접",
            "questions": [
                {
                    "category": "technical_depth",
                    "question": "카카오 백엔드 기술면접에서 가장 답변이 부족했던 기술 개념은 무엇이었나요?",
                    "reason": "기술 보완 포인트를 찾기 위함입니다.",
                    "priority": "high",
                    "source_template_ids": ["exact_high"],
                },
                {
                    "category": "system_design",
                    "question": "카카오 면접에서 시스템 설계 질문을 받았을 때 어디서 막혔나요?",
                    "reason": "설계 사고 과정을 회고하기 위함입니다.",
                    "priority": "medium",
                    "source_template_ids": ["exact_medium"],
                },
            ],
        }

    monkeypatch.setattr(
        "app.services.retrospective.service.load_retrospective_templates",
        build_templates,
    )
    monkeypatch.setattr(
        "app.services.retrospective.generator.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    request = RetrospectiveQuestionRequest.model_validate(build_request())
    result = generate_retrospective_questions(request)

    assert len(result.questions) == 4
    assert result.questions[0].source_template_ids == ["exact_high"]
    assert result.questions[1].source_template_ids == ["exact_medium"]
    assert result.questions[2].source_template_ids == ["role_all"]
    assert result.questions[3].source_template_ids == ["all_stage"]


def test_service_removes_duplicate_questions_and_preserves_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "question_set_title": "",
            "job_role": "wrong",
            "process_stage": "wrong",
            "questions": [
                {
                    "category": "technical_depth",
                    "question": "카카오 기술면접에서 가장 답변이 부족했던 개념은 무엇이었나요?",
                    "reason": "보완 포인트를 찾기 위함입니다.",
                    "priority": "high",
                    "source_template_ids": ["exact_high"],
                },
                {
                    "category": "technical_depth",
                    "question": "카카오 기술면접에서 가장 답변이 부족했던 개념은 무엇이었나요? ",
                    "reason": "중복 질문입니다.",
                    "priority": "high",
                    "source_template_ids": ["exact_high"],
                },
                {
                    "category": "communication",
                    "question": "후속 질문이 들어왔을 때 답변 구조가 흔들린 순간은 언제였나요?",
                    "reason": "답변 구조를 점검하기 위함입니다.",
                    "priority": "medium",
                    "source_template_ids": ["missing_template"],
                },
            ],
        }

    monkeypatch.setattr(
        "app.services.retrospective.service.load_retrospective_templates",
        build_templates,
    )
    monkeypatch.setattr(
        "app.services.retrospective.generator.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    request = RetrospectiveQuestionRequest.model_validate(build_request())
    result = generate_retrospective_questions(request)

    assert len(result.questions) == 4
    assert len({question.question for question in result.questions}) == 4
    assert result.question_set_title == "1차 기술면접 회고 질문"
    assert result.job_role == "백엔드 개발자"
    assert result.process_stage == "1차 기술면접"
    RetrospectiveQuestionResponse.model_validate(result.model_dump())


def test_endpoint_returns_valid_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "question_set_title": "백엔드 기술면접 회고 질문",
            "job_role": "백엔드 개발자",
            "process_stage": "1차 기술면접",
            "questions": [
                {
                    "category": "technical_depth",
                    "question": "카카오 백엔드 면접에서 가장 아쉬웠던 기술 답변은 무엇이었나요?",
                    "reason": "기술 보완 포인트를 정리하기 위함입니다.",
                    "priority": "high",
                    "source_template_ids": ["exact_high"],
                },
                {
                    "category": "system_design",
                    "question": "시스템 설계 관련 질문에서 어떤 가정을 더 명확히 말했어야 했나요?",
                    "reason": "설계 커뮤니케이션을 회고하기 위함입니다.",
                    "priority": "medium",
                    "source_template_ids": ["exact_medium"],
                },
                {
                    "category": "preparation",
                    "question": "이번 카카오 면접 준비에서 다음에도 유지하고 싶은 준비 방식은 무엇인가요?",
                    "reason": "효과적이었던 준비 전략을 남기기 위함입니다.",
                    "priority": "medium",
                    "source_template_ids": ["role_all"],
                },
                {
                    "category": "improvement",
                    "question": "다음 기술면접 전까지 가장 먼저 보완할 한 가지는 무엇인가요?",
                    "reason": "다음 액션을 구체화하기 위함입니다.",
                    "priority": "low",
                    "source_template_ids": ["all_all"],
                },
            ],
        }

    monkeypatch.setattr(
        "app.services.retrospective.service.load_retrospective_templates",
        build_templates,
    )
    monkeypatch.setattr(
        "app.services.retrospective.generator.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    response = client.post("/ai/retrospective/questions", json=build_request())

    assert response.status_code == 200
    body = response.json()
    assert body["question_set_title"] == "백엔드 기술면접 회고 질문"
    assert body["job_role"] == "백엔드 개발자"
    assert body["process_stage"] == "1차 기술면접"
    assert len(body["questions"]) == 4
