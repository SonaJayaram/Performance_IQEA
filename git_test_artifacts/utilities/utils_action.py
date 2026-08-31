# utils_action.py
import time
import re
import os
import json
import openai
from collections import defaultdict
from urllib.parse import urlparse
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
load_dotenv()

JS_action_listeners_agentflow= """(function (statusKey) {
    if (window.__intentRecorderInjected) return;
    window.__intentRecorderInjected = true;

    const ACTIONS_KEY = "recordedActions";
    const INPUT_DEBOUNCE_MS = 400;
    const CLICK_DEDUP_MS = 300;

    const elementState = new Map();
    const lastClickMap = new Map();

    // ---------------- SAFETY FILTERS ----------------
    function shouldRecord() {
        const p = location.pathname.toLowerCase();
        return !p.includes("login") &&
               !p.includes("auth") &&
               !p.includes("signin") &&
               !p.includes("microsoft") &&
               !p.includes("google");
    }
    function findToggleInput(el) {
        if (!el) return null;

        // If clicked element IS input
        if (el.tagName === "INPUT" && (el.type === "checkbox" || el.type === "radio")) {
            return el;
        }

        // Search inside
        const inside = el.querySelector?.("input[type='checkbox'],input[type='radio']");
        if (inside) return inside;

        // Search nearby
        const parent = el.closest("label,div");
        if (parent) {
            return parent.querySelector("input[type='checkbox'],input[type='radio']");
        }

        return null;
    }

    function isHugeText(el) {
        return el && el.innerText && el.innerText.length > 150;
    }
    function isToggleLike(el) {
        if (!el) return false;
        return (
            el.type === "checkbox" ||
            el.type === "radio" ||
            el.getAttribute("role") === "switch" ||
            el.getAttribute("aria-checked") !== null ||
            el.closest("[role='switch'],[role='checkbox']")
        );
    }    
    function isToggleWrapper(el) {
        return el && el.closest &&
               el.closest("[role='switch'],[role='checkbox'],.MuiSwitch-root,.ant-switch,.react-switch");
    }
    function flushPendingInputs() {
        if (!window.__pendingInputs) return;

        Object.values(window.__pendingInputs).forEach(state => {
            if (state.value && state.value.trim() !== "") {
                saveAction({
                    action: "enter_text",
                    label: state.label || "[unlabeled]",
                    value: state.value,
                    xpath: state.xpath,
                    url: location.href,
                    windowId: window.name || statusKey,
                    timestamp: new Date().toISOString(),
                    forced: true
                });
            }
        });

        window.__pendingInputs = {};
    }
    function isReactOption(el) {
        return el &&
            (el.getAttribute("role") === "option" ||
             el.getAttribute("aria-selected") !== null ||
             el.closest("[role='listbox']"));
    }
    function getXPath(el) {
        const getPos = e => {
            let pos = 1;
            while (e.previousElementSibling) { e = e.previousElementSibling; pos++; }
            return pos;
        };
        const parts = [];
        while (el && el.nodeType === Node.ELEMENT_NODE) {
            parts.unshift(`${el.tagName.toLowerCase()}[${getPos(el)}]`);
            el = el.parentNode;
        }
        return "/" + parts.join("/");
    }

    // ---------------- LABEL FIX ----------------
    function getLabel(el) {
        let e = el;
        for (let i = 0; i < 3 && e; i++) {
            const tag = e.tagName?.toLowerCase();
            let label =
                e.getAttribute("aria-label") ||
                e.name ||
                e.id ||
                e.placeholder;

            if (!label && (tag === "button" || tag === "a")) {
                label = e.innerText && e.innerText.trim().slice(0, 60);
            }

            if (label) return label.trim();
            e = e.parentElement;
        }
        return "[unlabeled]";
    }

    function loadActions() {
        return JSON.parse(localStorage.getItem(ACTIONS_KEY) || "[]");
    }

    function saveAction(action) {
        const actions = loadActions();
        actions.push(action);
        localStorage.setItem(ACTIONS_KEY, JSON.stringify(actions));
        window.dispatchEvent(new CustomEvent("__action_recorded", { detail: action }));
    }
    // ---------------- INPUT COMMIT (BLUR) ----------------
    document.addEventListener("focusout", e => {
        const el = e.target;
        if (!el || !["INPUT", "TEXTAREA"].includes(el.tagName)) return;

        const xpath = getXPath(el);
        if (!window.__pendingInputs || !window.__pendingInputs[xpath]) return;

        const state = window.__pendingInputs[xpath];
        if (!state.value || state.value.trim() === "") return;

        saveAction({
            action: "enter_text",
            label: state.label || getLabel(el),
            value: state.value,
            xpath: state.xpath,
            url: location.href,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString()
        });

        delete window.__pendingInputs[xpath];
    }, true);

    // ---------------- CLICK (INTENT) ----------------
    document.addEventListener("click", e => {
        if (!shouldRecord()) return;

        const el = e.target.closest("a,button,input,textarea,select,[role='option'],[role='listbox']");


        if (!el) return;

        //if (isToggleLike(el) || isToggleWrapper(el)) return; // 🔥 NEW
        const toggleInput = findToggleInput(el);
        if (toggleInput) {
            const checked = !toggleInput.checked; // predict next state

            saveAction({
                action: checked ? "check" : "uncheck",
                label: getLabel(toggleInput),
                value: checked,
                xpath: getXPath(toggleInput),
                url: location.href,
                windowId: window.name || statusKey,
                timestamp: new Date().toISOString()
            });
            return; // ⛔ stop click chain
        }

        if (["script", "style"].includes(el.tagName?.toLowerCase())) return;
        if (isHugeText(el)) return;

        const xpath = getXPath(el);
        const now = Date.now();
        const lastClickTime = lastClickMap.get(xpath) || 0;

        if (now - lastClickTime < CLICK_DEDUP_MS) return;
        lastClickMap.set(xpath, now);

        if (isReactOption(el)) {
            saveAction({
                action: "select",
                label: getLabel(el),
                value: el.innerText?.trim(),
                xpath,
                url: location.href,
                windowId: window.name || statusKey,
                timestamp: new Date().toISOString()
            });
            return;
        }

        saveAction({
            action: "click",
            label: getLabel(el),
            xpath,
            url: location.href,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString()
        });
    }, true);


    // --- Wrap all listeners in try/catch to prevent exceptions ---
    document.addEventListener("input", e => {
        try {
            if (isReactOption(e.target) || isToggleLike(e.target) || isToggleWrapper(e.target)) return;

            const el = e.target;
            if (!el || !["INPUT", "TEXTAREA"].includes(el.tagName)) return;

            const xpath = getXPath(el);
            if (!window.__pendingInputs) window.__pendingInputs = {};

            window.__pendingInputs[xpath] = {
                value: el.value,
                label: getLabel(el),
                xpath,
                time: Date.now()
            };
        } catch (err) {
            console.warn("Input listener error:", err);
        }
    }, true);


    document.addEventListener("change", e => {
        try {s
            if (isReactOption(e.target)) return;
            if (isToggleLike(e.target) || isToggleWrapper(e.target)) return;

            const wrappedToggle = findToggleInput(e.target);
            if (wrappedToggle && e.target !== wrappedToggle) return;

            const el = e.target;
            if (!el) return;

            const tag = el.tagName.toLowerCase();

            if (tag === "select") {
                saveAction({
                    action: "select",
                    label: getLabel(el),
                    value: el.value,
                    xpath: getXPath(el),
                    url: location.href,
                    windowId: window.name || statusKey,
                    timestamp: new Date().toISOString()
                });
                return;
            }

            if (el.type === "radio") {
                saveAction({
                    action: "select_radio",
                    label: getLabel(el),
                    value: el.value,
                    xpath: getXPath(el),
                    url: location.href,
                    windowId: window.name || statusKey,
                    timestamp: new Date().toISOString()
                });
                return;
            }

            if (el.type === "checkbox") {
                saveAction({
                    action: el.checked ? "check" : "uncheck",
                    label: getLabel(el),
                    xpath: getXPath(el),
                    value: el.checked,
                    url: location.href,
                    windowId: window.name || statusKey,
                    timestamp: new Date().toISOString()
                });
            }
        } catch (err) {
            console.warn("Change listener error:", err);
        }
    }, true);


    // ---------------- SAFE FLUSH (NO beforeunload) ----------------
    window.addEventListener("popstate", flushPendingInputs);
    window.addEventListener("hashchange", flushPendingInputs);

    // ---------------- NAVIGATION ----------------
    let lastUrl = location.href;
    setInterval(() => {
        if (location.href !== lastUrl && shouldRecord()) {
            lastUrl = location.href;
            saveAction({
                action: "navigate",
                label: document.title || "page",
                url: lastUrl,
                windowId: window.name || statusKey,
                timestamp: new Date().toISOString()
            });
        }
    }, 500);
    if (location.hostname.includes("microsoft") || location.hostname.includes("google")) {
    window.addEventListener("beforeunload", () => {
        try {
            localStorage.setItem("__oauth_closed", Date.now());
        } catch (e) {}
    });
}
    console.log("✅ Intent-level action recorder enabled (SAFE MODE):", statusKey);
})(STATUS_KEY_PLACEHOLDER);
"""
JS_action_listeners_march11 = """(function (statusKey) {
    if (window.__intentRecorderInjected) return;
    window.__intentRecorderInjected = true;

    const ACTIONS_KEY = "recordedActions";
    const INPUT_DEBOUNCE_MS = 400;
    const CLICK_DEDUP_MS = 300;

    const elementState = new Map();
    const lastClickMap = new Map();

    // ---------------- SAFETY FILTERS ----------------
    function shouldRecord() {
        const p = location.pathname.toLowerCase();
        return !p.includes("login") &&
               !p.includes("auth") &&
               !p.includes("signin") &&
               !p.includes("microsoft") &&
               !p.includes("google");
    }

    function isHugeText(el) {
        return el && el.innerText && el.innerText.length > 150;
    }

    function flushPendingInputs() {
        if (!window.__pendingInputs) return;

        Object.values(window.__pendingInputs).forEach(state => {
            if (state.value && state.value.trim() !== "") {
                saveAction({
                    action: "enter_text",
                    label: state.label || "[unlabeled]",
                    value: state.value,
                    xpath: state.xpath,
                    url: location.href,
                    windowId: window.name || statusKey,
                    timestamp: new Date().toISOString(),
                    forced: true
                });
            }
        });

        window.__pendingInputs = {};
    }
    function isReactOption(el) {
        return el &&
            (el.getAttribute("role") === "option" ||
             el.getAttribute("aria-selected") !== null ||
             el.closest("[role='listbox']"));
    }
    function getXPath(el) {
        const getPos = e => {
            let pos = 1;
            while (e.previousElementSibling) { e = e.previousElementSibling; pos++; }
            return pos;
        };
        const parts = [];
        while (el && el.nodeType === Node.ELEMENT_NODE) {
            parts.unshift(`${el.tagName.toLowerCase()}[${getPos(el)}]`);
            el = el.parentNode;
        }
        return "/" + parts.join("/");
    }

    // ---------------- LABEL FIX ----------------
    function getLabel(el) {
        let e = el;
        for (let i = 0; i < 3 && e; i++) {
            const tag = e.tagName?.toLowerCase();
            let label =
                e.getAttribute("aria-label") ||
                e.name ||
                e.id ||
                e.placeholder;

            if (!label && (tag === "button" || tag === "a")) {
                label = e.innerText && e.innerText.trim().slice(0, 60);
            }

            if (label) return label.trim();
            e = e.parentElement;
        }
        return "[unlabeled]";
    }

    function loadActions() {
        return JSON.parse(localStorage.getItem(ACTIONS_KEY) || "[]");
    }

    function saveAction(action) {
        const actions = loadActions();
        actions.push(action);
        localStorage.setItem(ACTIONS_KEY, JSON.stringify(actions));
        window.dispatchEvent(new CustomEvent("__action_recorded", { detail: action }));
    }
    // ---------------- INPUT COMMIT (BLUR) ----------------
    document.addEventListener("focusout", e => {
        const el = e.target;
        if (!el || !["INPUT", "TEXTAREA"].includes(el.tagName)) return;

        const xpath = getXPath(el);
        if (!window.__pendingInputs || !window.__pendingInputs[xpath]) return;

        const state = window.__pendingInputs[xpath];
        if (!state.value || state.value.trim() === "") return;

        saveAction({
            action: "enter_text",
            label: state.label || getLabel(el),
            value: state.value,
            xpath: state.xpath,
            url: location.href,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString()
        });

        delete window.__pendingInputs[xpath];
    }, true);

    // ---------------- CLICK (INTENT) ----------------
    document.addEventListener("click", e => {
        if (!shouldRecord()) return;

        const el = e.target.closest("a,button,input,textarea,select,[role='option'],[role='listbox']");

        if (!el || ["script", "style"].includes(el.tagName?.toLowerCase())) return;
        if (isHugeText(el)) return;

        const xpath = getXPath(el);
        const now = Date.now();
        const lastClickTime = lastClickMap.get(xpath) || 0;

        if (now - lastClickTime < CLICK_DEDUP_MS) return;
        lastClickMap.set(xpath, now);
        // React dropdown option → record only as select
        if (isReactOption(el)) {
            saveAction({
                action: "select",
                label: getLabel(el),
                value: el.innerText?.trim(),
                xpath: getXPath(el),
                url: location.href,
                windowId: window.name || statusKey,
                timestamp: new Date().toISOString()
            });
            return; // ⛔ block click/check/input chain
        }
        saveAction({
            action: "click",
            label: getLabel(el),
            xpath,
            url: location.href,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString()
        });
    }, true);

    // --- Wrap all listeners in try/catch to prevent exceptions ---
    document.addEventListener("input", e => {
        try {
            if (isReactOption(e.target)) return; // skip React virtual options

            const el = e.target;
            if (!el || !["INPUT", "TEXTAREA"].includes(el.tagName)) return;

            const xpath = getXPath(el);
            if (!window.__pendingInputs) window.__pendingInputs = {};

            window.__pendingInputs[xpath] = {
                value: el.value,          // actual typed value
                label: getLabel(el),
                xpath,
                time: Date.now()
            };
        } catch (err) {
            console.warn("Input listener error:", err);
        }
    }, true);

    document.addEventListener("change", e => {
        try {
            if (isReactOption(e.target)) return; // skip React virtual options

            const el = e.target;
            if (!el) return;

            const tag = el.tagName.toLowerCase();

            if (tag === "select") {
                saveAction({
                    action: "select",
                    label: getLabel(el),
                    value: el.value,
                    xpath: getXPath(el),
                    url: location.href,
                    windowId: window.name || statusKey,
                    timestamp: new Date().toISOString()
                });
                return;
            }

            if (el.type === "radio") {
                saveAction({
                    action: "select_radio",
                    label: getLabel(el),
                    value: el.value,
                    xpath: getXPath(el),
                    url: location.href,
                    windowId: window.name || statusKey,
                    timestamp: new Date().toISOString()
                });
                return;
            }

            if (el.type === "checkbox") {
                saveAction({
                    action: el.checked ? "check" : "uncheck",
                    label: getLabel(el),
                    xpath: getXPath(el),
                    value: el.checked,
                    url: location.href,
                    windowId: window.name || statusKey,
                    timestamp: new Date().toISOString()
                });
            }
        } catch (err) {
            console.warn("Change listener error:", err);
        }
    }, true);

    // ---------------- SAFE FLUSH (NO beforeunload) ----------------
    window.addEventListener("popstate", flushPendingInputs);
    window.addEventListener("hashchange", flushPendingInputs);

    // ---------------- NAVIGATION ----------------
    let lastUrl = location.href;
    setInterval(() => {
        if (location.href !== lastUrl && shouldRecord()) {
            lastUrl = location.href;
            saveAction({
                action: "navigate",
                label: document.title || "page",
                url: lastUrl,
                windowId: window.name || statusKey,
                timestamp: new Date().toISOString()
            });
        }
    }, 500);
    if (location.hostname.includes("microsoft") || location.hostname.includes("google")) {
    window.addEventListener("beforeunload", () => {
        try {
            localStorage.setItem("__oauth_closed", Date.now());
        } catch (e) {}
    });
}
    console.log("✅ Intent-level action recorder enabled (SAFE MODE):", statusKey);
})(STATUS_KEY_PLACEHOLDER);
"""
JS_action_listeners_jan_21="""(function (statusKey) {
    if (window.__intentRecorderInjected) return;
    window.__intentRecorderInjected = true;

    const ACTIONS_KEY = "recordedActions";
    const INPUT_DEBOUNCE_MS = 400;
    const CLICK_DEDUP_MS = 300;

    const elementState = new Map();
    const lastClickMap = new Map();
    
    function getXPath(el) {
        const getPos = e => {
            let pos = 1;
            while (e.previousElementSibling) { e = e.previousElementSibling; pos++; }
            return pos;
        };
        const parts = [];
        while (el && el.nodeType === Node.ELEMENT_NODE) {
            parts.unshift(`${el.tagName.toLowerCase()}[${getPos(el)}]`);
            el = el.parentNode;
        }
        return "/" + parts.join("/");
    }
   
    function getLabel(el) {
    let e = el;
    for (let i = 0; i < 3 && e; i++) {
        const label =
            e.getAttribute("aria-label") ||
            e.name ||
            e.id ||
            e.placeholder ||
            (e.innerText && e.innerText.trim());
        if (label) return label.trim();
        e = e.parentElement;
        }
    return "[unlabeled]";
    }

    function loadActions() {
        return JSON.parse(localStorage.getItem(ACTIONS_KEY) || "[]");
    }

    function saveAction(action) {
        const actions = loadActions();
        actions.push(action);
        localStorage.setItem(ACTIONS_KEY, JSON.stringify(actions));
        window.dispatchEvent(new CustomEvent("__action_recorded", { detail: action }));
    }

    // ---------------- CLICK (INTENT) ----------------
    document.addEventListener("click", e => {
        const el = e.target;
        if (!el || ["script", "style"].includes(el.tagName?.toLowerCase())) return;

        const xpath = getXPath(el);
        const now = Date.now();
        const lastClickTime = lastClickMap.get(xpath) || 0;

        if (now - lastClickTime < CLICK_DEDUP_MS) return;
        lastClickMap.set(xpath, now);

        saveAction({
            action: "click",
            label: getLabel(el),
            xpath,
            url: location.href,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString()
        });
    }, true);

    // ---------------- INPUT TRACKING ----------------
    document.addEventListener("input", e => {
        const el = e.target;
        if (!el || !["INPUT", "TEXTAREA"].includes(el.tagName)) return;

        const xpath = getXPath(el);
        const state = elementState.get(xpath) || {};
        state.lastValue = el.value;
        state.lastInputTime = Date.now();
        elementState.set(xpath, state);
    }, true);

    // ---------------- INPUT COMMIT (BLUR) ----------------
    document.addEventListener("focusout", e => {
        const el = e.target;
        if (!el || !["INPUT", "TEXTAREA"].includes(el.tagName)) return;

        const xpath = getXPath(el);
        const state = elementState.get(xpath);
        if (!state) return;

        const stable =
            Date.now() - state.lastInputTime >= INPUT_DEBOUNCE_MS &&
            state.lastValue &&
            state.lastValue.trim() !== "";

        if (!stable) return;

        saveAction({
            action: "enter_text",
            label: getLabel(el),
            value: state.lastValue,
            xpath,
            url: location.href,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString()
        });

        elementState.delete(xpath);
    }, true);

    // ---------------- CHECKBOX / RADIO ----------------
    document.addEventListener("change", e => {
        const el = e.target;
        if (!el || el.type !== "checkbox") return;

        saveAction({
            action: el.checked ? "check" : "uncheck",
            label: getLabel(el),
            xpath: getXPath(el),
            value: el.checked,
            url: location.href,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString()
        });
    }, true);

    // ---------------- NAVIGATION ----------------
    let lastUrl = location.href;
    setInterval(() => {
        if (location.href !== lastUrl) {
            lastUrl = location.href;
            saveAction({
            action: "navigate",
            label: document.title || "page",
            url: lastUrl,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString()
            });
        }
    }, 500);

    console.log("✅ Intent-level action recorder enabled:", statusKey);
})(STATUS_KEY_PLACEHOLDER);
"""
JS_action_listeners = """/**
 * IQEA Enhanced Action Listener v2.0 (fixed: no duplicates, no hover noise)
 */
(function (statusKey) {

    // ─── Guard: SPA-safe reinject (URL-bound) ─────────────────────────────────
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

    // BroadcastChannel for cross-tab relay
    try {
        if (!window.__iqeaChannel) {
            window.__iqeaChannel = new BroadcastChannel("__iqea_channel");
            window.__iqeaChannel.onmessage = (e) => {
                if (e.data && e.data.__relay && e.data.payload) saveAction(e.data.payload);
            };
        }
    } catch (_) {}

    // Cross-window postMessage relay
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

    // ─── Smart XPath builder ───────────────────────────────────────────────────
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

        // ── Element metadata for accurate script generation ──────────────────
        const tag       = (target.tagName || "").toLowerCase();
        const elId      = target.id || "";
        const elName    = target.getAttribute("name") || target.name || "";
        const elType    = target.getAttribute("type") || target.type || "";
        const elHref    = tag === "a" ? (target.getAttribute("href") || target.href || "") : "";
        const dataTest  = target.getAttribute("data-testid") ||
                          target.getAttribute("data-test")   ||
                          target.getAttribute("data-qa")     ||
                          target.getAttribute("data-cy")     || "";
        const ariaLabel = target.getAttribute("aria-label") || "";
        const cssClasses = (typeof target.className === "string")
            ? target.className.split(/\s+/).filter(c => c && !c.match(/^\d/)).join(" ")
            : "";
        // isNavLink: true only for real page-navigation anchors (not same-page hash, not JS)
        const isNavLink = tag === "a" &&
            elHref &&
            !elHref.startsWith("javascript") &&
            !elHref.startsWith("#")          &&
            !elHref.startsWith("mailto");

        const actionObj = {
            step:       nextStepNumber(),
            action:     type,
            xpath,
            label:      label?.trim(),
            value:      String(value).trim(),
            url:        window.location.href,
            // ── new metadata fields ──────────────────────────────────────────
            tagName:    tag,
            elementId:  elId,
            elementName: elName,
            elementType: elType,
            href:       elHref,
            dataTestId: dataTest,
            ariaLabel:  ariaLabel,
            cssClasses: cssClasses,
            isNavLink:  isNavLink,
            // ────────────────────────────────────────────────────────────────
            windowId:   window.name || statusKey,
            timestamp:  new Date().toISOString(),
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

    // ─── Attach listeners — FIX: use AbortController per root ─────────────────
    // OLD approach: root.__iqea_attached = true flag — but this flag was being
    // reset to false by injection_script_updated_fixed() before the old script
    // tag was removed, so the old listeners were still alive AND new ones were
    // added → every event fired twice.
    //
    // NEW approach: each root gets an AbortController. On reinject, the old
    // controller is aborted (removes all its listeners cleanly), then a new
    // controller is created. This guarantees exactly ONE set of listeners
    // per root at all times, regardless of how many reinjections happen.
    function attachListeners(root) {
        // Abort and replace any existing listeners on this root
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

        // Scroll — passive listeners also support AbortController signal
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

        // ── HOVER DISABLED ─────────────────────────────────────────────────────
        // Hover events (mouseenter/mouseleave) are intentionally NOT recorded.
        // They generate extreme noise (every button mouseover = 2 entries) and
        // are not useful for test case generation or script replay.
        // To re-enable, uncomment the block below.
        //
        // doc.addEventListener("mouseenter", e => {
        //     const tag = e.target.tagName?.toLowerCase();
        //     if (["button","a","select"].includes(tag) || ...)
        //         recordAction("hover", e.target);
        // }, opts);
        // doc.addEventListener("mouseleave", e => {
        //     const tag = e.target.tagName?.toLowerCase();
        //     if (["button","a"].includes(tag)) recordAction("hover_end", e.target);
        // }, opts);

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

    if (!window.__iqea_shadow_observer) {
        window.__iqea_shadow_observer = new MutationObserver(mutations => {
            mutations.forEach(m => m.addedNodes.forEach(n => {
                if (n.nodeType === Node.ELEMENT_NODE) injectIntoShadowRoots(n);
            }));
        });
        window.__iqea_shadow_observer.observe(document.documentElement,
            { childList: true, subtree: true });
    }

    // ─── iFrame support ───────────────────────────────────────────────────────
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

})(window.__iqea_windowId);"""

# ─────────────────────────────────────────────────────────────────────────────
# AgentFlow (React Flow / xyflow) dedicated listener  — IQEA v3.0
# Built on the v2.0 architecture (smart-xpath, cross-window relay, SPA history
# patch) PLUS React-Flow-specific capture:
#   • node-aware labels           -> "<node title> (<CATEGORY>)"
#   • palette drag (HTML5 DnD)    -> add_node with the dragged node type
#   • Slate.js prompt editor      -> serialized text with {{smart-chips}}
#   • MUI Select / react-select   -> select_option with the chosen option text
#   • flow graph snapshot         -> nodes + edges captured on Save/Test/Deploy
# Login is handled by a pre-authenticated Chrome profile, so OAuth origins are
# simply skipped here (belt-and-braces).
# ─────────────────────────────────────────────────────────────────────────────
JS_action_listeners_agentflow_v2 = """(function (statusKey) {

    const _currentUrl = window.location.href;
    if (window.__iqeaAF_url === _currentUrl) return;
    window.__iqeaAF_url = _currentUrl;

    // ─── Skip cross-origin OAuth pages (pre-auth profile handles login) ───────
    function onAuthPage() {
        const h = location.hostname.toLowerCase();
        const p = location.pathname.toLowerCase();
        return h.includes("google") || h.includes("microsoft") ||
               h.includes("login.microsoftonline") || h.includes("accounts.") ||
               p.includes("/signin") || p.includes("/auth");
    }

    function nextStepNumber() {
        const n = parseInt(localStorage.getItem("__iqea_step") || "0") + 1;
        localStorage.setItem("__iqea_step", String(n));
        return n;
    }

    // ─── Persistence + cross-window relay (same as v2.0) ──────────────────────
    if (!window.__recordedActions) {
        window.__recordedActions = JSON.parse(localStorage.getItem("recordedActions") || "[]");
    }
    function saveAction(action) {
        const existing = JSON.parse(localStorage.getItem("recordedActions") || "[]");
        const last = existing.length > 0 ? existing[existing.length - 1] : null;
        // de-dupe identical rapid-fire events (but never drop snapshots/drops)
        if (last && !["flow_snapshot","add_node"].includes(action.action) &&
            last.action === action.action &&
            last.label === action.label &&
            last.url === action.url &&
            (!action.value || action.value === last.value) &&
            (new Date(action.timestamp) - new Date(last.timestamp)) < 500) {
            return;
        }
        existing.push(action);
        localStorage.setItem("recordedActions", JSON.stringify(existing));
        window.__recordedActions.push(action);
        try {
            window.dispatchEvent(new CustomEvent("__action_recorded", { detail: action }));
            if (window.opener && window.opener !== window)
                window.opener.postMessage({ __relay: true, payload: action }, "*");
            if (window.__iqeaChannel)
                window.__iqeaChannel.postMessage({ __relay: true, payload: action });
        } catch (err) { console.warn("Relay failed:", err); }
    }
    try {
        if (!window.__iqeaChannel) {
            window.__iqeaChannel = new BroadcastChannel("__iqea_channel");
            window.__iqeaChannel.onmessage = (e) => {
                if (e.data && e.data.__relay && e.data.payload) saveAction(e.data.payload);
            };
        }
    } catch (_) {}
    if (!window.__iqeaAF_msg) {
        window.__iqeaAF_msg = true;
        window.addEventListener("message", function (event) {
            if (event.data && event.data.__relay && event.data.payload) {
                saveAction(event.data.payload);
                if (window.opener && window.opener !== window)
                    window.opener.postMessage(event.data, "*");
            }
        });
    }

    // ─── Small helpers ─────────────────────────────────────────────────────────
    // Collapse whitespace/newlines and cap length so a container's innerText can
    // never become a giant multi-line label.
    function clean(s, max) {
        s = (s || "").replace(/[\\u200B\\uFEFF]/g, "").replace(/\\s+/g, " ").trim();
        max = max || 60;
        return s.length > max ? s.slice(0, max) : s;
    }
    // react-select / MUI-Select carry hidden <input>s that fire change/blur with
    // the option value — we already capture the visible option click, so ignore.
    function isWidgetInternalInput(el) {
        if (!el || !el.closest) return false;
        return el.classList?.contains("select__input") ||
               el.classList?.contains("MuiSelect-nativeInput") ||
               !!el.closest(".select__control") ||
               !!el.closest(".MuiSelect-root") ||
               el.getAttribute("aria-hidden") === "true";
    }
    // Elements worth recording a click on. Anything else (empty div/span, bare
    // svg icon, canvas background) is skipped.
    const CLICK_SEL = "a,button,[role='button'],[role='option'],[role='menuitem']," +
        "[role='tab'],[role='switch'],[role='checkbox'],[role='combobox'],[role='textbox']," +
        "input,select,textarea,label,summary," +
        ".react-flow__node[data-id],.react-flow__handle,[draggable='true']," +
        ".MuiButtonBase-root,.select__option,li[role='option']";

    // ─── React-Flow helpers ───────────────────────────────────────────────────
    function flowNode(el) {
        return el && el.closest ? el.closest(".react-flow__node[data-id]") : null;
    }
    function nodeInfo(node) {
        if (!node) return null;
        const title = (node.querySelector(".font-semibold")?.innerText || "").trim();
        const cat   = (node.querySelector(".text-gray-500")?.innerText || "").trim();
        const pos   = (node.getAttribute("style")?.match(/translate\\(([^)]+)\\)/) || [])[1] || "";
        const kind  = (node.className || "").includes("node-core_node") ? "core" : "custom";
        return {
            id: node.getAttribute("data-id"),
            title: title, category: cat, pos: pos, kind: kind
        };
    }

    // ─── Slate.js prompt serializer (keeps {{smart-chips}}) ───────────────────
    function serializeSlate(editor) {
        let out = "";
        (function walk(n) {
            n.childNodes.forEach(ch => {
                if (ch.nodeType === Node.TEXT_NODE) { out += ch.nodeValue; return; }
                if (ch.nodeType !== Node.ELEMENT_NODE) return;
                if (ch.getAttribute && ch.getAttribute("data-cy") === "smart-chip") {
                    const name = (ch.textContent || "").replace(/[\\u200B\\uFEFF\\u00A0]/g, "").trim();
                    if (name) out += " {{" + name + "}} ";
                    return;
                }
                if (ch.getAttribute && ch.getAttribute("data-slate-spacer") !== null) return;
                walk(ch);
            });
        })(editor);
        return out.replace(/[\\u200B\\uFEFF]/g, "").replace(/\\u00A0/g, " ")
                  .replace(/[ \\t]+/g, " ").trim();
    }

    // ─── Smart XPath (id / testid / data-id / aria / name -> positional) ──────
    function getSmartXPath(el) {
        if (!el || el.nodeType !== Node.ELEMENT_NODE) return "";
        const node = flowNode(el);
        if (node) {
            const tid = node.getAttribute("data-testid");
            if (tid) return '//div[@data-testid="' + tid + '"]';
        }
        if (el.id && !/^[0-9]/.test(el.id) && el.id !== "submit-btn")
            return '//*[@id="' + el.id + '"]';
        for (const a of ["data-testid","data-cy","data-id","data-handleid"]) {
            const v = el.getAttribute(a);
            if (v) return '//' + el.tagName.toLowerCase() + '[@' + a + '="' + v + '"]';
        }
        const it = ["input","button","select","textarea","a"];
        if (it.includes(el.tagName.toLowerCase())) {
            for (const a of ["aria-label","name","placeholder","title"]) {
                const v = el.getAttribute(a);
                if (v) return '//' + el.tagName.toLowerCase() + '[@' + a + '="' + v + '"]';
            }
        }
        const parts = [];
        let cur = el;
        while (cur && cur.nodeType === Node.ELEMENT_NODE) {
            let i = 1, sib = cur.previousElementSibling;
            while (sib) { if (sib.tagName === cur.tagName) i++; sib = sib.previousElementSibling; }
            const t = cur.tagName.toLowerCase();
            parts.unshift(i > 1 ? t + "[" + i + "]" : t);
            cur = cur.parentNode;
        }
        return "/" + parts.join("/");
    }

    // ─── Label extractor (node-aware) ─────────────────────────────────────────
    function getLabel(el) {
        if (!el) return "";
        const node = flowNode(el);
        if (node) {
            const info = nodeInfo(node);
            // prefer the button intent (Edit/Clone) inside the node when present
            const btn = el.closest("button[title]");
            const btnT = btn ? btn.getAttribute("title") : "";
            const base = info.title ? (info.title + " (" + info.category + ")") : "flow-node";
            return btnT ? (btnT + " · " + base) : base;
        }
        return clean(
            el.getAttribute("aria-label") ||
            el.getAttribute("title") ||
            el.getAttribute("data-testid") ||
            el.getAttribute("name") ||
            (el.id && el.id !== "submit-btn" ? el.id : "") ||
            el.getAttribute("placeholder") ||
            el.innerText ||
            el.type || ""
        );
    }

    // ─── Core record ──────────────────────────────────────────────────────────
    function recordAction(type, target, extra = {}) {
        if (onAuthPage()) return;
        if (!target || ["script","style","html","body","head"].includes(
            target.tagName?.toLowerCase())) return;
        const node = flowNode(target);
        const info = node ? nodeInfo(node) : null;
        const actionObj = {
            step: nextStepNumber(),
            action: type,
            xpath: getSmartXPath(target),
            label: (getLabel(target) || "").trim(),
            value: extra.value !== undefined ? String(extra.value).trim()
                   : (["input","change","select"].includes(type)
                        ? (target.value || target.innerText || "") : ""),
            url: window.location.href,
            tagName: (target.tagName || "").toLowerCase(),
            nodeId: info ? info.id : "",
            nodeTitle: info ? info.title : "",
            nodeCategory: info ? info.category : "",
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString(),
            ...extra
        };
        saveAction(actionObj);
        console.log("IQEA-AF:", actionObj);
    }

    // ─── Flow graph snapshot (the real source of truth for the built flow) ────
    function snapshotFlow(trigger) {
        const nodes = [...document.querySelectorAll(".react-flow__node[data-id]")]
            .map(n => nodeInfo(n));
        const edges = [...document.querySelectorAll(".react-flow__edge[data-id]")]
            .map(e => ({ id: e.getAttribute("data-id"),
                         label: e.getAttribute("aria-label") || "" }));
        saveAction({
            step: nextStepNumber(),
            action: "flow_snapshot",
            label: "flow after " + (trigger || "change"),
            value: JSON.stringify({ nodes, edges }),
            url: window.location.href,
            nodeCount: nodes.length,
            edgeCount: edges.length,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString()
        });
        console.log("IQEA-AF snapshot:", nodes.length, "nodes,", edges.length, "edges");
    }

    // ─── Listeners (AbortController = exactly one set per document) ────────────
    let _dragType = null;

    function attachListeners(root) {
        if (root.__iqeaAF_ctl) root.__iqeaAF_ctl.abort();
        const ctl = new AbortController();
        const opts = { signal: ctl.signal, capture: true };
        root.__iqeaAF_ctl = ctl;
        const doc = root.ownerDocument || root;

        // CLICK — record ONLY meaningful intents (never bare wrappers/icons)
        doc.addEventListener("click", e => {
            // 1) dropdown option chosen (MUI menu item or react-select option)
            const opt = e.target.closest(
                "[role='option'],.select__option,.MuiMenuItem-root,li[role='option']");
            if (opt) { recordAction("select_option", opt, { value: clean(opt.innerText) }); return; }

            // 2) resolve to the nearest interactive element; ignore clicks that
            //    land on empty <div>/<span>/<svg> wrappers or the canvas background
            const t = e.target.closest(CLICK_SEL);
            if (!t) return;

            recordAction("click", t);

            // snapshot the flow after meaningful saves
            const btn = t.closest("button");
            const label = clean(btn ? btn.innerText : t.innerText).toLowerCase();
            if (/^(save|deploy|test|publish|continue)$/.test(label)) {
                setTimeout(() => snapshotFlow(label), 700);
            }
        }, opts);

        doc.addEventListener("contextmenu", e => recordAction("right_click", e.target), opts);

        // Non-text form controls only. Text/number <input> and <textarea> are
        // intentionally NOT captured here — they are committed once on blur by
        // the focusout handler below. Recording them in both places produced
        // duplicate "Enter ..." lines (change + focusout fire on the same blur).
        // Skip react-select / MUI-Select hidden inputs (captured as select_option).
        doc.addEventListener("change", e => {
            const el = e.target, tag = el.tagName.toLowerCase();
            if (isWidgetInternalInput(el)) return;
            if      (tag === "select")       recordAction("select",   el, { value: el.options[el.selectedIndex]?.text || el.value });
            else if (el.type === "checkbox") recordAction("checkbox", el, { value: el.checked ? "checked" : "unchecked" });
            else if (el.type === "radio")    recordAction("radio",    el, { value: el.value });
        }, opts);

        // Commit text / Slate prompt on blur
        doc.addEventListener("focusout", e => {
            const el = e.target;
            const slate = el.closest ? el.closest("[data-slate-editor='true']") : null;
            if (slate) {
                const txt = serializeSlate(slate);
                if (txt && txt !== slate.__iqeaLastVal) {
                    slate.__iqeaLastVal = txt;
                    recordAction("enter_prompt", slate, { value: txt });
                }
                return;
            }
            if (isWidgetInternalInput(el)) return;
            const tag = el.tagName ? el.tagName.toLowerCase() : "";
            if (["input","textarea"].includes(tag) && el.value)
                recordAction("enter_text", el, { value: el.value });
        }, opts);

        // Keyboard (Enter/Escape only — enough for this app)
        doc.addEventListener("keydown", e => {
            if (e.key === "Enter")  recordAction("key_enter",  e.target, { value: "Enter" });
            if (e.key === "Escape") recordAction("key_escape", e.target, { value: "Escape" });
        }, opts);

        // ── Palette drag-and-drop (HTML5 DnD) ────────────────────────────────
        // Palette items are MUI buttons [draggable=true]; node type = button text.
        doc.addEventListener("dragstart", e => {
            const btn = e.target.closest ? e.target.closest("[draggable='true']") : null;
            if (!btn) return;
            // ignore drags that originate inside the canvas (moving a node / slate chip)
            if (btn.closest(".react-flow__renderer") || btn.closest("[data-slate-editor]")) {
                _dragType = null; return;
            }
            _dragType = (btn.innerText || "").trim() || getLabel(btn);
        }, opts);

        doc.addEventListener("drop", e => {
            if (!_dragType) return;
            const onCanvas = e.target.closest &&
                (e.target.closest(".react-flow__pane") || e.target.closest(".react-flow__renderer"));
            recordAction("add_node", e.target, {
                value: _dragType,
                dropX: Math.round(e.clientX),
                dropY: Math.round(e.clientY),
                onCanvas: !!onCanvas
            });
            _dragType = null;
            // capture the graph shortly after the node lands
            setTimeout(() => snapshotFlow("add_node"), 700);
        }, opts);

        console.log("IQEA-AF listeners attached:", root);
    }

    // ─── SPA route changes (React Router pushState) ───────────────────────────
    if (!window.__iqeaAF_history) {
        window.__iqeaAF_history = true;
        const wrap = orig => function (...a) {
            const r = orig.apply(this, a);
            window.dispatchEvent(new Event("__iqeaAF_nav"));
            return r;
        };
        history.pushState = wrap(history.pushState);
        history.replaceState = wrap(history.replaceState);
        window.addEventListener("popstate", () => window.dispatchEvent(new Event("__iqeaAF_nav")));
        window.addEventListener("__iqeaAF_nav", () => {
            window.__iqeaAF_url = null;
            setTimeout(() => attachListeners(document), 300);
        });
    }

    function init() {
        if (onAuthPage()) { console.log("IQEA-AF: auth page skipped"); return; }
        attachListeners(document);
        console.log("IQEA-AF v3.0 ready. statusKey:", statusKey);
    }
    if (document.readyState === "complete" || document.readyState === "interactive") init();
    else window.addEventListener("load", init, { once: true });

})(window.__iqea_windowId || window.name);"""

JS_action_listeners_clode_mar17="""/**
 * IQEA Enhanced Action Listener v2.0
 * Supports: click, keyboard, scroll, drag-drop, right-click, copy/paste,
 *           file upload, hover, shadow DOM, iframes, SPA reinject fix,
 *           smart XPath, multi-window relay, step sequencing
 */
(function (statusKey) {

    // ─── Guard: SPA-safe reinject (don't use persistent __listenersInjected) ───
    // Instead of a permanent flag, use a URL-bound flag so SPA route changes re-attach
    const _currentUrl = window.location.href;
    if (window.__iqea_injected_url === _currentUrl) return;
    window.__iqea_injected_url = _currentUrl;

    // ─── Global step counter (shared across windows via localStorage) ──────────
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

        // Skip exact duplicate (same action+label+url+value within 500ms)
        if (last &&
            last.action === action.action &&
            last.label === action.label &&
            last.url === action.url &&
            (!action.value || action.value === last.value) &&
            (new Date(action.timestamp) - new Date(last.timestamp)) < 500) {
            console.log("⏭️ Duplicate action skipped:", action);
            return;
        }

        // Replace a trailing orphan "switch" action with the real action
        if (last && last.action === "switch" && last.windowId === action.windowId) {
            existing.pop();
            window.__recordedActions.pop();
        }

        existing.push(action);
        localStorage.setItem("recordedActions", JSON.stringify(existing));
        window.__recordedActions.push(action);

        try {
            window.dispatchEvent(new CustomEvent("__action_recorded", { detail: action }));
            // Relay to opener (popup → parent)
            if (window.opener && window.opener !== window) {
                window.opener.postMessage({ __relay: true, payload: action }, "*");
            }
            // Relay to all same-origin frames via BroadcastChannel
            if (window.__iqeaChannel) {
                window.__iqeaChannel.postMessage({ __relay: true, payload: action });
            }
        } catch (err) {
            console.warn("Relay failed:", err);
        }
    }

    // BroadcastChannel for cross-tab/window relay (same origin)
    try {
        window.__iqeaChannel = new BroadcastChannel("__iqea_channel");
        window.__iqeaChannel.onmessage = (e) => {
            if (e.data && e.data.__relay && e.data.payload) {
                saveAction(e.data.payload);
            }
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

    // Focus tracking
    window.addEventListener("focus", () => {
        localStorage.setItem("lastFocusedWindow", window.location.href);
    });

    // ─── Smart XPath builder ───────────────────────────────────────────────────
    function getSmartXPath(el) {
        if (!el || el.nodeType !== Node.ELEMENT_NODE) return "";

        // 1. Prefer unique ID
        if (el.id && !/^\d/.test(el.id)) {
            return `//*[@id="${el.id}"]`;
        }

        // 2. Prefer unique data-testid / data-qa / data-cy
        const testAttrs = ["data-testid", "data-qa", "data-cy", "data-id", "data-automation-id"];
        for (const attr of testAttrs) {
            const val = el.getAttribute(attr);
            if (val) return `//${el.tagName.toLowerCase()}[@${attr}="${val}"]`;
        }

        // 3. Prefer aria-label or name on interactive elements
        const interactiveTags = ["input", "button", "select", "textarea", "a"];
        if (interactiveTags.includes(el.tagName.toLowerCase())) {
            const ariaLabel = el.getAttribute("aria-label");
            if (ariaLabel) return `//${el.tagName.toLowerCase()}[@aria-label="${ariaLabel}"]`;
            const name = el.getAttribute("name");
            if (name) return `//${el.tagName.toLowerCase()}[@name="${name}"]`;
            const placeholder = el.getAttribute("placeholder");
            if (placeholder) return `//${el.tagName.toLowerCase()}[@placeholder="${placeholder}"]`;
        }

        // 4. Fallback: positional path (robust version with tag+index only)
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
            el.type ||
            ""
        );
    }

    // ─── Core record function ──────────────────────────────────────────────────
    function recordAction(type, target, extra = {}) {
        if (Date.now() - (window.__reinjectionGrace || 0) < 800) return;
        if (!target || ["script", "style", "html", "body", "head"].includes(target.tagName?.toLowerCase())) return;

        const xpath = getSmartXPath(target);
        const label = getLabel(target);
        const value = extra.value !== undefined
            ? extra.value
            : (["input", "change", "input_others", "select"].includes(type)
                ? (target.value || target.innerText || "")
                : "");

        const actionObj = {
            step: nextStepNumber(),
            action: type,
            xpath,
            label: label?.trim(),
            value: String(value).trim(),
            url: window.location.href,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString(),
            ...extra
        };

        saveAction(actionObj);
        console.log("✅ Recorded:", actionObj);
    }

    // ─── Scroll throttle helper ────────────────────────────────────────────────
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
        // Prevent double-attach on same root
        if (root.__iqea_attached) return;
        root.__iqea_attached = true;

        const doc = root.ownerDocument || root;

        // ── Click ──────────────────────────────────────────────────────────────
        doc.addEventListener("click", e => recordAction("click", e.target), true);

        // ── Right-click / Context menu ─────────────────────────────────────────
        doc.addEventListener("contextmenu", e => recordAction("right_click", e.target), true);

        // ── Input / Change / Select ────────────────────────────────────────────
        doc.addEventListener("change", e => {
            const el = e.target;
            const tag = el.tagName.toLowerCase();
            if (tag === "select") {
                recordAction("select", el, {
                    value: el.options[el.selectedIndex]?.text || el.value
                });
            } else if (el.type === "checkbox") {
                recordAction("checkbox", el, { value: el.checked ? "checked" : "unchecked" });
            } else if (el.type === "radio") {
                recordAction("radio", el, { value: el.value });
            } else if (el.type === "file") {
                const files = Array.from(el.files || []).map(f => f.name).join(", ");
                recordAction("file_upload", el, { value: files });
            } else {
                recordAction("input", el);
            }
        }, true);

        // ── Focusout (for non-button/input elements like divs) ─────────────────
        doc.addEventListener("focusout", e => {
            const tag = e.target.tagName.toLowerCase();
            if (!["button", "input", "textarea", "select"].includes(tag)) {
                recordAction("change", e.target);
            }
        }, true);

        // ── Keyboard: Enter, Escape, shortcuts ─────────────────────────────────
        doc.addEventListener("keydown", e => {
            const key = e.key;
            const ctrl = e.ctrlKey || e.metaKey;
            const shift = e.shiftKey;

            // Enter / Escape
            if (key === "Enter") {
                recordAction("key_enter", e.target, { value: "Enter" });
                return;
            }
            if (key === "Escape") {
                recordAction("key_escape", e.target, { value: "Escape" });
                return;
            }
            if (key === "Tab") {
                recordAction("key_tab", e.target, { value: shift ? "Shift+Tab" : "Tab" });
                return;
            }

            // Ctrl/Cmd shortcuts
            if (ctrl) {
                const shortcutMap = {
                    "c": "copy", "x": "cut", "v": "paste",
                    "z": "undo", "y": "redo",
                    "a": "select_all", "f": "find",
                    "s": "save", "p": "print"
                };
                const action = shortcutMap[key.toLowerCase()];
                if (action) {
                    recordAction(`shortcut_${action}`, e.target, {
                        value: `${ctrl ? "Ctrl" : "Cmd"}+${key.toUpperCase()}`
                    });
                }
            }

            // Function keys
            if (key.startsWith("F") && !isNaN(key.slice(1))) {
                recordAction("function_key", e.target, { value: key });
            }
        }, true);

        // ── Copy / Paste (clipboard events) ────────────────────────────────────
        doc.addEventListener("copy", e => {
            const sel = (doc.getSelection() || "").toString().substring(0, 200);
            recordAction("copy", e.target, { value: sel });
        }, true);

        doc.addEventListener("cut", e => {
            const sel = (doc.getSelection() || "").toString().substring(0, 200);
            recordAction("cut", e.target, { value: sel });
        }, true);

        doc.addEventListener("paste", e => {
            let pasted = "";
            try {
                pasted = (e.clipboardData || window.clipboardData)?.getData("text") || "";
                pasted = pasted.substring(0, 200);
            } catch (_) {}
            recordAction("paste", e.target, { value: pasted });
        }, true);

        // ── Scroll ─────────────────────────────────────────────────────────────
        window.addEventListener("scroll", e => throttledScroll(e.target), { passive: true, capture: true });
        doc.addEventListener("scroll", e => {
            if (e.target !== window && e.target !== doc) throttledScroll(e.target);
        }, { passive: true, capture: true });

        // ── Drag & Drop ────────────────────────────────────────────────────────
        doc.addEventListener("dragstart", e => {
            _dragSource = e.target;
            recordAction("drag_start", e.target, { value: getLabel(e.target) });
        }, true);

        doc.addEventListener("drop", e => {
            recordAction("drop", e.target, {
                value: `from: ${getLabel(_dragSource)} → to: ${getLabel(e.target)}`
            });
            _dragSource = null;
        }, true);

        // ── Hover (mouse enter/leave on interactive elements) ──────────────────
        const hoverTags = ["button", "a", "select", "input", "li", "[role='menuitem']", "[role='option']"];
        doc.addEventListener("mouseenter", e => {
            const tag = e.target.tagName?.toLowerCase();
            if (["button", "a", "select"].includes(tag) ||
                e.target.getAttribute("role") === "menuitem" ||
                e.target.getAttribute("role") === "option") {
                recordAction("hover", e.target);
            }
        }, true);

        doc.addEventListener("mouseleave", e => {
            const tag = e.target.tagName?.toLowerCase();
            if (["button", "a"].includes(tag)) {
                recordAction("hover_end", e.target);
            }
        }, true);

        console.log("✅ IQEA listeners attached to:", root);
    }

    // ─── Shadow DOM support ────────────────────────────────────────────────────
    function injectIntoShadowRoots(node) {
        if (!node || node.nodeType !== Node.ELEMENT_NODE) return;
        if (node.shadowRoot) {
            attachListeners(node.shadowRoot);
            node.shadowRoot.querySelectorAll("*").forEach(injectIntoShadowRoots);
        }
        node.querySelectorAll && node.querySelectorAll("*").forEach(child => {
            if (child.shadowRoot) {
                attachListeners(child.shadowRoot);
                injectIntoShadowRoots(child);
            }
        });
    }

    // MutationObserver to catch dynamically added shadow roots
    const _shadowObserver = new MutationObserver(mutations => {
        mutations.forEach(m => m.addedNodes.forEach(n => {
            if (n.nodeType === Node.ELEMENT_NODE) injectIntoShadowRoots(n);
        }));
    });
    _shadowObserver.observe(document.documentElement, { childList: true, subtree: true });

    // ─── iFrame support ────────────────────────────────────────────────────────
    function injectIntoIframe(iframe) {
        try {
            const iDoc = iframe.contentDocument || iframe.contentWindow?.document;
            if (iDoc && iDoc.body) {
                attachListeners(iDoc);
                injectIntoShadowRoots(iDoc.documentElement);
                // Watch for new iframes inside this one
                new MutationObserver(mutations => {
                    mutations.forEach(m => m.addedNodes.forEach(n => {
                        if (n.tagName === "IFRAME") injectIntoIframe(n);
                    }));
                }).observe(iDoc, { childList: true, subtree: true });
            }
        } catch (e) {
            // Cross-origin iframe — can't inject (expected)
            console.warn("⚠️ Cross-origin iframe skipped:", iframe.src);
        }
    }

    function injectAllIframes() {
        document.querySelectorAll("iframe").forEach(injectIntoIframe);
    }

    // Watch for dynamically added iframes
    new MutationObserver(mutations => {
        mutations.forEach(m => m.addedNodes.forEach(n => {
            if (n.tagName === "IFRAME") injectIntoIframe(n);
            if (n.querySelectorAll) n.querySelectorAll("iframe").forEach(injectIntoIframe);
        }));
    }).observe(document.documentElement, { childList: true, subtree: true });

    // ─── SPA route change detection ────────────────────────────────────────────
    // Patch pushState / replaceState to detect SPA navigation
    function patchHistory() {
        const wrap = (orig) => function (...args) {
            const result = orig.apply(this, args);
            window.dispatchEvent(new Event("__iqea_spa_navigate"));
            return result;
        };
        if (!window.__iqea_history_patched) {
            history.pushState = wrap(history.pushState);
            history.replaceState = wrap(history.replaceState);
            window.__iqea_history_patched = true;
        }
    }

    window.addEventListener("popstate", () => window.dispatchEvent(new Event("__iqea_spa_navigate")));
    window.addEventListener("__iqea_spa_navigate", () => {
        // Clear the URL-bound guard so next inject call re-attaches
        window.__iqea_injected_url = null;
        // Re-attach to document (new DOM nodes may have appeared)
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
        console.log("✅ IQEA v2.0 Action Listener ready. Key:", statusKey);
    }

    if (document.readyState === "complete" || document.readyState === "interactive") {
        init();
    } else {
        window.addEventListener("load", init, { once: true });
    }

})(STATUS_KEY_PLACEHOLDER);"""
JS_action_listeners_mar16= """(function (statusKey) {
    if (window.__listenersInjected) return;
    window.__listenersInjected = true;

    // --- Action persistence ---
    if (!window.__recordedActions) {
        window.__recordedActions = JSON.parse(localStorage.getItem("recordedActions") || "[]");
    }

    function saveAction(action) {
        const existing = JSON.parse(localStorage.getItem("recordedActions") || "[]");
        const last = existing.length > 0 ? existing[existing.length - 1] : null;

        // ✅ Skip duplicate (same action+label+url+value)
        if (last &&
            last.action === action.action &&
            last.label === action.label &&
            last.url === action.url &&
            (!action.value || action.value === last.value)) {
            console.log("⏭️ Duplicate action skipped:", action);
            return;
        }

        existing.push(action);
        localStorage.setItem("recordedActions", JSON.stringify(existing));
        window.__recordedActions.push(action);

        try {
            window.dispatchEvent(new CustomEvent("__action_recorded", { detail: action }));
            if (window.opener && window.opener !== window) {
                window.opener.postMessage({ __relay: true, payload: action }, "*");
            }
        } catch (err) {
            console.warn("Relay failed:", err);
        }
    }

    // --- Focus listener ---
    window.addEventListener("focus", () => {
        localStorage.setItem("lastFocusedWindow", window.location.href);
    });

    // --- XPath helper ---
    function getXPath(el) {
        const getPos = e => {
            let pos = 1;
            while (e.previousElementSibling) { e = e.previousElementSibling; pos++; }
            return pos;
        };
        const parts = [];
        while (el && el.nodeType === Node.ELEMENT_NODE) {
            let index = getPos(el);
            parts.unshift(el.tagName.toLowerCase() + '[' + index + ']');
            el = el.parentNode;
        }
        return '/' + parts.join('/');
    }

    // --- Record action ---
    function recordAction(type, target) {
        // ⛔ Skip if still in grace period (reinjection)
        if (Date.now() - (window.__reinjectionGrace || 0) < 800) return;
        if (!target || ["script", "style"].includes(target.tagName?.toLowerCase())) return;

        const xpath = getXPath(target);
        const label = target.getAttribute("aria-label") ||
                      target.name || target.id ||
                      target.innerText || target.placeholder ||
                      target.value || target.type ||
                      target.getAttribute('alt') || target.getAttribute('class');
        const value = (["input","change","input_others"].includes(type))
                        ? target.value || target.innerText || "" : "";
        const currentUrl = window.location.href;
        const actionObj = {
            action: type,
            xpath,
            label: label?.trim(),
            value,
            url: currentUrl,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString()
        };

        // ✅ If last recorded action was only a "switch", replace it with this real action
        const last = window.__recordedActions.length > 0 ? window.__recordedActions[window.__recordedActions.length - 1] : null;
        if (last && last.action === "switch" && last.windowId === actionObj.windowId) {
            window.__recordedActions.pop();
            let existing = JSON.parse(localStorage.getItem("recordedActions") || "[]");
            existing.pop();
            localStorage.setItem("recordedActions", JSON.stringify(existing));
        }

        saveAction(actionObj);
        console.log("Recorded:", actionObj);
    }

    // --- Attach listeners ---
    function attachListeners() {
        if (window.__listenersAttached) return;
        window.__listenersAttached = true;

        document.addEventListener('click', e => recordAction('click', e.target), true);
        document.addEventListener('change', e => {
            if (e.target.type === 'checkbox' || e.target.type === 'radio')
                recordAction('input_others', e.target);
            else
                recordAction('input', e.target);
        }, true);
        document.addEventListener('focusout', e => {
            const tag = e.target.tagName.toLowerCase();
            if (tag !== 'button' && tag !== 'input' && tag !== 'textarea')
                recordAction('change', e.target);
        }, true);
    }

    // --- Relay handler ---
    window.addEventListener("message", function(event) {
        if (event.data && event.data.__relay && event.data.payload) {
            saveAction(event.data.payload);
            if (window.opener && window.opener !== window) {
                window.opener.postMessage(event.data, "*");
            }
        }
    });

    if (document.readyState === "complete") attachListeners();
    else window.addEventListener('load', attachListeners, { once:true });

    console.log("✅ Action listeners bound with key:", statusKey);
})(STATUS_KEY_PLACEHOLDER);
"""
JS_action_listeners_1 = """(function (statusKey) {
    if (window.__listenersInjected) return;
    window.__listenersInjected = true;

    // --- Action persistence ---
    if (!window.__recordedActions) {
        window.__recordedActions = JSON.parse(localStorage.getItem("recordedActions") || "[]");
    }

    function saveAction(action) {
        const existing = JSON.parse(localStorage.getItem("recordedActions") || "[]");
        existing.push(action);
        localStorage.setItem("recordedActions", JSON.stringify(existing));

        window.__recordedActions.push(action);

        try {
            window.dispatchEvent(new CustomEvent("__action_recorded", { detail: action }));
            if (window.opener && window.opener !== window) {
                window.opener.postMessage({ __relay: true, payload: action }, "*");
            }
        } catch (err) {
            console.warn("Relay failed:", err);
        }
    }

    // --- Focus listener ---
    window.addEventListener("focus", () => {
        localStorage.setItem("lastFocusedWindow",  window.location.href);
    });

    // --- XPath helper ---
    function getXPath(el) {
        const getPos = e => {
            let pos = 1;
            while (e.previousElementSibling) { e = e.previousElementSibling; pos++; }
            return pos;
        };
        const parts = [];
        while (el && el.nodeType === Node.ELEMENT_NODE) {
            let index = getPos(el);
            parts.unshift(el.tagName.toLowerCase() + '[' + index + ']');
            el = el.parentNode;
        }
        return '/' + parts.join('/');
    }

    // --- Record action ---
    function recordAction(type, target) {
        // ⛔ Skip if still in grace period (800ms default)
        if (Date.now() - (window.__reinjectionGrace || 0) < 800) return;
        if (!target || ["script", "style"].includes(target.tagName?.toLowerCase())) return;

        const xpath = getXPath(target);
        const label = target.getAttribute("aria-label") || target.name || target.id || target.innerText || target.placeholder || target.value || target.type || target.getAttribute('alt') || target.getAttribute('class');
        const value = (["input","change","input_others"].includes(type)) ? target.value || target.innerText || "" : "";

        const actionObj = {
            action: type,
            xpath,
            label: label?.trim(),
            value,
            url: window.location.href,
            windowId: window.name || statusKey,
            timestamp: new Date().toISOString()
        };

        saveAction(actionObj);
        console.log("Recorded:", actionObj);
    }

    // --- Attach listeners ---
    function attachListeners() {
        if (window.__listenersAttached) return;
        window.__listenersAttached = true;

        document.addEventListener('click', e => recordAction('click', e.target), true);
        document.addEventListener('change', e => {
            if (e.target.type === 'checkbox' || e.target.type === 'radio')
                recordAction('input_others', e.target);
            else
                recordAction('input', e.target);
        }, true);
        document.addEventListener('focusout', e => {
            const tag = e.target.tagName.toLowerCase();
            if (tag !== 'button' && tag !== 'input' && tag !== 'textarea')
                recordAction('change', e.target);
        }, true);
    }

    // --- Relay handler ---
    window.addEventListener("message", function(event) {
        if (event.data && event.data.__relay && event.data.payload) {
            saveAction(event.data.payload);
            if (window.opener && window.opener !== window) {
                window.opener.postMessage(event.data, "*");
            }
        }
    });

    if (document.readyState === "complete") attachListeners();
    else window.addEventListener('load', attachListeners, { once:true });

    console.log("✅ Action listeners bound with key:", statusKey);
})(STATUS_KEY_PLACEHOLDER);
"""

def injection_script_updated_fixed():
    return f"""
    (function() {{
        if (window.__recorderInjected) return;
        window.__recorderInjected = true;

        // Ensure a stable windowId
        if (!window.name || window.name.trim() === "") {{
            window.name = "recorder_" + Math.random().toString(36).substr(2, 9);
        }}
        const windowId = window.name;

        const statusKey = "recorder_status_" + windowId;

        function updateStatus(alive = true) {{
            localStorage.setItem(statusKey, JSON.stringify({{
                windowId: windowId,
                alive: alive,
                url: window.location.href,
                ts: Date.now()
            }}));
        }}

        // Initial write
        updateStatus(true);

        // Refresh every 2s
        setInterval(() => updateStatus(true), 2000);

        // Mark as dead when page unloads
        window.addEventListener("beforeunload", () => updateStatus(false));

        // ---- Inject listeners with SAME statusKey ----
        {JS_action_listeners
            .replace("STATUS_KEY_PLACEHOLDER", "statusKey")
            .replace("WINDOW_ID_PLACEHOLDER", "windowId")}
        // ✅ Reinjection grace flag
        window.__reinjectionGrace = Date.now();    

        console.log("✅ Recorder JS injected + heartbeat + listeners active (aligned key)");
    }})();
    """

def injection_script_agentflow():
    """
    Injection wrapper for the AgentFlow (React Flow) recorder — IQEA v3.0.
    Mirrors injection_script_updated_fixed() (stable windowId + heartbeat +
    cross-window relay) but loads JS_action_listeners_agentflow_v2, which adds
    React-Flow node capture, palette drag, Slate prompt serialization and flow
    graph snapshots. Use this instead of injection_script_updated_fixed() when
    recording on AgentFlow; every other app keeps using the generic recorder.
    """
    return f"""
    (function() {{
        if (window.__recorderInjected) return;
        window.__recorderInjected = true;

        if (!window.name || window.name.trim() === "") {{
            window.name = "recorder_" + Math.random().toString(36).substr(2, 9);
        }}
        const windowId = window.name;
        const statusKey = "recorder_status_" + windowId;
        window.__iqea_windowId = statusKey;

        function updateStatus(alive = true) {{
            localStorage.setItem(statusKey, JSON.stringify({{
                windowId: windowId, alive: alive,
                url: window.location.href, ts: Date.now()
            }}));
        }}
        updateStatus(true);
        setInterval(() => updateStatus(true), 2000);
        window.addEventListener("beforeunload", () => updateStatus(false));

        // ---- Inject the AgentFlow listeners ----
        {JS_action_listeners_agentflow_v2}
        window.__reinjectionGrace = Date.now();

        console.log("✅ AgentFlow recorder (v3.0) injected + heartbeat active");
    }})();
    """

FINAL_JS_ACTION_LISTENER="""(function () {
    if (!window.__recordedActions) {
        window.__recordedActions = JSON.parse(localStorage.getItem("recordedActions") || "[]");
    }

    function saveAction(action) {
        const existing = JSON.parse(localStorage.getItem("recordedActions") || "[]");
        existing.push(action);
        localStorage.setItem("recordedActions", JSON.stringify(existing));
    }

    function getXPath(el) {
        const getPos = e => {
            let pos = 1;
            while (e.previousElementSibling) { e = e.previousElementSibling; pos++; }
            return pos;
        };
        const parts = [];
        while (el && el.nodeType === Node.ELEMENT_NODE) {
            let index = getPos(el);
            parts.unshift(el.tagName.toLowerCase() + '[' + index + ']');
            el = el.parentNode;
        }
        return '/' + parts.join('/');
    }

    function recordAction(type, target) {
        if (!target || ["script", "style"].includes(target.tagName?.toLowerCase())) return;
        const xpath = getXPath(target);
        const label = target.getAttribute("aria-label") || target.name || target.id || target.innerText || target.placeholder || target.value || target.type || target.getAttribute('alt') || target.getAttribute('class');
        const value = (["input","change","input_others"].includes(type)) ? target.value || target.innerText || "" : "";
        const url = window.location.href;
        const actionObj = {
            action: type,
            xpath,
            label: label?.trim(),
            value,
            url,
            windowId: window.name || window.location.href,
            timestamp: new Date().toISOString()
        };

        window.__recordedActions.push(actionObj);
        saveAction(actionObj);

        // 🔑 Always try to bubble the event up to the root window
        if (window.opener && window.opener !== window) {
            window.opener.postMessage({ __relay: true, payload: actionObj }, "*");
        }

        console.log("Recorded:", actionObj);
    }

    function attachListeners() {
        if (window.__listenersAttached) return;
        window.__listenersAttached = true;

        document.addEventListener('click', e => recordAction('click', e.target), true);
        document.addEventListener('change', e => {
            if(e.target.type === 'checkbox' || e.target.type === 'radio') recordAction('input_others', e.target);
            else recordAction('input', e.target);
        }, true);
        document.addEventListener('focusout', e => {
            const tag = e.target.tagName.toLowerCase();
            if(tag !== 'button' && tag !== 'input' && tag !== 'textarea') recordAction('change', e.target);
        }, true);
    }

    // 🔑 Relay + root collector
    window.addEventListener("message", function(event) {
        if (event.data && event.data.__relay && event.data.payload) {
            // Save locally
            saveAction(event.data.payload);

            // If this window also has an opener, keep bubbling up until root
            if (window.opener && window.opener !== window) {
                window.opener.postMessage(event.data, "*");
            }
        }
    });

    if (document.readyState === "complete") attachListeners();
    else window.addEventListener('load', attachListeners, {once:true});

    console.log("✅ Multi-window action recording active...");
})();
"""
FINAL_JS_ACTION_LISTENER_old1= """
(function () {
    // Prevent duplicate injection across reloads/navigations
    if (localStorage.getItem("__recorderInjected") === "true") {
        console.log("ℹ️ Recorder already injected, skipping...");
        return;
    }
    localStorage.setItem("__recorderInjected", "true");
    window.__recorderInjected = true;

    // Initialize global action store
    if (!window.recordedActions) {
        window.recordedActions = JSON.parse(localStorage.getItem("recordedActions") || "[]");
    }

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
        const label = target.getAttribute("aria-label") || target.name || target.id || target.innerText || target.placeholder || target.value || target.getAttribute('alt') || target.getAttribute('class') || target.getAttribute('type');
        const value = (["input", "change", "input_others"].includes(type)) ? target.value || target.innerText || "" : "";
        const url = window.location.href;
        const actionObj = { 
            action: type, 
            xpath, 
            label: label?.trim(), 
            value, 
            url,
            windowId: window.name || window.location.href, 
            timestamp: new Date().toISOString()
        };

        // Save locally
        window.recordedActions.push(actionObj);
        saveAction(actionObj);

        // Send to parent if this is a popup/child window
        if (window.opener) {
            window.opener.postMessage(actionObj, "*");
        }
        console.log("Recorded:", actionObj);
    }

    function attachListeners() {    
        if (window.__listenersAttached) return; // prevent duplicates
        window.__listenersAttached = true;

        document.addEventListener('click', e => recordAction('click', e.target), true);

        document.addEventListener('change', e => {
            if (e.target.type === 'checkbox' || e.target.type === 'radio') {
                recordAction('input_others', e.target);
            } else if (e.target.type !== 'submit') {
                recordAction('input', e.target);
            }
        });

        document.addEventListener('focusout', e => {
            const tag = e.target.tagName.toLowerCase();
            if(tag !== 'button' && tag !== 'input' && tag !== 'textarea') {
                recordAction('change', e.target);
            }
        });
    }

    // Listen to messages from child windows
    window.addEventListener("message", function(event) {
        if (event.data && event.data.action) {
            saveAction(event.data);
        }
    });

    if (document.readyState === "complete") {
        attachListeners();
    } else {
        window.addEventListener('load', attachListeners, { once: true });
    }

    // Minimal observer: don’t reattach global listeners
    const observer = new MutationObserver(() => {
        // If new inputs/buttons appear dynamically, they’ll still work
        // since we attach at the document level
    });
    observer.observe(document.body, { childList: true, subtree: true });

    console.log("✅ Recording actions (multi-window safe)...");
})();
"""


FINAL_JS_ACTION_LISTENER_old= """ 
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

        //const exists = window.recordedActions.some(action => action.xpath === xpath && action.action === type && action.value === value);
        //if (!exists) {
            const actionObj = { action: type, xpath, label: label?.trim(), value, url };
            window.recordedActions.push(actionObj);
            saveAction(actionObj);
            console.log("Recorded:", actionObj);
        //}
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
# in action_utils.py (or wherever)
def injection_script_updated():
    # keep this definition in your file as you posted earlier
    return f"""
        if (!document.getElementById("recorder_script")) {{
            var script = document.createElement('script');
            script.type = 'text/javascript';
            script.id = 'recorder_script';
            script.text = {json.dumps(FINAL_JS_ACTION_LISTENER)};
            document.documentElement.appendChild(script);
            console.log("✅ Recorder injected");
        }} else {{
            console.log("ℹ️ Recorder already present, skipping reinjection");
        }}
    """
def injection_script_updated_old():
    return f"""
        if (!document.getElementById("recorder_script")) {{
            var script = document.createElement('script');
            script.type = 'text/javascript';
            script.id = 'recorder_script';
            script.text = {json.dumps(FINAL_JS_ACTION_LISTENER)};
            document.documentElement.appendChild(script);
            console.log("✅ Recorder injected");
        }} else {{
            console.log("ℹ️ Recorder already present, skipping reinjection");
        }}
    """
def start_recording(driver):
    driver.execute_script(injection_script_updated())
    ####domain change handled action
def get_new_actions(driver):
    return driver.execute_script("""
        const actions = window.__recordedActions || [];
        window.__recordedActions = []; // clear after reading
        return actions;
    """)
def get_recorded_actions(driver):
    """
    Collect recorded actions from all windows, merge by timestamp.
    injected_windows: dict of {window_handle: True}
    """
    all_actions = []
    handles = driver.window_handles
    # Iterate through all known windows
    for handle in handles:
        try:
            driver.switch_to.window(handle)

            # Fetch actions from this window's localStorage
            actions = driver.execute_script("""
                return JSON.parse(localStorage.getItem('recordedActions') || '[]');
            """)
            if actions:
                all_actions.extend(actions)

        except Exception as e:
            print(f"⚠ Error fetching actions from window {handle}: {e}")

    # Sort all actions by timestamp
    all_actions.sort(key=lambda x: x.get('timestamp', ''))
    return all_actions

def get_recorded_actions_old(driver):
    # return driver.execute_script("return window.recordedActions || []")
    raw_actions = driver.execute_script("return localStorage.getItem('recordedActions') || '[]';")
    print("------------------recorder raw action--------------------")
    print(raw_actions)
    driver.execute_script("return localStorage.setItem('recordedActions','[]');")
    return json.loads(raw_actions) if raw_actions else []

def wait_for_url_change(driver, initial_url, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if driver.current_url != initial_url:
            return True
        time.sleep(1)
    return False
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
client = openai.OpenAI(api_key =  os.environ["OPENAI_API_KEY"],
                       base_url = os.environ["OPENAI_API_BASE"])
def generate_workflow(actions):
    # Access the variables
    print("*************Recorded Action *****************")
    print(actions)
    print("****************Recorded Action end**************")
    # api_key = os.getenv("AZURE_OPENAI_API_KEY")
    # endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    #
    # # Set the environment variables explicitly if needed
    # os.environ["AZURE_OPENAI_API_KEY"] = api_key
    # os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint
    #
    # model = AzureChatOpenAI(
    #     openai_api_version="2023-05-15",
    #     azure_deployment="qepracticekey",
    # )
    #
    prompt = f"""
    You are an expert test automation assistant. 
    Convert the raw recorded actions into a clean, deduplicated, and human-readable workflow 
    that can directly be used for writing test cases, scripts, and Gherkin feature files.

    Input Actions:
    {actions}

    Transformation Rules:
    1. **Deduplication**
       - Remove repeated actions on the same element (keep only the latest meaningful step).
       - If the same text input occurs multiple times in sequence, keep only the final input.
       - Ignore duplicate clicks when nothing changes.

    2. **Noise Filtering**
       - Ignore technical IDs (e.g., "a-xxxx", "ketch-*", "mx-auto", cryptic auto-generated IDs).
       - Skip redundant "Change the value to…" lines when already captured as "Enter…" or "Select…".
       - Remove empty clicks like `Click on ""`.

    3. **Action Normalization**
       - Merge "Click" + "Change the value" into a single meaningful action (e.g., `Select "Alabama" from "State" dropdown`).
       - Replace cryptic field names with human-readable labels using this mapping:
         - "first_name[0][value]" → "First Name"
         - "last_name[0][value]" → "Last Name"
         - "field_company[0][value]" → "Company"
         - "mail" → "Email"
         - "phoneNumber" → "Phone Number"
         - "dateOfBirthMasked" → "Date of Birth"
         - "addressLine1" → "Address Line 1"
         - "addressLine2" → "Address Line 2"
         - "cityName" → "City"
         - "zipCode" → "Zip Code"
         - "saveConsumer" → "Save"
         - "terms-of-use" → "Terms of Use"
         - "op" → "Submit"
       - If an element is not in the mapping, keep its best human-readable form.

    4. **Window Management**
       - Start with: `User opened page: [URL]`.
       - For new windows: `Switched to new window: [URL]`.
       - For revisits: `Switched to window: [URL]`.

    5. **Output Format**
       - Numbered steps.
       - Each step on its own line.
       - Use consistent phrasing:
         - Click → `Click the "LABEL" button` or `Click the "LABEL" link`
         - Input → `Enter "VALUE" in "LABEL" field`
         - Select → `Select "VALUE" from "LABEL" dropdown`
         - Checkbox → `Select "LABEL"`
       - No explanations, only the cleaned workflow.

    Output:
    - A perfectly cleaned workflow with numbered steps, 
    ready to be used for test case and feature file creation.
    """

    model = "gpt-5-mini"
    try:
        response = client.chat.completions.create(model=model,
                                                  messages=[{"role": "user",
                                                             "content": prompt
                                                             }
                                                            ])
        print(response)
        output_value = response.choices[0].message.content
        print(output_value)
        return output_value
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return None
    # message = HumanMessage(content=prompt)
    # output_value = model([message])
    # print(output_value)
    # return output_value.content
def generate_workflow_manual(actions):
    """
    Convert recorded actions into human-readable workflow suitable for AI feature/test case generation.
    Handles multiple windows and avoids duplicate window messages.
    """
    workflow_lines = []
    current_window = None
    seen_windows = set()
    last_action_url = None   # ✅ NEW: track previous action URL

    for act in actions:
        window_id = act.get("windowId", "MainWindow")
        url = act.get("url", "Unknown")

        # Detect window switch or new window
        if window_id != current_window:
            if window_id in seen_windows:
                workflow_lines.append(f'Switched to window: [{url}]')
            else:
                if window_id == "MainWindow":
                    workflow_lines.append(f'User opened page: [{url}]')
                else:
                    workflow_lines.append(f'Switched to new window: [{url}]')
                seen_windows.add(window_id)

            current_window = window_id
            last_action_url = None  # ✅ reset when window changes

        # Human-readable action
        readable = humanize_action(act)
        if readable:
            # ✅ URL comparison logic
            if url != last_action_url:
                workflow_lines.append(f'{readable} (URL: {url})')
                last_action_url = url
            else:
                workflow_lines.append(f'{readable}')

    return workflow_lines

def generate_workflow_manual_bug(actions):
    """
    Convert recorded actions into human-readable workflow suitable for AI feature/test case generation.
    Handles multiple windows and avoids duplicate window messages.
    """
    print("************Actions***************")
    print(actions)
    workflow_lines = []
    current_window = None
    seen_windows = set()

    for act in actions:
        window_id = act.get("windowId", "MainWindow")
        url = act.get("url", "Unknown")

        # Detect window switch or new window
        if window_id != current_window:
            if window_id in seen_windows:
                workflow_lines.append(f'Switched to window: [{url}]')
            else:
                if window_id == "MainWindow":
                    workflow_lines.append(f'User opened page: [{url}]')
                else:
                    workflow_lines.append(f'Switched to new window: [{url}]')
                seen_windows.add(window_id)

            current_window = window_id

        # Human-readable action
        readable = humanize_action(act)
        if readable:
            workflow_lines.append(f'{readable} (URL: {url})')
            #workflow_lines.append(f'{readable}')
    print("*********workflow_lines************")
    print(workflow_lines)
    print("*********workflow_lines ends************")

   # generate_workflow(workflow_lines)
    return workflow_lines


def humanize_action(action_dict):
    """
    Converts a recorded action into a human-readable sentence suitable for AI consumption.
    """
    action_type = action_dict.get("action")
    # v3.0 stores tag under "tagName" and id under "elementId"; keep back-compat
    tag = (action_dict.get("tag") or action_dict.get("tagName") or "").lower()
    label = (action_dict.get("label") or "").strip()
    raw = action_dict.get("value")
    value = str(raw).strip() if raw is not None else ""
    placeholder = (action_dict.get("placeholder") or "").strip()
    element_id = (action_dict.get("id") or action_dict.get("elementId") or "").strip()

    display_label = label or placeholder or element_id.replace("-", " ").replace("_", " ").title()

    # ── AgentFlow (React Flow) specific actions — additive only; the generic
    #    recorder never emits these, so existing apps are unaffected. All
    #    AgentFlow noise filtering happens in the listener, not here. ──────────
    if action_type == "add_node":
        return f'Drag and drop a "{value}" node onto the canvas'

    elif action_type == "enter_prompt":
        return f'Enter the prompt: "{value}"'

    elif action_type == "select_option":
        return f'Select "{value}" from the dropdown'

    elif action_type == "enter_text":
        return f'Enter "{value}" in the "{display_label}" field'

    elif action_type == "flow_snapshot":
        n = action_dict.get("nodeCount", "?")
        m = action_dict.get("edgeCount", "?")
        return f'[Flow state: {n} node(s), {m} connection(s)]'

    elif action_type == "key_enter":
        return f'Press Enter in "{display_label}"'

    elif action_type == "key_escape":
        return f'Press Escape'

    elif action_type == "checkbox":
        return f'{"Check" if value == "checked" else "Uncheck"} "{display_label}"'

    elif action_type == "radio":
        return f'Select radio option "{value}" ({display_label})'

    # ── Generic web actions ───────────────────────────────────────────────────
    if action_type == "click":
        if tag == "button" or "btn" in element_id.lower():
            return f'Click the "{display_label}" button'
        elif tag == "a":
            return f'Click the "{display_label}" link'
        else:
            return f'Click on "{display_label}"'

    elif action_type == "input_others":
        return f'Select "{value}" in the "{display_label}" field'

    elif action_type == "select":
        return f'Select "{value}" from the "{display_label}" dropdown'

    elif action_type == "input":
        return f'Enter "{value}" in the "{display_label}" field'

    elif action_type == "change":
        return f'Change the value to "{value}" in "{display_label}"'

    elif action_type == "navigate":
        return f'Navigate to "{display_label}" page'

    elif action_type:
        return f'{action_type.capitalize()} on "{display_label}"'
    elif action_type == "scroll":
        return f'Scroll the page'

    elif action_type == "hover":
        return f'Hover over "{display_label}"'

    elif action_type == "keypress":
        return f'Press key in "{display_label}" field'

    elif action_type == "ajax":
        return f'Wait for page load/update triggered by "{display_label}"'

    else:
        return f'Perform action on "{display_label}"'


# ── Record & Playback: Script Generation ──────────────────────────────────────
def format_actions_for_script_generation(actions):
    """
    Convert raw recorded action dicts into a structured format for LLM script
    generation.  Uses the enriched element metadata captured by the JS recorder
    (tagName, elementId, elementName, href, dataTestId, isNavLink) to produce
    EXACT Selenium locators — no guessing needed by the LLM.

    Outputs one line per step plus [PAGE_CHANGE] markers between URL transitions.
    Each line includes all fields the LLM needs to write the correct Selenium call.
    """
    if not actions:
        return ""

    lines = []
    prev_url = None

    for idx, act in enumerate(actions, start=1):
        action_type  = (act.get("action") or "").strip().lower()
        url          = (act.get("url") or "").strip()
        value        = (act.get("value") or "").strip()

        # ── New enriched fields (may be absent for old recordings — handle gracefully)
        tag          = (act.get("tagName") or act.get("tag") or "").strip().lower()
        el_id        = (act.get("elementId") or "").strip()
        el_name      = (act.get("elementName") or "").strip()
        el_type      = (act.get("elementType") or "").strip().lower()
        href         = (act.get("href") or "").strip()
        data_test    = (act.get("dataTestId") or "").strip()
        aria_label   = (act.get("ariaLabel") or "").strip()
        css_classes  = (act.get("cssClasses") or "").strip()
        is_nav_link  = act.get("isNavLink", False)
        raw_label    = (act.get("label") or "").strip()
        xpath        = (act.get("xpath") or "").strip()

        # ── Insert page-transition marker ────────────────────────────────────
        if prev_url is not None and url and url != prev_url:
            lines.append(f"--- [PAGE_CHANGE: {prev_url} → {url}] ---")
        prev_url = url or prev_url

        # ── Build the best possible Selenium locator from recorded metadata ──
        # Priority: elementId > dataTestId > ariaLabel > elementName > label-derived > xpath
        if el_id:
            locator = f"By.ID='{el_id}'"
        elif data_test:
            locator = f"By.CSS_SELECTOR='[data-testid=\"{data_test}\"]'"
        elif aria_label:
            locator = f"By.XPATH='//{tag or '*'}[@aria-label=\"{aria_label}\"]'" if tag else f"By.XPATH='//*[@aria-label=\"{aria_label}\"]'"
        elif el_name:
            locator = f"By.NAME='{el_name}'"
        elif raw_label and not raw_label.isdigit() and len(raw_label) >= 3:
            clean = raw_label.replace("-", "").replace("_", "")
            if clean.isalnum():
                locator = f"By.ID='{raw_label}' (derived-from-label)"
            elif css_classes:
                first_class = css_classes.split()[0]
                locator = f"By.CLASS_NAME='{first_class}'"
            else:
                locator = f"By.XPATH='{xpath}'"
        elif raw_label and raw_label.isdigit():
            # Numeric label = badge/counter text — find the parent nav link instead
            locator = f"badge_text={raw_label} USE_PARENT_NAV_LINK css_classes='{css_classes}'"
        else:
            locator = f"By.XPATH='{xpath}'"

        # ── Nav-link flag: SPA anchors need JS click ─────────────────────────
        nav_flag  = f" | NAV_LINK href='{href}'" if is_nav_link else ""
        tag_info  = f" | tag={tag}" if tag else ""
        type_info = f" | inputType={el_type}" if el_type and tag == "input" else ""

        display = el_id or raw_label or xpath[:60] or "unknown"

        if action_type == "click":
            line = (f"Step {idx}: [CLICK]"
                    f" | Element: {display}"
                    f" | Locator: {locator}"
                    f"{nav_flag}{tag_info}{type_info}"
                    f" | URL: {url}")
        elif action_type in ("input", "change", "input_others"):
            line = (f"Step {idx}: [TYPE '{value}']"
                    f" | Element: {display}"
                    f" | Locator: {locator}"
                    f"{tag_info}{type_info}"
                    f" | URL: {url}")
        elif action_type in ("key_tab", "key_enter", "key_escape"):
            # Skip tab/escape — not needed in automation; flag for LLM to skip
            line = f"Step {idx}: [SKIP_{action_type.upper()}] (keyboard nav — not needed in automation)"
        else:
            line = (f"Step {idx}: [{action_type.upper()}]"
                    f" | Element: {display}"
                    f" | Locator: {locator}"
                    f"{nav_flag}{tag_info}"
                    f" | URL: {url}")

        lines.append(line)

    return "\n".join(lines)



# def generate_workflow(actions):
#     print("------------------recorder raw action--------------------")
#     print(actions)
#     workflow_lines = []
#     recorded = set()
#     prev_url = None
#     prev_window = None
#
#     for act in actions:
#         url = act.get("url", "Unknown")
#         window_id = act.get("windowId", "MainWindow")
#
#         # Group by window and URL
#         if url != prev_url or window_id != prev_window:
#             workflow_lines.append(f"\nWindow: [{window_id}] | Page: [{url}]")
#             prev_url, prev_window = url, window_id
#
#         readable = humanize_action(act)
#         if readable and (window_id, readable) not in recorded:
#             workflow_lines.append(f"- {readable}")
#             recorded.add((window_id, readable))
#
#     return workflow_lines

def generate_workflow_old(actions):
    print("------------------recorder raw action--------------------")
    print(actions)
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
# def generate_workflow(actions):
#     grouped = defaultdict(list)
#     for act in actions:
#         url = act.get("url", "Unknown")
#         grouped[url].append(act)
#
#     workflow_lines = []
#     for url, acts in grouped.items():
#         workflow_lines.append(f"Page: [{url}]")
#         recorded = set()
#
#         for act in acts:
#             readable=humanize_action(act)
#             if readable and readable not in recorded:
#                 workflow_lines.append(f"- {readable}")
#                 recorded.add(readable)
#
#             # action = act.get("action", "").strip()
#             # label = act.get("label", "").strip()
#             #
#             # if not action or not label:
#             #     continue
#             #
#             # if action == 'click':
#             #     line = f"Click {label}"
#             # elif action == 'input':
#             #     line = f"Enter {label}"
#             # elif action == 'change':
#             #     line = f"Change {label}"
#             # else:
#             #     line = f"{action.capitalize()} {label}"
#             #
#             # if line and line not in recorded:
#             #     workflow_lines.append(f"- {line}")
#             #     recorded.add(line)
#
#         workflow_lines.append("")  # separate pages with blank line
#
#     return workflow_lines

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def take_screenshot(driver, folder):
    url = driver.current_url
    parsed_url = urlparse(url)
    page_name = sanitize_filename(parsed_url.path.strip("/")) or "home"
    file_path = os.path.join(folder, f"{page_name}.png")
    driver.save_screenshot(file_path)
    return file_path
# def humanize_action(action_dict):
#     action_type = action_dict.get("action")
#     tag = (action_dict.get("tag") or "").lower()
#
#     label = (action_dict.get("label") or "").strip()
#     value = (action_dict.get("value") or "").strip()
#     placeholder = (action_dict.get("placeholder") or "").strip()
#     element_id = (action_dict.get("id") or "").strip()
#
#     # Fallback label
#     display_label = label or placeholder or element_id.replace("-", " ").replace("_", " ").title()
#
#     # Add window info for clarity
#     window_id = action_dict.get("windowId", "MainWindow")
#
#     if action_type == "click":
#         if tag == "button" or "btn" in element_id.lower():
#             return f'[{window_id}] Click the "{display_label}" button'
#         elif tag == "a":
#             return f'[{window_id}] Click the "{display_label}" link'
#         else:
#             return f'[{window_id}] Click on "{display_label}"'
#
#     elif action_type == "input_others":
#         return f'[{window_id}] Select "{value}" in the "{display_label}" field'
#
#     elif action_type == "select":
#         return f'[{window_id}] Select "{value}" from the "{display_label}" dropdown'
#
#     elif action_type == "input":
#         return f'[{window_id}] Enter "{value}" in the "{display_label}" field'
#
#     elif action_type == "change":
#         return f'[{window_id}] Change the {value} in "{display_label}"'
#
#     elif action_type == "navigate":
#         return f'[{window_id}] Navigate to "{display_label}" page'
#
#     # Fallback
#     if action_type:
#         return f'[{window_id}] {action_type.capitalize()} on "{display_label}"'
#     else:
#         return f'[{window_id}] Perform action on "{display_label}"'

def humanize_action_old(action_dict):

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