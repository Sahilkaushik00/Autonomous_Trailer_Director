"""Budget gate for model/media/render costs."""

from src.models.schemas import ConstraintMap, EpisodePackage, StoryMap, TrailerPlan, ValidationIssue, ValidationResult
from src.services.cost_estimator import within_budget


class BudgetValidator:
    name = "budget"

    def validate(self, plan: TrailerPlan, episode: EpisodePackage, story: StoryMap, constraints: ConstraintMap) -> ValidationResult:
        if within_budget(plan.estimated_cost_usd, episode.cost_sheet):
            return ValidationResult(self.name, "PASS", [])
        return ValidationResult(
            self.name,
            "FAIL",
            [ValidationIssue("BUDGET_EXCEEDED", "hard_block", f"Estimated cost ${plan.estimated_cost_usd:.4f} exceeds budget ${episode.cost_sheet.budget_usd:.4f}.", repair_hint="Use the lower-cost fallback plan or reduce expensive processing calls.")],
        )
