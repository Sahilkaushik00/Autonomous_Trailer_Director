"""Model-provider abstraction.

The deterministic replay provider is usable during evaluation. A live provider can
implement this protocol without changing planning or validation contracts.
"""

from __future__ import annotations

from typing import Any, Protocol


class ModelProvider(Protocol):
    name: str

    def generate_json(self, task: str, context: dict[str, Any], schema: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
        ...


class ReplayModelProvider:
    name = "replay"

    def __init__(self, responses: dict[str, dict[str, Any]] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[str] = []

    def generate_json(self, task: str, context: dict[str, Any], schema: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
        self.calls.append(task)
        return dict(self.responses.get(task, {}))
