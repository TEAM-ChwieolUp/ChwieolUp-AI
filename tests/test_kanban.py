from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.schemas.kanban import KanbanMoveRecommendRequest
from app.services.kanban.service import recommend_kanban_move


client = TestClient(app)


def build_request() -> dict:
    return {
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


def test_final_interview_mail_recommends_move(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        assert "current_kanban_stage" in user_prompt
        assert "user_kanban_stages" in user_prompt
        return {
            "recommend_move": True,
            "to_stage": {"id": 4, "name": "최종 면접", "order": 4},
            "confidence": 0.88,
            "reason": "메일 본문에 최종 인터뷰 일정이 명시되어 있습니다.",
            "evidence": ["최종 인터뷰 일정을 안내드립니다"],
            "needs_user_confirmation": False,
        }

    monkeypatch.setattr(
        "app.services.kanban.recommender.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    response = client.post("/ai/kanban/move-recommend", json=build_request())

    assert response.status_code == 200
    body = response.json()
    assert body["recommend_move"] is True
    assert body["from_stage"]["id"] == 2
    assert body["to_stage"]["id"] == 4
    assert body["needs_user_confirmation"] is True


def test_same_stage_prediction_does_not_recommend_move(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "recommend_move": True,
            "to_stage": {"id": 2, "name": "코딩테스트", "order": 2},
            "confidence": 0.92,
            "reason": "현재 단계와 동일합니다.",
            "evidence": ["코딩테스트 안내"],
            "needs_user_confirmation": True,
        }

    monkeypatch.setattr(
        "app.services.kanban.recommender.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    response = client.post("/ai/kanban/move-recommend", json=build_request())

    assert response.status_code == 200
    body = response.json()
    assert body["recommend_move"] is False
    assert body["to_stage"] is None


def test_non_adjacent_stage_move_is_allowed_when_mail_is_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "recommend_move": True,
            "to_stage": {"id": 4, "name": "최종 면접", "order": 4},
            "confidence": 0.9,
            "reason": "최종 인터뷰로 진행됨이 명확합니다.",
            "evidence": ["최종 인터뷰 일정 안내"],
            "needs_user_confirmation": True,
        }

    monkeypatch.setattr(
        "app.services.kanban.recommender.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    request = KanbanMoveRecommendRequest.model_validate(build_request())
    result = recommend_kanban_move(request)

    assert result.recommend_move is True
    assert result.to_stage is not None
    assert result.to_stage.id == 4


def test_invalid_stage_id_from_llm_becomes_no_move(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "recommend_move": True,
            "to_stage": {"id": 999, "name": "없는 단계", "order": 99},
            "confidence": 0.95,
            "reason": "잘못된 단계입니다.",
            "evidence": ["최종 인터뷰 일정 안내"],
            "needs_user_confirmation": True,
        }

    monkeypatch.setattr(
        "app.services.kanban.recommender.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    response = client.post("/ai/kanban/move-recommend", json=build_request())

    assert response.status_code == 200
    body = response.json()
    assert body["recommend_move"] is False
    assert body["to_stage"] is None


def test_ambiguous_mail_with_low_confidence_does_not_recommend_move(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "recommend_move": True,
            "to_stage": {"id": 3, "name": "1차 면접", "order": 3},
            "confidence": 0.42,
            "reason": "메일이 다소 애매합니다.",
            "evidence": ["추후 다시 안내드리겠습니다"],
            "needs_user_confirmation": True,
        }

    monkeypatch.setattr(
        "app.services.kanban.recommender.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    response = client.post("/ai/kanban/move-recommend", json=build_request())

    assert response.status_code == 200
    body = response.json()
    assert body["recommend_move"] is False
    assert body["to_stage"] is None


def test_evidence_is_limited_to_three_items(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "recommend_move": True,
            "to_stage": {"id": 4, "name": "최종 면접", "order": 4},
            "confidence": 0.85,
            "reason": "최종 면접 메일입니다.",
            "evidence": ["a", "b", "c", "d", "e"],
            "needs_user_confirmation": True,
        }

    monkeypatch.setattr(
        "app.services.kanban.recommender.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    request = KanbanMoveRecommendRequest.model_validate(build_request())
    result = recommend_kanban_move(request)

    assert result.evidence == ["a", "b", "c"]


def test_needs_user_confirmation_is_always_true(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "recommend_move": True,
            "to_stage": {"id": 4, "name": "최종 면접", "order": 4},
            "confidence": 0.88,
            "reason": "최종 면접 안내입니다.",
            "evidence": ["최종 인터뷰 일정 안내"],
            "needs_user_confirmation": False,
        }

    monkeypatch.setattr(
        "app.services.kanban.recommender.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    response = client.post("/ai/kanban/move-recommend", json=build_request())

    assert response.status_code == 200
    assert response.json()["needs_user_confirmation"] is True


def test_current_stage_must_exist_in_user_stages() -> None:
    payload = build_request()
    payload["current_kanban_stage"]["id"] = 99

    response = client.post("/ai/kanban/move-recommend", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "current_kanban_stage must exist in user_kanban_stages."
