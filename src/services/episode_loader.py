"""Load and validate a supplied episode package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models.schemas import (
    ContractRule,
    CostSheet,
    DialogueLine,
    EpisodePackage,
    RatingRule,
    Scene,
)


class EpisodePackageLoader:
    required_top_level = {"episode_id"}

    def load(self, path: Path) -> EpisodePackage:
        if not path.is_file():
            raise FileNotFoundError(f"Episode package not found: {path}")
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError("Episode package must be a JSON object.")
        return self.from_dict(payload)

    def from_dict(self, payload: dict[str, Any]) -> EpisodePackage:
        missing = self.required_top_level - payload.keys()
        if missing:
            raise ValueError(f"Episode package is missing: {', '.join(sorted(missing))}")

        episode = EpisodePackage(
            episode_id=str(payload["episode_id"]),
            duration_seconds=float(payload.get("duration_seconds", 0.0)),
            scenes=[self._scene(item) for item in payload.get("scenes", [])],
            dialogue=[self._dialogue(item) for item in payload.get("dialogue", [])],
            subtitles={
                str(track): [self._dialogue(item) for item in lines]
                for track, lines in payload.get("subtitles", {}).items()
            },
            contracts=[self._contract(item) for item in payload.get("contracts", [])],
            rating_policies=[self._rating(item) for item in payload.get("rating_policies", [])],
            historic_performance=list(payload.get("historic_performance", [])),
            cost_sheet=self._cost_sheet(payload.get("cost_sheet", {})),
            metadata=dict(payload.get("metadata", {})),
        )
        self.validate_package(episode)
        return episode

    @staticmethod
    def validate_package(episode: EpisodePackage) -> None:
        if episode.duration_seconds < 0:
            raise ValueError("Episode duration cannot be negative.")

        scene_ids: set[str] = set()
        for scene in episode.scenes:
            if scene.id in scene_ids:
                raise ValueError(f"Duplicate scene id: {scene.id}")
            scene_ids.add(scene.id)
            if scene.start < 0 or scene.end <= scene.start:
                raise ValueError(f"Invalid scene range: {scene.id}")
            if episode.duration_seconds and scene.end > episode.duration_seconds + 1e-6:
                raise ValueError(f"Scene {scene.id} extends beyond episode duration.")

        dialogue_ids: set[str] = set()
        for line in episode.dialogue:
            if line.id in dialogue_ids:
                raise ValueError(f"Duplicate dialogue id: {line.id}")
            dialogue_ids.add(line.id)
            if line.scene_id not in scene_ids:
                raise ValueError(f"Dialogue {line.id} references missing scene {line.scene_id}.")
            if not (line.start < line.end):
                raise ValueError(f"Invalid dialogue range: {line.id}")

    @staticmethod
    def _scene(item: dict[str, Any]) -> Scene:
        return Scene(
            id=str(item["id"]),
            start=float(item["start"]),
            end=float(item["end"]),
            description=str(item.get("description", "")),
            characters=[str(x) for x in item.get("characters", [])],
            relationship_claims=[str(x) for x in item.get("relationship_claims", [])],
            emotional_turn=item.get("emotional_turn"),
            event_tags=[str(x) for x in item.get("event_tags", [])],
            sensitive_content=[str(x) for x in item.get("sensitive_content", [])],
            spoiler_facts=[str(x) for x in item.get("spoiler_facts", [])],
            visual_evidence=[str(x) for x in item.get("visual_evidence", [])],
            audio_evidence=[str(x) for x in item.get("audio_evidence", [])],
            music_asset_id=item.get("music_asset_id"),
        )

    @staticmethod
    def _dialogue(item: dict[str, Any]) -> DialogueLine:
        return DialogueLine(
            id=str(item["id"]),
            scene_id=str(item["scene_id"]),
            start=float(item["start"]),
            end=float(item["end"]),
            speaker=str(item.get("speaker", "unknown")),
            text=str(item.get("text", "")),
            subtitle_variants={str(k): str(v) for k, v in item.get("subtitle_variants", {}).items()},
        )

    @staticmethod
    def _contract(item: dict[str, Any]) -> ContractRule:
        return ContractRule(
            id=str(item["id"]),
            asset_type=str(item.get("asset_type", "unknown")),
            asset_id=str(item.get("asset_id", "")),
            allowed=bool(item.get("allowed", True)),
            territories=[str(x) for x in item.get("territories", [])],
            promotional_use=bool(item.get("promotional_use", True)),
            valid_from=item.get("valid_from"),
            valid_until=item.get("valid_until"),
            notes=str(item.get("notes", "")),
            version=int(item.get("version", 1)),
        )

    @staticmethod
    def _rating(item: dict[str, Any]) -> RatingRule:
        return RatingRule(
            id=str(item["id"]),
            audience_id=str(item["audience_id"]),
            max_rating=str(item.get("max_rating", "")),
            blocked_terms=[str(x).lower() for x in item.get("blocked_terms", [])],
            blocked_tags=[str(x).lower() for x in item.get("blocked_tags", [])],
            notes=str(item.get("notes", "")),
        )

    @staticmethod
    def _cost_sheet(item: dict[str, Any]) -> CostSheet:
        return CostSheet(
            model_call_usd=float(item.get("model_call_usd", 0.0)),
            media_analysis_usd=float(item.get("media_analysis_usd", 0.0)),
            rendering_usd_per_second=float(item.get("rendering_usd_per_second", 0.0)),
            budget_usd=float(item.get("budget_usd", 0.0)),
        )
