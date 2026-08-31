"""Intent routing — the 'understanding' half of the hybrid engine.

Milestone 1 uses a deterministic keyword scorer so the loop works with zero
network dependency. `classify_llm` is the seam where, in a later milestone, we
plug in the Azure OpenAI call (tool-calling if the deployment supports it, else
a structured-JSON prompt). It is intentionally not called yet.
"""
from chatbot.skills.registry import REGISTRY, DEFAULT_SKILL


def classify(text):
    """Return a skill id for the user's message (keyword scoring)."""
    low = f" {text.lower()} "
    best_id, best_score = DEFAULT_SKILL, 0
    for sid, skill in REGISTRY.items():
        if sid == DEFAULT_SKILL:
            continue
        score = sum(1 for kw in skill.triggers if kw in low)
        # longer trigger phrases are stronger signals
        score += sum(len(kw.split()) for kw in skill.triggers if kw in low)
        if score > best_score:
            best_id, best_score = sid, score
    return best_id if best_score > 0 else DEFAULT_SKILL


def classify_llm(text, history=None):
    """Placeholder for the LLM-backed classifier (Milestone 2+).

    Will return {'skill_id': str, 'slots': dict} using either tool-calling or a
    JSON-structured prompt against Azure OpenAI. Not wired in Milestone 1.
    """
    raise NotImplementedError("LLM intent routing lands in a later milestone.")
