"""Rule-based repair layer that acts only on validator evidence."""

from __future__ import annotations

from dataclasses import replace

from src.models.schemas import EpisodePackage, Evidence, TrailerPlan, TrailerSegment, ValidationResult
from src.services.cost_estimator import estimate_cost


class RepairAgent:
    def repair(self, plan: TrailerPlan, episode: EpisodePackage, results: list[ValidationResult], *, changed_by_event: str | None = None) -> TrailerPlan:
        blocked = {
            issue.segment_id
            for result in results
            if result.status == "FAIL"
            for issue in result.issues
            if issue.severity == "hard_block" and issue.segment_id
        }
        if not blocked:
            return plan

        used = {seg.source_scene_id for seg in plan.segments if seg.segment_id not in blocked}
        blocked_family_tags = {"frightening_sound", "graphic", "suggestive"} if plan.audience.id == "family" else set()
        candidates = [
            scene for scene in episode.scenes
            if scene.id not in used
            and not scene.spoiler_facts
            and not (blocked_family_tags & {tag.lower() for tag in scene.event_tags + scene.sensitive_content})
        ]
        candidate_iter = iter(candidates)
        repaired: list[TrailerSegment] = []
        for segment in plan.segments:
            if segment.segment_id not in blocked:
                repaired.append(segment)
                continue
            replacement = next(candidate_iter, None)
            if replacement is None:
                continue
            repaired.append(
                replace(
                    segment,
                    source_scene_id=replacement.id,
                    timecode=replacement.timecode,
                    video=f"scene:{replacement.id}",
                    subtitle=None,
                    reason=f"Replaced after validation failure in {segment.segment_id}.",
                    evidence=[Evidence("scene", replacement.id, replacement.description)],
                    risk_flags=[],
                )
            )

        revised = replace(plan, segments=repaired, revision=plan.revision + 1)
        revised.duration_seconds = round(sum(seg.timecode.duration_seconds for seg in revised.segments), 3)
        revised.estimated_cost_usd = estimate_cost(revised, episode.cost_sheet)
        return revised
