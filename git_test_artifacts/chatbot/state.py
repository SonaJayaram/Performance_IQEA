"""Session-scoped chat state.

Everything is stored as plain dicts/lists (NOT dataclass instances) because
`IQEA.run_page` evicts and re-imports this module on every Streamlit rerun —
storing class instances would break `isinstance` checks after a reload.

All keys are namespaced `chat_*` so they can never collide with the existing
pages' session state.
"""
import streamlit as st

_MESSAGES = "chat_messages"
_TASK = "chat_task"
_ARTIFACTS = "chat_artifacts"


def init():
    st.session_state.setdefault(_MESSAGES, [])
    st.session_state.setdefault(_TASK, None)
    st.session_state.setdefault(_ARTIFACTS, {})


# ---- messages -----------------------------------------------------------
def messages():
    return st.session_state[_MESSAGES]


def add_message(role, text, kind="text", data=None):
    """role: 'user' | 'assistant'.  kind: 'text' | 'result'."""
    st.session_state[_MESSAGES].append(
        {"role": role, "text": text, "kind": kind, "data": data}
    )


# ---- active task --------------------------------------------------------
def task():
    return st.session_state[_TASK]


def new_task(skill_id):
    t = {"skill_id": skill_id, "slots": {}, "pending": None, "status": "active"}
    st.session_state[_TASK] = t
    return t


def clear_task():
    st.session_state[_TASK] = None


# ---- artifacts (produced files, chainable across skills) ----------------
def artifacts():
    return st.session_state[_ARTIFACTS]


def register_artifact(artifact_id, kind, label, path=None, data=None):
    st.session_state[_ARTIFACTS][artifact_id] = {
        "kind": kind, "label": label, "path": path, "data": data
    }


# ---- reset --------------------------------------------------------------
def reset():
    st.session_state[_MESSAGES] = []
    st.session_state[_TASK] = None
    st.session_state[_ARTIFACTS] = {}
