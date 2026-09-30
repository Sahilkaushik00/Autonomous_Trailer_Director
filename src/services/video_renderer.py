"""Optional FFmpeg renderer for validated trailer edit decision lists."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from src.models.schemas import TrailerPlan


class RenderError(RuntimeError):
    """Raised when FFmpeg cannot render a trailer."""


class FFmpegTrailerRenderer:
    def __init__(self, ffmpeg_binary: str | None = None) -> None:
        self.ffmpeg = ffmpeg_binary or shutil.which("ffmpeg")
        if not self.ffmpeg:
            raise RenderError("FFmpeg was not found on PATH.")

    def render(self, plan: TrailerPlan, source_video: Path, output_path: Path) -> dict[str, object]:
        if not source_video.is_file():
            raise FileNotFoundError(f"Source video not found: {source_video}")
        if plan.status == "FAIL":
            raise RenderError(f"Refusing to render {plan.trailer_id}: validation status is FAIL.")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="trailer_render_") as tmp:
            tmp_dir = Path(tmp)
            clip_paths: list[Path] = []
            for idx, segment in enumerate(plan.segments, 1):
                if segment.timecode.duration_seconds <= 0:
                    raise RenderError(f"Cannot render zero-length segment {segment.segment_id}.")
                clip = tmp_dir / f"clip_{idx:03d}.mp4"
                self._run(
                    [
                        self.ffmpeg,
                        "-y",
                        "-i",
                        str(source_video),
                        "-ss",
                        f"{segment.timecode.start:.3f}",
                        "-t",
                        f"{segment.timecode.duration_seconds:.3f}",
                        "-map",
                        "0:v:0",
                        "-map",
                        "0:a:0?",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "veryfast",
                        "-crf",
                        "20",
                        "-c:a",
                        "aac",
                        "-b:a",
                        "128k",
                        "-pix_fmt",
                        "yuv420p",
                        str(clip),
                    ]
                )
                clip_paths.append(clip)

            concat_file = tmp_dir / "concat.txt"
            concat_file.write_text("\n".join(f"file '{path.as_posix()}'" for path in clip_paths) + "\n", encoding="utf-8")
            self._run(
                [
                    self.ffmpeg,
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_file),
                    "-c",
                    "copy",
                    "-movflags",
                    "+faststart",
                    str(output_path),
                ]
            )

        return {
            "status": "RENDERED",
            "output": str(output_path),
            "segment_count": len(plan.segments),
            "duration_seconds": plan.duration_seconds,
            "notes": [
                "Rendering uses the source clip audio embedded in the selected segments.",
                "External replacement music, voice-over synthesis, and text-card composition remain separate editorial steps.",
            ],
        }

    def _run(self, command: list[str]) -> None:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RenderError((result.stderr or result.stdout or "FFmpeg failed").strip())
