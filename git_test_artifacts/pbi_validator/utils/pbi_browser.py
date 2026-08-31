import base64
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def start_browser(url: str, headless: bool = False):
    """Open Chrome and navigate to the PBI report URL. Returns the Selenium driver."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.maximize_window()
    driver.get(url)
    return driver


def is_driver_alive(driver) -> bool:
    """Check whether the Selenium driver session is still active."""
    try:
        _ = driver.current_url
        return True
    except Exception:
        return False


def take_screenshot(driver) -> tuple:
    """
    Take a screenshot of the current browser view.
    Returns (png_bytes, base64_string).
    """
    png_bytes = driver.get_screenshot_as_png()
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    return png_bytes, b64


def extract_kpis_via_llm(screenshot_b64: str, client) -> tuple:
    """
    Send PBI screenshot to LLM vision and extract all visible KPI values plus
    active slicer/filter values.
    Returns (kpis: list[dict], slicers: list[dict])
      kpis    — {visual_name, kpi_name, value, value_type, visual_type}
      slicers — {slicer_name, selected_value}
    """
    prompt = (
        "You are a Power BI data extraction expert. "
        "Analyze this Power BI report screenshot and extract ALL visible KPI values "
        "plus every active slicer/filter control.\n\n"
        "Return a JSON object with exactly two keys:\n\n"
        "\"kpis\" — array of all visible metrics, each with:\n"
        "  - visual_name: title/header of the card or chart (use 'Unknown' if not visible)\n"
        "  - kpi_name: metric label (e.g. 'Total Revenue', 'YoY Growth')\n"
        "  - value: displayed value exactly as shown (e.g. '$1.2M', '94.3%', '12,456')\n"
        "  - value_type: one of 'currency', 'percentage', 'number', 'text', 'date'\n"
        "  - visual_type: one of 'card', 'kpi_visual', 'table', 'matrix', "
        "'bar_chart', 'line_chart', 'pie_chart', 'other'\n\n"
        "\"slicers\" — array of active slicer/filter controls, each with:\n"
        "  - slicer_name: the slicer label (e.g. 'Year', 'Region', 'Category')\n"
        "  - selected_value: currently selected value(s) as a string (e.g. '2024', 'West, East')\n\n"
        "Include ALL numbers, percentages, totals visible on screen.\n"
        "Exclude axis labels, page titles, navigation buttons, and empty/unselected slicers.\n\n"
        "Return ONLY a valid JSON object, no markdown fences.\n"
        'Example: {"kpis": [{"visual_name": "Revenue Card", "kpi_name": "Total Revenue", '
        '"value": "$1.2M", "value_type": "currency", "visual_type": "card"}], '
        '"slicers": [{"slicer_name": "Year", "selected_value": "2024"}]}'
    )

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{screenshot_b64}",
                        "detail": "high"
                    }
                },
                {"type": "text", "text": prompt}
            ]
        }],
        max_tokens=4000,
        timeout=600,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw)

    # Backward-compat: LLM may return a plain list (old format without slicers)
    if isinstance(data, list):
        return data, []
    return data.get("kpis", []), data.get("slicers", [])


def try_show_as_table(driver, wait_seconds: int = 6) -> list:
    """
    For every PBI visual on screen:
      1. Find visual containers via JavaScript
      2. Fire contextmenu event via JS (Selenium right-click is blocked by PBI published view)
      3. Find and click 'Show as a table' via JS
      4. Wait for Focus Mode to load (PBI opens a full page, NOT a modal)
      5. Scrape the focus-mode table with position-based JS extraction
      6. Click 'Back to report' to return before moving to the next visual
    Returns list of dicts: {visual_title, headers, rows}
    """
    _JS_FIND_VISUALS = """
        var selectors = [
            'visual-container-modern',
            'visual-container',
            '[class*="visualContainer"]',
            '[class*="visual-container"]'
        ];
        var found = [];
        selectors.forEach(function(sel) {
            Array.from(document.querySelectorAll(sel)).forEach(function(el) {
                var r = el.getBoundingClientRect();
                if (r.width > 50 && r.height > 50 && found.indexOf(el) === -1) {
                    found.push(el);
                }
            });
        });

        // De-duplicate nested matches. PBI wraps each visual in several nested
        // containers (e.g. visual-container-modern > visual-container), so the
        // same visual gets matched 2x and scraped twice. Keep the OUTER element
        // (it carries the title) and drop the inner duplicate.
        // Guard: ignore any candidate that wraps 3+ others — that is a page /
        // canvas wrapper, not a single visual.
        found = found.filter(function(el) {
            var wraps = found.filter(function(o) {
                return o !== el && el.contains(o);
            });
            return wraps.length < 3;
        });
        found = found.filter(function(el) {
            return !found.some(function(o) {
                return o !== el && o.contains(el);
            });
        });

        return found;
    """

    results = []

    # Count visuals once upfront — used only for the loop range.
    # Element references are re-fetched on EVERY iteration because
    # Focus Mode re-renders the entire DOM, making prior references stale.
    initial_visuals = driver.execute_script(_JS_FIND_VISUALS)
    total = len(initial_visuals)
    print(f"[PBI] Found {total} visible visual(s)")
    if total == 0:
        print("[PBI] No visual containers found")
        return results

    for idx in range(total):
        title = "Untitled"
        try:
            # Re-fetch fresh elements — previous references are invalid after
            # any Focus Mode round-trip (PBI re-renders the whole DOM on return)
            visuals = driver.execute_script(_JS_FIND_VISUALS)
            if idx >= len(visuals):
                print(f"[PBI] Visual {idx + 1} no longer in DOM — stopping")
                break

            visual = visuals[idx]

            # Slicers have no 'Show as a table' — they are scraped separately by
            # extract_slicers_via_dom(). Skip them so they don't get mis-scraped
            # into the visuals list as a garbage table.
            if _is_slicer(visual):
                print(f"[PBI] Visual {idx + 1}/{total}: slicer — skipped "
                      f"(handled by slicer scraper)")
                continue

            title = _get_visual_title(visual)
            print(f"[PBI] Visual {idx + 1}/{total}: '{title}'")

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', inline:'center'});", visual
            )
            time.sleep(0.5)

            # Fire contextmenu via JS — bypasses PBI's synthetic-event block
            driver.execute_script("""
                var el = arguments[0];
                var rect = el.getBoundingClientRect();
                var cx = rect.left + rect.width  / 2;
                var cy = rect.top  + rect.height / 2;
                ['mousedown', 'mouseup', 'contextmenu'].forEach(function(evtName) {
                    el.dispatchEvent(new MouseEvent(evtName, {
                        bubbles: true, cancelable: true, view: window,
                        button: 2, buttons: 2, clientX: cx, clientY: cy
                    }));
                });
            """, visual)
            time.sleep(1.2)

            # Find 'Show as a table' via JS — language/whitespace agnostic
            show_btn = driver.execute_script("""
                var kw = ['show as a table', 'show as table', 'show data'];
                return Array.from(document.querySelectorAll('*')).find(function(el) {
                    if (!el.offsetParent) return false;
                    if (el.children.length > 0) return false;
                    var t = (el.textContent || '').trim().toLowerCase();
                    return kw.indexOf(t) !== -1;
                }) || null;
            """)

            if not show_btn:
                print(f"[PBI]   → 'Show as a table' not in context menu — skipping")
                _dismiss_menu(driver)
                continue

            print(f"[PBI]   → Clicking 'Show as a table'")
            show_btn.click()

            # PBI opens Focus Mode (full page view) — wait for 'Back to report'
            try:
                WebDriverWait(driver, wait_seconds).until(
                    lambda d: d.find_elements(
                        By.XPATH, "//*[contains(text(),'Back to report')]"
                    )
                )
                print(f"[PBI]   → Focus mode loaded")
            except Exception:
                time.sleep(wait_seconds)

            time.sleep(1.5)  # let table fully render

            table_data = _scrape_focus_mode_table(driver)
            if table_data and (table_data.get("headers") or table_data.get("rows")):
                table_data["visual_title"] = title
                results.append(table_data)
                print(f"[PBI]   → {len(table_data.get('rows', []))} row(s) collected")
            else:
                print(f"[PBI]   → Focus mode loaded but no data scraped")

            # Navigate back — waits internally until visuals reappear
            _navigate_back_to_report(driver)

        except Exception as exc:
            print(f"[PBI]   → Error on '{title}': {exc}")
            _navigate_back_to_report(driver)
            continue

    print(f"[PBI] Done — {len(results)} table(s) extracted")
    return results


def _get_visual_title(visual_el) -> str:
    """
    Resolve a visual's display title. PBI stores the title in several different
    DOM shapes depending on the visual type / version, so try them in order of
    reliability. Falls back to the container's aria-label / title attribute
    before giving up.
    """
    selectors = [
        ".visualTitle",
        "[class*='preTextTitle']",
        "[class*='visualTitle']",
        "[class*='titleText']",
        ".visual-title",
        ".title",
    ]
    for selector in selectors:
        try:
            el = visual_el.find_element(By.CSS_SELECTOR, selector)
            text = (el.text or el.get_attribute("title") or "").strip()
            if text:
                return text
        except Exception:
            pass

    # Fallback: aria-label / title attribute on the container itself
    for attr in ("aria-label", "title"):
        try:
            val = (visual_el.get_attribute(attr) or "").strip()
            if val and val.lower() not in ("visual", "chart"):
                return val
        except Exception:
            pass

    return "Untitled Visual"


def _is_slicer(visual_el) -> bool:
    """A visual is a slicer if it contains any element with a 'slicer' class."""
    try:
        return len(visual_el.find_elements(By.CSS_SELECTOR, '[class*="slicer"]')) > 0
    except Exception:
        return False


def extract_slicers_via_dom(driver) -> list:
    """
    Scrape every slicer visual's field name + selected value(s) straight from
    the PBI DOM — no LLM, no screenshot. Returns a list of dicts:
        {slicer_name, selected_value}

    Handles the three common slicer shapes:
      - dropdown  → '.slicer-restatement' text (e.g. 'Africa')
      - date/range → the slicer's <input> values joined (e.g. '1/1/2011 - ...')
      - list      → selected/checked item labels joined by comma
    """
    slicers = driver.execute_script(r"""
        function txt(el){ return ((el.innerText || el.textContent) || '').trim(); }

        var containers = Array.from(document.querySelectorAll(
            'visual-container-modern, visual-container, ' +
            '[class*="visualContainer"], [class*="visual-container"]'
        ));

        var out = [];
        var seen = [];
        containers.forEach(function(c){
            if (seen.indexOf(c) !== -1) return;
            seen.push(c);

            // Only slicer visuals
            if (!c.querySelector('[class*="slicer"]')) return;
            var r = c.getBoundingClientRect();
            if (r.width < 20 || r.height < 20) return;

            // ── field / slicer name ───────────────────────────────────────
            var name = '';
            var hdr = c.querySelector(
                '.slicer-header-text, [class*="slicer-header"], ' +
                '.slicerHeader, [class*="slicerHeader"], [class*="headerText"], ' +
                '.visualTitle, [class*="preTextTitle"], [class*="titleText"]'
            );
            if (hdr) name = txt(hdr);
            if (!name) {
                var al = c.getAttribute('aria-label') || '';
                if (al) name = al.trim();
            }

            // ── selected value(s) ─────────────────────────────────────────
            var value = '';

            // 1) dropdown restatement
            var rest = c.querySelector('.slicer-restatement, [class*="restatement"]');
            if (rest) value = txt(rest);

            // 2) date / numeric range inputs
            if (!value) {
                var inputs = Array.from(c.querySelectorAll('input'))
                    .map(function(i){ return (i.value || '').trim(); })
                    .filter(function(v){ return v.length > 0; });
                if (inputs.length) value = inputs.join(' - ');
            }

            // 3) explicitly selected list items
            if (!value) {
                var sel = Array.from(c.querySelectorAll(
                    '[aria-selected="true"], .slicerItemContainer.selected, ' +
                    '[class*="slicerItemContainer"][aria-checked="true"], li.selected'
                )).map(txt).filter(function(t){ return t.length > 0; });
                if (sel.length) value = sel.join(', ');
            }

            out.push({
                slicer_name:    name || 'Slicer',
                selected_value: value || '(all)'
            });
        });
        return out;
    """)
    print(f"[PBI] Slicers found: {len(slicers or [])}")
    return slicers or []


# ── Filter-sweep support: enumerate slicer values + apply a combination ──────────
#
#  These drive Phase-2 (multi-combination extraction). They are best-effort and
#  PBI-version-specific — verify against the live report and watch the [PBI] logs.

_JS_FIND_SLICER_CONTAINERS = """
    // Primary: the true slicer root '.slicer-container'. The values popup lives
    // separately at the document root as '.slicer-dropdown-popup' and uses
    // '.slicerContainer' (no hyphen), so it is NOT matched here — that removes
    // the phantom duplicate ('REGION (2)').
    var out = Array.from(document.querySelectorAll(
        '.slicer-container, [class*="slicer-container"]'
    )).filter(function(c){
        if (c.closest('.slicer-dropdown-popup, [class*="dropdown-popup"], [class*="dropdownPopup"]'))
            return false;
        var r = c.getBoundingClientRect();
        return r.width >= 20 && r.height >= 20;
    });

    // Fallback for older reports that wrap slicers in visual-containers
    if (!out.length) {
        var containers = Array.from(document.querySelectorAll(
            'visual-container-modern, visual-container, ' +
            '[class*="visualContainer"], [class*="visual-container"]'
        ));
        var seen = [];
        containers.forEach(function(c){
            if (seen.indexOf(c) !== -1) return;
            seen.push(c);
            if (!c.querySelector('[class*="slicer"]')) return;
            var r = c.getBoundingClientRect();
            if (r.width < 20 || r.height < 20) return;
            out.push(c);
        });
    }

    // Collapse nested duplicates (keep outermost per slicer, drop page wrappers)
    out = out.filter(function(el){
        var wraps = out.filter(function(o){ return o !== el && el.contains(o); });
        return wraps.length < 3;
    });
    out = out.filter(function(el){
        return !out.some(function(o){ return o !== el && o.contains(el); });
    });
    return out;
"""


def _slicer_name(container) -> str:
    """Field/label of a slicer container (same heuristics as extract_slicers)."""
    js = """
        var c = arguments[0];
        function txt(el){ return ((el.innerText || el.textContent) || '').trim(); }
        var hdr = c.querySelector(
            '.slicer-header-text, [class*="slicer-header"], ' +
            '.slicerHeader, [class*="slicerHeader"], [class*="headerText"], ' +
            '.visualTitle, [class*="preTextTitle"], [class*="titleText"]'
        );
        if (hdr) { var t = txt(hdr); if (t) return t; }
        return (c.getAttribute('aria-label') || '').trim();
    """
    try:
        return (driver_exec(container, js) or "").strip()
    except Exception:
        return ""


def driver_exec(element, script):
    """Run JS with `element` as arguments[0] using its own parent driver."""
    return element.parent.execute_script(script, element)


# JS predicate: element is actually visible on screen (not a hidden/collapsed node)
_JS_VIS_FN = """
    function vis(el){
        if (!el || el.offsetParent === null) return false;
        var r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
    }
"""

# JS helper: read the value labels inside a scope by drilling to the .slicerText
# leaf nodes (the real value text), falling back to item-container / role=option
# for other slicer layouts. Requires _JS_VIS_FN to be prepended.
_JS_READ_VALUES = """
    function readValues(scope){
        function txt(el){ return ((el.innerText || el.textContent) || '').trim(); }
        if (!scope) return [];
        var nodes = Array.from(scope.querySelectorAll(
            '.slicerText, [class*="slicerText"]'
        )).filter(vis);
        if (!nodes.length) {
            nodes = Array.from(scope.querySelectorAll(
                '.slicerItemContainer, [class*="slicerItemContainer"], [role="option"]'
            )).filter(vis);
        }
        var vals = nodes.map(txt).filter(function(t){
            return t.length > 0 && t.toLowerCase() !== 'select all';
        });
        var seen = {}, out = [];
        vals.forEach(function(v){ if(!seen[v]){ seen[v]=1; out.push(v); } });
        return out;
    }
"""


def _slicer_kind(container) -> str:
    """
    Classify a slicer: 'range' (date/numeric slider — no discrete values) or
    'list' (list or dropdown of selectable values).
    """
    js = """
        var c = arguments[0];
        if (c.querySelector(
            '[class*="slicer-slider"], [class*="numericSlider"], ' +
            '[class*="dateSlicer"], [class*="date-slicer"], [class*="slider"], ' +
            'input[type="date"], input[type="number"]'
        )) return 'range';
        return 'list';
    """
    try:
        return driver_exec(container, js) or "list"
    except Exception:
        return "list"


def _read_visible_options(container) -> list:
    """
    Read option labels that are ACTUALLY VISIBLE in a slicer (list-type). A
    collapsed dropdown keeps its items hidden in the DOM, so filtering on
    visibility makes this return [] for dropdowns → the caller opens them.
    """
    js = _JS_VIS_FN + _JS_READ_VALUES + """
        var c = arguments[0];
        var wrapper = c.querySelector('.slicer-content-wrapper, [class*="slicer-content"]') || c;
        return readValues(wrapper);
    """
    try:
        return driver_exec(container, js) or []
    except Exception:
        return []


def _open_dropdown(container) -> bool:
    """
    Expand a dropdown slicer so its popup renders. The toggle lives inside
    '.slicer-content-wrapper'; click it (or the wrapper itself as fallback).
    """
    js = """
        var c = arguments[0];
        var wrap = c.querySelector('.slicer-content-wrapper, [class*="slicer-content"]') || c;
        var caret = wrap.querySelector(
            '.slicer-dropdown-menu, [class*="dropdown-menu"], [class*="dropdown"], ' +
            '[aria-haspopup="true"]'
        ) || wrap;
        caret.click();
        return true;
    """
    try:
        return bool(driver_exec(container, js))
    except Exception:
        return False


# The values popup is specifically PBI's slicer dropdown popup. Do NOT include
# generic [role="listbox"] / .transform-list here — a chart LEGEND (e.g. the
# Ship Mode visual) matches those and the reader would grab legend items.
_JS_FIND_SLICER_POPUP = _JS_VIS_FN + """
    function _slicerPops(){
        return Array.from(document.querySelectorAll(
            '.slicer-dropdown-popup, [class*="slicer-dropdown-popup"], [class*="dropdownPopup"]'
        )).filter(function(p){
            return vis(p) && p.querySelector(
                '.slicerItemContainer, [class*="slicerItemContainer"], ' +
                '.slicerText, [class*="slicerText"]'
            );
        });
    }
    // The popup belonging to slicer container c: the visible popup best aligned
    // with the slicer (horizontal centre + directly below it). This is robust to
    // PBI REUSING one popup element that it repositions under whichever slicer is
    // open, and to a lingering popup from another slicer (different position).
    function slicerPopupFor(c){
        var pops = _slicerPops();
        if (!pops.length) return null;
        if (!c) return pops[pops.length - 1];
        var cr = c.getBoundingClientRect();
        var best = null, bestD = 1e12;
        pops.forEach(function(p){
            var r = p.getBoundingClientRect();
            // A slicer's popup opens directly UNDER it, so require real
            // horizontal overlap — this rejects a lingering popup from a
            // different slicer (the cause of first-slicer values leaking into
            // the second).
            var overlap = Math.min(r.right, cr.right) - Math.max(r.left, cr.left);
            if (overlap < Math.min(cr.width, r.width) * 0.4) return;
            // And require vertical proximity (popup near the slicer, not far off)
            var vgap = r.top - cr.bottom;               // >0 below, <0 overlapping
            if (vgap > 140 || vgap < -(cr.height + 60)) return;
            var d = Math.abs((r.left + r.width / 2) - (cr.left + cr.width / 2)) * 2
                    + Math.abs(vgap);
            if (d < bestD) { bestD = d; best = p; }
        });
        return best;
    }
    // The scrollable element inside a popup (virtualized lists render on scroll)
    function popupScroller(pop){
        var cs = [pop].concat(Array.from(pop.querySelectorAll('*')));
        for (var i = 0; i < cs.length; i++) {
            if (cs[i].scrollHeight > cs[i].clientHeight + 5) return cs[i];
        }
        return pop;
    }
"""


def _collect_popup_values(driver, container, max_rounds: int = 80) -> list:
    """
    Read ALL values from the slicer's open popup, scrolling to force virtualized
    rows to render and accumulating until no new value appears at the bottom.
    """
    seen = []
    stagnant = 0
    for _ in range(max_rounds):
        vals = driver.execute_script(_JS_READ_VALUES + _JS_FIND_SLICER_POPUP + """
            var pop = slicerPopupFor(arguments[0]);
            return pop ? readValues(pop) : [];
        """, container) or []
        added = 0
        for v in vals:
            if v not in seen:
                seen.append(v)
                added += 1

        at_bottom = driver.execute_script(_JS_FIND_SLICER_POPUP + """
            var pop = slicerPopupFor(arguments[0]);
            if (!pop) return true;
            var sc = popupScroller(pop);
            var before = sc.scrollTop;
            sc.scrollTop = before + Math.max(sc.clientHeight * 0.9, 80);
            return sc.scrollTop <= before;      // could not advance -> at bottom
        """, container)
        time.sleep(0.22)

        stagnant = stagnant + 1 if added == 0 else 0
        if at_bottom and stagnant >= 1:
            break
    return seen


def _wait_popup_open(driver, container, timeout: int = 4) -> bool:
    """Wait until the slicer's dropdown popup (aligned with it) is visible."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(
                _JS_FIND_SLICER_POPUP + "return !!slicerPopupFor(arguments[0]);", container)
        )
        return True
    except Exception:
        return False


def _close_popups(driver, timeout: int = 3):
    """
    Close any open dropdown popup and VERIFY none remains. Retries because a
    single Escape does not always dismiss a PBI slicer popup — and a lingering
    popup is what lets one slicer's values leak into the next.
    """
    for _ in range(4):
        try:
            still_open = bool(driver.execute_script(
                _JS_FIND_SLICER_POPUP + "return !!slicerPopupFor(null);"))
        except Exception:
            still_open = False
        if not still_open:
            return
        _dismiss_menu(driver)          # Escape
        time.sleep(0.35)
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(_JS_FIND_SLICER_POPUP + "return !slicerPopupFor(null);")
        )
    except Exception:
        pass


def _close_dropdown(driver, container):
    """Collapse THIS slicer's own dropdown (click its toggle again) if open."""
    try:
        is_open = bool(driver.execute_script(
            _JS_FIND_SLICER_POPUP + "return !!slicerPopupFor(arguments[0]);", container))
        if is_open:
            _open_dropdown(container)   # toggle → collapses
            time.sleep(0.3)
    except Exception:
        pass


def get_slicer_options(driver, max_per_slicer: int = 60) -> dict:
    """
    Enumerate the available values of every slicer in the report.
    Returns {slicer_name: [value, ...]}.

    Handles list slicers (visible items) and dropdown slicers (opens the popup,
    reads the VISIBLE popup, then closes it before moving on). Range/date
    slicers return [] and are logged as such — enter their values manually.
    """
    containers = driver.execute_script(_JS_FIND_SLICER_CONTAINERS) or []
    options = {}

    for c in containers:
        name = _slicer_name(c) or f"Slicer {len(options) + 1}"

        # Range/date slider — cannot enumerate discrete values
        if _slicer_kind(c) == "range":
            options.setdefault(name, [])
            print(f"[PBI] Slicer '{name}': range/date slider — no discrete "
                  f"values (enter manually)")
            continue

        # List slicer: items already visible
        vals = _read_visible_options(c)

        # Dropdown slicer: open → read the popup aligned with THIS slicer → close
        if not vals:
            _close_popups(driver)                 # ensure no stale popup lingers
            if _open_dropdown(c):
                _wait_popup_open(driver, c)       # wait for this slicer's popup
                vals = _collect_popup_values(driver, c)   # scroll + accumulate ALL
            _close_dropdown(driver, c)            # collapse THIS slicer's dropdown
            _close_popups(driver)                 # verify nothing lingers

        vals = vals[:max_per_slicer]

        # Merge into the same real name rather than inventing 'NAME (2)':
        # two containers for one slicer (header vs content) must not become two
        # keys, or the fabricated name breaks the apply-time lookup.
        if name in options:
            for v in vals:
                if v not in options[name]:
                    options[name].append(v)
        else:
            options[name] = vals

        print(f"[PBI] Slicer '{name}': {len(options[name])} option(s) -> "
              f"{options[name][:5]}{' ...' if len(options[name]) > 5 else ''}")

    return options


def apply_combination(driver, combo: dict, settle_seconds: float = 3.0) -> dict:
    """
    Apply one filter combination — set each named slicer to its value — then
    wait for the report to refresh.

    Each slicer is re-located FRESH right before it is set: applying one slicer
    refreshes the report and can invalidate the DOM references of the others
    (that is why previously only the last/second slicer stuck).

    Args:
        combo — {slicer_name: value_to_select}
    Returns:
        {slicer_name: applied_bool} so the caller can log partial failures.
    """
    result = {}
    for slicer_name, value in combo.items():
        candidates = _find_slicer_candidates(driver, slicer_name)
        if not candidates:
            print(f"[PBI] apply: slicer '{slicer_name}' not found")
            result[slicer_name] = False
            continue

        # Try every container that matches this name until one actually applies
        # (handles duplicate header/content containers for the same slicer).
        ok = False
        for cand in candidates:
            if _select_value(driver, cand, value):
                ok = True
                break
        print(f"[PBI] apply: {slicer_name} = '{value}' -> {'OK' if ok else 'FAILED'} "
              f"({len(candidates)} candidate container(s))")
        result[slicer_name] = ok

        time.sleep(0.8)          # let this slicer's change settle before the next
        _wait_no_spinner(driver)

    time.sleep(settle_seconds)   # final settle before the caller scrapes
    _wait_no_spinner(driver)
    return result


def _base_name(name: str) -> str:
    """Strip a trailing ' (N)' disambiguation suffix and lower-case."""
    return re.sub(r"\s*\(\d+\)\s*$", "", (name or "")).strip().lower()


def _find_slicer_candidates(driver, slicer_name: str) -> list:
    """
    Re-fetch slicer containers (fresh — prior refresh may have invalidated old
    references) and return ALL whose header matches, base-name aware so a combo
    key like 'REGION (2)' still resolves to the real 'REGION' container(s).
    """
    containers = driver.execute_script(_JS_FIND_SLICER_CONTAINERS) or []
    target = _base_name(slicer_name)
    exact = [c for c in containers if _base_name(_slicer_name(c)) == target]
    if exact:
        return exact
    return [c for c in containers
            if target and (target in (_slicer_name(c) or "").lower()
                           or (_slicer_name(c) or "").lower() in target)]


def _select_value(driver, container, value: str) -> bool:
    """
    Select `value` in a slicer — robust to dropdowns, search boxes and
    virtualized/scrollable lists (the reason a long slicer like Region did not
    apply while a short one like Segment did).
    """
    try:
        # 1. Always start clean and open THIS slicer's own fresh popup. Do NOT
        #    gate on _values_visible — a lingering popup from the previous slicer
        #    would otherwise be mistaken for this one's (the SEGMENT-got-REGION
        #    bug), so the dropdown would never actually open.
        _close_popups(driver)
        _open_dropdown(container)
        _wait_popup_open(driver, container)

        # 2. Clear any prior selection — checkbox slicers ACCUMULATE, so without
        #    this each combo would stack on top of the last one's boxes.
        _clear_slicer(driver, container)
        time.sleep(0.5)
        if not _values_visible(container):     # clear may collapse the dropdown
            _open_dropdown(container)
            _wait_popup_open(driver, container)

        # 3. Fast path — value already rendered
        if _click_value(driver, container, value):
            return True

        # 4. Search box (best for long lists) — type to filter, then check
        if _try_search(driver, container, value):
            time.sleep(1.0)
            if _click_value(driver, container, value):
                return True

        # 5. Scroll the list and retry — virtualized rows render on scroll
        for step in range(8):
            _scroll_list(driver, container, step)
            time.sleep(0.3)
            if _click_value(driver, container, value):
                return True

        # Diagnostic — show exactly what the popup contained so a mismatch is
        # obvious (wrong popup, trailing counts, empty popup, etc.)
        avail = driver.execute_script(_JS_READ_VALUES + _JS_FIND_SLICER_POPUP + """
            var pop = slicerPopupFor(arguments[0]);
            return pop ? readValues(pop) : [];
        """, container) or []
        print(f"[PBI] apply: value '{value}' NOT found. Popup had {len(avail)} "
              f"item(s): {avail[:12]}")
        return False
    except Exception as exc:
        print(f"[PBI] apply: error selecting '{value}': {exc}")
        return False
    finally:
        _close_popups(driver)


def _clear_slicer(driver, container) -> bool:
    """
    Reset a slicer's selection using its 'Clear selections' (eraser) control, so
    a fresh single value can be checked without the previous combo's boxes still
    set. Falls back to unchecking every currently-checked visible row.
    """
    try:
        return bool(driver.execute_script(_JS_FIND_SLICER_POPUP + """
            var c = arguments[0];
            // 1) header eraser / clear button (clears ALL, even scrolled-out)
            var btn = c.querySelector(
                '.slicer-clear, [class*="clearSelection"], [class*="clear-selection"], ' +
                '[aria-label*="Clear"], [title*="Clear"], [class*="eraser"]'
            );
            if (btn) { btn.click(); return true; }

            // 2) fallback: uncheck currently-checked visible rows
            function isChecked(row){
                if (row.getAttribute('aria-selected') === 'true') return true;
                if (row.getAttribute('aria-checked')  === 'true') return true;
                var cb = row.querySelector('input[type="checkbox"]');
                if (cb && cb.checked) return true;
                return /(^|\\s)(selected|checked|isSelected)(\\s|$)/.test(row.className || '');
            }
            var scope = slicerPopupFor(c) || c;
            var rows = Array.from(scope.querySelectorAll(
                '.slicerItemContainer, [class*="slicerItemContainer"], [role="option"]'
            )).filter(vis);
            var n = 0;
            rows.forEach(function(row){
                if (isChecked(row)) {
                    (row.querySelector('input[type="checkbox"]') || row).click();
                    n++;
                }
            });
            return n > 0;
        """, container))
    except Exception:
        return False


def _values_visible(container) -> bool:
    """
    True if slicer values are currently rendered — either an open dropdown popup
    (values live there, at the document root) or an always-visible list slicer.
    """
    js = _JS_FIND_SLICER_POPUP + """
        var c = arguments[0];
        // A popup aligned with THIS slicer = its values are visible. Position
        // match avoids counting a lingering popup from a different slicer.
        if (slicerPopupFor(c)) return true;
        // List slicer: values already inside the content wrapper
        var wrapper = c.querySelector('.slicer-content-wrapper, [class*="slicer-content"]') || c;
        var nodes = Array.from(wrapper.querySelectorAll(
            '.slicerText, [class*="slicerText"]'
        )).filter(vis);
        return nodes.length > 0;
    """
    try:
        return bool(driver_exec(container, js))
    except Exception:
        return False


def _click_value(driver, container, value: str) -> bool:
    """
    Ensure the checkbox row whose .slicerText matches `value` is CHECKED.
    Returns True if the row was found (and checked it if it wasn't already).
    Never clicks a target that is already checked — that would toggle it off.
    """
    return bool(driver.execute_script(_JS_FIND_SLICER_POPUP + """
        var c = arguments[0], target = (arguments[1] || '').trim().toLowerCase();
        function txt(el){ return ((el.innerText||el.textContent)||'').trim(); }
        function isChecked(row){
            if (row.getAttribute('aria-selected') === 'true') return true;
            if (row.getAttribute('aria-checked')  === 'true') return true;
            var cb = row.querySelector('input[type="checkbox"]');
            if (cb && cb.checked) return true;
            return /(^|\\s)(selected|checked|isSelected)(\\s|$)/.test(row.className || '');
        }
        var scope = slicerPopupFor(c) || c;
        var wrapper = scope.querySelector('.slicer-content-wrapper, [class*="slicer-content"]') || scope;
        var nodes = Array.from(wrapper.querySelectorAll(
            '.slicerText, [class*="slicerText"]'
        )).filter(vis);
        if (!nodes.length) {
            nodes = Array.from(wrapper.querySelectorAll(
                '.slicerItemContainer, [class*="slicerItemContainer"], [role="option"]'
            )).filter(vis);
        }
        // Tolerant match: exact first, then contains (handles trailing counts /
        // whitespace like 'Consumer (1,234)').
        var idx = -1;
        for (var i = 0; i < nodes.length; i++) {
            if (txt(nodes[i]).toLowerCase() === target) { idx = i; break; }
        }
        if (idx < 0) {
            for (var i = 0; i < nodes.length; i++) {
                var t = txt(nodes[i]).toLowerCase();
                if (t === target || t.indexOf(target) === 0) { idx = i; break; }
            }
        }
        if (idx < 0) return false;

        var row = nodes[idx].closest(
            '.slicerItemContainer, [class*="slicerItemContainer"], [role="option"]'
        ) || nodes[idx];
        row.scrollIntoView({block:'center'});
        if (!isChecked(row)) {
            var box = row.querySelector('input[type="checkbox"]') || row;
            box.click();
        }
        return true;
    """, container, value))


def _try_search(driver, container, value: str) -> bool:
    """Type `value` into the slicer's search box (if present) to filter the list."""
    return bool(driver.execute_script(_JS_FIND_SLICER_POPUP + """
        var c = arguments[0], val = arguments[1];
        var scope = slicerPopupFor(c) || c;
        var box = scope.querySelector(
            'input[type="search"], input[type="text"], input[aria-label*="Search"], ' +
            '[class*="searchInput"] input, input[class*="searchInput"]'
        );
        if (!box) return false;
        box.focus();
        // Native setter so PBI's framework registers the change
        var setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
        setter.call(box, val);
        ['input','change','keyup'].forEach(function(ev){
            box.dispatchEvent(new Event(ev, {bubbles:true}));
        });
        return true;
    """, container, value))


def _scroll_list(driver, container, step: int):
    """Scroll the slicer's scroll area so virtualized rows render."""
    try:
        driver.execute_script(_JS_FIND_SLICER_POPUP + """
            var c = arguments[0], step = arguments[1];
            var pop = slicerPopupFor(c);
            var el = (pop && popupScroller(pop))
                   || c.querySelector('[class*="scroll"], .slicer-content-wrapper, [class*="slicer-content"]')
                   || c;
            el.scrollTop = (step + 1) * Math.max(el.clientHeight * 0.8, 60);
        """, container, step)
    except Exception:
        pass


def _wait_no_spinner(driver, timeout: int = 15):
    """Best-effort wait until PBI's loading spinner disappears."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("""
                var s = document.querySelectorAll(
                    '.circleProgress, [class*="loadingContainer"], ' +
                    '[class*="spinner"], .powerbi-spinner'
                );
                return Array.from(s).every(function(el){
                    var r = el.getBoundingClientRect();
                    return r.width === 0 || r.height === 0;
                });
            """)
        )
    except Exception:
        pass


def _dismiss_menu(driver):
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)
    except Exception:
        pass


def _navigate_back_to_report(driver):
    """
    Exit PBI Focus Mode by clicking 'Back to report'.
    Never calls history.back() — that navigates away from PBI entirely.
    After clicking, waits until visual containers reappear so the next
    iteration gets fresh, valid element references.
    """
    clicked = False

    # Try JS find first
    try:
        back_btn = driver.execute_script("""
            return Array.from(document.querySelectorAll('*')).find(function(el) {
                if (!el.offsetParent) return false;
                var t = (el.textContent || '').trim().toLowerCase();
                return t === 'back to report';
            }) || null;
        """)
        if back_btn:
            back_btn.click()
            clicked = True
    except Exception:
        pass

    # XPath fallback
    if not clicked:
        try:
            btn = driver.find_element(
                By.XPATH, "//*[contains(text(),'Back to report')]"
            )
            btn.click()
            clicked = True
        except Exception:
            pass

    if not clicked:
        print("[PBI]   → 'Back to report' button not found — staying on current page")
        return

    # Wait until visual containers reappear (report fully restored)
    try:
        WebDriverWait(driver, 8).until(
            lambda d: d.execute_script("""
                var found = document.querySelectorAll(
                    'visual-container-modern, visual-container, [class*="visualContainer"]'
                );
                return found.length > 0;
            """)
        )
        print("[PBI]   → Back to report — visuals loaded")
    except Exception:
        time.sleep(2.0)  # fallback wait if WebDriverWait times out


def _scrape_focus_mode_table(driver) -> dict:
    """
    Scrape the data table from PBI Focus Mode.

    Focus Mode layout:
      - Top ~35% of viewport  → chart / visual
      - Bottom ~65% of viewport → data table (column headers + data rows)

    Three strategies tried in order:
      1. role-grid (lower-half scoped):
           Finds all grids then picks the one whose top >= 35% viewport so we
           get the DATA table, not the chart/KPI-card grid at the top.
           hasRowHeader is detected from DATA rows (non-empty rowheader = real
           dimension value like "APAC"; empty placeholder = KPI card).
      2. lower-half position scan:
           Same 35% cutoff. Detects dimension column headers by finding
           rowheader elements at the same Y position as the columnheaders.
      3. class-based: innerText of known PBI table container classes.

    innerText is used throughout (not textContent) so sibling text nodes are
    separated by whitespace and values like "Total Sales$12.64M" cannot occur.
    """
    result = driver.execute_script("""
        var cutoff = window.innerHeight * 0.35;

        function cellText(el) {
            return ((el.innerText || el.textContent) || '').trim();
        }

        // Focus Mode is an OVERLAY — the underlying report page (with its own
        // grids, e.g. the region table) is still laid out in the DOM behind it.
        // elementFromPoint returns the TOPMOST element at a coordinate, so it
        // hits the focus-mode content and skips the hidden background. We use it
        // to (a) find the real focus grid and (b) reject background cells.
        function topGridAt(x, y) {
            var el = document.elementFromPoint(x, y);
            return el ? el.closest('[role="grid"], [role="table"], [role="treegrid"]') : null;
        }
        function isOnTop(el) {
            var r = el.getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) return false;
            var cx = r.left + r.width  / 2;
            var cy = r.top  + r.height / 2;
            var top = document.elementFromPoint(cx, cy);
            return !!top && (el === top || el.contains(top) || top.contains(el));
        }

        // ── Strategy 1: the focus-mode grid that is actually on top ───────────
        var allGrids = Array.from(document.querySelectorAll(
            '[role="grid"], [role="table"], [role="treegrid"]'
        ));

        // Sample points down the lower half; the first on-top grid we hit is the
        // focus-mode table, NOT the background report's grid.
        var focusGrid = null;
        var sampleXs = [window.innerWidth * 0.3, window.innerWidth * 0.5, window.innerWidth * 0.7];
        var sampleYs = [window.innerHeight * 0.55, window.innerHeight * 0.65,
                        window.innerHeight * 0.75, window.innerHeight * 0.88];
        for (var yi = 0; yi < sampleYs.length && !focusGrid; yi++) {
            for (var xi = 0; xi < sampleXs.length && !focusGrid; xi++) {
                var g = topGridAt(sampleXs[xi], sampleYs[yi]);
                if (g) focusGrid = g;
            }
        }

        // Fallbacks only if elementFromPoint found nothing (rare).
        var lowerGrids = allGrids.filter(function(g) {
            var r = g.getBoundingClientRect();
            return r.top >= cutoff && r.height > 30 && r.width > 50;
        });
        var grid = focusGrid
                 ? focusGrid
                 : lowerGrids.length > 0 ? lowerGrids[0]
                 : allGrids.length > 0   ? allGrids[allGrids.length - 1]
                 : null;

        if (grid) {
            var gridRows = Array.from(grid.querySelectorAll('[role="row"]'));

            // Find the first row that owns a columnheader — that is the header row.
            var headerRow = null;
            for (var ri = 0; ri < gridRows.length; ri++) {
                if (gridRows[ri].querySelector('[role="columnheader"]')) {
                    headerRow = gridRows[ri];
                    break;
                }
            }

            // Build column header list (keep rowheader + columnheader from header row
            // so "MARKET" is captured regardless of which ARIA role PBI uses for it).
            var hdrs = headerRow
                ? Array.from(headerRow.querySelectorAll(
                      '[role="rowheader"], [role="columnheader"]'
                  )).map(cellText).filter(function(t) { return t.length > 0; })
                : Array.from(grid.querySelectorAll('[role="columnheader"]'))
                      .map(cellText).filter(function(t) { return t.length > 0; });

            // Detect hasRowHeader from DATA rows (not the header row).
            // PBI uses [role="rowheader"] for dimension values in data rows (e.g. "APAC",
            // "EU") but adds an EMPTY placeholder rowheader in pure-metric tables (KPI
            // cards). Checking rhText.length means:
            //   - "APAC" (len > 0) -> real dimension -> hasRowHeader = true, include it
            //   - ""     (len = 0) -> KPI card placeholder -> skip, collect only gridcells
            // This prevents both bugs:
            //   MARKET chart -> row[0]="APAC", kpi_name="Total Sales [APAC]"
            //   KPI card     -> all 6 gridcells aligned with 6 column headers (no shift)
            var dRows = [];
            var hasRowHeader = false;

            gridRows.forEach(function(row) {
                if (row.querySelector('[role="columnheader"]')) return; // skip header row

                var rhEl    = row.querySelector('[role="rowheader"]');
                var rhText  = rhEl ? cellText(rhEl) : '';
                var gcTexts = Array.from(
                    row.querySelectorAll('[role="gridcell"], [role="cell"]')
                ).map(cellText);

                if (rhText.length > 0) {
                    // Non-empty rowheader = real dimension value (e.g. "APAC", "EU")
                    hasRowHeader = true;
                    dRows.push([rhText].concat(gcTexts));
                } else if (gcTexts.length > 0) {
                    // Empty/absent rowheader = pure metric row (KPI cards) -> gridcells only
                    dRows.push(gcTexts);
                }
                // Both empty -> blank spacer row -> skip
            });

            if (dRows.length > 0) {
                return { headers: hdrs, rows: dRows,
                         has_row_header: hasRowHeader, strategy: 'role-grid+rowheader' };
            }
        }

        // ── Strategy 2: lower-half viewport position scan ─────────────────────
        // Require isOnTop so background-report cells (behind the focus overlay)
        // are excluded — same leak that Strategy 1 now guards against.
        function inTableArea(el) {
            var r = el.getBoundingClientRect();
            return r.top >= cutoff && r.width > 0 && r.height > 0 && isOnTop(el);
        }

        var colHdrs   = Array.from(document.querySelectorAll('[role="columnheader"]')).filter(inTableArea);
        var rowHdrs   = Array.from(document.querySelectorAll('[role="rowheader"]')).filter(inTableArea);
        var dataCells = Array.from(document.querySelectorAll('[role="gridcell"]')).filter(inTableArea);

        if (colHdrs.length > 0) {
            // Rowheader elements at the same Y level as the colHdrs are dimension
            // column HEADERS (e.g. "MARKET"), not data values — separate them out.
            var colHdrTop = Math.min.apply(null, colHdrs.map(function(el) {
                return el.getBoundingClientRect().top;
            }));
            var dimHdrEls = rowHdrs.filter(function(el) {
                return Math.abs(el.getBoundingClientRect().top - colHdrTop) < 6;
            });
            var dataRowHdrs = rowHdrs.filter(function(el) {
                return dimHdrEls.indexOf(el) === -1;
            });

            // Dimension column exists only when a non-empty rowheader sits in the
            // header row (same Y level as the columnheaders).
            var hasRowHeader2 = dimHdrEls.length > 0;

            // Full header list: dimension col(s) first (if any), then metric cols.
            var dimHdrTexts    = dimHdrEls.map(cellText);
            var metricHdrTexts = colHdrs.map(cellText);
            var headers2 = hasRowHeader2
                ? dimHdrTexts.concat(metricHdrTexts)
                : metricHdrTexts;
            var numCols = headers2.length > 0 ? headers2.length : metricHdrTexts.length;

            // Pure-metric tables: skip dataRowHdrs (empty placeholder cells) and
            // use only gridcells so indices align with the metric-only header list.
            var cellSrc = hasRowHeader2
                ? dataRowHdrs.concat(dataCells)
                : dataCells;

            var allCells = cellSrc.sort(function(a, b) {
                var ra = a.getBoundingClientRect();
                var rb = b.getBoundingClientRect();
                var dy = Math.round((ra.top - rb.top) / 5) * 5;
                return dy !== 0 ? dy : ra.left - rb.left;
            }).map(cellText);

            var dataRows2 = [];
            for (var i = 0; i < allCells.length; i += numCols) {
                var chunk = allCells.slice(i, i + numCols);
                if (chunk.some(function(c) { return c.length > 0; })) {
                    dataRows2.push(chunk);
                }
            }

            if (dataRows2.length > 0) {
                return { headers: headers2, rows: dataRows2,
                         has_row_header: hasRowHeader2, strategy: 'lower-half' };
            }
        }

        // ── Strategy 3: PBI class-based table container ───────────────────────
        var tbl = document.querySelector(
            '[class*="dataTable"], [class*="tablixContainer"], ' +
            '[class*="matrixContainer"], [class*="tableContainer"]'
        );
        if (tbl) {
            var lines = (tbl.innerText || tbl.textContent).split('\\n')
                .map(function(l) { return l.trim(); })
                .filter(function(l) { return l.length > 0; });
            if (lines.length > 0) {
                return {
                    headers: [],
                    rows: lines.map(function(l) { return [l]; }),
                    strategy: 'class-innerText'
                };
            }
        }

        return null;
    """)

    if result:
        print(f"[PBI]   → Strategy: {result.get('strategy')} | "
              f"Headers: {result.get('headers')} | "
              f"Rows: {len(result.get('rows', []))}")

    return result or {}
