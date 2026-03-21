from __future__ import annotations

from esf_agent_service.core.config import Settings


def test_agent_skills_search_roots_accepts_comma_separated_env(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_API_KEY", "dummy-token")
    monkeypatch.setenv("AGENT_SKILLS_SEARCH_ROOTS", ".agents/skills,.codex/skills")

    settings = Settings()

    assert [str(path) for path in settings.agent_skills_search_roots] == [
        ".agents/skills",
        ".codex/skills",
    ]
