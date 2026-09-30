# AI Collaboration Note

## Tool-assisted development

AI coding assistance was used to accelerate scaffolding, module generation, test creation, and documentation. Generated code was reviewed against the assignment requirements and exercised with deterministic tests before packaging.

## Model usage in the product

The product supports a local-first LLM path through Ollama and an optional Gemini fallback. Either provider is delegated specific tasks rather than being given end-to-end authority:

1. advisory story understanding
2. audience-specific creative planning
3. optional visual grounding of the episode

The default local model is a Qwen3-VL model served by Ollama. Source fields are explicitly treated as untrusted data, so instructions embedded inside scene descriptions, subtitles, contracts or metadata cannot change system constraints.

## Verification of AI output

The planner output is converted back onto deterministic source scene IDs, timecodes and source dialogue. Independent validators then check source existence, spoilers, story truth, rights, policy, cultural respect, accessibility, budget, audience bias, input safety and video grounding.

A plausible model response is therefore not sufficient to become a final trailer decision.
