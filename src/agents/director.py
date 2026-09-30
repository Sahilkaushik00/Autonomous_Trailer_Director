"""Top-level autonomous workflow: strategy -> plan -> verify -> repair -> reverify."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from src.agents.constraint_mapper import ConstraintMapper
from src.agents.gemini_trailer_planner import LLMTrailerPlanner
from src.agents.llm_story_mapper import LLMStoryMapper
from src.agents.repair_agent import RepairAgent
from src.agents.replanner import Replanner
from src.agents.story_mapper import StoryMapper
from src.agents.trailer_planner import TrailerPlanner
from src.models.schemas import AudienceProfile, ChangeEvent, EpisodePackage, TrailerPlan
from src.services.change_impact import ChangeImpactAnalyzer
from src.services.cost_estimator import estimate_cost
from src.services.decision_log import DecisionLogger
from src.services.model_provider import ModelProvider
from src.validators.validator import TrailerValidator


class TrailerDirector:
    """Orchestrate creative decisions and independent verification gates."""

    def __init__(
        self,
        max_repair_rounds: int = 2,
        model_provider: ModelProvider | None = None,
        planner: Any | None = None,
    ) -> None:
        self.story_mapper = StoryMapper()
        self.llm_story_mapper = LLMStoryMapper(model_provider) if model_provider else None
        self.constraint_mapper = ConstraintMapper()
        self.planner = planner or (LLMTrailerPlanner(model_provider) if model_provider else TrailerPlanner())
        self.validator = TrailerValidator()
        self.repairer = RepairAgent()
        self.replanner = Replanner()
        self.impact_analyzer = ChangeImpactAnalyzer()
        self.model_provider = model_provider
        self.max_repair_rounds = max_repair_rounds

    def run(self, episode: EpisodePackage, audiences: list[AudienceProfile]) -> tuple[list[TrailerPlan], DecisionLogger]:
        story = self.story_mapper.build(episode)
        if self.llm_story_mapper:
            story = self.llm_story_mapper.enhance(episode, story)
        constraints = self.constraint_mapper.build(episode, audiences)
        logger = DecisionLogger()
        plans: list[TrailerPlan] = []

        for audience in audiences:
            plan = self.planner.build(episode, story, audience)
            logger.record(
                f"plan:{plan.trailer_id}:1",
                plan.trailer_id,
                "planning",
                "create_plan",
                plan.audience_promise,
                revision=plan.revision,
            )
            plan = self._validate_with_repair(plan, episode, story, constraints, logger)
            plan.estimated_cost_usd = estimate_cost(
                plan,
                episode.cost_sheet,
                model_calls=1 if self.model_provider else 0,
            )
            plans.append(plan)

        return plans, logger

    def _validate_with_repair(
        self,
        plan: TrailerPlan,
        episode: EpisodePackage,
        story,
        constraints,
        logger: DecisionLogger,
        *,
        changed_by_event: str | None = None,
    ) -> TrailerPlan:
        for round_number in range(1, self.max_repair_rounds + 2):
            results = self.validator.validate(plan, episode, story, constraints)
            plan = replace(plan, validation=results, status=self.validator.overall_status(results))
            logger.record(
                f"validate:{plan.trailer_id}:{plan.revision}:{round_number}",
                plan.trailer_id,
                "validation",
                "validate" if round_number == 1 else "revalidate",
                plan.status,
                changed_by_event=changed_by_event,
                revision=plan.revision,
            )
            if plan.status != "FAIL" or round_number > self.max_repair_rounds:
                break
            repaired = self.repairer.repair(plan, episode, results, changed_by_event=changed_by_event)
            if repaired.revision == plan.revision:
                break
            plan = repaired
            logger.record(
                f"repair:{plan.trailer_id}:{plan.revision}",
                plan.trailer_id,
                "repair",
                "replace_blocked_segments",
                "Repair was driven by independent validator evidence.",
                changed_by_event=changed_by_event,
                revision=plan.revision,
            )
        return plan

    def apply_change_event(self, plan: TrailerPlan, episode: EpisodePackage, audiences: list[AudienceProfile], event: ChangeEvent) -> TrailerPlan:
        """Apply a change, revise only affected decisions, and rerun relevant safety gates."""
        story = self.story_mapper.build(episode)
        constraints = self.constraint_mapper.build(episode, audiences)
        impacted = self.impact_analyzer.affected_validators(event)

        revised = plan
        if event.event_type == "contract_changed":
            revised = self.replanner.apply_event(plan, episode, event)
        elif event.event_type == "marketing_request":
            revised = replace(plan, revision=plan.revision + 1)
        elif event.event_type == "subtitle_changed":
            revised = replace(plan, revision=plan.revision + 1)

        revised.assumptions = list(revised.assumptions) + [
            f"Change {event.event_id} impacted validators: {', '.join(sorted(impacted))}."
        ]
        return self._validate_with_repair(
            revised, episode, story, constraints, DecisionLogger(), changed_by_event=event.event_id
        )
