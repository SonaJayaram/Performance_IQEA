"""Embeddable Web Workflow Recorder.

Reuses the exact backend the IQEA recorder panel uses — the JS action injection,
the four monitor threads, get_recorded_actions, generate_workflow_manual — but
with its own `chat_rec_*` session keys so it never interferes with the panel's
recorder. Renders inside a chat message; returns {"done": True, "page": ...}
once the workflow is saved.
"""
import os
import threading

import streamlit as st

import utilities.utils_action as action_utils
import utilities.Utilities_Xpath as utils
from config.settings_reader import get_source
from chatbot.services import locator_service

_OUT = os.path.join(os.getcwd(), "output")
ACTION_COLLECTION = os.path.join(_OUT, "Action_collection")
SCREENSHOT_FOLDER = os.path.join(ACTION_COLLECTION, "Sauce_demo")
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)


_IMG_EXTS = (".png", ".jpg", ".jpeg", ".gif")


def _list_shots():
    try:
        return [f for f in os.listdir(SCREENSHOT_FOLDER) if f.lower().endswith(_IMG_EXTS)]
    except FileNotFoundError:
        return []


def _init():
    ss = st.session_state
    ss.setdefault("chat_rec_started", False)
    ss.setdefault("chat_rec_actions", [])
    ss.setdefault("chat_rec_threads", [])
    ss.setdefault("chat_rec_stop", {"stop": False})
    ss.setdefault("chat_rec_injected", {})
    ss.setdefault("chat_rec_last_urls", {})
    ss.setdefault("chat_rec_winref", {"handle": None})
    ss.setdefault("chat_rec_saved", False)
    ss.setdefault("chat_rec_page", "")
    ss.setdefault("chat_rec_pre", [])       # screenshots present before this recording


def render_recorder(key_prefix="chatrec", slots=None):
    _init()
    ss = st.session_state
    k = key_prefix

    st.caption("Open your app, record your journey, then save it — screenshots are captured automatically.")

    # already finished (in case of an extra render before advance)
    if ss.chat_rec_saved:
        return {"done": True, "page": ss.chat_rec_page,
                "summary": f"Recorded workflow saved as “{ss.chat_rec_page}”."}

    # --- open the browser ---
    c1, c2 = st.columns([4, 1])
    url = c1.text_input("URL to record", key=f"{k}_url", placeholder="https://www.saucedemo.com",
                        label_visibility="collapsed")
    if c2.button("Open", key=f"{k}_open", use_container_width=True):
        try:
            locator_service.open_browser(url)
            st.success("Browser opened — interact with it after you start recording.")
        except Exception as e:
            st.error(f"Couldn't open the browser: {e}")

    driver = ss.get("driver")
    if driver is None:
        st.info("Open a URL first to enable recording.")
        return {"done": False}

    # --- start recording ---
    if not ss.chat_rec_started and st.button("🎥 Start Recording", key=f"{k}_start", type="primary"):
        ss.chat_rec_stop["stop"] = True
        for t in ss.chat_rec_threads:
            if t and t.is_alive():
                t.join(timeout=2)

        ss.chat_rec_injected = {}
        ss.chat_rec_last_urls = {}
        ss.chat_rec_winref = {"handle": None}
        ss.chat_rec_stop = {"stop": False}
        ss.chat_rec_threads = []
        ss.chat_rec_actions = []
        ss.chat_rec_pre = _list_shots()      # snapshot so we can tell THIS recording's shots apart

        handle = driver.current_window_handle
        driver.execute_script(action_utils.injection_script_agentflow())
        ss.chat_rec_injected[handle] = True

        source = get_source()
        t1 = threading.Thread(target=utils.thread_new_window_checker, args=(
            driver, ss.chat_rec_injected, ss.chat_rec_last_urls, ss.chat_rec_stop,
            SCREENSHOT_FOLDER, ss.chat_rec_winref), daemon=True)
        t2 = threading.Thread(target=utils.thread_focus_and_url_monitor, args=(
            driver, ss.chat_rec_injected, ss.chat_rec_last_urls, ss.chat_rec_stop,
            SCREENSHOT_FOLDER, ss.chat_rec_winref), daemon=True)
        t3 = threading.Thread(target=utils.thread_focus_screenshot, args=(
            driver, ss.chat_rec_stop, SCREENSHOT_FOLDER, source), daemon=True)
        t4 = threading.Thread(target=utils.thread_reinject_action_check, args=(
            driver, ss.chat_rec_stop, ss.chat_rec_last_urls, ss.chat_rec_winref,
            ss.chat_rec_injected), daemon=True)
        for t in (t1, t2, t3, t4):
            t.start()
        ss.chat_rec_threads = [t1, t2, t3, t4]
        ss.chat_rec_started = True
        st.success("Recording started — interact in the browser, then click Stop.")

    # --- stop recording ---
    if ss.chat_rec_started and st.button("🛑 Stop Recording", key=f"{k}_stop"):
        ss.chat_rec_actions = action_utils.get_recorded_actions(driver)
        ss.chat_rec_started = False
        ss.chat_rec_stop["stop"] = True
        for t in ss.chat_rec_threads:
            if t and t.is_alive():
                t.join(timeout=2)
        ss.chat_rec_threads = []
        ss.chat_rec_injected.clear()
        st.success(f"Recording stopped — {len(ss.chat_rec_actions)} action(s) captured.")

    # --- save workflow ---
    if ss.chat_rec_actions:
        st.markdown(f"**{len(ss.chat_rec_actions)} action(s) captured.**")
        page_name = st.text_input("Name this workflow", key=f"{k}_name")
        if st.button("💾 Save Workflow", key=f"{k}_save", type="primary"):
            if not page_name:
                st.warning("Please enter a name for the workflow.")
            else:
                workflow_text = action_utils.generate_workflow_manual(ss.chat_rec_actions)
                source = get_source()
                if source == "database":
                    from config.settings_reader import get_update_user
                    import utilities.db_utils.handler as db_handler
                    db_handler.save_action_to_db(page_name, workflow_text, get_update_user())
                else:
                    fn = os.path.join(ACTION_COLLECTION, f"{page_name}_actions.txt")
                    cleaned = [x.replace("​", "").replace("\xa0", " ").strip() for x in workflow_text]
                    with open(fn, "w", encoding="utf-8") as f:
                        f.write("\n".join(cleaned))
                # reset the browser-side action buffer for the next recording
                try:
                    driver.execute_script(
                        "window.__recordedActions=[];localStorage.removeItem('recordedActions');")
                except Exception:
                    pass
                # screenshots created DURING this recording (ordered by capture time)
                pre = set(ss.get("chat_rec_pre") or [])
                new_shots = [f for f in _list_shots() if f not in pre]
                new_shots.sort(key=lambda f: os.path.getmtime(os.path.join(SCREENSHOT_FOLDER, f)))

                ss.chat_rec_saved = True
                ss.chat_rec_page = page_name
                return {
                    "done": True,
                    "page": page_name,
                    "action_file": os.path.join(ACTION_COLLECTION, f"{page_name}_actions.txt"),
                    "screenshots": new_shots,
                    "summary": f"Recorded workflow saved as “{page_name}” "
                               f"({len(new_shots)} screenshot(s)).",
                }

    return {"done": False}
