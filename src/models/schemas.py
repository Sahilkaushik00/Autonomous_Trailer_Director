"""Domain models for the Autonomous Trailer Director.

The project deliberately keeps the core data contract in standard-library dataclasses.
A model provider can be swapped in later without changing the validators or output schema.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ValidationStatus = Literal["PASS", "PASS_WITH_WARNINGS", "FAIL", "NOT_RUN"]
Severity = Literal["info", "warning", "error", "hard_block"]
AudienceID = Literal["family", "young_adult", "dialect_region"]


@dataclass(frozen=True)
class Timecode:
    start: float
    end: float
    source_in: str
    source_out: str

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class DialogueLine:
    id: str
    scene_id: str
    start: float
    end: float
    speaker: str
    text: str
    subtitle_variants: dict[str, str] = field(default_factory=dict)


@dataclass
class Scene:
    id: str
    start: float
    end: float
    description: str
    characters: list[str] = field(default_factory=list)
    relationship_claims: list[str] = field(default_factory=list)
    emotional_turn: str | None = None
    event_tags: list[str] = field(default_factory=list)
    sensitive_content: list[str] = field(default_factory=list)
    spoiler_facts: list[str] = field(default_factory=list)
    visual_evidence: list[str] = field(default_factory=list)
    audio_evidence: list[str] = field(default_factory=list)
    music_asset_id: str | None = None

    @property
    def timecode(self) -> Timecode:
        return Timecode(
            start=self.start,
            end=self.end,
            source_in=seconds_to_timecode(self.start),
            source_out=seconds_to_timecode(self.end),
        )


@dataclass
class ContractRule:
    id: str
    asset_type: str
    asset_id: str
    allowed: bool = True
    territories: list[str] = field(default_factory=list)
    promotional_use: bool = True
    valid_from: str | None = None
    valid_until: str | None = None
    notes: str = ""
    version: int = 1


@dataclass
class RatingRule:
    id: str
    audience_id: str
    max_rating: str
    blocked_terms: list[str] = field(default_factory=list)
    blocked_tags: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class AudienceProfile:
    id: str
    name: str
    goal: str
    special_care: str
    territory: str | None = None
    preferred_language: str | None = None
    dialect: str | None = None
    engagement_signals: dict[str, float] = field(default_factory=dict)


@dataclass
class CostSheet:
    model_call_usd: float = 0.0
    media_analysis_usd: float = 0.0
    rendering_usd_per_second: float = 0.0
    budget_usd: float = 0.0


@dataclass
class EpisodePackage:
    episode_id: str
    duration_seconds: float
    scenes: list[Scene] = field(default_factory=list)
    dialogue: list[DialogueLine] = field(default_factory=list)
    subtitles: dict[str, list[DialogueLine]] = field(default_factory=dict)
    contracts: list[ContractRule] = field(default_factory=list)
    rating_policies: list[RatingRule] = field(default_factory=list)
    historic_performance: list[dict[str, Any]] = field(default_factory=list)
    cost_sheet: CostSheet = field(default_factory=CostSheet)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StoryMap:
    episode_id: str
    characters: dict[str, dict[str, Any]] = field(default_factory=dict)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    major_events: list[dict[str, Any]] = field(default_factory=list)
    emotional_turns: list[dict[str, Any]] = field(default_factory=list)
    spoiler_facts: list[str] = field(default_factory=list)
    sensitive_content: list[dict[str, Any]] = field(default_factory=list)
    # Advisory LLM insights are stored separately so deterministic source facts remain authoritative.
    llm_insights: dict[str, Any] = field(default_factory=dict)


@dataclass
class Constraint:
    id: str
    category: str
    rule: str
    severity: Severity
    applies_to: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass
class ConstraintMap:
    constraints: list[Constraint] = field(default_factory=list)
    version: int = 1


@dataclass
class Evidence:
    source_type: str
    source_id: str
    detail: str


@dataclass
class TrailerSegment:
    segment_id: str
    source_scene_id: str
    timecode: Timecode
    video: str
    audio: str
    subtitle: str | None = None
    text_card: str | None = None
    voice_over: str | None = None
    reason: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)


@dataclass
class ValidationIssue:
    code: str
    severity: Severity
    message: str
    segment_id: str | None = None
    evidence: list[Evidence] = field(default_factory=list)
    repair_hint: str | None = None


@dataclass
class ValidationResult:
    validator: str
    status: ValidationStatus
    issues: list[ValidationIssue] = field(default_factory=list)


@dataclass
class TrailerPlan:
    trailer_id: str
    audience: AudienceProfile
    duration_seconds: float
    audience_promise: str
    emotional_journey: list[str]
    segments: list[TrailerSegment] = field(default_factory=list)
    validation: list[ValidationResult] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    human_approvals_required: list[str] = field(default_factory=list)
    estimated_cost_usd: float = 0.0
    fallback_plan: str = ""
    revision: int = 1
    status: ValidationStatus = "NOT_RUN"


@dataclass
class DecisionLogEntry:
    decision_id: str
    trailer_id: str
    stage: str
    action: str
    reason: str
    evidence: list[Evidence] = field(default_factory=list)
    changed_by_event: str | None = None
    revision: int = 1


@dataclass
class ChangeEvent:
    event_id: str
    event_type: str
    message: str
    target_ids: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


def seconds_to_timecode(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    return value
