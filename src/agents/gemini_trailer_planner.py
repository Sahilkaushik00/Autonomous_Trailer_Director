"""LLM-powered creative planner with hard source-ID and dialogue grounding."""

from __future__ import annotations

from src.models.schemas import AudienceProfile, EpisodePackage, Evidence, StoryMap, Timecode, TrailerPlan, TrailerSegment
from src.services.cost_estimator import estimate_cost
from src.services.model_provider import ModelProvider
from src.services.source_index import SourceIndex


PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "audience_promise": {"type": "string"},
        "emotional_journey": {"type": "array", "items": {"type": "string"}},
        "segments": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "source_scene_id": {"type": "string"},
                    "dialogue_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "subtitle_track": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "text_card": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "voice_over": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "reason": {"type": "string"},
                },
                "required": ["source_scene_id", "dialogue_id", "subtitle_track", "text_card", "voice_over", "reason"],
            },
        },
        "fallback_plan": {"type": "string"},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["audience_promise", "emotional_journey", "segments", "fallback_plan", "uncertainties"],
}


class LLMTrailerPlanner:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def build(self, episode: EpisodePackage, story: StoryMap, audience: AudienceProfile) -> TrailerPlan:
        index = SourceIndex.build(episode)
        allowed_territory = audience.territory or episode.metadata.get("default_territory")
        scene_catalog = [
            {
                "id": scene.id,
                "start": scene.start,
                "end": scene.end,
                "description": scene.description,
                "characters": scene.characters,
                "event_tags": scene.event_tags,
                "sensitive_content": scene.sensitive_content,
                "spoiler_facts": scene.spoiler_facts,
                "visual_evidence": scene.visual_evidence,
                "audio_evidence": scene.audio_evidence,
                "music_asset_id": scene.music_asset_id,
            }
            for scene in episode.scenes
        ]
        context = {
            "audience": {
                "id": audience.id,
                "name": audience.name,
                "goal": audience.goal,
                "special_care": audience.special_care,
                "territory": allowed_territory,
                "dialect": audience.dialect,
            },
            "story_map": {
                "characters": story.characters,
                "relationships": story.relationships,
                "major_events": story.major_events,
                "emotional_turns": story.emotional_turns,
                "spoiler_facts": story.spoiler_facts,
                "sensitive_content": story.sensitive_content,
            },
            "scene_catalog": scene_catalog,
            "dialogue": [
                {
                    "id": line.id,
                    "scene_id": line.scene_id,
                    "speaker": line.speaker,
                    "text": line.text,
                    "subtitle_variants": line.subtitle_variants,
                }
                for line in episode.dialogue
            ],
            "contracts": [
                {
                    "id": c.id,
                    "asset_type": c.asset_type,
                    "asset_id": c.asset_id,
                    "allowed": c.allowed,
                    "territories": c.territories,
                    "promotional_use": c.promotional_use,
                    "valid_until": c.valid_until,
                }
                for c in episode.contracts
            ],
            "rating_policies": [
                {
                    "id": p.id,
                    "audience_id": p.audience_id,
                    "max_rating": p.max_rating,
                    "blocked_terms": p.blocked_terms,
                    "blocked_tags": p.blocked_tags,
                }
                for p in episode.rating_policies
            ],
            "historic_performance": episode.historic_performance,
            "video_grounding_advisory": episode.metadata.get("video_analysis", {}),
        }
        result = self.provider.generate_json(
            "Create one precise 25-45 second trailer edit decision plan for this audience. "
            "Choose 2-5 segments and make the three audience plans meaningfully distinct. "
            "Use only scene IDs from scene_catalog. Never invent timecodes or dialogue. "
            "Do not reveal spoiler_facts or create a misleading causal relationship. "
            "The final plan will be independently validated, so preserve uncertainty rather than hiding it. "
            "For dialect-region viewers, personalize from supplied subtitle evidence and cultural context, not stereotypes.",
            context,
            PLAN_SCHEMA,
        )

        valid_scene_ids = {scene.id for scene in episode.scenes}
        segments: list[TrailerSegment] = []
        seen_scene_ids: set[str] = set()
        for number, raw in enumerate(result.get("segments", []), 1):
            scene_id = str(raw.get("source_scene_id", ""))
            scene = next((item for item in episode.scenes if item.id == scene_id), None)
            if scene_id in seen_scene_ids:
                continue
            seen_scene_ids.add(scene_id)

            if scene is None:
                segments.append(
                    TrailerSegment(
                        segment_id=f"{audience.id}_seg_{number:02d}",
                        source_scene_id=scene_id,
                        timecode=Timecode(0.0, 0.0, "00:00:00.000", "00:00:00.000"),
                        video=f"scene:{scene_id}",
                        audio="dialogue_only",
                        reason=str(raw.get("reason", "Model proposed an unknown scene.")),
                        evidence=[Evidence("llm", self.provider.name, "Unknown source scene proposed by model; validator must reject it.")],
                        risk_flags=["LLM_SELECTED_UNKNOWN_SCENE"],
                    )
                )
                continue

            dialogue_id = raw.get("dialogue_id")
            dialogue_line = None
            if dialogue_id:
                candidate = index.dialogue.get(str(dialogue_id))
                if candidate and candidate.scene_id == scene.id:
                    dialogue_line = candidate
            if dialogue_line is None:
                dialogue_candidates = index.dialogue_for_scene(scene.id)
                dialogue_line = dialogue_candidates[0] if dialogue_candidates else None

            subtitle = dialogue_line.text if dialogue_line else None
            subtitle_track = raw.get("subtitle_track")
            if audience.id == "dialect_region" and audience.dialect and dialogue_line:
                subtitle = dialogue_line.subtitle_variants.get(audience.dialect, subtitle)
            elif subtitle_track and dialogue_line:
                subtitle = dialogue_line.subtitle_variants.get(str(subtitle_track), subtitle)

            segments.append(
                TrailerSegment(
                    segment_id=f"{audience.id}_seg_{number:02d}",
                    source_scene_id=scene.id,
                    timecode=scene.timecode,
                    video=f"scene:{scene.id}",
                    audio=f"music:{scene.music_asset_id}" if scene.music_asset_id else "dialogue_only",
                    subtitle=subtitle,
                    text_card=str(raw["text_card"]) if raw.get("text_card") else None,
                    voice_over=str(raw["voice_over"]) if raw.get("voice_over") else None,
                    reason=str(raw.get("reason", "LLM audience-aware selection.")),
                    evidence=[Evidence("scene", scene.id, scene.description), Evidence("llm", self.provider.name, "Creative selection proposal.")],
                    risk_flags=[],
                )
            )

        # A fully hallucinated segment should not be silently omitted; validators need to see it.
        # The exact source timecode remains deterministic for real scenes.
        if not segments and valid_scene_ids:
            first = episode.scenes[0]
            segments.append(
                TrailerSegment(
                    segment_id=f"{audience.id}_seg_01",
                    source_scene_id=first.id,
                    timecode=first.timecode,
                    video=f"scene:{first.id}",
                    audio=f"music:{first.music_asset_id}" if first.music_asset_id else "dialogue_only",
                    subtitle=None,
                    reason="Fallback to first source scene because the LLM returned no usable segments.",
                    evidence=[Evidence("system", "planner-fallback", "No usable model-selected segments.")],
                    risk_flags=["LLM_EMPTY_PLAN"],
                )
            )

        plan = TrailerPlan(
            trailer_id=f"{audience.id}_gemini_v1",
            audience=audience,
            duration_seconds=round(sum(s.timecode.duration_seconds for s in segments), 3),
            audience_promise=str(result.get("audience_promise", audience.goal)),
            emotional_journey=[str(x) for x in result.get("emotional_journey", [])],
            segments=segments,
            assumptions=[
                "The selected LLM proposes creative choices; deterministic validators remain authoritative.",
                "Source dialogue and timecodes are resolved from the supplied episode package, not copied from model text.",
                *[f"LLM uncertainty: {x}" for x in result.get("uncertainties", [])],
            ],
            human_approvals_required=["editorial_final_cut", "rights_approval", "cultural_review" if audience.id == "dialect_region" else "editorial_review"],
            fallback_plan=str(result.get("fallback_plan", "Replace blocked segments with the next validated source candidate.")),
        )
        plan.estimated_cost_usd = estimate_cost(plan, episode.cost_sheet, model_calls=1)
        return plan


# Backward-compatible name.
GeminiTrailerPlanner = LLMTrailerPlanner
