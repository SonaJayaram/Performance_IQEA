# utils_action.py  — IQEA v2.0  (bug-fixed: reinject signature, driver_lock, grace period)
import time
import re
import os
import json
import threading
from datetime import datetime
from urllib.parse import urlparse

from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# ─── IQEA v2 Enhanced Action Listener (embedded) ──────────────────────────────
# FIX 3: Grace period reduced to 300ms (was 800ms) and only applied on FIRST
#         inject, not on every URL-change reinject. This prevents the grace
#         window from eating user actions on every page navigation.
JS_action_listeners = """/**
 * IQEA Enhanced Action Listener v2.0
 */
(function (statusKey) {

    // ─── Guard: SPA-safe reinject (URL-bound, not permanent) ──────────────────
    const _currentUrl = window.location.href;
    if (window.__iqea_injected_url === _currentUrl) return;
    window.__iqea_injected_url = _currentUrl;

    // ─── Global step counter ──────────────────────────────────────────────────
    function nextStepNumber() {
        const n = parseInt(localStorage.getItem("__iqea_step") || "0") + 1;
        localStorage.setItem("__iqea_step", String(n));
        return n;
    }

    // ─── Action persistence ────────────────────────────────────────────────────
    if (!window.__recordedActions) {
        window.__recordedActions = JSON.parse(localStorage.getItem("recordedActions") || "[]");
    }

    function saveAction(action) {
        const existing = JSON.parse(localStorage.getItem("recordedActions") || "[]");
        const last = existing.length > 0 ? existing[existing.length - 1] : null;

        // Skip exact duplicate within 500ms
        if (last &&
            last.action === action.action &&
            last.label === action.label &&
            last.url === action.url &&
            (!action.value || action.value === last.value) &&
            (new Date(action.timestamp) - new Date(last.timestamp)) < 500) {
            return;
        }

        // Replace trailing orphan "switch" with real action
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

    // BroadcastChannel for cross-tab relay (same origin)
    try {
        window.__iqeaChannel = new BroadcastChannel("__iqea_channel");
        window.__iqeaChannel.onmessage = (e) => {
            if (e.data && e.data.__relay && e.data.payload) saveAction(e.data.payload);
        };
    } catch (_) {}

    // Cross-window postMessage relay
    window.addEventListener("message", function (event) {
        if (event.data && event.data.__relay && event.data.payload) {
            saveAction(event.data.payload);
            if (window.opener && window.opener !== window) {
                window.opener.postMessage(event.data, "*");
            }
        }
    });

    window.addEventListener("focus", () => {
        localStorage.setItem("lastFocusedWindow", window.location.href);
    });

    // ─── Smart XPath builder ───────────────────────────────────────────────────
    function getSmartXPath(el) {
        if (!el || el.nodeType !== Node.ELEMENT_NODE) return "";

        if (el.id && !/^\d/.test(el.id)) return `//*[@id="${el.id}"]`;

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

        // Positional fallback
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

    // ─── Element label extractor ───────────────────────────────────────────────
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

    // ─── Core record function ──────────────────────────────────────────────────
    // FIX 3: Grace check uses 300ms (not 800ms) and only blocks if grace was
    //        set within the last 300ms — prevents eating real user actions
    //        on every URL-change reinject.
    function recordAction(type, target, extra = {}) {
        const grace = window.__reinjectionGrace || 0;
        if (grace > 0 && (Date.now() - grace) < 300) return;

        if (!target || ["script", "style", "html", "body", "head"].includes(target.tagName?.toLowerCase())) return;

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

    // ─── Scroll throttle ──────────────────────────────────────────────────────
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

    // ─── Drag state ───────────────────────────────────────────────────────────
    let _dragSource = null;

    // ─── Attach all listeners ──────────────────────────────────────────────────
    function attachListeners(root) {
        if (root.__iqea_attached) return;
        root.__iqea_attached = true;
        const doc = root.ownerDocument || root;

        doc.addEventListener("click",       e => recordAction("click", e.target), true);
        doc.addEventListener("contextmenu", e => recordAction("right_click", e.target), true);

        doc.addEventListener("change", e => {
            const el  = e.target;
            const tag = el.tagName.toLowerCase();
            if      (tag === "select")       recordAction("select",      el, { value: el.options[el.selectedIndex]?.text || el.value });
            else if (el.type === "checkbox") recordAction("checkbox",    el, { value: el.checked ? "checked" : "unchecked" });
            else if (el.type === "radio")    recordAction("radio",       el, { value: el.value });
            else if (el.type === "file")     recordAction("file_upload", el, { value: Array.from(el.files || []).map(f => f.name).join(", ") });
            else                             recordAction("input",       el);
        }, true);

        doc.addEventListener("focusout", e => {
            const tag = e.target.tagName.toLowerCase();
            if (!["button", "input", "textarea", "select"].includes(tag))
                recordAction("change", e.target);
        }, true);

        doc.addEventListener("keydown", e => {
            const key   = e.key;
            const ctrl  = e.ctrlKey || e.metaKey;
            const shift = e.shiftKey;

            if (key === "Enter")  { recordAction("key_enter",  e.target, { value: "Enter" });                     return; }
            if (key === "Escape") { recordAction("key_escape", e.target, { value: "Escape" });                    return; }
            if (key === "Tab")    { recordAction("key_tab",    e.target, { value: shift ? "Shift+Tab" : "Tab" }); return; }

            if (ctrl) {
                const shortcutMap = { c:"copy", x:"cut", v:"paste", z:"undo", y:"redo", a:"select_all", f:"find", s:"save", p:"print" };
                const action = shortcutMap[key.toLowerCase()];
                if (action) recordAction(`shortcut_${action}`, e.target, { value: `${e.metaKey ? "Cmd" : "Ctrl"}+${key.toUpperCase()}` });
            }
            if (key.startsWith("F") && !isNaN(key.slice(1)))
                recordAction("function_key", e.target, { value: key });
        }, true);

        doc.addEventListener("copy",  e => recordAction("copy",  e.target, { value: (doc.getSelection()||"").toString().substring(0,200) }), true);
        doc.addEventListener("cut",   e => recordAction("cut",   e.target, { value: (doc.getSelection()||"").toString().substring(0,200) }), true);
        doc.addEventListener("paste", e => {
            let pasted = "";
            try { pasted = (e.clipboardData || window.clipboardData)?.getData("text")?.substring(0,200) || ""; } catch(_) {}
            recordAction("paste", e.target, { value: pasted });
        }, true);

        window.addEventListener("scroll", e => throttledScroll(e.target), { passive: true, capture: true });
        doc.addEventListener("scroll", e => {
            if (e.target !== window && e.target !== doc) throttledScroll(e.target);
        }, { passive: true, capture: true });

        doc.addEventListener("dragstart", e => {
            _dragSource = e.target;
            recordAction("drag_start", e.target, { value: getLabel(e.target) });
        }, true);
        doc.addEventListener("drop", e => {
            recordAction("drop", e.target, { value: `from: ${getLabel(_dragSource)} to: ${getLabel(e.target)}` });
            _dragSource = null;
        }, true);

        doc.addEventListener("mouseenter", e => {
            const tag = e.target.tagName?.toLowerCase();
            if (["button","a","select"].includes(tag) ||
                e.target.getAttribute("role") === "menuitem" ||
                e.target.getAttribute("role") === "option")
                recordAction("hover", e.target);
        }, true);
        doc.addEventListener("mouseleave", e => {
            const tag = e.target.tagName?.toLowerCase();
            if (["button","a"].includes(tag)) recordAction("hover_end", e.target);
        }, true);

        console.log("IQEA listeners attached to:", root);
    }

    // ─── Shadow DOM support ───────────────────────────────────────────────────
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
    new MutationObserver(mutations => {
        mutations.forEach(m => m.addedNodes.forEach(n => {
            if (n.nodeType === Node.ELEMENT_NODE) injectIntoShadowRoots(n);
        }));
    }).observe(document.documentElement, { childList: true, subtree: true });

    // ─── iFrame support ───────────────────────────────────────────────────────
    function injectIntoIframe(iframe) {
        try {
            const iDoc = iframe.contentDocument || iframe.contentWindow?.document;
            if (iDoc && iDoc.body) {
                attachListeners(iDoc);
                injectIntoShadowRoots(iDoc.documentElement);
                new MutationObserver(mutations => {
                    mutations.forEach(m => m.addedNodes.forEach(n => {
                        if (n.tagName === "IFRAME") injectIntoIframe(n);
                    }));
                }).observe(iDoc, { childList: true, subtree: true });
            }
        } catch (e) {
            console.warn("Cross-origin iframe skipped:", iframe.src);
        }
    }
    function injectAllIframes() { document.querySelectorAll("iframe").forEach(injectIntoIframe); }
    new MutationObserver(mutations => {
        mutations.forEach(m => m.addedNodes.forEach(n => {
            if (n.tagName === "IFRAME") injectIntoIframe(n);
            if (n.querySelectorAll) n.querySelectorAll("iframe").forEach(injectIntoIframe);
        }));
    }).observe(document.documentElement, { childList: true, subtree: true });

    // ─── SPA route change detection ───────────────────────────────────────────
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
    window.addEventListener("popstate", () => window.dispatchEvent(new Event("__iqea_spa_navigate")));
    window.addEventListener("__iqea_spa_navigate", () => {
        window.__iqea_injected_url = null;
        setTimeout(() => {
            document.__iqea_attached = false;
            attachListeners(document);
            injectAllIframes();
            injectIntoShadowRoots(document.documentElement);
        }, 300);
    });

    // ─── Bootstrap ────────────────────────────────────────────────────────────
    function init() {
        patchHistory();
        attachListeners(document);
        injectAllIframes();
        injectIntoShadowRoots(document.documentElement);
        console.log("IQEA v2.0 ready. statusKey:", statusKey);
    }

    if (document.readyState === "complete" || document.readyState === "interactive") init();
    else window.addEventListener("load", init, { once: true });

})(STATUS_KEY_PLACEHOLDER);"""


# ─── Clear actions JS ──────────────────────────────────────────────────────────
CLEAR_ACTIONS_JS = """
(function() {
    window.__recordedActions      = [];
    window.__iqea_injected_url    = null;
    window.__iqea_lastReadIdx     = 0;
    if (document.__iqea_attached) document.__iqea_attached = false;
    localStorage.removeItem('recordedActions');
    localStorage.removeItem('lastReinjectTime');
    localStorage.setItem('__iqea_step', '0');
    console.log("IQEA: Cleared all recorded actions.");
})();
"""


# ─── Injection ────────────────────────────────────────────────────────────────
# FIX 1: Removed the `handle` parameter — function takes 0 args, matching all
#         existing call sites. windowId is computed inside the JS itself.
#         Thread 2 was passing `handle` here which caused the TypeError and
#         meant JS was NEVER injected on URL changes → zero actions recorded.
def injection_script_updated_fixed():
    """
    Wraps and injects the IQEA v2 JS listener into the current page.

    NOTE: No parameters — windowId is assigned inside the JS via window.name.
    All threads should call this as: driver.execute_script(injection_script_updated_fixed())
    """
    # ── Do the STATUS_KEY_PLACEHOLDER replacement HERE in Python ──────────────
    # The JS ends with })(STATUS_KEY_PLACEHOLDER); — no quotes around it.
    # Replacing at JS runtime with .replace('"STATUS_KEY_PLACEHOLDER"', ...)
    # never matched because the search string had quotes but the source didn't.
    # Result: ReferenceError → listener IIFE never ran → zero actions recorded.
    #
    # Fix: inject a real JS string literal directly into the source before
    # json.dumps so the IIFE receives the windowId as a proper string value.
    # We use a two-step approach:
    #   1. Python replaces STATUS_KEY_PLACEHOLDER with a JS expression that
    #      reads window.name at the moment the outer wrapper runs.
    #   2. The IIFE receives that value as its `statusKey` parameter.
    js_code = JS_action_listeners.replace(
        "STATUS_KEY_PLACEHOLDER",
        "window.__iqea_windowId"          # resolved in outer wrapper below
    )

    return f"""
    (function() {{

        // 1. Stable windowId — assigned once, persists for window lifetime
        if (!window.name || window.name.trim() === "") {{
            window.name = "recorder_" + Math.random().toString(36).substr(2, 9);
        }}
        // Store on window so the injected script tag can read it
        window.__iqea_windowId = window.name;
        const windowId  = window.__iqea_windowId;
        const statusKey = "recorder_status_" + windowId;

        // 2. Clear URL-bound SPA guard -> forces reinject even on same URL
        window.__iqea_injected_url = null;

        // 3. Grace: only on first ever injection (no actions yet).
        //    Skipped on URL-change reinjections so clicks right after
        //    navigation are NOT swallowed by the 300ms dead zone.
        var hasExistingActions = (window.__recordedActions || []).length > 0;
        window.__reinjectionGrace = hasExistingActions ? 0 : Date.now();

        // 4. Remove stale script tag -> prevents duplicate listener stacking
        var old = document.getElementById("iqea_recorder_v2");
        if (old) {{
            old.remove();
            window.__iqea_history_patched = false;
            if (document.__iqea_attached) document.__iqea_attached = false;
        }}

        // 5. Heartbeat (guarded - only one interval per window)
        function updateStatus(alive) {{
            localStorage.setItem(statusKey, JSON.stringify({{
                windowId: windowId,
                alive:    alive,
                url:      window.location.href,
                ts:       Date.now()
            }}));
        }}
        updateStatus(true);
        if (!window.__iqea_heartbeat) {{
            window.__iqea_heartbeat = setInterval(function() {{ updateStatus(true); }}, 2000);
        }}
        window.addEventListener("beforeunload", function() {{ updateStatus(false); }}, {{ once: true }});

        // 6. Inject v2 listener as a script tag.
        //    STATUS_KEY_PLACEHOLDER was already replaced by Python above with
        //    window.__iqea_windowId, so the IIFE receives the correct value.
        var s = document.createElement("script");
        s.id   = "iqea_recorder_v2";
        s.type = "text/javascript";
        s.text = {json.dumps(js_code)};
        document.documentElement.appendChild(s);

        console.log("IQEA v2 injected | windowId:", windowId);
    }})();
    """


# ─── Action collection ────────────────────────────────────────────────────────
def get_recorded_actions(driver) -> list:
    """
    Collect and deduplicate actions from ALL open windows, sorted by step -> timestamp.
    Always restores the original window handle after collection.
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
                key = (a.get("step"), a.get("action"), a.get("xpath"), a.get("timestamp"))
                if key not in seen:
                    seen.add(key)
                    all_actions.append(a)
        except Exception as e:
            print(f"Warning: Error fetching actions from window {handle}: {e}")

    try:
        driver.switch_to.window(original_handle)
    except Exception:
        pass

    all_actions.sort(key=lambda a: (a.get("step", 99999), a.get("timestamp", "")))
    return all_actions


def get_new_actions(driver) -> list:
    """
    Non-destructive in-session action peek using a read-index pointer.
    Safe to call mid-session — does NOT clear localStorage.
    """
    return driver.execute_script("""
        const actions  = window.__recordedActions || [];
        const lastIdx  = window.__iqea_lastReadIdx || 0;
        const newItems = actions.slice(lastIdx);
        window.__iqea_lastReadIdx = actions.length;
        return newItems;
    """)


# ─── Action -> human-readable description ────────────────────────────────────
def humanize_action(action_dict: dict) -> str:
    action_type = action_dict.get("action", "")
    label_raw   = action_dict.get("label") or ""
    value_raw   = action_dict.get("value") or ""
    element_id  = action_dict.get("id") or ""
    xpath       = action_dict.get("xpath") or ""

    label = label_raw.strip()
    value = value_raw.strip()
    display_label = (
        label or
        element_id.replace("-", " ").replace("_", " ").title() or
        xpath.split("/")[-1].split("[")[0] or
        "element"
    )

    if action_type == "navigate":       return f'Navigate to "{action_dict.get("url", display_label)}"'
    if action_type == "switch":         return f'Switch to window "{action_dict.get("windowId", "")}" | URL: {action_dict.get("url", "")}'
    if action_type == "click":
        tag = (action_dict.get("tag") or xpath.split("/")[-1].split("[")[0] or "").lower()
        if tag == "button" or "btn" in element_id.lower(): return f'Click the "{display_label}" button'
        if tag == "a":                                      return f'Click the "{display_label}" link'
        return f'Click on "{display_label}"'
    if action_type == "right_click":    return f'Right-click on "{display_label}"'
    if action_type == "input":          return f'Enter "{value}" in the "{display_label}" field'
    if action_type == "input_others":   return f'Set "{display_label}" to "{value}"'
    if action_type == "change":         return f'Change "{display_label}" to "{value}"' if value else f'Change value in "{display_label}"'
    if action_type == "select":         return f'Select "{value}" from the "{display_label}" dropdown'
    if action_type == "checkbox":       return f'{value.capitalize()} the "{display_label}" checkbox'
    if action_type == "radio":          return f'Select radio option "{value}" in "{display_label}"'
    if action_type == "file_upload":    return f'Upload file(s) "{value}" via "{display_label}"'
    if action_type == "key_enter":      return f'Press Enter on "{display_label}"'
    if action_type == "key_escape":     return 'Press Escape'
    if action_type == "key_tab":        return f'Press {value or "Tab"}'
    if action_type == "function_key":   return f'Press {value}'
    if action_type == "shortcut_copy":  return f'Copy selected text "{value}"'
    if action_type == "shortcut_cut":   return f'Cut selected text "{value}"'
    if action_type == "shortcut_paste": return f'Paste "{value}"'
    if action_type == "shortcut_undo":  return 'Undo (Ctrl+Z)'
    if action_type == "shortcut_redo":  return 'Redo (Ctrl+Y)'
    if action_type == "shortcut_save":  return 'Save (Ctrl+S)'
    if action_type == "shortcut_select_all": return 'Select All (Ctrl+A)'
    if action_type == "copy":           return f'Copy text "{value}"'
    if action_type == "cut":            return f'Cut text "{value}"'
    if action_type == "paste":          return f'Paste "{value}" into "{display_label}"'
    if action_type == "scroll":         return f'Scroll page ({value})'
    if action_type == "hover":          return f'Hover over "{display_label}"'
    if action_type == "hover_end":      return f'Mouse leave "{display_label}"'
    if action_type == "drag_start":     return f'Start dragging "{display_label}"'
    if action_type == "drop":           return f'Drop -> {value}'
    if action_type:                     return f'{action_type.replace("_", " ").capitalize()} on "{display_label}"'
    return f'Perform action on "{display_label}"'


# ─── Workflow generators ───────────────────────────────────────────────────────
def generate_workflow_manual(actions: list) -> list:
    lines = []
    current_url    = None
    current_window = None

    for action in actions:
        url       = action.get("url", "")
        window_id = action.get("windowId", "")
        ts        = action.get("timestamp", "")
        step      = action.get("step", "?")

        if url != current_url or window_id != current_window:
            lines.append("")
            lines.append(f"## Window: {window_id} | URL: {url}")
            lines.append("")
            current_url    = url
            current_window = window_id

        time_str = ""
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            time_str = dt.strftime("%H:%M:%S")
        except Exception:
            pass

        lines.append(f"Step {step} [{time_str}]: {humanize_action(action)}")

    return lines


def generate_workflow(actions: list) -> str:
    print("─── Raw actions sent to AI ───")
    print(actions)
    print("─────────────────────────────")

    humanized_text = "\n".join(
        f"{i+1}. {humanize_action(a)}" for i, a in enumerate(actions)
    )

    api_key  = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    os.environ["AZURE_OPENAI_API_KEY"]  = api_key
    os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint

    model = AzureChatOpenAI(
        openai_api_version="2023-05-15",
        azure_deployment="qepracticekey",
    )

    prompt = f"""
You are an expert test automation assistant.
Convert the pre-processed recorded actions below into a clean, deduplicated,
human-readable workflow ready for test case and Gherkin feature file creation.

Pre-processed Actions:
{humanized_text}

Transformation Rules:
1. Deduplication — remove repeated actions on the same element; keep only the final meaningful step.
2. Noise Filtering — remove empty clicks, redundant "Change" lines already captured as "Enter/Select".
3. Action Normalization — merge Click + Change into a single meaningful step where appropriate.
4. Window Management — start with "User opened page: [URL]"; note window switches.
5. Output Format — numbered steps, consistent phrasing:
   - Click     -> Click the "LABEL" button / link
   - Input     -> Enter "VALUE" in "LABEL" field
   - Select    -> Select "VALUE" from "LABEL" dropdown
   - Checkbox  -> Check / Uncheck the "LABEL" checkbox
   - Keyboard  -> Press Enter / Escape / Tab
   - Drag/Drop -> Drag "SOURCE" and drop onto "TARGET"
   - Scroll    -> Scroll the page (direction/position)
   - Hover     -> Hover over "LABEL"
   - Copy/Paste -> Copy "TEXT" / Paste "TEXT" into "LABEL"

Output: A perfectly cleaned, numbered workflow. No explanations - steps only.
"""

    response = model.invoke([HumanMessage(content=prompt)])
    print(response)
    return response.content


# ─── Utilities ────────────────────────────────────────────────────────────────
def wait_for_url_change(driver, initial_url: str, timeout: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if driver.current_url != initial_url:
            return True
        time.sleep(1)
    return False


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def take_screenshot(driver, folder: str) -> str:
    """Timestamped screenshot — never overwrites previous captures."""
    os.makedirs(folder, exist_ok=True)
    parsed    = urlparse(driver.current_url)
    page_name = sanitize_filename(parsed.path.strip("/")) or "home"
    timestamp = datetime.now().strftime("%H%M%S_%f")[:9]
    file_path = os.path.join(folder, f"{page_name}_{timestamp}.png")
    driver.save_screenshot(file_path)
    return file_path