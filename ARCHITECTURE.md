# Architecture Note

## 1. Design goal

The system is built around a simple safety property: **creative generation proposes; independent validators decide whether a proposal may proceed.**

The pipeline follows:

```text
load -> understand -> constrain -> plan -> validate -> repair -> revalidate -> emit
```

## 2. Components

### Deterministic Story Mapper
Builds characters, relationship claims, major events, emotional turns, sensitive-content annotations and protected spoiler facts from supplied source metadata.

### LLM Story Enhancer
In live mode, the selected LLM provider adds an advisory layer containing candidate emotional arcs, possible spoilers, sensitive moments and uncertainties. These insights are stored separately from the deterministic story facts and are never promoted to authoritative rights or safety facts automatically.

### Constraint Mapper
Converts supplied contracts, rating policies and audience-care requirements into structured testable constraints. Contracts and policies are data, not free-form prompt instructions.

### Creative Strategy / LLM Planner
In mock mode the deterministic planner selects from supplied scene tags. In live mode a local Ollama model or Gemini Flash proposes the audience promise, emotional journey and source scene choices. The adapter is constrained to the supplied scene catalog and source dialogue is resolved locally from the package rather than trusted from model text.

### Video Grounding
When a real MP4 is supplied, local mode samples frames at known timestamps and sends them to a local vision-language model. Gemini mode can instead use the cloud video API. Observations are stored as advisory video evidence. The video grounding validator checks whether selected source scene IDs and timecodes have matching observations. A model mismatch produces a review warning rather than silently becoming truth.

### Validators
Validation is intentionally split into independent gates:

- source accuracy
- spoiler
- story truth
- rights
- audience policy
- cultural respect
- accessibility
- budget
- audience-data bias
- input safety
- video grounding

A hard block prevents a plan from being treated as valid.

### Repair Agent
Consumes validator evidence and replaces only blocked segments with grounded candidates. It does not get to waive the failed constraint.

### Change Impact Analyzer / Replanner
Maps evaluator events to affected validation areas. Contract changes can replace only segments referencing the affected asset while preserving unaffected segments where possible. The complete validator suite remains the final safety gate.

### Decision Logger
Records planning, validation and repair decisions with evidence, revision numbers and change-event references.

### Model Provider Interface
`ModelProvider` defines a JSON generation boundary. `ReplayModelProvider` provides deterministic no-key behavior. `OllamaModelProvider` is the default live adapter and uses Ollama structured JSON output over localhost. `GeminiModelProvider` remains an optional cloud adapter.

### FFmpeg Renderer
The optional renderer executes validated time ranges against the actual source video. It refuses to render `FAIL` plans, normalizes each clip to a common H.264/AAC format, then concatenates the resulting clips.

## 3. Memory

The current implementation uses explicit structured state:

- `EpisodePackage` is source memory.
- `StoryMap` is derived story memory.
- `ConstraintMap` is policy/contract memory.
- `TrailerPlan` is decision state.
- `DecisionLogEntry` is audit memory.
- `episode.metadata["video_analysis"]` is advisory multimodal evidence.

## 4. Trust boundaries

Scene descriptions, transcripts, subtitles and historical-performance notes are untrusted content. Instructions embedded in them cannot change control flow or constraint priority. Gemini is also not allowed to manufacture timecodes or source dialogue in the final plan.

## 5. Failure recovery

```text
candidate
   |
   v
validators
   |
   +---- PASS ----------> emit / render
   |
   +---- FAIL ----------> repair evidence-backed segments
                               |
                               v
                           revalidate
                               |
                           pass / reject
```

A maximum repair-round limit prevents infinite loops. If no safe replacement exists, the plan remains rejected.

## 6. Cost control

The `CostSheet` tracks model-call, media-analysis and rendering costs. The budget validator blocks plans exceeding the configured budget.

## 7. Intentional tradeoffs

The submission prioritizes the rubric's creative planning, multimodal grounding, safety/rights, verification/recovery and engineering signals over building a large UI or a production render farm.
