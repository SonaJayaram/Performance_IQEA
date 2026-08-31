"""Embeddable feature components.

Each component is a real, interactive feature UI that the chat surfaces inline
at the right point in a flow. A component renders itself and returns a status
dict; when it returns {"done": True, ...} the orchestrator advances the flow.

They reuse the same backend the panels use — the chat brings the real
functionality to the user, it doesn't reimplement it.
"""
from chatbot.components import (
    recorder_component, screenshot_review_component, image_upload_component,
    tmt_component,
)

COMPONENTS = {
    "recorder": recorder_component.render_recorder,
    "screenshot_review": screenshot_review_component.render_screenshot_review,
    "image_upload": image_upload_component.render_image_upload,
    "tmt_fetch": tmt_component.render_tmt_fetch,
}


def render(name, key_prefix, slots=None):
    fn = COMPONENTS.get(name)
    if fn is None:
        import streamlit as st
        st.warning(f"Unknown component: {name}")
        return {"done": False}
    return fn(key_prefix=key_prefix, slots=slots)
