"""Basic accessibility checks for subtitles and text cards."""

from src.models.schemas import ConstraintMap, EpisodePackage, StoryMap, TrailerPlan, ValidationIssue, ValidationResult


class AccessibilityValidator:
    name = "accessibility"

    def validate(self, plan: TrailerPlan, episode: EpisodePackage, story: StoryMap, constraints: ConstraintMap) -> ValidationResult:
        issues: list[ValidationIssue] = []
        for segment in plan.segments:
            if segment.video and not segment.subtitle and not segment.text_card and plan.audience.id != "dialect_region":
                issues.append(ValidationIssue("MISSING_ACCESSIBLE_TEXT", "warning", "Segment has spoken/dialogue audio but no subtitle or text-card representation.", segment.segment_id, repair_hint="Attach verified subtitles when dialogue is present."))
        return ValidationResult(self.name, "PASS_WITH_WARNINGS" if issues else "PASS", issues)
