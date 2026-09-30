from pathlib import Path

from src.main import load_audiences, run_pipeline
from src.utils.io import read_json

ROOT = Path(__file__).resolve().parents[1]


def test_loads_three_target_audiences():
    payload = read_json(ROOT / "data" / "audiences_demo.json")
    audiences = load_audiences(payload)
    assert [a.id for a in audiences] == ["family", "young_adult", "dialect_region"]


def test_mock_pipeline_returns_three_trailers():
    result = run_pipeline(ROOT / "data" / "episode_demo.json", ROOT / "data" / "audiences_demo.json", "mock")
    assert len(result["trailers"]) == 3
    assert result["mode"] == "mock"
    assert result["validation"]["status"] in {"PASS", "PASS_WITH_WARNINGS", "FAIL"}


def test_run_demo_skips_optional_render_without_ffmpeg(monkeypatch, tmp_path):
    import run_demo

    monkeypatch.setattr(run_demo.shutil, "which", lambda name: None)
    assert run_demo.main() == 0

    summary = run_demo.read_json(run_demo.ROOT / "sample_run" / "run_summary.json")
    assert len(summary["trailers"]) == 3
    assert all(item["status"] == "SKIPPED" for item in summary["renders"].values())
