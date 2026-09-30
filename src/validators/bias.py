"""Audit audience signals for potentially stereotyping personalization inputs."""

from src.models.schemas import ConstraintMap, EpisodePackage, StoryMap, TrailerPlan, ValidationIssue, ValidationResult


class AudienceBiasValidator:
    name = "audience_bias"
    sensitive_signal_tokens = {
        "accent", "dialect", "region", "ethnicity", "religion", "gender", "race", "caste", "income",
    }

    def validate(self, plan: TrailerPlan, episode: EpisodePackage, story: StoryMap, constraints: ConstraintMap) -> ValidationResult:
        risky = []
        for key in plan.audience.engagement_signals:
            normalized = key.lower().replace("-", "_")
            if any(token in normalized for token in self.sensitive_signal_tokens):
                risky.append(key)
        if not risky:
            return ValidationResult(self.name, "PASS", [])
        return ValidationResult(
            self.name,
            "PASS_WITH_WARNINGS",
            [ValidationIssue(
                "SENSITIVE_AUDIENCE_SIGNAL",
                "warning",
                f"Audience data contains identity/regional signal(s): {', '.join(sorted(risky))}. These must not be used as stereotype proxies.",
                repair_hint="Use explicit episode evidence and language/context attributes instead of demographic assumptions.",
            )],
        )
