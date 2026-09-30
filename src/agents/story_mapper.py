"""Build a grounded story map from supplied scene-level evidence."""

from __future__ import annotations

from src.models.schemas import EpisodePackage, StoryMap


class StoryMapper:
    def build(self, episode: EpisodePackage) -> StoryMap:
        characters: dict[str, dict[str, object]] = {}
        major_events: list[dict[str, object]] = []
        emotional_turns: list[dict[str, object]] = []
        sensitive: list[dict[str, object]] = []
        spoilers: list[str] = []
        relationships: list[dict[str, object]] = []

        for scene in sorted(episode.scenes, key=lambda item: item.start):
            for character in scene.characters:
                characters.setdefault(character, {"scenes": []})
                cast = characters[character]["scenes"]
                assert isinstance(cast, list)
                cast.append(scene.id)
            for claim in scene.relationship_claims:
                relationships.append({"scene_id": scene.id, "claim": claim})
            if scene.event_tags:
                major_events.append({"scene_id": scene.id, "tags": scene.event_tags, "description": scene.description})
            if scene.emotional_turn:
                emotional_turns.append({"scene_id": scene.id, "turn": scene.emotional_turn})
            if scene.sensitive_content:
                sensitive.append({"scene_id": scene.id, "content": scene.sensitive_content})
            spoilers.extend(scene.spoiler_facts)

        return StoryMap(
            episode_id=episode.episode_id,
            characters=characters,
            relationships=relationships,
            major_events=major_events,
            emotional_turns=emotional_turns,
            spoiler_facts=list(dict.fromkeys(spoilers)),
            sensitive_content=sensitive,
        )
