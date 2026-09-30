"""Fast evidence lookup over the source episode package."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.schemas import DialogueLine, EpisodePackage, Scene


@dataclass
class SourceIndex:
    scenes: dict[str, Scene]
    dialogue: dict[str, DialogueLine]

    @classmethod
    def build(cls, episode: EpisodePackage) -> "SourceIndex":
        return cls(
            scenes={scene.id: scene for scene in episode.scenes},
            dialogue={line.id: line for line in episode.dialogue},
        )

    def scene(self, scene_id: str) -> Scene | None:
        return self.scenes.get(scene_id)

    def dialogue_for_scene(self, scene_id: str) -> list[DialogueLine]:
        return sorted(
            (line for line in self.dialogue.values() if line.scene_id == scene_id),
            key=lambda line: line.start,
        )
