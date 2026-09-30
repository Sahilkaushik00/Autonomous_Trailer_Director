"""Timecode parsing/formatting helpers."""

from __future__ import annotations

from src.models.schemas import seconds_to_timecode


def timecode_to_seconds(value: str) -> float:
    parts = value.strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid timecode: {value}")
    hours, minutes, seconds = parts
    result = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if result < 0:
        raise ValueError(f"Invalid timecode: {value}")
    return result


__all__ = ["seconds_to_timecode", "timecode_to_seconds"]
