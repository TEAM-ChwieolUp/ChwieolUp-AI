from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.schemas.retrospective import RetrospectiveQuestionTemplate


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "retrospective_questions.json"


@lru_cache(maxsize=1)
def load_retrospective_templates() -> list[RetrospectiveQuestionTemplate]:
    raw_templates = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw_templates, list):
        raise ValueError("retrospective_questions.json must contain a JSON array.")
    return [RetrospectiveQuestionTemplate.model_validate(item) for item in raw_templates]
