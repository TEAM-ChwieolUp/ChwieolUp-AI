from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.schemas.mail_stage import MailStageClassifyRequest
from app.services.mail_analysis.service import classify_mail_stage


client = TestClient(app)


def build_request() -> dict:
    return {
        "mail_subject": "[카카오] 1차 인터뷰 일정 안내",
        "mail_body": "안녕하세요. 카카오 채용팀입니다. 백엔드 개발자 포지션 1차 기술 인터뷰 일정을 안내드립니다.",
        "user_stage_categories": [
            {
                "id": 1,
                "name": "서류",
                "description": "지원서 제출 및 서류 심사 단계",
                "order": 1,
            },
            {
                "id": 2,
                "name": "코딩테스트",
                "description": "온라인 코딩테스트 및 과제 테스트",
                "order": 2,
            },
            {
                "id": 3,
                "name": "1차 면접",
                "description": "기술면접 또는 실무진 면접",
                "order": 3,
            },
        ],
    }


def test_interview_schedule_mail_classifies_to_first_interview(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        assert "user_stage_categories" in user_prompt
        assert "mail_body" in user_prompt
        return {
            "predicted_stage": {"id": 3, "name": "1차 면접", "order": 3},
            "confidence": 0.91,
            "reason": "메일에 1차 기술 인터뷰 일정이 명시되어 있습니다.",
            "evidence": ["1차 기술 인터뷰 일정을 안내드립니다"],
            "needs_user_confirmation": False,
        }

    monkeypatch.setattr(
        "app.services.mail_analysis.classifier.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    response = client.post("/ai/mail/stage-classify", json=build_request())

    assert response.status_code == 200
    body = response.json()
    assert body["predicted_stage"]["id"] == 3
    assert body["predicted_stage"]["name"] == "1차 면접"
    assert body["confidence"] == 0.91
    assert body["needs_user_confirmation"] is True


def test_coding_test_mail_classifies_to_coding_test(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "predicted_stage": {"id": 2, "name": "코딩테스트", "order": 2},
            "confidence": 0.88,
            "reason": "온라인 코딩테스트 안내가 포함되어 있습니다.",
            "evidence": ["온라인 코딩테스트를 진행합니다"],
            "needs_user_confirmation": True,
        }

    monkeypatch.setattr(
        "app.services.mail_analysis.classifier.generate_json_with_llm",
        fake_generate_json_with_llm,
    )
    payload = build_request()
    payload["mail_subject"] = "[카카오] 코딩테스트 안내"
    payload["mail_body"] = "안녕하세요. 온라인 코딩테스트를 진행합니다. 응시 링크를 확인해주세요."

    response = client.post("/ai/mail/stage-classify", json=payload)

    assert response.status_code == 200
    assert response.json()["predicted_stage"]["id"] == 2


def test_ambiguous_mail_returns_low_confidence_or_null_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "predicted_stage": None,
            "confidence": 0.25,
            "reason": "구체적인 전형 단계가 드러나지 않습니다.",
            "evidence": ["추후 전형 일정은 다시 안내드리겠습니다"],
            "needs_user_confirmation": True,
        }

    monkeypatch.setattr(
        "app.services.mail_analysis.classifier.generate_json_with_llm",
        fake_generate_json_with_llm,
    )
    payload = build_request()
    payload["mail_subject"] = "안내"
    payload["mail_body"] = "안녕하세요. 지원해주셔서 감사합니다. 추후 전형 일정은 다시 안내드리겠습니다."

    response = client.post("/ai/mail/stage-classify", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["predicted_stage"] is None
    assert body["confidence"] <= 0.4


def test_invalid_stage_id_from_llm_becomes_null(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "predicted_stage": {"id": 999, "name": "존재하지 않는 단계", "order": 99},
            "confidence": 0.95,
            "reason": "잘못된 단계가 반환되었습니다.",
            "evidence": ["인터뷰 일정 안내"],
            "needs_user_confirmation": True,
        }

    monkeypatch.setattr(
        "app.services.mail_analysis.classifier.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    response = client.post("/ai/mail/stage-classify", json=build_request())

    assert response.status_code == 200
    assert response.json()["predicted_stage"] is None


def test_confidence_is_clamped_into_range(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "predicted_stage": {"id": 3, "name": "1차 면접", "order": 3},
            "confidence": 1.7,
            "reason": "면접 메일입니다.",
            "evidence": ["1차 기술 인터뷰 일정을 안내드립니다"],
            "needs_user_confirmation": True,
        }

    monkeypatch.setattr(
        "app.services.mail_analysis.classifier.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    request = MailStageClassifyRequest.model_validate(build_request())
    result = classify_mail_stage(request)

    assert result.confidence == 1.0


def test_evidence_is_limited_to_three_items(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "predicted_stage": {"id": 3, "name": "1차 면접", "order": 3},
            "confidence": 0.93,
            "reason": "면접 일정 메일입니다.",
            "evidence": ["a", "b", "c", "d", "e"],
            "needs_user_confirmation": True,
        }

    monkeypatch.setattr(
        "app.services.mail_analysis.classifier.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    request = MailStageClassifyRequest.model_validate(build_request())
    result = classify_mail_stage(request)

    assert result.evidence == ["a", "b", "c"]


def test_needs_user_confirmation_is_always_true(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict:
        return {
            "predicted_stage": {"id": 3, "name": "1차 면접", "order": 3},
            "confidence": 0.8,
            "reason": "면접 일정 안내입니다.",
            "evidence": ["1차 기술 인터뷰 일정"],
            "needs_user_confirmation": False,
        }

    monkeypatch.setattr(
        "app.services.mail_analysis.classifier.generate_json_with_llm",
        fake_generate_json_with_llm,
    )

    response = client.post("/ai/mail/stage-classify", json=build_request())

    assert response.status_code == 200
    assert response.json()["needs_user_confirmation"] is True
