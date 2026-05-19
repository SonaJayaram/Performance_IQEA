"""
IQEA Enhanced Action Utils v2.0
Handles JS injection, action collection, workflow text generation.
"""

import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path

# ─── Load enhanced JS from file ───────────────────────────────────────────────
_JS_FILE = Path(__file__).parent / "enhanced_action_listener.js"

def _load_js() -> str:
    with open(_JS_FILE, "r", encoding="utf-8") as f:
        return f.read()

ENHANCED_JS_ACTION_LISTENER = _load_js()


# ─── Injection script builder ──────────────────────────────────────────────────
def injection_script(status_key: str = "main") -> str:
    """
    Returns a JS snippet that:
    1. Clears the URL-bound SPA guard so reinject works after navigation.
    2. Injects the enhanced listener if not already on this exact URL.
    """
    js_code = ENHANCED_JS_ACTION_LISTENER.replace("STATUS_KEY_PLACEHOLDER", json.dumps(status_key))
    escaped = json.dumps(js_code)

    return f"""
    (function() {{
        // Clear SPA guard to allow reinject after navigation
        window.__iqea_injected_url = null;

        var scriptId = 'iqea_recorder_v2';
        var old = document.getElementById(scriptId);
        if (old) old.remove();

        var s = document.createElement('script');
        s.id = scriptId;
        s.type = 'text/javascript';
        s.text = {escaped};
        document.documentElement.appendChild(s);
        console.log("✅ IQEA v2 Recorder injected");
    }})();
    """


# ─── Clear actions ─────────────────────────────────────────────────────────────
CLEAR_ACTIONS_JS = """
(function() {
    window.__recordedActions = [];
    window.__iqea_injected_url = null;
    window.__listenersAttached = false;
    localStorage.removeItem('recordedActions');
    localStorage.removeItem('lastReinjectTime');
    localStorage.setItem('__iqea_step', '0');
    console.log("🧹 IQEA: Cleared all recorded actions.");
})();
"""


# ─── Collect actions from all windows ─────────────────────────────────────────
def get_recorded_actions(driver) -> list:
    """
    Collect and merge recorded actions from all open windows, sorted by step number then timestamp.
    Falls back to timestamp sort if step numbers are missing.
    """
    all_actions = []
    seen = set()
    original_handle = driver.current_window_handle

    for handle in driver.window_handles:
        try:
            driver.switch_to.window(handle)
            actions = driver.execute_script(
                "return JSON.parse(localStorage.getItem('recordedActions') || '[]');"
            )
            for a in actions:
                # Deduplicate by (step, action, xpath, timestamp)
                key = (a.get("step"), a.get("action"), a.get("xpath"), a.get("timestamp"))
                if key not in seen:
                    seen.add(key)
                    all_actions.append(a)
        except Exception as e:
            print(f"⚠️ Error fetching actions from window {handle}: {e}")

    try:
        driver.switch_to.window(original_handle)
    except Exception:
        pass

    # Sort: by step number if available, else by timestamp
    def sort_key(a):
        step = a.get("step", 99999)
        ts = a.get("timestamp", "")
        return (step, ts)

    all_actions.sort(key=sort_key)
    return all_actions


# ─── Action type → human readable description ─────────────────────────────────
ACTION_DESCRIPTIONS = {
    "click":            lambda a: f"Click on '{a.get('label', '')}' [{a.get('xpath', '')}]",
    "right_click":      lambda a: f"Right-click on '{a.get('label', '')}' [{a.get('xpath', '')}]",
    "input":            lambda a: f"Enter text '{a.get('value', '')}' in '{a.get('label', '')}' [{a.get('xpath', '')}]",
    "input_others":     lambda a: f"Set '{a.get('label', '')}' to '{a.get('value', '')}' [{a.get('xpath', '')}]",
    "select":           lambda a: f"Select '{a.get('value', '')}' from dropdown '{a.get('label', '')}' [{a.get('xpath', '')}]",
    "checkbox":         lambda a: f"Set checkbox '{a.get('label', '')}' to {a.get('value', '')} [{a.get('xpath', '')}]",
    "radio":            lambda a: f"Select radio '{a.get('label', '')}' value='{a.get('value', '')}' [{a.get('xpath', '')}]",
    "file_upload":      lambda a: f"Upload file(s) '{a.get('value', '')}' via '{a.get('label', '')}' [{a.get('xpath', '')}]",
    "key_enter":        lambda a: f"Press Enter on '{a.get('label', '')}' [{a.get('xpath', '')}]",
    "key_escape":       lambda a: f"Press Escape [{a.get('xpath', '')}]",
    "key_tab":          lambda a: f"Press {a.get('value', 'Tab')} [{a.get('xpath', '')}]",
    "function_key":     lambda a: f"Press {a.get('value', '')} [{a.get('xpath', '')}]",
    "shortcut_copy":    lambda a: f"Copy selected text '{a.get('value', '')}' [{a.get('xpath', '')}]",
    "shortcut_cut":     lambda a: f"Cut selected text '{a.get('value', '')}' [{a.get('xpath', '')}]",
    "shortcut_paste":   lambda a: f"Paste '{a.get('value', '')}' [{a.get('xpath', '')}]",
    "shortcut_undo":    lambda a: f"Undo (Ctrl+Z) [{a.get('xpath', '')}]",
    "shortcut_redo":    lambda a: f"Redo (Ctrl+Y) [{a.get('xpath', '')}]",
    "shortcut_save":    lambda a: f"Save (Ctrl+S) [{a.get('xpath', '')}]",
    "shortcut_select_all": lambda a: f"Select All (Ctrl+A) [{a.get('xpath', '')}]",
    "copy":             lambda a: f"Copy text '{a.get('value', '')}' [{a.get('xpath', '')}]",
    "cut":              lambda a: f"Cut text '{a.get('value', '')}' [{a.get('xpath', '')}]",
    "paste":            lambda a: f"Paste text '{a.get('value', '')}' [{a.get('xpath', '')}]",
    "scroll":           lambda a: f"Scroll on '{a.get('label', 'page')}' → {a.get('value', '')}",
    "drag_start":       lambda a: f"Start drag on '{a.get('label', '')}' [{a.get('xpath', '')}]",
    "drop":             lambda a: f"Drop → {a.get('value', '')}",
    "hover":            lambda a: f"Hover over '{a.get('label', '')}' [{a.get('xpath', '')}]",
    "hover_end":        lambda a: f"Mouse leave '{a.get('label', '')}' [{a.get('xpath', '')}]",
    "change":           lambda a: f"Change '{a.get('label', '')}' [{a.get('xpath', '')}]",
    "switch":           lambda a: f"Switch to window '{a.get('windowId', '')}' | URL: {a.get('url', '')}",
    "navigate":         lambda a: f"Navigate to URL: {a.get('url', '')}",
}

def describe_action(action: dict) -> str:
    action_type = action.get("action", "unknown")
    formatter = ACTION_DESCRIPTIONS.get(action_type)
    if formatter:
        return formatter(action)
    return f"{action_type.replace('_', ' ').title()} on '{action.get('label', '')}' [{action.get('xpath', '')}]"


# ─── Workflow text generator ───────────────────────────────────────────────────
def generate_workflow_manual(actions: list) -> list:
    """
    Converts a list of action dicts into readable workflow step strings.
    Groups actions by URL/window for clarity.
    """
    lines = []
    current_url = None
    current_window = None

    for action in actions:
        url = action.get("url", "")
        window_id = action.get("windowId", "")
        ts = action.get("timestamp", "")
        step = action.get("step", "?")

        # Emit URL/window change header
        if url != current_url or window_id != current_window:
            lines.append("")
            lines.append(f"## Window: {window_id} | URL: {url}")
            lines.append("")
            current_url = url
            current_window = window_id

        description = describe_action(action)
        time_str = ""
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            time_str = dt.strftime("%H:%M:%S")
        except Exception:
            pass

        lines.append(f"Step {step} [{time_str}]: {description}")

    return lines


# ─── Screenshot helpers ────────────────────────────────────────────────────────
def take_screenshot(driver, folder: str) -> str:
    """Save screenshot to folder, return filepath."""
    os.makedirs(folder, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filepath = os.path.join(folder, f"screenshot_{ts}.png")
    driver.save_screenshot(filepath)
    return filepath


# ─── Thread: New window checker ────────────────────────────────────────────────
def thread_new_window_checker(driver, injected_windows, last_urls, stop_flag,
                               screenshot_folder, current_window_ref,
                               source="file", db_handler=None, driver_lock=None):
    """
    Detects newly opened windows/tabs and injects the recorder JS.
    """
    print("🧵 Thread 1 started: new window checker")
    _lock = driver_lock or threading.Lock()

    while not stop_flag["stop"]:
        try:
            with _lock:
                handles = driver.window_handles
            for handle in handles:
                if handle not in injected_windows:
                    with _lock:
                        driver.switch_to.window(handle)
                        driver.execute_script(injection_script(handle))
                        injected_windows[handle] = True
                        last_urls[handle] = driver.current_url
                        current_window_ref["handle"] = handle

                        if source == "file":
                            take_screenshot(driver, screenshot_folder)
                        elif source == "database" and db_handler:
                            db_handler.take_screenshot_db(driver, "iqea")

                    print(f"✅ JS injected in new window {handle}")
        except Exception as e:
            print(f"⚠️ New window checker error: {e}")
        time.sleep(2)

    print("🛑 Thread 1 stopped")


# ─── Thread: Focus & URL monitor ──────────────────────────────────────────────
def thread_focus_and_url_monitor(driver, injected_windows, last_urls, stop_flag,
                                  screenshot_folder, current_window_ref,
                                  source="file", db_handler=None, driver_lock=None):
    """
    Watches the active window for URL changes (SPA navigation) and reinjection.
    """
    print("🧵 Thread 2 started: focus/URL monitor")
    _lock = driver_lock or threading.Lock()

    while not stop_flag["stop"]:
        try:
            with _lock:
                handle = driver.current_window_handle
                current_window_ref["handle"] = handle
                current_url = driver.current_url

            if last_urls.get(handle) != current_url:
                with _lock:
                    driver.execute_script(action_utils.injection_script_updated_fixed(handle))
                    last_urls[handle] = current_url
                print(f"🔄 URL changed → reinjected in {handle} ({current_url})")

        except Exception as e:
            print(f"⚠️ Focus/URL monitor error: {e}")
        time.sleep(2)

    print("🛑 Thread 2 stopped")


# ─── Thread: Screenshot on page change ────────────────────────────────────────
def thread_focus_screenshot(driver, stop_flag, screenshot_folder,
                             source="file", db_handler=None, driver_lock=None):
    """
    Takes a screenshot whenever the URL or DOM element count changes.
    """
    print("📸 Thread 3 started: screenshot monitor")
    _lock = driver_lock or threading.Lock()
    last_url = None
    prev_count = None
    first_run = True

    while not stop_flag["stop"]:
        try:
            with _lock:
                current_url = driver.current_url
                current_count = len(driver.find_elements("xpath", "//*"))

            page_changed = first_run or current_url != last_url or current_count != prev_count
            first_run = False

            if page_changed:
                last_url = current_url
                prev_count = current_count

                # Wait for DOM ready
                for _ in range(50):
                    with _lock:
                        state = driver.execute_script("return document.readyState")
                    if state == "complete":
                        break
                    time.sleep(0.1)

                with _lock:
                    if source == "file":
                        fp = take_screenshot(driver, screenshot_folder)
                    elif source == "database" and db_handler:
                        fp = db_handler.take_screenshot_db(driver, "iqea")
                    else:
                        fp = None
                print(f"📸 Screenshot => {fp}")

        except Exception as e:
            print(f"❌ Screenshot thread error: {e}")
        time.sleep(1)

    print("🛑 Thread 3 stopped")


# ─── Thread: Idle reinjection checker ─────────────────────────────────────────
def thread_reinject_action_check(driver, stop_flag, last_urls=None,
                                  current_window_ref=None, injected_windows=None,
                                  idle_timeout=5, driver_lock=None):
    """
    If no action recorded for > idle_timeout seconds, clears injected_windows
    so threads 1 & 2 will reinject on next cycle.
    Prevents stale listeners after user inactivity.
    """
    print("🧵 Thread 4 started: idle reinject checker")
    _lock = driver_lock or threading.Lock()

    while not stop_flag["stop"]:
        try:
            with _lock:
                result = driver.execute_script("""
                    const actions = JSON.parse(localStorage.getItem('recordedActions') || '[]');
                    const lastReinject = localStorage.getItem('lastReinjectTime');
                    const lastAction = actions.length > 0 ? actions[actions.length - 1].timestamp : null;
                    return { lastAction, lastReinject };
                """)

            last_action = result.get("lastAction")
            last_reinject = result.get("lastReinject")

            last_action_ts = None
            if last_action:
                try:
                    dt = datetime.fromisoformat(str(last_action).replace("Z", "+00:00"))
                    last_action_ts = dt.timestamp()
                except Exception:
                    pass

            last_reinject_ts = None
            if last_reinject:
                try:
                    last_reinject_ts = float(last_reinject)
                except Exception:
                    pass

            if last_action_ts:
                now_ts = time.time()
                if not last_reinject_ts or last_action_ts > last_reinject_ts:
                    diff = now_ts - last_action_ts
                    if diff >= idle_timeout:
                        print(f"⏱️ Idle {round(diff,1)}s → clearing injected_windows for reinject")
                        if injected_windows is not None:
                            injected_windows.clear()
                        with _lock:
                            driver.execute_script(
                                "localStorage.setItem('lastReinjectTime', Date.now() / 1000);"
                            )

        except Exception as e:
            print(f"⚠️ Idle reinject checker error: {e}")

        time.sleep(2)

    print("🛑 Thread 4 stopped")