"""Provider-agnostic video grounding service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.models.schemas import EpisodePackage
from src.services.model_provider import ModelProvider


VIDEO_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene_id": {"type": ["string", "null"]},
                    "start_seconds": {"type": "number"},
                    "end_seconds": {"type": "number"},
                    "visual_summary": {"type": "string"},
                    "audio_summary": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["scene_id", "start_seconds", "end_seconds", "visual_summary", "audio_summary", "confidence"],
            },
        },
        "global_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["observations", "global_notes"],
}


class VideoAnalyzer:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def analyze(self, video_path: Path, episode: EpisodePackage) -> dict[str, Any]:
        scene_catalog = [
            {"id": s.id, "start": s.start, "end": s.end, "description": s.description}
            for s in episode.scenes
        ]
        result = self.provider.analyze_video(
            video_path,
            "Return timestamped visual observations for the episode. Align observations to supplied scene IDs "
            "when the visual evidence supports it. The video is evidence; the supplied package remains authoritative "
            "for contracts, ratings, and known spoiler facts. Pay special attention to important mismatches.",
            VIDEO_ANALYSIS_SCHEMA,
        )
        result["scene_catalog"] = scene_catalog
        episode.metadata["video_analysis"] = result
        episode.metadata["video_path"] = str(video_path)
        return result


# Backward-compatible name.
GeminiVideoAnalyzer = VideoAnalyzer
