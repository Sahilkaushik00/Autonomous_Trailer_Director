"""Verify promotional and territory rights for selected assets."""

from datetime import date

from src.models.schemas import ConstraintMap, EpisodePackage, StoryMap, TrailerPlan, ValidationIssue, ValidationResult


def _today_iso() -> str:
    return date.today().isoformat()


class RightsValidator:
    name = "rights"

    def validate(self, plan: TrailerPlan, episode: EpisodePackage, story: StoryMap, constraints: ConstraintMap) -> ValidationResult:
        issues: list[ValidationIssue] = []
        today = _today_iso()
        applicable = [c for c in episode.contracts if not c.allowed or not c.promotional_use or (c.valid_until and c.valid_until < today)]
        territory = plan.audience.territory
        for segment in plan.segments:
            for contract in applicable:
                references_asset = contract.asset_id in segment.video or contract.asset_id in segment.audio
                references_contract = any(ev.source_id == contract.id for ev in segment.evidence)
                territory_block = bool(territory and contract.territories and territory not in contract.territories)
                if references_asset or references_contract or territory_block:
                    detail = contract.asset_id
                    if territory_block:
                        detail += f" is not cleared for territory {territory}"
                    issues.append(ValidationIssue("RIGHTS_RESTRICTED", "hard_block", f"Restricted asset/contract: {detail}.", segment.segment_id, repair_hint="Replace the affected asset or segment and rerun rights validation."))
        return ValidationResult(self.name, "FAIL" if issues else "PASS", issues)
