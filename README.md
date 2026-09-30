# Autonomous Trailer Director

Agentic AI engineering take-home implementation for the OTT Dialect Platform challenge.

## Submission-ready behavior

This repository is designed to be evaluable **without Gemini, Ollama, or a personal API key**. The default `mock` / `replay` path runs locally from the supplied JSON episode package and deterministic sample media. Optional live adapters for a local Ollama VLM/LLM and Gemini are isolated behind the same model interface.

The system:

1. builds a grounded story map,
2. converts ratings/contracts/audience-care rules into testable constraints,
3. creates three audience-specific trailer edit plans,
4. independently validates source accuracy, spoilers, story truth, rights, policy, cultural respect, accessibility, budget, bias and input safety,
5. repairs blocked segments and revalidates them,
6. traces change events to affected decisions, and
7. optionally renders validated edit lists with FFmpeg.

The required artifact is the machine-readable **edit decision list** with exact source timecodes, reasons, evidence, validation status, warnings and human approvals. Video rendering is optional.

## Audiences

- Family viewers
- Young adult viewers
- Dialect-region viewers

## Architecture

```text
Episode package -> Story Map -----------+
                                       |
Policies + Contracts -> Constraint Map |
                                       v
                              Creative Planning
                         mock / Ollama / Gemini
                                       |
                                       v
                           Independent Validators
                           /       |        \
                        PASS     WARN       FAIL
                          |        |          |
                          |        |       Repair
                          |        |          |
                          +--------+---- Revalidate
                                       |
                                       v
                               Decision / Audit Log
                                       |
                                   FFmpeg render
                                  (optional)

Optional MP4 -> frame sampling -> local VLM/Gemini -> advisory video evidence
                                      |
                                      v
                              video_grounding gate
```

**Trust boundary:** the creative model proposes; deterministic validators decide whether a plan may proceed. Source descriptions, dialogue, subtitles and similar fields are treated as untrusted evidence, so instruction-like text embedded in content cannot override contracts or system constraints.

## Repository

```text
.
├── README.md
├── ARCHITECTURE.md
├── AI_COLLABORATION.md
├── KNOWN_LIMITATIONS.md
├── requirements.txt
├── requirements-live.txt
├── .env.example
├── pytest.ini
├── run_demo.py
├── run_demo.bat
├── run_local.bat
├── run_live.bat
├── setup_local.bat
├── data/
├── media/
├── src/
├── tests/
├── sample_run/
└── submission/
    ├── README.md
    ├── ARCHITECTURE.md
    ├── AI_COLLABORATION.md
    ├── KNOWN_LIMITATIONS.md
    ├── story_map.json
    ├── constraint_map.json
    ├── family_trailer.json
    ├── young_adult_trailer.json
    ├── dialect_region_trailer.json
    ├── validation_report.md
    └── decision_log.json
```

## Guaranteed offline test

From the repository root:

```bash
python -m pytest -q
```

Expected result in the shipped build:

```text
14 passed
```

Then run the complete deterministic demo:

```bash
python run_demo.py
```

No cloud API key is required. The demo writes the sample decision lists, story/constraint maps, decision log and validation report. It renders the bundled synthetic episode when FFmpeg is available; otherwise it skips the optional rendering step and exits successfully.

## Direct CLI

```bash
python -m src.main --episode data/episode_demo.json --audiences data/audiences_demo.json --mode mock --output sample_run/run_summary.json
```

Replay mode is also available for deterministic evaluator scenarios.

## Optional live model path

The live model is not required for submission validation.

### Local Ollama

Use a locally installed multimodal Ollama model such as `qwen3-vl:8b` or a smaller compatible model. The application calls Ollama over localhost HTTP and does not require an Ollama Python package.

```bash
python -m src.main --episode data/episode_demo.json --audiences data/audiences_demo.json --mode live --provider local --model qwen3-vl:8b --video path/to/episode.mp4 --render --output sample_run/local_run.json
```

### Gemini

Gemini remains an optional cloud adapter:

```bash
pip install -r requirements-live.txt
python -m src.main --episode data/episode_demo.json --audiences data/audiences_demo.json --mode live --provider gemini --video path/to/episode.mp4 --render --output sample_run/gemini_run.json
```

## Failure and recovery tests

The automated test suite includes the required negative cases from the brief:

- missing scene
- restricted rights
- major spoiler
- audience-policy failure
- changed contract / selective replanning
- instruction-like source text / prompt injection

It also covers the model-provider boundary and FFmpeg renderer.

## Submission evidence

`submission/` contains a copy of the evaluator-facing deliverables requested in the brief, while `sample_run/` contains the executable demo artifacts.

The bundled `media/demo_episode.mp4` is synthetic and exists only to make the optional rendering path demonstrable without external media. It is not presented as the supplied evaluation episode.

## Known limitations

See `KNOWN_LIMITATIONS.md`. In particular, live model inference was not executed in this packaging environment; the adapter boundaries are tested with fake providers, while the offline deterministic pipeline and renderer are executable.
