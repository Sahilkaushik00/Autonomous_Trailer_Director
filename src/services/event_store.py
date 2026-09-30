"""Small append-only event store used by replay mode and debugging."""

from __future__ import annotations

from src.models.schemas import ChangeEvent, to_dict


class EventStore:
    def __init__(self) -> None:
        self.events: list[ChangeEvent] = []

    def append(self, event: ChangeEvent) -> None:
        self.events.append(event)

    def export(self) -> list[dict]:
        return [to_dict(event) for event in self.events]
