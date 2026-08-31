"""Additional-screenshots upload — lets the user add extra images/wireframes to
the recording's set. Saves them into the screenshot folder and returns their
filenames so they join the generation context. Low-friction: a Skip is offered.
"""
import streamlit as st

from chatbot.services import testcase_service


def render_image_upload(key_prefix="imgup", slots=None):
    st.caption("Upload any extra screenshots or wireframes to include in generation.")
    files = st.file_uploader(
        "Extra images",
        type=["png", "jpg", "jpeg", "bmp", "tiff", "webp"],
        accept_multiple_files=True,
        key=f"{key_prefix}_fu",
        label_visibility="collapsed",
    )
    c1, c2 = st.columns(2)
    if c1.button("Add these", key=f"{key_prefix}_add", type="primary"):
        names = testcase_service.save_uploaded_images(files) if files else []
        return {"done": True, "filenames": names,
                "summary": f"Added {len(names)} image(s)." if names else "No images added."}
    if c2.button("Skip", key=f"{key_prefix}_skip"):
        return {"done": True, "filenames": [], "summary": "No extra images."}
    return {"done": False}
