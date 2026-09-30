"""Selective re-planning for evaluator surprise events."""

from __future__ import annotations

from dataclasses import replace

from src.models.schemas import ChangeEvent, ContractRule, EpisodePackage, Evidence, TrailerPlan


class Replanner:
    def apply_event(self, plan: TrailerPlan, episode: EpisodePackage, event: ChangeEvent) -> TrailerPlan:
        if event.event_type != "contract_changed":
            return plan
        contract = ContractRule(**event.payload["contract"])
        affected = {
            seg.segment_id
            for seg in plan.segments
            if contract.asset_id in seg.video or contract.asset_id in seg.audio
            or any(ev.source_id == contract.id for ev in seg.evidence)
        }
        if not affected:
            return plan

        used_scene_ids = {s.source_scene_id for s in plan.segments}
        blocked_family_tags = {"frightening_sound", "graphic", "suggestive"} if plan.audience.id == "family" else set()
        available = [
            scene for scene in episode.scenes
            if not scene.spoiler_facts
            and scene.id not in used_scene_ids
            and not (blocked_family_tags & {tag.lower() for tag in scene.event_tags + scene.sensitive_content})
        ]
        iterator = iter(available)
        segments = []
        for seg in plan.segments:
            if seg.segment_id not in affected:
                segments.append(seg)
                continue
            replacement = next(iterator, None)
            if replacement is None:
                continue
            segments.append(
                replace(
                    seg,
                    source_scene_id=replacement.id,
                    timecode=replacement.timecode,
                    video=f"scene:{replacement.id}",
                    audio="dialogue_only",
                    reason=f"Replanned after {event.event_id}: {event.message}",
                    evidence=[Evidence("scene", replacement.id, replacement.description), Evidence("event", event.event_id, event.message)],
                    risk_flags=[],
                )
            )
        return replace(plan, segments=segments, revision=plan.revision + 1)
