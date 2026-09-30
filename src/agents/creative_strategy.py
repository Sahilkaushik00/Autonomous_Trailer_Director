"""Audience strategy layer kept separate from source selection and validation."""

from __future__ import annotations

from src.models.schemas import AudienceProfile, StoryMap


class CreativeStrategyAgent:
    def build_promise(self, audience: AudienceProfile, story: StoryMap) -> dict[str, object]:
        promises = {
            "family": {
                "promise": "A warm family mystery with approachable stakes.",
                "journey": ["welcome", "curiosity", "warm unresolved question"],
            },
            "young_adult": {
                "promise": "A fast character conflict where a hidden truth changes the stakes.",
                "journey": ["hook", "conflict", "escalation", "unresolved question"],
            },
            "dialect_region": {
                "promise": "A character-led mystery presented through supplied regional language evidence.",
                "journey": ["familiar voice", "family tension", "curiosity", "unresolved question"],
            },
        }
        return promises.get(audience.id, {"promise": audience.goal, "journey": ["hook", "escalation", "open_question"]})
