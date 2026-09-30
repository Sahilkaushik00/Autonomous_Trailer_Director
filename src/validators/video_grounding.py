"""Non-authoritative video-grounding check based on recorded provider observations."""

from __future__ import annotations

from src.models.schemas import ConstraintMap, EpisodePackage, Evidence, StoryMap, TrailerPlan, ValidationIssue, ValidationResult


class VideoGroundingValidator:
    name = "video_grounding"

    def validate(self, plan: TrailerPlan, episode: EpisodePackage, story: StoryMap, constraints: ConstraintMap) -> ValidationResult:
        analysis = episode.metadata.get("video_analysis")
        if not analysis:
            return ValidationResult(self.name, "NOT_RUN", [ValidationIssue("VIDEO_ANALYSIS_NOT_AVAILABLE", "info", "No live video analysis was supplied; deterministic source checks still apply.")])

        observations = analysis.get("observations", []) if isinstance(analysis, dict) else []
        by_scene: dict[str, list[dict]] = {}
        for obs in observations:
            sid = obs.get("scene_id")
            if sid:
                by_scene.setdefault(str(sid), []).append(obs)

        issues: list[ValidationIssue] = []
        for segment in plan.segments:
            matching = by_scene.get(segment.source_scene_id, [])
            if not matching:
                issues.append(
                    ValidationIssue(
                        "VIDEO_SCENE_NOT_GROUNDED",
                        "warning",
                        f"Video analysis did not confidently align {segment.source_scene_id}; human review is required.",
                        segment.segment_id,
                        [Evidence("video_analysis", "gemini", "No aligned observation found.")],
                        "Review the source clip against the planned timecode before final export.",
                    )
                )
                continue
            overlap = any(
                float(obs.get("end_seconds", 0)) >= segment.timecode.start
                and float(obs.get("start_seconds", 0)) <= segment.timecode.end
                for obs in matching
            )
            if not overlap:
                issues.append(
                    ValidationIssue(
                        "VIDEO_TIME_MISMATCH",
                        "warning",
                        f"Video evidence for {segment.source_scene_id} does not overlap the planned timecode.",
                        segment.segment_id,
                        [Evidence("video_analysis", "gemini", "Observation timing did not overlap selected clip.")],
                        "Inspect the clip and regenerate the edit decision list if needed.",
                    )
                )

        status = "PASS_WITH_WARNINGS" if issues else "PASS"
        return ValidationResult(self.name, status, issues)
