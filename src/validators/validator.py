"""Independent validator suite and overall status logic."""

from __future__ import annotations

from src.models.schemas import ConstraintMap, EpisodePackage, StoryMap, TrailerPlan, ValidationResult
from src.validators.accessibility import AccessibilityValidator
from src.validators.budget import BudgetValidator
from src.validators.input_safety import InputSafetyValidator
from src.validators.bias import AudienceBiasValidator
from src.validators.cultural import CulturalRespectValidator
from src.validators.policy import PolicyValidator
from src.validators.rights import RightsValidator
from src.validators.source_accuracy import SourceAccuracyValidator
from src.validators.spoiler import SpoilerValidator
from src.validators.truth import StoryTruthValidator
from src.validators.video_grounding import VideoGroundingValidator


class TrailerValidator:
    def __init__(self) -> None:
        self.validators = [
            SourceAccuracyValidator(),
            SpoilerValidator(),
            StoryTruthValidator(),
            RightsValidator(),
            PolicyValidator(),
            CulturalRespectValidator(),
            AccessibilityValidator(),
            BudgetValidator(),
            AudienceBiasValidator(),
            InputSafetyValidator(),
            VideoGroundingValidator(),
        ]

    def validate(self, plan: TrailerPlan, episode: EpisodePackage, story: StoryMap, constraints: ConstraintMap) -> list[ValidationResult]:
        return [validator.validate(plan, episode, story, constraints) for validator in self.validators]

    @staticmethod
    def overall_status(results: list[ValidationResult]) -> str:
        if any(result.status == "FAIL" for result in results):
            return "FAIL"
        if any(result.status == "PASS_WITH_WARNINGS" for result in results):
            return "PASS_WITH_WARNINGS"
        return "PASS"
