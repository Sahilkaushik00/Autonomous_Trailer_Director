# Known Limitations

1. Local LLM/Gemini creative planning is model-assisted, but the planner still depends on the supplied scene catalog and deterministic source resolution.
2. Video grounding is advisory. Local mode samples frames and does not treat VLM output as the authoritative source for contracts, ratings or protected spoiler facts.
3. Real rights validity remains a supplied contract-data concern; production should integrate the platform rights service as the authoritative source.
4. Spoiler detection uses explicit protected source facts today. A production system should add semantic entailment checks across transcript/audio/vision plus human review for ambiguous cases.
5. Cultural-respect safeguards are conservative and cannot replace human cultural review.
6. Audience-bias detection is rule-based rather than a complete fairness/causal analysis.
7. Rendering preserves source audio. Replacement music, generated voice-over, text-card design and final mix remain editorial operations.
8. A real local-model inference was not executable in this packaging environment because Ollama is not installed here. The local adapter was covered with fake-provider tests; the first real local run should be treated as an environment/model verification step. The optional Gemini adapter has the same environment limitation here.
9. The bundled video is synthetic and exists only for renderer smoke testing, not as the supplied episode material.
10. Human approval remains required for final editorial, rights and cultural decisions.

## Local LLM mode

The default live path uses Ollama on localhost. The repository cannot execute a real local-model inference in this packaging environment, so the local adapter is covered by fake-provider tests while the deterministic planning/validation/render pipeline is fully executable.

Local video grounding samples frames rather than passing raw video directly to the local provider. Audio is intentionally not treated as VLM evidence; the supplied dialogue/subtitle package remains the source of truth for audio-related claims.
