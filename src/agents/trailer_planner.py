"""Deterministic audience-aware planner used by mock/replay mode."""

from __future__ import annotations

from src.models.schemas import AudienceProfile, EpisodePackage, Evidence, StoryMap, TrailerPlan, TrailerSegment
from src.agents.creative_strategy import CreativeStrategyAgent
from src.services.cost_estimator import estimate_cost
from src.services.source_index import SourceIndex


class TrailerPlanner:
    promise_by_audience = {
        "family": "Warmth, stakes and broad entertainment without frightening or suggestive context.",
        "young_adult": "Fast-moving character conflict, humour and identity while preserving the central mystery.",
        "dialect_region": "A character-led story grounded in the supplied language and cultural context.",
    }

    preferred_tags = {
        "family": {"family", "warmth", "humour", "discovery", "heart"},
        "young_adult": {"conflict", "humour", "identity", "mystery", "pace"},
        "dialect_region": {"dialogue", "family", "community", "identity", "culture"},
    }

    def build(self, episode: EpisodePackage, story: StoryMap, audience: AudienceProfile) -> TrailerPlan:
        index = SourceIndex.build(episode)
        strategy = CreativeStrategyAgent().build_promise(audience, story)
        scores: list[tuple[float, object]] = []
        for scene in episode.scenes:
            if scene.spoiler_facts:
                continue
            tags = {tag.lower() for tag in scene.event_tags}
            score = float(len(tags & self.preferred_tags.get(audience.id, set())))
            score += 0.25 if scene.emotional_turn else 0.0
            if scene.sensitive_content and audience.id == "family":
                score -= 5.0
            if audience.id == "dialect_region" and not (scene.characters or scene.description):
                score -= 1.0
            scores.append((score, scene))

        ranked = sorted(scores, key=lambda pair: (-pair[0], getattr(pair[1], "start", 0)))
        selected = [scene for _, scene in ranked[:4]]
        selected.sort(key=lambda scene: scene.start)

        segments: list[TrailerSegment] = []
        for number, scene in enumerate(selected, 1):
            dialogue = index.dialogue_for_scene(scene.id)
            subtitle = dialogue[0].text if dialogue else None
            if audience.id == "dialect_region" and audience.dialect:
                subtitle = next((line.subtitle_variants.get(audience.dialect) for line in dialogue if line.subtitle_variants.get(audience.dialect)), subtitle)
            segments.append(
                TrailerSegment(
                    segment_id=f"{audience.id}_seg_{number:02d}",
                    source_scene_id=scene.id,
                    timecode=scene.timecode,
                    video=f"scene:{scene.id}",
                    audio=f"music:{scene.music_asset_id}" if scene.music_asset_id else "dialogue_only",
                    subtitle=subtitle,
                    reason=f"Supports the {audience.id} audience promise using source scene evidence.",
                    evidence=[Evidence("scene", scene.id, scene.description)],
                    risk_flags=[],
                )
            )

        plan = TrailerPlan(
            trailer_id=f"{audience.id}_v1",
            audience=audience,
            duration_seconds=round(sum(s.timecode.duration_seconds for s in segments), 3),
            audience_promise=strategy["promise"],
            emotional_journey=list(strategy["journey"]),
            segments=segments,
            assumptions=["Mock planner uses supplied scene metadata as grounded evidence.", "Historic performance is treated as a hypothesis signal, not a selection rule."],
            human_approvals_required=["editorial_final_cut", "rights_approval", "cultural_review" if audience.id == "dialect_region" else "editorial_review"],
            fallback_plan="Drop the riskiest segment, replace it with the next validated candidate, then rerun all impacted validators.",
        )
        plan.estimated_cost_usd = estimate_cost(plan, episode.cost_sheet, model_calls=0, media_calls=0)
        return plan
