import time
import re
import os
import json
from urllib.parse import urlparse
from selenium.webdriver.support.ui import WebDriverWait

current_path = os.getcwd()
output_folder = os.path.join(current_path, "output")
Action_collection = os.path.join(output_folder, "Action_collection")
os.makedirs(Action_collection, exist_ok=True)

# ─── IQEA v2.0 Smart Action Listener ─────────────────────────────────────────
# Ported from IQEA utilities/utils_action.py
# Key improvements over old basic listener:
#   - Smart XPath: prefers id > data-testid/data-cy > aria-label/name > positional
#   - Full event coverage: keyboard, scroll, drag-drop, right-click, copy/paste, file upload
#   - Shadow DOM + iFrame support
#   - SPA-aware: patches pushState/replaceState and re-attaches on route change
#   - Cross-tab relay via BroadcastChannel
#   - AbortController prevents duplicate listener stacking on reinjection
#   - Step sequencing: every action has a step number
JS_action_listeners = """/**
 * IQEA Enhanced Action Listener v2.0
 */
(function (statusKey) {

    const _currentUrl = window.location.href;
    if (window.__iqea_injected_url === _currentUrl) return;
    window.__iqea_injected_url = _currentUrl;

    function nextStepNumber() {
        const n = parseInt(localStorage.getItem("__iqea_step") || "0") + 1;
        localStorage.setItem("__iqea_step", String(n));
        return n;
    }

    if (!window.__recordedActions) {
        window.__recordedActions = JSON.parse(localStorage.getItem("recordedActions") || "[]");
    }

    function saveAction(action) {
        const existing = JSON.parse(localStorage.getItem("recordedActions") || "[]");
        const last = existing.length > 0 ? existing[existing.length - 1] : null;

        if (last &&
            last.action === action.action &&
            last.label === action.label &&
            last.url === action.url &&
            (!action.value || action.value === last.value) &&
            (new Date(action.timestamp) - new Date(last.timestamp)) < 500) {
            return;
        }

        if (last && last.action === "switch" && last.windowId === action.windowId) {
            existing.pop();
            window.__recordedActions.pop();
        }

        existing.push(action);
        localStorage.setItem("recordedActions", JSON.stringify(existing));
        window.__recordedActions.push(action);

        try {
            window.dispatchEvent(new CustomEvent("__action_recorded", { detail: action }));
            if (window.opener && window.opener !== window) {
                window.opener.postMessage({ __relay: true, payload: action }, "*");
            }
            if (window.__iqeaChannel) {
                window.__iqeaChannel.postMessage({ __relay: true, payload: action });
            }
        } catch (err) {
            console.warn("Relay failed:", err);
        }
    }

    try {
        if (!window.__iqeaChannel) {
            window.__iqeaChannel = new BroadcastChannel("__iqea_channel");
            window.__iqeaChannel.onmessage = (e) => {
                if (e.data && e.data.__relay && e.data.payload) saveAction(e.data.payload);
            };
        }
    } catch (_) {}

    if (!window.__iqea_msg_listener) {
        window.__iqea_msg_listener = true;
        window.addEventListener("message", function (event) {
            if (event.data && event.data.__relay && event.data.payload) {
                saveAction(event.data.payload);
                if (window.opener && window.opener !== window) {
                    window.opener.postMessage(event.data, "*");
                }
            }
        });
    }

    if (!window.__iqea_focus_listener) {
        window.__iqea_focus_listener = true;
        window.addEventListener("focus", () => {
            localStorage.setItem("lastFocusedWindow", window.location.href);
        });
    }

    function getSmartXPath(el) {
        if (!el || el.nodeType !== Node.ELEMENT_NODE) return "";

        if (el.id && !/^\\d/.test(el.id)) return `//*[@id="${el.id}"]`;

        const testAttrs = ["data-testid", "data-qa", "data-cy", "data-id", "data-automation-id"];
        for (const attr of testAttrs) {
            const val = el.getAttribute(attr);
            if (val) return `//${el.tagName.toLowerCase()}[@${attr}="${val}"]`;
        }

        const interactiveTags = ["input", "button", "select", "textarea", "a"];
        if (interactiveTags.includes(el.tagName.toLowerCase())) {
            const ariaLabel = el.getAttribute("aria-label");
            if (ariaLabel) return `//${el.tagName.toLowerCase()}[@aria-label="${ariaLabel}"]`;
            const name = el.getAttribute("name");
            if (name) return `//${el.tagName.toLowerCase()}[@name="${name}"]`;
            const placeholder = el.getAttribute("placeholder");
            if (placeholder) return `//${el.tagName.toLowerCase()}[@placeholder="${placeholder}"]`;
        }

        const parts = [];
        let node = el;
        while (node && node.nodeType === Node.ELEMENT_NODE) {
            let index = 1;
            let sib = node.previousElementSibling;
            while (sib) {
                if (sib.tagName === node.tagName) index++;
                sib = sib.previousElementSibling;
            }
            const tag = node.tagName.toLowerCase();
            parts.unshift(index > 1 ? `${tag}[${index}]` : tag);
            node = node.parentNode;
        }
        return "/" + parts.join("/");
    }

    function getLabel(el) {
        if (!el) return "";
        return (
            el.getAttribute("aria-label") ||
            el.getAttribute("data-testid") ||
            el.getAttribute("name") ||
            el.id ||
            el.getAttribute("placeholder") ||
            el.getAttribute("alt") ||
            el.getAttribute("title") ||
            (el.innerText || "").trim().substring(0, 80) ||
            el.getAttribute("class") ||
            el.type || ""
        );
    }

    function recordAction(type, target, extra = {}) {
        const grace = window.__reinjectionGrace || 0;
        if (grace > 0 && (Date.now() - grace) < 300) return;

        if (!target || ["script", "style", "html", "body", "head"].includes(
            target.tagName?.toLowerCase())) return;

        const xpath = getSmartXPath(target);
        const label = getLabel(target);
        const value = extra.value !== undefined
            ? extra.value
            : (["input", "change", "input_others", "select"].includes(type)
                ? (target.value || target.innerText || "") : "");

        const actionObj = {
            step:      nextStepNumber(),
            action:    type,
            xpath,
            label:     label?.trim(),
            value:     String(value).trim(),
            url:       window.location.href,
            windowId:  window.name || statusKey,
            timestamp: new Date().toISOString(),
            ...extra
        };

        saveAction(actionObj);
        console.log("IQEA Recorded:", actionObj);
    }

    let _scrollTimer = null;
    function throttledScroll(target) {
        if (_scrollTimer) clearTimeout(_scrollTimer);
        _scrollTimer = setTimeout(() => {
            const scrollX = Math.round(window.scrollX || target.scrollLeft || 0);
            const scrollY = Math.round(window.scrollY || target.scrollTop || 0);
            recordAction("scroll", target === window ? document.body : target, {
                value: `scrollX:${scrollX},scrollY:${scrollY}`
            });
        }, 400);
    }

    let _dragSource = null;

    function attachListeners(root) {
        if (root.__iqea_controller) {
            root.__iqea_controller.abort();
        }
        const controller = new AbortController();
        const signal = controller.signal;
        root.__iqea_controller = controller;

        const doc = root.ownerDocument || root;
        const opts = { signal, capture: true };

        doc.addEventListener("click",       e => recordAction("click",       e.target), opts);
        doc.addEventListener("contextmenu", e => recordAction("right_click", e.target), opts);

        doc.addEventListener("change", e => {
            const el  = e.target;
            const tag = el.tagName.toLowerCase();
            if      (tag === "select")       recordAction("select",      el, { value: el.options[el.selectedIndex]?.text || el.value });
            else if (el.type === "checkbox") recordAction("checkbox",    el, { value: el.checked ? "checked" : "unchecked" });
            else if (el.type === "radio")    recordAction("radio",       el, { value: el.value });
            else if (el.type === "file")     recordAction("file_upload", el, { value: Array.from(el.files || []).map(f => f.name).join(", ") });
            else                             recordAction("input",       el);
        }, opts);

        doc.addEventListener("focusout", e => {
            const tag = e.target.tagName.toLowerCase();
            if (!["button", "input", "textarea", "select"].includes(tag))
                recordAction("change", e.target);
        }, opts);

        doc.addEventListener("keydown", e => {
            const key   = e.key;
            const ctrl  = e.ctrlKey || e.metaKey;
            const shift = e.shiftKey;

            if (key === "Enter")  { recordAction("key_enter",  e.target, { value: "Enter" });                     return; }
            if (key === "Escape") { recordAction("key_escape", e.target, { value: "Escape" });                    return; }
            if (key === "Tab")    { recordAction("key_tab",    e.target, { value: shift ? "Shift+Tab" : "Tab" }); return; }

            if (ctrl) {
                const map = { c:"copy", x:"cut", v:"paste", z:"undo", y:"redo",
                              a:"select_all", f:"find", s:"save", p:"print" };
                const action = map[key.toLowerCase()];
                if (action) recordAction(`shortcut_${action}`, e.target,
                    { value: `${e.metaKey ? "Cmd" : "Ctrl"}+${key.toUpperCase()}` });
            }
            if (key.startsWith("F") && !isNaN(key.slice(1)))
                recordAction("function_key", e.target, { value: key });
        }, opts);

        doc.addEventListener("copy",  e => recordAction("copy",  e.target,
            { value: (doc.getSelection()||"").toString().substring(0,200) }), opts);
        doc.addEventListener("cut",   e => recordAction("cut",   e.target,
            { value: (doc.getSelection()||"").toString().substring(0,200) }), opts);
        doc.addEventListener("paste", e => {
            let pasted = "";
            try { pasted = (e.clipboardData || window.clipboardData)?.getData("text")?.substring(0,200) || ""; } catch(_) {}
            recordAction("paste", e.target, { value: pasted });
        }, opts);

        window.addEventListener("scroll", e => throttledScroll(e.target),
            { passive: true, capture: true, signal });
        doc.addEventListener("scroll", e => {
            if (e.target !== window && e.target !== doc) throttledScroll(e.target);
        }, { passive: true, capture: true, signal });

        doc.addEventListener("dragstart", e => {
            _dragSource = e.target;
            recordAction("drag_start", e.target, { value: getLabel(e.target) });
        }, opts);
        doc.addEventListener("drop", e => {
            recordAction("drop", e.target,
                { value: `from: ${getLabel(_dragSource)} to: ${getLabel(e.target)}` });
            _dragSource = null;
        }, opts);

        console.log("IQEA listeners attached to:", root);
    }

    function injectIntoShadowRoots(node) {
        if (!node || node.nodeType !== Node.ELEMENT_NODE) return;
        if (node.shadowRoot) {
            attachListeners(node.shadowRoot);
            node.shadowRoot.querySelectorAll("*").forEach(injectIntoShadowRoots);
        }
        node.querySelectorAll && node.querySelectorAll("*").forEach(child => {
            if (child.shadowRoot) { attachListeners(child.shadowRoot); injectIntoShadowRoots(child); }
        });
    }

    if (!window.__iqea_shadow_observer) {
        window.__iqea_shadow_observer = new MutationObserver(mutations => {
            mutations.forEach(m => m.addedNodes.forEach(n => {
                if (n.nodeType === Node.ELEMENT_NODE) injectIntoShadowRoots(n);
            }));
        });
        window.__iqea_shadow_observer.observe(document.documentElement,
            { childList: true, subtree: true });
    }

    function injectIntoIframe(iframe) {
        try {
            const iDoc = iframe.contentDocument || iframe.contentWindow?.document;
            if (iDoc && iDoc.body) {
                attachListeners(iDoc);
                injectIntoShadowRoots(iDoc.documentElement);
                if (!iframe.__iqea_iframe_observer) {
                    iframe.__iqea_iframe_observer = new MutationObserver(mutations => {
                        mutations.forEach(m => m.addedNodes.forEach(n => {
                            if (n.tagName === "IFRAME") injectIntoIframe(n);
                        }));
                    });
                    iframe.__iqea_iframe_observer.observe(iDoc, { childList: true, subtree: true });
                }
            }
        } catch (e) {
            console.warn("Cross-origin iframe skipped:", iframe.src);
        }
    }

    function injectAllIframes() {
        document.querySelectorAll("iframe").forEach(injectIntoIframe);
    }

    if (!window.__iqea_iframe_observer) {
        window.__iqea_iframe_observer = new MutationObserver(mutations => {
            mutations.forEach(m => m.addedNodes.forEach(n => {
                if (n.tagName === "IFRAME") injectIntoIframe(n);
                if (n.querySelectorAll) n.querySelectorAll("iframe").forEach(injectIntoIframe);
            }));
        });
        window.__iqea_iframe_observer.observe(document.documentElement,
            { childList: true, subtree: true });
    }

    function patchHistory() {
        const wrap = (orig) => function (...args) {
            const result = orig.apply(this, args);
            window.dispatchEvent(new Event("__iqea_spa_navigate"));
            return result;
        };
        if (!window.__iqea_history_patched) {
            history.pushState    = wrap(history.pushState);
            history.replaceState = wrap(history.replaceState);
            window.__iqea_history_patched = true;
        }
    }

    if (!window.__iqea_popstate_listener) {
        window.__iqea_popstate_listener = true;
        window.addEventListener("popstate", () =>
            window.dispatchEvent(new Event("__iqea_spa_navigate")));
        window.addEventListener("__iqea_spa_navigate", () => {
            window.__iqea_injected_url = null;
            setTimeout(() => {
                attachListeners(document);
                injectAllIframes();
                injectIntoShadowRoots(document.documentElement);
            }, 300);
        });
    }

    function init() {
        patchHistory();
        attachListeners(document);
        injectAllIframes();
        injectIntoShadowRoots(document.documentElement);
        console.log("IQEA v2.0 ready. statusKey:", statusKey);
    }

    if (document.readyState === "complete" || document.readyState === "interactive") init();
    else window.addEventListener("load", init, { once: true });

})(window.__iqea_windowId);"""


def injection_script():
    return f"""
    (function() {{
        if (window.__recorderInjected) return;
        window.__recorderInjected = true;

        if (!window.name || window.name.trim() === "") {{
            window.name = "sh_recorder_" + Math.random().toString(36).substr(2, 9);
        }}
        const windowId = window.name;
        window.__iqea_windowId = windowId;

        const statusKey = "recorder_status_" + windowId;

        function updateStatus(alive = true) {{
            localStorage.setItem(statusKey, JSON.stringify({{
                windowId: windowId,
                alive: alive,
                url: window.location.href,
                ts: Date.now()
            }}));
        }}

        updateStatus(true);
        setInterval(() => updateStatus(true), 2000);
        window.addEventListener("beforeunload", () => updateStatus(false));

        {JS_action_listeners
            .replace("STATUS_KEY_PLACEHOLDER", "statusKey")
            .replace("WINDOW_ID_PLACEHOLDER", "windowId")}

        window.__reinjectionGrace = Date.now();
        console.log("✅ Self-Healing Recorder v2.0 active. windowId:", windowId);
    }})();
    """


def start_recording(driver):
    driver.execute_script(injection_script())


def get_recorded_actions(driver):
    raw = driver.execute_script("return localStorage.getItem('recordedActions') || '[]';")
    return json.loads(raw) if raw else []


def clear_recorded_actions(driver):
    driver.execute_script("localStorage.removeItem('recordedActions'); localStorage.removeItem('__iqea_step');")


def wait_for_url_change(driver, initial_url, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if driver.current_url != initial_url:
            return True
        time.sleep(1)
    return False


def is_page_loaded(driver):
    return driver.execute_script("return document.readyState") == "complete"


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def take_screenshot(driver, folder):
    url = driver.current_url
    parsed_url = urlparse(url)
    page_name = sanitize_filename(parsed_url.path.strip("/")) or "home"
    file_path = os.path.join(folder, f"{page_name}.png")
    driver.save_screenshot(file_path)
    return file_path


def monitor_url_changes_for_each_nav(driver, stop_flag):
    last_url = ""
    while not stop_flag["stop"]:
        try:
            current_url = driver.current_url
            if current_url != last_url:
                last_url = current_url
                for _ in range(50):
                    state = driver.execute_script("return document.readyState")
                    if state == "complete":
                        break
                    time.sleep(0.1)
                start_recording(driver)
        except Exception as e:
            print("Error during URL monitoring:", e)
        time.sleep(1)


def humanize_action(action_dict):
    action_type = action_dict.get("action", "")
    label = action_dict.get("label", "")
    label = label.strip() if isinstance(label, str) else ""
    value = action_dict.get("value", "")
    value = value.strip() if isinstance(value, str) else ""
    url = action_dict.get("url", "")

    display_label = label or "[element]"

    if action_type == "click":
        return f'Click on "{display_label}"'
    elif action_type == "right_click":
        return f'Right-click on "{display_label}"'
    elif action_type in ("input", "enter_text", "change"):
        return f'Enter "{value}" in the "{display_label}" field'
    elif action_type == "select":
        return f'Select "{value}" from the "{display_label}" dropdown'
    elif action_type == "select_radio" or action_type == "radio":
        return f'Select radio "{value}" for "{display_label}"'
    elif action_type == "checkbox":
        return f'Set checkbox "{display_label}" to {value}'
    elif action_type == "check":
        return f'Check "{display_label}"'
    elif action_type == "uncheck":
        return f'Uncheck "{display_label}"'
    elif action_type == "navigate":
        return f'Navigate to "{url}"'
    elif action_type == "key_enter":
        return f'Press Enter on "{display_label}"'
    elif action_type == "key_escape":
        return f'Press Escape on "{display_label}"'
    elif action_type == "key_tab":
        return f'Press Tab on "{display_label}"'
    elif action_type.startswith("shortcut_"):
        shortcut = action_type.replace("shortcut_", "").capitalize()
        return f'{shortcut} shortcut ({value}) on "{display_label}"'
    elif action_type == "function_key":
        return f'Press {value} on "{display_label}"'
    elif action_type == "scroll":
        return f'Scroll on "{display_label}" ({value})'
    elif action_type == "drag_start":
        return f'Start drag from "{display_label}"'
    elif action_type == "drop":
        return f'Drop — {value}'
    elif action_type == "file_upload":
        return f'Upload file "{value}" via "{display_label}"'
    elif action_type in ("copy", "cut", "paste"):
        return f'{action_type.capitalize()} on "{display_label}"'
    elif action_type == "hover":
        return f'Hover over "{display_label}"'
    else:
        return f'{action_type.capitalize()} on "{display_label}"' if action_type else None


def generate_workflow(actions):
    """Convert raw recorded actions to human-readable workflow text."""
    workflow_lines = []
    prev_url = None

    for act in actions:
        url = act.get("url", "Unknown")
        if url != prev_url:
            workflow_lines.append(f"Page: [{url}]")
            prev_url = url
        readable = humanize_action(act)
        if readable:
            xpath = act.get("xpath", "")
            label = act.get("label", "")
            value = act.get("value", "")
            # Include element details as a comment for DOM collection use
            workflow_lines.append(
                f"- {readable} | xpath={xpath} | label={label} | value={value}"
            )

    return workflow_lines
