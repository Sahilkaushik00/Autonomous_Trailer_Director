"""Verify every selected source scene and timecode."""

from src.models.schemas import ConstraintMap, EpisodePackage, StoryMap, TrailerPlan, ValidationIssue, ValidationResult


class SourceAccuracyValidator:
    name = "source_accuracy"

    def validate(self, plan: TrailerPlan, episode: EpisodePackage, story: StoryMap, constraints: ConstraintMap) -> ValidationResult:
        scene_map = {scene.id: scene for scene in episode.scenes}
        issues: list[ValidationIssue] = []
        for segment in plan.segments:
            scene = scene_map.get(segment.source_scene_id)
            if scene is None:
                issues.append(ValidationIssue("MISSING_SCENE", "hard_block", f"Scene {segment.source_scene_id} does not exist.", segment.segment_id, repair_hint="Replace with a verified scene id."))
                continue
            if not (scene.start <= segment.timecode.start < segment.timecode.end <= scene.end):
                issues.append(ValidationIssue("INVALID_TIMECODE", "hard_block", f"Timecode for {segment.segment_id} is outside scene {scene.id}.", segment.segment_id, repair_hint="Use a source range inside the selected scene."))
        return ValidationResult(self.name, "FAIL" if issues else "PASS", issues)
