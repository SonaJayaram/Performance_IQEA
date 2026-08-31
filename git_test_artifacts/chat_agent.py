"""IQEA Chat Agent — Streamlit page (v1, Milestone 1).

Independent of every existing feature page. Launched from IQEA.py via run_page.
Renders the conversation, hosts inline human-in-the-loop widgets, and drives the
orchestrator. No st.set_page_config here — the host app already set it.
"""
import streamlit as st

from chatbot import state, orchestrator, components

state.init()

ORANGE = "#F47B20"
ORANGE_DK = "#E8650A"

st.markdown(f"""
<style>
.chat-hero {{
    background:linear-gradient(100deg,{ORANGE_DK} 0%,{ORANGE} 100%);
    color:#fff;border-radius:14px;padding:18px 22px;margin-bottom:8px;
    box-shadow:0 4px 16px rgba(232,101,10,.22);
}}
.chat-hero h2 {{ margin:0;font-size:22px;font-weight:800;color:#fff; }}
.chat-hero p  {{ margin:4px 0 0;font-size:13.5px;opacity:.92; }}
.stButton>button[kind="primary"]{{background:{ORANGE};border-color:{ORANGE};}}
div[data-testid="stChatMessage"] {{ background:transparent; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="chat-hero">
  <h2>💬 iQEA Chat Agent</h2>
  <p>Tell me what you want in plain language — I'll ask what I need and drive the platform for you.</p>
</div>
""", unsafe_allow_html=True)

# --- toolbar ---------------------------------------------------------------
tb1, tb2 = st.columns([6, 1])
with tb2:
    if st.button("🧹 New chat", use_container_width=True):
        state.reset()
        st.rerun()

# --- greet on first load ---------------------------------------------------
if not state.messages():
    state.add_message(
        "assistant",
        "Hi! I can generate test cases or extract locators / build a Page Object for you. "
        "What would you like to do? _(type **help** to see options)_",
    )

# --- render conversation ---------------------------------------------------
for m in state.messages():
    avatar = "🤖" if m["role"] == "assistant" else "🧑‍💻"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["text"])

# --- render the active inline widget (human-in-the-loop step) --------------
task = state.task()
pending = task["pending"] if task else None

if pending:
    ptype = pending["type"]
    slot = pending["slot"]
    wkey = f"chat_w_{len(state.messages())}_{slot}"

    with st.chat_message("assistant", avatar="🤖"):
        if ptype == "CHOICE":
            cols = st.columns(len(pending["options"]))
            for i, opt in enumerate(pending["options"]):
                if cols[i].button(opt["label"], key=f"{wkey}_{i}", use_container_width=True):
                    with st.spinner("Working…"):
                        orchestrator.submit_value(slot, opt["value"], display=opt["label"])
                    st.rerun()

        elif ptype == "MULTISELECT":
            labels = [o["label"] for o in pending["options"]]
            picked = st.multiselect("Select one or more", labels, key=f"{wkey}_ms",
                                    label_visibility="collapsed")
            if st.button("Continue", key=f"{wkey}_go", type="primary"):
                values = [o["value"] for o in pending["options"] if o["label"] in picked]
                with st.spinner("Working…"):
                    orchestrator.submit_value(slot, values)
                st.rerun()

        elif ptype == "CONFIRM":
            c1, c2 = st.columns(2)
            if c1.button("✅ Yes", key=f"{wkey}_yes", type="primary", use_container_width=True):
                with st.spinner("Working…"):
                    orchestrator.submit_value(slot, True, display="Yes")
                st.rerun()
            if c2.button("❌ No", key=f"{wkey}_no", use_container_width=True):
                with st.spinner("Working…"):
                    orchestrator.submit_value(slot, False, display="No")
                st.rerun()

        elif ptype == "EMBED":
            result = components.render(pending["meta"].get("component"), key_prefix=wkey,
                                       slots=(task["slots"] if task else {}))
            if result and result.get("done"):
                orchestrator.submit_value(slot, result, display=result.get("summary", "Done."))
                st.rerun()

        else:  # TEXT (and any not-yet-implemented type) -> use the chat box
            st.caption("Type your answer below 👇")

# --- free-text input -------------------------------------------------------
user_text = st.chat_input("Message the QE assistant…")
if user_text:
    with st.spinner("Working…"):
        orchestrator.handle_text(user_text)
    st.rerun()
