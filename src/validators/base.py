"""Validator protocol and shared helpers."""

from __future__ import annotations

from typing import Protocol

from src.models.schemas import EpisodePackage, StoryMap, ConstraintMap, TrailerPlan, ValidationResult


class Validator(Protocol):
    name: str

    def validate(
        self,
        plan: TrailerPlan,
        episode: EpisodePackage,
        story: StoryMap,
        constraints: ConstraintMap,
    ) -> ValidationResult:
        ...
