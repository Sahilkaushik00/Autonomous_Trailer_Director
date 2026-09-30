"""Check that plan text does not claim unsupported story facts."""

from src.models.schemas import ConstraintMap, EpisodePackage, StoryMap, TrailerPlan, ValidationIssue, ValidationResult


class StoryTruthValidator:
    name = "story_truth"

    def validate(self, plan: TrailerPlan, episode: EpisodePackage, story: StoryMap, constraints: ConstraintMap) -> ValidationResult:
        known_claims = {claim["claim"].lower() for claim in story.relationships if "claim" in claim}
        issues: list[ValidationIssue] = []
        for segment in plan.segments:
            if not segment.reason:
                issues.append(ValidationIssue("UNSUPPORTED_REASON", "warning", "Segment has no explicit grounded reason.", segment.segment_id, repair_hint="Add source-based rationale."))
            if segment.voice_over and known_claims and segment.voice_over.lower() not in known_claims:
                # We don't treat every creative VO as false; this is a warning for human review.
                issues.append(ValidationIssue("VO_NEEDS_GROUNDING", "warning", "Voice-over contains a claim that is not directly linked to a supplied relationship claim.", segment.segment_id, repair_hint="Attach supporting evidence or remove the claim."))
        return ValidationResult(self.name, "PASS_WITH_WARNINGS" if issues else "PASS", issues)
