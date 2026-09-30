"""CLI entry point for the Autonomous Trailer Director."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # Optional for mock/replay mode.
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False

from src.agents import TrailerDirector
from src.models.schemas import AudienceProfile, to_dict
from src.services import EpisodePackageLoader
from src.services.cost_estimator import estimate_cost
from src.services.gemini_provider import GeminiModelProvider, GeminiProviderError
from src.services.ollama_provider import OllamaModelProvider, OllamaProviderError
from src.services.video_analyzer import VideoAnalyzer
from src.services.video_renderer import FFmpegTrailerRenderer, RenderError
from src.utils.io import read_json, write_json

load_dotenv()

SUPPORTED_AUDIENCES = {
    "family": "family viewers",
    "young_adult": "young adult viewers",
    "dialect_region": "dialect-region viewers",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trailer-director",
        description="Plan, verify, optionally analyze, and render audience-specific trailers.",
    )
    parser.add_argument("--episode", type=Path, required=True, help="Episode package JSON")
    parser.add_argument("--audiences", type=Path, required=True, help="Audience definitions JSON")
    parser.add_argument("--mode", choices=("mock", "replay", "live"), default="mock")
    parser.add_argument("--video", type=Path, default=None, help="Optional source episode MP4 for local VLM/cloud grounding and rendering")
    parser.add_argument("--render", action="store_true", help="Render validated trailers with FFmpeg")
    parser.add_argument("--render-dir", type=Path, default=Path("sample_run/rendered"))
    parser.add_argument("--provider", choices=("local", "gemini"), default=os.getenv("TRAILER_LLM_PROVIDER", "local"), help="Live LLM provider")
    parser.add_argument("--model", default=None, help="Model name; defaults to provider-specific environment setting")
    parser.add_argument("--ollama-host", default=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    parser.add_argument("--output", type=Path, default=Path("sample_run/run_summary.json"))
    return parser


def load_audiences(payload: Any) -> list[AudienceProfile]:
    values = payload.get("audiences", payload) if isinstance(payload, dict) else payload
    if isinstance(values, dict):
        items = [{"id": key, **(value if isinstance(value, dict) else {"goal": str(value)})} for key, value in values.items()]
    elif isinstance(values, list):
        items = values
    else:
        raise ValueError("Audience definitions must be a JSON object or list.")

    result: list[AudienceProfile] = []
    for item in items:
        audience_id = str(item["id"])
        result.append(
            AudienceProfile(
                id=audience_id,
                name=SUPPORTED_AUDIENCES.get(audience_id, audience_id),
                goal=str(item.get("goal", "")),
                special_care=str(item.get("special_care", "")),
                territory=item.get("territory"),
                preferred_language=item.get("preferred_language"),
                dialect=item.get("dialect"),
                engagement_signals={str(k): float(v) for k, v in item.get("engagement_signals", {}).items()},
            )
        )
    return result


def run_pipeline(
    episode_path: Path,
    audiences_path: Path,
    mode: str,
    *,
    video_path: Path | None = None,
    render: bool = False,
    render_dir: Path = Path("sample_run/rendered"),
    model: str | None = None,
    provider_name: str = "local",
    ollama_host: str | None = None,
) -> dict[str, Any]:
    episode = EpisodePackageLoader().load(episode_path)
    audiences = load_audiences(read_json(audiences_path))

    provider = None
    video_analysis = None
    if mode == "live":
        if provider_name == "local":
            provider = OllamaModelProvider(model=model, host=ollama_host)
        else:
            provider = GeminiModelProvider(model=model)
        if video_path:
            video_analysis = VideoAnalyzer(provider).analyze(video_path, episode)
    elif mode not in {"mock", "replay"}:
        raise ValueError(f"Unsupported mode: {mode}")

    director = TrailerDirector(model_provider=provider)
    plans, logger = director.run(episode, audiences)

    # Shared story understanding + one creative model call per audience.
    model_calls = provider.calls if provider else 0
    media_calls = provider.media_calls if provider else 0
    per_call_cost = episode.cost_sheet.model_call_usd if provider_name == "gemini" else 0.0
    media_call_cost = episode.cost_sheet.media_analysis_usd if provider_name == "gemini" else 0.0
    for plan in plans:
        plan.estimated_cost_usd = estimate_cost(
            plan,
            type(episode.cost_sheet)(
                model_call_usd=per_call_cost,
                media_analysis_usd=media_call_cost,
                rendering_usd_per_second=episode.cost_sheet.rendering_usd_per_second,
                budget_usd=episode.cost_sheet.budget_usd,
            ),
            model_calls=(1 if provider else 0),
            media_calls=0,
        )

    rendered: dict[str, Any] = {}
    if render:
        if not video_path:
            raise ValueError("--render requires --video PATH")
        renderer = FFmpegTrailerRenderer()
        for plan in plans:
            if plan.status == "FAIL":
                rendered[plan.trailer_id] = {"status": "SKIPPED", "reason": "Validation status is FAIL."}
                continue
            output_path = render_dir / f"{plan.trailer_id}.mp4"
            rendered[plan.trailer_id] = renderer.render(plan, video_path, output_path)

    overall = (
        "FAIL"
        if any(plan.status == "FAIL" for plan in plans)
        else "PASS_WITH_WARNINGS"
        if any(plan.status == "PASS_WITH_WARNINGS" for plan in plans)
        else "PASS"
    )
    creative_calls = len(plans) if provider else 0
    shared_model_calls = max(0, model_calls - creative_calls)
    total_estimated_cost = round(
        sum(plan.estimated_cost_usd for plan in plans)
        + shared_model_calls * per_call_cost
        + media_calls * media_call_cost,
        6,
    )
    return {
        "system": "autonomous_trailer_director",
        "mode": mode,
        "provider": provider.name if provider else None,
        "model": provider.model if provider else None,
        "model_calls": model_calls,
        "media_calls": media_calls,
        "episode": to_dict(episode),
        "audiences": to_dict(audiences),
        "trailers": to_dict(plans),
        "decision_log": logger.export(),
        "video_analysis": video_analysis,
        "rendered": rendered,
        "estimated_total_cost_usd": total_estimated_cost,
        "validation": {"status": overall},
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_pipeline(
            args.episode,
            args.audiences,
            args.mode,
            video_path=args.video,
            render=args.render,
            render_dir=args.render_dir,
            model=args.model,
            provider_name=args.provider,
            ollama_host=args.ollama_host,
        )
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, GeminiProviderError, OllamaProviderError, RenderError) as exc:
        parser.error(str(exc))
    print(f"Pipeline completed: {args.output}")
    print(f"Mode: {args.mode}")
    if args.mode == "live":
        print(f"Provider: {result['provider']} | model: {result['model']}")
        print(f"LLM calls: {result['model_calls']} | media calls: {result['media_calls']}")
    print(f"Trailers generated: {len(result['trailers'])}")
    print(f"Overall validation: {result['validation']['status']}")
    if args.render:
        print(f"Rendered outputs: {args.render_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
