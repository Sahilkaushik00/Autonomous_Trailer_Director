"""Evidence-based spoiler detection."""

from src.models.schemas import ConstraintMap, EpisodePackage, StoryMap, TrailerPlan, ValidationIssue, ValidationResult


class SpoilerValidator:
    name = "spoiler"

    def validate(self, plan: TrailerPlan, episode: EpisodePackage, story: StoryMap, constraints: ConstraintMap) -> ValidationResult:
        issues: list[ValidationIssue] = []
        protected = [fact.lower() for fact in story.spoiler_facts if fact.strip()]
        for segment in plan.segments:
            scene = next((item for item in episode.scenes if item.id == segment.source_scene_id), None)
            if scene is None:
                continue
            text = " ".join([
                scene.description,
                " ".join(scene.spoiler_facts),
                segment.reason,
                segment.text_card or "",
                segment.voice_over or "",
                segment.subtitle or "",
            ]).lower()
            leaked = [fact for fact in protected if fact in text]
            if leaked:
                issues.append(ValidationIssue("SPOILER_DETECTED", "hard_block", f"Protected fact disclosed: {', '.join(leaked)}", segment.segment_id, repair_hint="Replace the segment or remove the revealing wording."))
            elif scene.spoiler_facts:
                issues.append(ValidationIssue("SPOILER_RISK", "warning", f"Scene {scene.id} is marked as containing protected facts.", segment.segment_id, repair_hint="Prefer a non-spoiler scene."))
        status = "FAIL" if any(i.severity == "hard_block" for i in issues) else "PASS_WITH_WARNINGS" if issues else "PASS"
        return ValidationResult(self.name, status, issues)
