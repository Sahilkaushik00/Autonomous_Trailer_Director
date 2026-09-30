"""Translate contracts, audience policies and supplied safeguards into rules."""

from __future__ import annotations

from src.models.schemas import AudienceProfile, Constraint, ConstraintMap, EpisodePackage


class ConstraintMapper:
    def build(self, episode: EpisodePackage, audiences: list[AudienceProfile]) -> ConstraintMap:
        constraints = [
            Constraint("source.scene_exists", "source_accuracy", "Every selected scene must exist in the episode package.", "hard_block"),
            Constraint("source.timecodes_valid", "source_accuracy", "Every selected timecode must be inside its source scene.", "hard_block"),
            Constraint("story.no_major_spoilers", "spoiler", "Protected facts must not be disclosed.", "hard_block"),
            Constraint("story.truth", "story_truth", "Do not imply unsupported relationships, threats or promises.", "hard_block"),
            Constraint("accessibility.readable_text", "accessibility", "Text/subtitles should remain usable without depending only on audio.", "error"),
            Constraint("rights.valid_contract", "rights", "Selected assets must be permitted for promotional use and territory at plan time.", "hard_block"),
            Constraint("budget.within_limit", "budget", "Estimated processing cost must remain within the configured budget.", "hard_block"),
        ]
        for contract in episode.contracts:
            constraints.append(
                Constraint(
                    id=f"rights.{contract.id}",
                    category="rights",
                    rule=f"Asset {contract.asset_id}: allowed={contract.allowed}, promotional_use={contract.promotional_use}.",
                    severity="hard_block",
                    applies_to=[contract.asset_id],
                    evidence=[f"contract:{contract.id}"],
                )
            )
        for policy in episode.rating_policies:
            constraints.append(
                Constraint(
                    id=f"rating.{policy.id}",
                    category="audience_safety",
                    rule=f"Audience {policy.audience_id}: max_rating={policy.max_rating}.",
                    severity="hard_block",
                    applies_to=[policy.audience_id],
                    evidence=[f"rating_policy:{policy.id}"],
                )
            )
        for audience in audiences:
            constraints.append(
                Constraint(
                    id=f"audience.{audience.id}.respect",
                    category="cultural_respect",
                    rule=audience.special_care,
                    severity="hard_block",
                    applies_to=[audience.id],
                    evidence=[f"audience:{audience.id}"],
                )
            )
        return ConstraintMap(constraints=constraints, version=1)
