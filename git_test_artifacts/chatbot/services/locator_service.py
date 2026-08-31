"""Locators / POM flow — headless backend for the chat agent.

Wraps the same functions the IQEA Locator/POM panel uses:
  get_visible_element_iframe / get_visible_element_powerBi  → live-DOM scrape
  get_queries_from_ai("Web"|"PowerBi")                      → xpath variations
  selecting_xpath + filter_duplicate_xpaths                 → parse + dedupe
  adding_selected_xapth_excel                               → persist selection
  generate_pom_from_excel_with_action + get_queries_from_ai("Page_File")
  create_java_file                                          → write page object
"""
import os
import streamlit as st

import utilities.Utilities_Xpath as utils


# -- browser ---------------------------------------------------------------
def open_browser(url):
    """Open (or reuse) a Chrome session at `url`. Stored on st.session_state.driver
    so it's shared with the recorder/POM panels — one browser across the app."""
    clean = (url or "").strip()
    if clean and not clean.startswith(("http://", "https://")):
        clean = "https://" + clean

    drv = st.session_state.get("driver")
    if drv is not None:
        try:
            _ = drv.current_url            # probe: is it still alive?
            drv.get(clean)
            return drv
        except Exception:
            pass                           # dead handle -> make a new one

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.wait import WebDriverWait

    opts = Options()
    for arg in ("--disable-gpu", "--disable-software-rasterizer",
                "--remote-debugging-port=9222", "--no-sandbox",
                "--remote-allow-origins=*", "--disable-dev-shm-usage"):
        opts.add_argument(arg)

    driver = webdriver.Chrome(options=opts)
    driver.get(clean)
    driver.maximize_window()
    try:
        WebDriverWait(driver, 30).until(utils.is_page_loaded)
    except Exception:
        pass
    st.session_state.driver = driver
    return driver


# -- extraction ------------------------------------------------------------
def extract_xpaths(app_type, tags):
    """Scrape the current page and return {element_label: [xpath, ...]}."""
    driver = st.session_state.get("driver")
    if driver is None:
        raise RuntimeError("No browser session — open a URL first.")

    page_id = driver.current_url
    if app_type == "PowerBi":
        summary = utils.get_visible_element_powerBi(driver, page_id)
        response = utils.get_queries_from_ai("PowerBi", summary)
    else:
        summary = utils.get_visible_element_iframe(driver, page_id, tags or [])
        response = utils.get_queries_from_ai("Web", summary)

    if not response:
        return {}
    return utils.filter_duplicate_xpaths(utils.selecting_xpath(response))


def flatten(xpath_dict):
    """Flatten {element: [xpath,...]} to [{'element','xpath'}, ...] for the picker."""
    out = []
    for element, xpaths in (xpath_dict or {}).items():
        for xp in xpaths:
            if xp and xp.strip():
                out.append({"element": element, "xpath": xp.strip()})
    return out


# -- persist + generate ----------------------------------------------------
def save_selected(items, page_name):
    """Persist the chosen locators to the shared xpath workbook."""
    st.session_state.selected_xpaths = list(items)
    utils.adding_selected_xapth_excel(page_name)


def generate_page_object(page_name, language, action_data=""):
    """Generate + write the Page Object file. Returns the written file path."""
    prompt = utils.generate_pom_from_excel_with_action(language, page_name, language, action_data)
    response = utils.get_queries_from_ai("Page_File", prompt)
    utils.create_java_file(page_name, language, response)

    ext = "java" if language.startswith("Java") else "py"
    return os.path.join(utils.Page_file_generator, f"{page_name}.{ext}")
