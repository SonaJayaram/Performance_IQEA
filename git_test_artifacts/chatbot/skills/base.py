"""Skill framework.

A skill is an ordered list of steps + an `on_complete` callback. There are two
kinds of step:

  • input  — ask the user something (TEXT / CHOICE / MULTISELECT / CONFIRM ...)
  • action — run backend work (open browser, extract, save, generate)

`next_step(slots)` is deterministic and stateless-per-call: given what's
collected so far it returns the next thing to do — an input to ask, an action
to run, or the final result. The orchestrator drives it in a loop, running
actions and filling slots until an input is needed or the skill completes.
This shape is exactly what Streamlit's rerun model needs (no paused coroutines).

Options for CHOICE / MULTISELECT may be a static list OR a callable(slots)->list,
so a picker can be built from data produced by an earlier action (e.g. the
xpaths just extracted).
"""


def step(slot, type, prompt, options=None, condition=None):
    """An input step. `condition` (fn(slots)->bool) can skip it."""
    return {"kind": "input", "slot": slot, "type": type, "prompt": prompt,
            "options": options, "condition": condition}


def action(name, fn, status=None, condition=None):
    """A backend step. `fn(slots)->dict` result is merged into slots.
    `status` is a message (str or fn(slots)->str) posted after it runs."""
    return {"kind": "action", "name": name, "fn": fn,
            "status": status, "condition": condition}


def embed(slot, component, prompt="", condition=None):
    """Surface a REAL feature component inline (e.g. the recorder). The page
    renders `component`; when the component reports done, its result is stored
    in `slot` and the flow advances."""
    return {"kind": "input", "slot": slot, "type": "EMBED", "prompt": prompt,
            "options": None, "condition": condition, "component": component}


class GuidedSkill:
    def __init__(self, id, triggers, description, steps, on_complete, suggest=None):
        self.id = id
        self.triggers = triggers
        self.description = description
        self.steps = steps
        self.on_complete = on_complete
        self.suggest = suggest

    def next_step(self, slots):
        for s in self.steps:
            cond = s.get("condition")
            if cond and not cond(slots):
                continue

            if s["kind"] == "action":
                if f"__done__{s['name']}" not in slots:
                    return {"kind": "action", "step": s}
                continue

            # input step
            if s["slot"] not in slots:
                return {"kind": "pending", "action": {
                    "type": s["type"], "slot": s["slot"], "prompt": s["prompt"],
                    "options": _resolve_options(s.get("options"), slots),
                    "meta": {"component": s.get("component")}}}

        # every applicable step done -> complete
        out = {"kind": "result", "text": self.on_complete(slots), "suggest": None}
        if self.suggest:
            out["suggest"] = self.suggest(slots)
        return out


def _resolve_options(options, slots):
    if callable(options):
        options = options(slots)
    return _norm_options(options)


def _norm_options(options):
    if not options:
        return None
    norm = []
    for o in options:
        if isinstance(o, dict):
            norm.append({"label": o["label"], "value": o.get("value", o["label"])})
        else:
            norm.append({"label": str(o), "value": str(o)})
    return norm
