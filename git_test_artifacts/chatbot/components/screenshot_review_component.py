"""Screenshot review — shows the screenshots auto-collected from the recording
as thumbnails (all pre-selected). The user can deselect any, then continue.
Low-friction: doing nothing keeps them all.

Reads the candidate list from the flow slots (`_rec_shots`); returns
{"done": True, "selected": [...]} on Continue.
"""
import os
import streamlit as st

from chatbot.components.recorder_component import SCREENSHOT_FOLDER

_PER_ROW = 4


def render_screenshot_review(key_prefix="shots", slots=None):
    slots = slots or {}
    shots = slots.get("_rec_shots") or []
    k = key_prefix

    if not shots:
        # nothing to review -> auto-complete with empty selection
        return {"done": True, "selected": [], "summary": "No screenshots from this recording."}

    st.caption("From your recording — untick any you don't want, then continue. "
               "Leaving them all is fine.")

    keep = []
    for i, name in enumerate(shots):
        if i % _PER_ROW == 0:
            cols = st.columns(_PER_ROW)
        col = cols[i % _PER_ROW]
        path = os.path.join(SCREENSHOT_FOLDER, name)
        with col:
            if os.path.exists(path):
                st.image(path, use_container_width=True)
            checked = st.checkbox(f"{i + 1}", value=True, key=f"{k}_cb_{i}")
            if checked:
                keep.append(name)

    st.markdown(f"**{len(keep)} of {len(shots)} selected.**")
    if st.button("Continue", key=f"{k}_go", type="primary"):
        return {"done": True, "selected": keep,
                "summary": f"Kept {len(keep)} of {len(shots)} screenshot(s)."}

    return {"done": False}
