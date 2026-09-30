"""Cultural-respect checks for regional/dialect personalization."""

from src.models.schemas import ConstraintMap, EpisodePackage, StoryMap, TrailerPlan, ValidationIssue, ValidationResult


class CulturalRespectValidator:
    name = "cultural_respect"
    stereotype_terms = {"funny accent", "backward", "primitive", "uncultured", "comic accent"}

    def validate(self, plan: TrailerPlan, episode: EpisodePackage, story: StoryMap, constraints: ConstraintMap) -> ValidationResult:
        if plan.audience.id != "dialect_region":
            return ValidationResult(self.name, "PASS", [])
        issues: list[ValidationIssue] = []
        for segment in plan.segments:
            content = " ".join([segment.reason, segment.text_card or "", segment.voice_over or "", segment.subtitle or ""]).lower()
            hits = sorted(term for term in self.stereotype_terms if term in content)
            if hits:
                issues.append(ValidationIssue("DIALECT_STEREOTYPE", "hard_block", f"Potentially stereotypical framing: {', '.join(hits)}.", segment.segment_id, repair_hint="Anchor personalization in supplied language/context evidence."))
        return ValidationResult(self.name, "FAIL" if issues else "PASS", issues)
