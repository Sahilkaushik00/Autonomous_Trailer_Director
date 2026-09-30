"""Map change events to the minimum validation scope."""

from __future__ import annotations

from src.models.schemas import ChangeEvent


class ChangeImpactAnalyzer:
    mapping = {
        "contract_changed": {"rights", "budget"},
        "policy_changed": {"audience_policy", "spoiler"},
        "audience_data_changed": {"audience_bias"},
        "subtitle_changed": {"story_truth", "cultural_respect", "accessibility"},
        "source_changed": {"source_accuracy", "spoiler", "story_truth", "audience_policy", "rights"},
        "marketing_request": {"story_truth", "spoiler", "audience_policy"},
        "model_unavailable": {"source_accuracy", "story_truth", "audience_policy"},
    }

    def affected_validators(self, event: ChangeEvent) -> set[str]:
        return set(self.mapping.get(event.event_type, {"source_accuracy", "spoiler", "story_truth", "rights", "audience_policy", "cultural_respect", "accessibility", "budget", "audience_bias"}))
