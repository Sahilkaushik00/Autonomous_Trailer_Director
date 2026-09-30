"""Replayable evaluator scenarios for the surprise events in the brief."""

from __future__ import annotations

from copy import deepcopy

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents import TrailerDirector
from src.models.schemas import ChangeEvent, ContractRule, EpisodePackage, TrailerPlan


class ScenarioRunner:
    """Run controlled changes against an existing plan without needing external APIs."""

    def __init__(self, director: "TrailerDirector" | None = None) -> None:
        if director is None:
            from src.agents import TrailerDirector
            director = TrailerDirector()
        self.director = director

    def contract_expiry(self, episode: EpisodePackage, plan: TrailerPlan, audiences) -> TrailerPlan:
        affected = next((c for c in episode.contracts if any(c.asset_id in s.audio for s in plan.segments)), None)
        if affected is None:
            return deepcopy(plan)
        event = ChangeEvent(
            event_id=f"expire:{affected.id}",
            event_type="contract_changed",
            message=f"Contract {affected.id} expired after planning.",
            target_ids=[affected.id],
            payload={
                "contract": {
                    "id": affected.id,
                    "asset_type": affected.asset_type,
                    "asset_id": affected.asset_id,
                    "allowed": False,
                    "territories": affected.territories,
                    "promotional_use": False,
                    "valid_until": "2000-01-01",
                    "notes": "Replay scenario: license expired.",
                    "version": affected.version + 1,
                }
            },
        )
        updated = deepcopy(episode)
        for idx, contract in enumerate(updated.contracts):
            if contract.id == affected.id:
                updated.contracts[idx] = ContractRule(**event.payload["contract"])
        return self.director.apply_change_event(plan, updated, audiences, event)
