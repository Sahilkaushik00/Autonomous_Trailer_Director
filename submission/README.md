# Submission Package

This directory is the evaluator-facing snapshot requested by the assignment brief.

## Included

- `README.md` — submission overview and run instructions
- `ARCHITECTURE.md` — planning, memory, multimodal processing, verification and failure recovery
- `AI_COLLABORATION.md` — AI delegation and verification notes
- `KNOWN_LIMITATIONS.md` — known limitations and human-only decisions
- `story_map.json` — grounded story representation
- `constraint_map.json` — executable policy/contract/audience constraints
- `family_trailer.json` — family audience edit decision list
- `young_adult_trailer.json` — young adult audience edit decision list
- `dialect_region_trailer.json` — dialect-region audience edit decision list
- `validation_report.md` — human-readable validation results
- `decision_log.json` — structured decision/audit history

## Reproduce

The repository root contains the runnable implementation. No personal API key is needed for the mock/replay path.

```bash
python -m pytest -q
python run_demo.py
```

## Design note

Creative planning and validation are deliberately separated. The planner may propose a compelling clip, but source accuracy, spoiler, rights, rating, truth, cultural-respect, accessibility, budget, bias and input-safety gates can reject it. Change events trigger selective replanning followed by revalidation.


### Rendering note

Video rendering is optional. If FFmpeg is not installed or not available on `PATH`, `run_demo.py` skips rendering and still completes the required planning, validation, and machine-readable edit-decision-list workflow.
