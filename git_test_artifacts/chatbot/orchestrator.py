"""Dialog manager — advances a task per event, running backend actions inline.

Entry points (called by chat_agent.py):
  • handle_text(text)         — free-text from the chat box
  • submit_value(slot, value) — a chat-embedded widget was submitted

`_advance` loops: it asks the skill for the next step and runs any backend
actions (with error capture) until it needs user input or the skill completes.
"""
from chatbot import state, engine
from chatbot.skills import registry

_MAX_STEPS = 60  # safety bound against a mis-specified skill


def handle_text(text):
    text = (text or "").strip()
    if not text:
        return
    state.add_message("user", text)

    t = state.task()
    if t and t.get("pending") and t["pending"]["type"] == "TEXT":
        _fill(t, t["pending"]["slot"], text)
        _advance(t)
        return

    skill_id = engine.classify(text)
    t = state.new_task(skill_id)
    _advance(t)


def submit_value(slot, value, display=None):
    t = state.task()
    if not t:
        return
    state.add_message("user", display if display is not None else _fmt(value))
    _fill(t, slot, value)
    _advance(t)


# ---- internals ----------------------------------------------------------
def _fill(t, slot, value):
    t["slots"][slot] = value
    t["pending"] = None


def _advance(t):
    skill = registry.get(t["skill_id"])
    slots = t["slots"]

    for _ in range(_MAX_STEPS):
        out = skill.next_step(slots)

        if out["kind"] == "action":
            s = out["step"]
            slots[f"__done__{s['name']}"] = True   # mark first — never re-run on failure
            try:
                slots.update(s["fn"](slots) or {})
            except Exception as e:
                t["status"] = "error"
                t["pending"] = None
                state.add_message(
                    "assistant",
                    f"⚠️ Something went wrong during **{s['name']}**: {e}\n\n"
                    "Nothing was left half-done. You can start that request again.",
                )
                state.clear_task()
                return
            msg = s.get("status")
            if msg:
                state.add_message("assistant", msg(slots) if callable(msg) else msg)
            continue

        if out["kind"] == "pending":
            t["pending"] = out["action"]
            state.add_message("assistant", out["action"]["prompt"])
            return

        # result
        t["status"] = "done"
        t["pending"] = None
        state.add_message("assistant", out["text"], kind="result")
        if out.get("suggest"):
            state.add_message("assistant", out["suggest"])
        state.clear_task()
        return


def _fmt(value):
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "(none)"
    return str(value)
