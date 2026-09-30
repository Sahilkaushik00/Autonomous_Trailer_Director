"""LLM-assisted story understanding that never replaces deterministic source facts."""

from __future__ import annotations

from src.models.schemas import EpisodePackage, StoryMap
from src.services.model_provider import ModelProvider


STORY_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_emotional_arc": {"type": "array", "items": {"type": "string"}},
        "candidate_sensitive_moments": {"type": "array", "items": {"type": "string"}},
        "candidate_spoilers": {"type": "array", "items": {"type": "string"}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
        "grounding_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "candidate_emotional_arc",
        "candidate_sensitive_moments",
        "candidate_spoilers",
        "uncertainties",
        "grounding_notes",
    ],
}


class LLMStoryMapper:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def enhance(self, episode: EpisodePackage, story: StoryMap) -> StoryMap:
        scene_catalog = [
            {
                "id": scene.id,
                "start": scene.start,
                "end": scene.end,
                "description": scene.description,
                "characters": scene.characters,
                "relationship_claims": scene.relationship_claims,
                "event_tags": scene.event_tags,
                "sensitive_content": scene.sensitive_content,
                "spoiler_facts": scene.spoiler_facts,
                "visual_evidence": scene.visual_evidence,
                "audio_evidence": scene.audio_evidence,
            }
            for scene in episode.scenes
        ]
        dialogue = [
            {"id": line.id, "scene_id": line.scene_id, "speaker": line.speaker, "text": line.text}
            for line in episode.dialogue
        ]
        result = self.provider.generate_json(
            "Build an advisory story-understanding layer from the scene and dialogue evidence. "
            "Identify candidate emotional arcs, possible spoilers, sensitive moments, and uncertainties. "
            "Candidate spoilers must remain advisory: the deterministic spoiler map remains authoritative.",
            {"episode_id": episode.episode_id, "scene_catalog": scene_catalog, "dialogue": dialogue},
            STORY_SCHEMA,
        )
        story.llm_insights = result
        return story


# Backward-compatible name used by earlier tests and documentation.
GeminiStoryMapper = LLMStoryMapper
