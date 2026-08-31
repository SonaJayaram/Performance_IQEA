"""Service layer — UI-free wrappers around the existing platform backend.

These call the same `utilities.Utilities_Xpath` functions the panels call, so
the chat agent and the panels share one implementation. They run inside the
chat page's Streamlit context (some underlying utils emit st.* / read
st.session_state), but they never render input widgets — human-in-the-loop
happens in the chat, not here.
"""
