# Validation Report

Plans evaluated: 3

## family_v1
Audience: family viewers
Revision: 1
Status: **PASS**
Duration: 45.000s
Estimated cost: $0.0450

- `source_accuracy`: **PASS** (0 issue(s))
- `spoiler`: **PASS** (0 issue(s))
- `story_truth`: **PASS** (0 issue(s))
- `rights`: **PASS** (0 issue(s))
- `audience_policy`: **PASS** (0 issue(s))
- `cultural_respect`: **PASS** (0 issue(s))
- `accessibility`: **PASS** (0 issue(s))
- `budget`: **PASS** (0 issue(s))
- `audience_bias`: **PASS** (0 issue(s))
- `input_safety`: **PASS** (0 issue(s))
- `video_grounding`: **NOT_RUN** (1 issue(s))
  - `VIDEO_ANALYSIS_NOT_AVAILABLE` [info] No live video analysis was supplied; deterministic source checks still apply.
- Human approvals: editorial_final_cut, rights_approval, editorial_review

## young_adult_v1
Audience: young adult viewers
Revision: 1
Status: **PASS_WITH_WARNINGS**
Duration: 40.000s
Estimated cost: $0.0400

- `source_accuracy`: **PASS** (0 issue(s))
- `spoiler`: **PASS** (0 issue(s))
- `story_truth`: **PASS** (0 issue(s))
- `rights`: **PASS** (0 issue(s))
- `audience_policy`: **PASS** (0 issue(s))
- `cultural_respect`: **PASS** (0 issue(s))
- `accessibility`: **PASS_WITH_WARNINGS** (1 issue(s))
  - `MISSING_ACCESSIBLE_TEXT` [warning] Segment has spoken/dialogue audio but no subtitle or text-card representation.
- `budget`: **PASS** (0 issue(s))
- `audience_bias`: **PASS** (0 issue(s))
- `input_safety`: **PASS** (0 issue(s))
- `video_grounding`: **NOT_RUN** (1 issue(s))
  - `VIDEO_ANALYSIS_NOT_AVAILABLE` [info] No live video analysis was supplied; deterministic source checks still apply.
- Human approvals: editorial_final_cut, rights_approval, editorial_review

## dialect_region_v1
Audience: dialect-region viewers
Revision: 1
Status: **PASS_WITH_WARNINGS**
Duration: 45.000s
Estimated cost: $0.0450

- `source_accuracy`: **PASS** (0 issue(s))
- `spoiler`: **PASS** (0 issue(s))
- `story_truth`: **PASS** (0 issue(s))
- `rights`: **PASS** (0 issue(s))
- `audience_policy`: **PASS** (0 issue(s))
- `cultural_respect`: **PASS** (0 issue(s))
- `accessibility`: **PASS** (0 issue(s))
- `budget`: **PASS** (0 issue(s))
- `audience_bias`: **PASS_WITH_WARNINGS** (1 issue(s))
  - `SENSITIVE_AUDIENCE_SIGNAL` [warning] Audience data contains identity/regional signal(s): dialect_affinity. These must not be used as stereotype proxies.
- `input_safety`: **PASS** (0 issue(s))
- `video_grounding`: **NOT_RUN** (1 issue(s))
  - `VIDEO_ANALYSIS_NOT_AVAILABLE` [info] No live video analysis was supplied; deterministic source checks still apply.
- Human approvals: editorial_final_cut, rights_approval, cultural_review
