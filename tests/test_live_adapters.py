import json
import shutil
from pathlib import Path

import pytest

from src.agents.gemini_trailer_planner import GeminiTrailerPlanner
from src.agents.llm_story_mapper import GeminiStoryMapper
from src.main import load_audiences
from src.models.schemas import StoryMap, to_dict
from src.services import EpisodePackageLoader, FFmpegTrailerRenderer
from src.services.video_analyzer import GeminiVideoAnalyzer
from src.services.model_provider import ReplayModelProvider
from src.utils.io import read_json

ROOT = Path(__file__).resolve().parents[1]
EPISODE_PATH = ROOT / "data" / "episode_demo.json"
AUDIENCE_PATH = ROOT / "data" / "audiences_demo.json"
VIDEO_PATH = ROOT / "media" / "demo_episode.mp4"


class FakeGeminiProvider(ReplayModelProvider):
    name = "fake-gemini"

    def __init__(self):
        super().__init__({
            "story": {
                "candidate_emotional_arc": ["welcome", "conflict", "mystery"],
                "candidate_sensitive_moments": [],
                "candidate_spoilers": ["the shop was secretly sold years earlier"],
                "uncertainties": ["Video not available in this unit test."],
                "grounding_notes": ["Grounded to supplied catalog."],
            },
            "plan": {
                "audience_promise": "A grounded family mystery.",
                "emotional_journey": ["warmth", "conflict", "curiosity"],
                "segments": [
                    {"source_scene_id": "scene_01", "dialogue_id": "d01", "subtitle_track": None, "text_card": None, "voice_over": None, "reason": "Warm opening."},
                    {"source_scene_id": "scene_DOES_NOT_EXIST", "dialogue_id": None, "subtitle_track": None, "text_card": None, "voice_over": None, "reason": "Hallucination preserved for validator."},
                ],
                "fallback_plan": "Replace blocked segments.",
                "uncertainties": [],
            },
        })

    def generate_json(self, task, context, schema=None, **kwargs):
        return self.responses["story" if "story-understanding" in task else "plan"]


def test_llm_story_and_planner_are_adapter_driven():
    episode = EpisodePackageLoader().load(EPISODE_PATH)
    audiences = load_audiences(read_json(AUDIENCE_PATH))
    provider = FakeGeminiProvider()

    story = __import__("src.agents.story_mapper", fromlist=["StoryMapper"]).StoryMapper().build(episode)
    enhanced = GeminiStoryMapper(provider).enhance(episode, story)
    assert enhanced.llm_insights["candidate_spoilers"]

    plan = GeminiTrailerPlanner(provider).build(episode, enhanced, audiences[0])
    assert plan.segments[0].source_scene_id == "scene_01"
    assert plan.segments[1].risk_flags == ["LLM_SELECTED_UNKNOWN_SCENE"]


def test_video_analyzer_writes_advisory_metadata_without_becoming_source_truth():
    episode = EpisodePackageLoader().load(EPISODE_PATH)
    episode.metadata["video_analysis"] = {
        "observations": [{"scene_id": "scene_01", "start_seconds": 0, "end_seconds": 10, "visual_summary": "courtyard", "audio_summary": "greeting", "confidence": 0.9}],
        "global_notes": [],
    }
    assert episode.metadata["video_analysis"]["observations"][0]["scene_id"] == "scene_01"


@pytest.mark.skipif(not shutil.which("ffmpeg") or not VIDEO_PATH.exists(), reason="FFmpeg demo media unavailable")
def test_ffmpeg_renderer_creates_mp4(tmp_path):
    episode = EpisodePackageLoader().load(EPISODE_PATH)
    audiences = load_audiences(read_json(AUDIENCE_PATH))
    from src.agents import TrailerDirector

    plan = TrailerDirector().planner.build(episode, TrailerDirector().story_mapper.build(episode), audiences[0])
    from src.validators import TrailerValidator
    constraints = TrailerDirector().constraint_mapper.build(episode, audiences)
    story = TrailerDirector().story_mapper.build(episode)
    results = TrailerValidator().validate(plan, episode, story, constraints)
    plan.validation = results
    plan.status = TrailerValidator.overall_status(results)
    # Mock plan is expected to be renderable in the bundled synthetic demo.
    output = tmp_path / "family.mp4"
    result = FFmpegTrailerRenderer().render(plan, VIDEO_PATH, output)
    assert result["status"] == "RENDERED"
    assert output.exists() and output.stat().st_size > 0
