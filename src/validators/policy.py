"""Validate audience-specific safety/rating constraints."""

from src.models.schemas import ConstraintMap, EpisodePackage, StoryMap, TrailerPlan, ValidationIssue, ValidationResult


class PolicyValidator:
    name = "audience_policy"

    def validate(self, plan: TrailerPlan, episode: EpisodePackage, story: StoryMap, constraints: ConstraintMap) -> ValidationResult:
        rules = [r for r in episode.rating_policies if r.audience_id == plan.audience.id]
        blocked_terms = {x.lower() for rule in rules for x in rule.blocked_terms}
        blocked_tags = {x.lower() for rule in rules for x in rule.blocked_tags}
        issues: list[ValidationIssue] = []
        for segment in plan.segments:
            scene = next((item for item in episode.scenes if item.id == segment.source_scene_id), None)
            if scene is None:
                continue
            text = " ".join([scene.description, segment.reason, segment.subtitle or "", segment.text_card or "", segment.voice_over or ""]).lower()
            term_hits = sorted(term for term in blocked_terms if term and term in text)
            tag_hits = sorted(tag for tag in blocked_tags if tag in {x.lower() for x in scene.event_tags + scene.sensitive_content})
            for hit in term_hits:
                issues.append(ValidationIssue("BLOCKED_TERM", "hard_block", f"Blocked term '{hit}' appears in segment {segment.segment_id}.", segment.segment_id, repair_hint="Remove or replace the affected material."))
            for hit in tag_hits:
                issues.append(ValidationIssue("BLOCKED_TAG", "hard_block", f"Blocked content tag '{hit}' appears in scene {scene.id}.", segment.segment_id, repair_hint="Select a scene compatible with the audience policy."))
        return ValidationResult(self.name, "FAIL" if issues else "PASS", issues)
