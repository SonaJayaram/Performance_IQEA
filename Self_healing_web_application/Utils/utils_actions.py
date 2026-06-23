# utils_action.py
import time
import re
import os
import json
from collections import defaultdict
from urllib.parse import urlparse
#from utilities.db_utils.models import Screenshot
# Setup output folder
current_path = os.getcwd()
output_folder = os.path.join(current_path, "output")
Action_collection = os.path.join(output_folder, "Action_collection")
JS_EVENT_LISTENER_allsite="""(function () {
    if (!window.recordedActions) {
        window.recordedActions = [];
    }

    function getXPath(el) {
        const getPos = e => {
            let pos = 1;
            while (e.previousElementSibling) {
                e = e.previousElementSibling;
                pos++;
            }
            return pos;
        };

        const parts = [];
        while (el && el.nodeType === Node.ELEMENT_NODE) {
            let index = getPos(el);
            let tag = el.nodeName.toLowerCase();
            parts.unshift(`${tag}[${index}]`);
            el = el.parentNode;
        }
        return '/' + parts.join('/');
    }

    function recordAction(type, target) {
        if (!target || ["script", "style"].includes(target.tagName?.toLowerCase())) return;

        const xpath = getXPath(target);
        const label = target.getAttribute("aria-label") || target.name || target.id || target.innerText || target.placeholder || target.value || target.type;
        const value = (type === "input" || type === "change") ? target.value || "" : "";
        const url = window.location.href;

        const exists = window.recordedActions.some(action => action.xpath === xpath && action.action === type);
        if (!exists) {
            window.recordedActions.push({ action: type, xpath, label: label?.trim(), value, url });
            console.log("Recorded:", { action: type, xpath, label, value });
        }
    }

    function attachListeners() {
        document.addEventListener('click', e => {
            recordAction('click', e.target);
        });

        document.addEventListener('change', e => {
            recordAction('change', e.target);
        });

        document.addEventListener('blur', e => {
            if (e.target.tagName.toLowerCase() === 'input' || e.target.tagName.toLowerCase() === 'textarea') {
                recordAction('input', e.target);
            }
        }, true);
    }

    if (document.readyState === "complete") {
        attachListeners();
    } else {
        window.addEventListener('load', attachListeners);
    }

    // Optionally observe DOM changes
    const observer = new MutationObserver(() => {
        attachListeners();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    console.log("Recording actions...");
})();
"""

JS_EVENT_LISTENER_Ecommerce = """
(function () {
    const attached = new WeakSet();

    function getXPath(el) {
        if (!el || el.nodeType !== Node.ELEMENT_NODE) return '';
        if (el.id) return `//*[@id="${el.id}"]`;

        const parts = [];
        while (el && el.nodeType === Node.ELEMENT_NODE) {
            let tag = el.nodeName.toLowerCase();
            let index = 1;
            let sibling = el.previousElementSibling;
            while (sibling) {
                if (sibling.nodeName.toLowerCase() === tag) index++;
                sibling = sibling.previousElementSibling;
            }
            parts.unshift(`${tag}[${index}]`);
            el = el.parentNode;
        }
        return '/' + parts.join('/');
    }

    function getLabel(target) {
        return (
            target.getAttribute("aria-label") ||
            target.getAttribute("data-testid") ||
            target.getAttribute("data-label") ||
            target.name ||
            target.id ||
            target.placeholder ||
            target.innerText?.trim() ||
            target.value ||
            target.type ||
            ''
        );
    }

    function saveAction(action) {
        const existing = JSON.parse(localStorage.getItem("recordedActions") || "[]");
        existing.push(action);
        localStorage.setItem("recordedActions", JSON.stringify(existing));
    }

    function recordAction(type, target) {
        try {
            if (!target || ["script", "style"].includes(target.tagName?.toLowerCase())) return;

            const xpath = getXPath(target);
            const label = getLabel(target).trim();
            const value = (type === "input" || type === "change") ? (target.value || "") : "";
            const url = window.location.href;
            const timestamp = new Date().toISOString();

            const last = JSON.parse(localStorage.getItem("recordedActions") || "[]").slice(-1)[0];
            if (last && last.action === type && last.xpath === xpath && last.value === value) return;

            const actionObj = { action: type, xpath, label, value, url, timestamp };
            saveAction(actionObj);
            console.log("🔴 Recorded:", actionObj);
        } catch (err) {
            console.error("Recording error:", err);
        }
    }

    function addListenersTo(documentRoot = document) {
        if (attached.has(documentRoot)) return;
        attached.add(documentRoot);

        // Event types to monitor
        const events = [
            { type: 'click', options: { capture: true } },
            { type: 'pointerdown', options: { capture: true } },
            { type: 'change', options: { capture: true } },
            { type: 'blur', options: { capture: true } }
        ];

        events.forEach(({ type, options }) => {
            documentRoot.addEventListener(type, (e) => {
                const target = e.target;

                if (type === 'blur' && (target.tagName.toLowerCase() === 'input' || target.tagName.toLowerCase() === 'textarea')) {
                    recordAction('input', target);
                } else {
                    recordAction(type, target);
                }
            }, options);
        });
    }

    function init() {
        addListenersTo(document);

        const observer = new MutationObserver(mutations => {
            for (const mutation of mutations) {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {
                        addListenersTo(node);
                        node.querySelectorAll('*').forEach(el => addListenersTo(el));
                    }
                });
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });
        console.log("✅ Action recorder initialized...");
    }

    if (document.readyState === "complete" || document.readyState === "interactive") {
        init();
    } else {
        window.addEventListener("DOMContentLoaded", init);
    }
})();
"""

FINAL_JS_ACTION_LISTENER = """ 
(function () {
    // Initialize recordedActions from localStorage or empty array
    window.recordedActions = JSON.parse(localStorage.getItem("recordedActions") || "[]");

    function saveAction(action) {
        const existing = JSON.parse(localStorage.getItem("recordedActions") || "[]");
        existing.push(action);
        localStorage.setItem("recordedActions", JSON.stringify(existing));
    }

    function getXPath(el) {
        const getPos = e => {
            let pos = 1;
            while (e.previousElementSibling) {
                e = e.previousElementSibling;
                pos++;
            }
            return pos;
        };

        const parts = [];
        while (el && el.nodeType === Node.ELEMENT_NODE) {
            let index = getPos(el);
            let tag = el.nodeName.toLowerCase();
            parts.unshift(`${tag}[${index}]`);
            el = el.parentNode;
        }
        return '/' + parts.join('/');
    }

    function recordAction(type, target) {
        if (!target || ["script", "style"].includes(target.tagName?.toLowerCase())) return;

        const xpath = getXPath(target);
        const label = target.getAttribute("aria-label") || target.name || target.id || target.innerText || target.placeholder || target.value || target.type;
        const value = (type === "input" || type === "change") ? target.value || "" : "";
        const url = window.location.href;

        const exists = window.recordedActions.some(action => action.xpath === xpath && action.action === type && action.value === value);
        if (!exists) {
            const actionObj = { action: type, xpath, label: label?.trim(), value, url };
            window.recordedActions.push(actionObj);
            saveAction(actionObj);
            console.log("Recorded:", actionObj);
        }
    }

    function attachListeners() {
        document.addEventListener('click', e => {
            recordAction('click', e.target);
        });

        document.addEventListener('change', e => {
            recordAction('change', e.target);
        });

        document.addEventListener('blur', e => {
            const tag = e.target.tagName.toLowerCase();
            if (tag === 'input' || tag === 'textarea') {
                recordAction('input', e.target);
            }
        }, true);
    }

    if (document.readyState === "complete") {
        attachListeners();
    } else {
        window.addEventListener('load', attachListeners);
    }

    // Observe DOM changes to reattach listeners if needed (optional)
    const observer = new MutationObserver(() => {
        attachListeners();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    console.log("Recording actions...");
})();
"""


injection_script = f"""
var script = document.createElement('script');
script.type = 'text/javascript';
script.text = {json.dumps(FINAL_JS_ACTION_LISTENER)};
document.documentElement.appendChild(script);
"""


def start_recording(driver):
    driver.execute_script(injection_script)

def get_recorded_actions(driver):
    # return driver.execute_script("return window.recordedActions || []")
    raw_actions = driver.execute_script("return localStorage.getItem('recordedActions') || '[]';")
    return json.loads(raw_actions) if raw_actions else []

def wait_for_url_change(driver, initial_url, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if driver.current_url != initial_url:
            return True
        time.sleep(1)
    return False


def generate_workflow(actions):
    workflow_lines = []
    recorded = set()
    prev_url = None

    for act in actions:
        url = act.get("url", "Unknown")

        # Only add "Page:" line if URL changes from previous
        if url != prev_url:
            workflow_lines.append(f"Page: [{url}]")
            prev_url = url

        readable = humanize_action(act)
        if readable and readable not in recorded:
            workflow_lines.append(f"- {readable}")
            recorded.add(readable)

    return workflow_lines

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def take_screenshot(driver, folder):
    url = driver.current_url
    parsed_url = urlparse(url)
    page_name = sanitize_filename(parsed_url.path.strip("/")) or "home"
    file_path = os.path.join(folder, f"{page_name}.png")
    driver.save_screenshot(file_path)
    return file_path

def humanize_action(action_dict):

    action_type = action_dict.get("action")
    tag = (action_dict.get("tag") or "").lower()

    label = action_dict.get("label")
    label = label.strip() if isinstance(label, str) else ""

    value = action_dict.get("value")
    value = value.strip() if isinstance(value, str) else ""

    placeholder = action_dict.get("placeholder")
    placeholder = placeholder.strip() if isinstance(placeholder, str) else ""

    element_id = action_dict.get("id")
    element_id = element_id.strip() if isinstance(element_id, str) else ""

    # Fallback-friendly label logic
    display_label = label or placeholder or element_id.replace("-", " ").replace("_", " ").title()

    if action_type == "click":
        if tag == "button" or "btn" in element_id.lower():
            return f'Click the "{display_label}" button'
        elif tag == "a":
            return f'Click the "{display_label}" link'
        else:
            return f'Click on "{display_label}"'

    elif action_type == "input":
        return f'Enter "{value}" in the "{display_label}" field'

    elif action_type == "change":
        return f'Change the value in "{display_label}"'

    elif action_type == "select":
        return f'Select "{value}" from the "{display_label}" dropdown'

    elif action_type == "navigate":
        return f'Navigate to "{display_label}" page'

    # Safeguard for unknown or missing action_type
    if action_type:
        return f'{action_type.capitalize()} on "{display_label}"'
    else:
        return f'Perform action on "{display_label}"'

def monitor_url_changes_for_each_nav(driver, stop_flag):
    last_url = ""
    while not stop_flag["stop"]:
        try:
            current_url = driver.current_url
            if current_url != last_url:
                last_url = current_url

                # Wait for page to fully load
                for _ in range(50):  # up to ~5 seconds
                    state = driver.execute_script("return document.readyState")
                    if state == "complete":
                        break
                    time.sleep(0.1)

                # Re-inject your recorder JS here
                start_recording(driver)  # Make sure injection_script1 is in scope!

        except Exception as e:
            print("Error during URL monitoring:", e)
        time.sleep(1)  # check every second
def is_page_loaded(driver):
    return driver.execute_script("return document.readyState")