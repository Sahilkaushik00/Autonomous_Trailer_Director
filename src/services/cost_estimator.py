"""Deterministic model/media/render cost estimation."""

from __future__ import annotations

from src.models.schemas import CostSheet, TrailerPlan


def estimate_cost(plan: TrailerPlan, cost_sheet: CostSheet, *, model_calls: int = 0, media_calls: int = 0) -> float:
    planning_cost = model_calls * cost_sheet.model_call_usd
    media_cost = media_calls * cost_sheet.media_analysis_usd
    render_cost = plan.duration_seconds * cost_sheet.rendering_usd_per_second
    return round(planning_cost + media_cost + render_cost, 6)


def within_budget(estimated_cost_usd: float, cost_sheet: CostSheet) -> bool:
    return cost_sheet.budget_usd <= 0 or estimated_cost_usd <= cost_sheet.budget_usd
