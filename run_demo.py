"""Generate deterministic sample artifacts and optionally render the synthetic demo video."""

from pathlib import Path
import shutil

from src.agents import TrailerDirector
from src.main import load_audiences
from src.models.schemas import to_dict
from src.services import EpisodePackageLoader, FFmpegTrailerRenderer, ReportBuilder
from src.utils.io import read_json, write_json, write_text


ROOT = Path(__file__).resolve().parent


def main() -> int:
    episode_path = ROOT / "data" / "episode_demo.json"
    audiences_path = ROOT / "data" / "audiences_demo.json"
    video_path = ROOT / "media" / "demo_episode.mp4"

    episode = EpisodePackageLoader().load(episode_path)
    audiences = load_audiences(read_json(audiences_path))
    director = TrailerDirector()
    plans, logger = director.run(episode, audiences)

    sample = ROOT / "sample_run"
    submission = ROOT / "submission"
    render_dir = sample / "rendered"
    sample.mkdir(exist_ok=True)
    submission.mkdir(exist_ok=True)

    for plan in plans:
        name = {
            "family": "family_trailer.json",
            "young_adult": "young_adult_trailer.json",
            "dialect_region": "dialect_region_trailer.json",
        }[plan.audience.id]
        write_json(sample / name, to_dict(plan))

    story = director.story_mapper.build(episode)
    constraints = director.constraint_mapper.build(episode, audiences)
    write_json(sample / "story_map.json", to_dict(story))
    write_json(sample / "constraint_map.json", to_dict(constraints))
    write_json(sample / "decision_log.json", logger.export())
    write_text(submission / "validation_report.md", ReportBuilder().validation_markdown(plans))

    renders = {}
    if video_path.exists():
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            for plan in plans:
                renders[plan.trailer_id] = {
                    "status": "SKIPPED",
                    "reason": "FFmpeg is not installed or not on PATH. Rendering is optional; edit-decision-list artifacts were still generated.",
                }
            print("FFmpeg not found: skipping optional video rendering.")
        else:
            renderer = FFmpegTrailerRenderer(ffmpeg_binary=ffmpeg_path)
            for plan in plans:
                if plan.status == "FAIL":
                    renders[plan.trailer_id] = {"status": "SKIPPED", "reason": "Validation failed."}
                else:
                    renders[plan.trailer_id] = renderer.render(
                        plan, video_path, render_dir / f"{plan.trailer_id}.mp4"
                    )

    overall = (
        "FAIL"
        if any(p.status == "FAIL" for p in plans)
        else "PASS_WITH_WARNINGS"
        if any(p.status == "PASS_WITH_WARNINGS" for p in plans)
        else "PASS"
    )
    write_json(sample / "run_summary.json", {
        "system": "autonomous_trailer_director",
        "mode": "mock",
        "episode_id": episode.episode_id,
        "overall_validation": overall,
        "trailers": [plan.trailer_id for plan in plans],
        "renders": renders,
        "artifacts": [
            "story_map.json",
            "constraint_map.json",
            "family_trailer.json",
            "young_adult_trailer.json",
            "dialect_region_trailer.json",
            "decision_log.json",
        ],
    })
    print(f"Generated {len(plans)} trailer plans with overall status {overall}.")
    print(f"Artifacts: {sample}")
    rendered_count = sum(1 for item in renders.values() if item.get("status") == "RENDERED")
    skipped_count = sum(1 for item in renders.values() if item.get("status") == "SKIPPED")
    if rendered_count:
        print(f"Rendered demo trailers ({rendered_count}): {render_dir}")
    elif skipped_count:
        print(f"Optional video rendering skipped ({skipped_count} trailers). Edit decision lists are ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
