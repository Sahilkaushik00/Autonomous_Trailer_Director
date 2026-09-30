"""Human-readable validation report generation."""

from __future__ import annotations

from src.models.schemas import TrailerPlan


class ReportBuilder:
    def validation_markdown(self, plans: list[TrailerPlan]) -> str:
        lines = ["# Validation Report", "", f"Plans evaluated: {len(plans)}", ""]
        for plan in plans:
            lines.extend([
                f"## {plan.trailer_id}",
                f"Audience: {plan.audience.name}",
                f"Revision: {plan.revision}",
                f"Status: **{plan.status}**",
                f"Duration: {plan.duration_seconds:.3f}s",
                f"Estimated cost: ${plan.estimated_cost_usd:.4f}",
                "",
            ])
            for result in plan.validation:
                lines.append(f"- `{result.validator}`: **{result.status}** ({len(result.issues)} issue(s))")
                for issue in result.issues:
                    lines.append(f"  - `{issue.code}` [{issue.severity}] {issue.message}")
            if plan.human_approvals_required:
                lines.append(f"- Human approvals: {', '.join(plan.human_approvals_required)}")
            lines.append("")
        return "\n".join(lines)
