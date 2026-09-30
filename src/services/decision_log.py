"""Structured, append-only decision logging."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.models.schemas import DecisionLogEntry, Evidence, to_dict


class DecisionLogger:
    def __init__(self) -> None:
        self.entries: list[DecisionLogEntry] = []

    def record(
        self,
        decision_id: str,
        trailer_id: str,
        stage: str,
        action: str,
        reason: str,
        evidence: list[Evidence] | None = None,
        changed_by_event: str | None = None,
        revision: int = 1,
    ) -> None:
        self.entries.append(
            DecisionLogEntry(
                decision_id=decision_id,
                trailer_id=trailer_id,
                stage=stage,
                action=action,
                reason=reason,
                evidence=evidence or [],
                changed_by_event=changed_by_event,
                revision=revision,
            )
        )

    def export(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        return [{**to_dict(entry), "logged_at": now} for entry in self.entries]
