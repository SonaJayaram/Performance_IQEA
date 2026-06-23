import os
import json
import asyncio
import subprocess
import threading
import pandas as pd
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

import Utils.utils_actions as action_utils
import Utils.Self_healing_utilities as healing_utils
import Utils.self_healing_framework_utilities as healing_framework_utils
import Utils.Self_healing_git_utilities as healing_git_utils
from config.config_reader import framework_source, git_details, get_source

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TigerQE Web Self-Healing",
    page_icon="🤖🛠️",
    layout="centered"
)

# ─── Session state ─────────────────────────────────────────────────────────────
defaults = {
    "page_url":              None,
    "Action_file_Location":  None,
    "Git_pages_Location":    None,
    "driver":                None,
    "recording_started":     False,
    "stop_monitor":          {"stop": False},
    "monitor_thread":        None,
    "actions":               [],
    "self_healing_response": [],
    "validated_df":          None,
    "approved_xpaths":       set(),
    "healing_done":          False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Config ────────────────────────────────────────────────────────────────────
source                                                      = get_source()
xpath_file_path, page_folder_path, _, _                    = framework_source()
git_file_path, git_repo_url, git_branch_name               = git_details()
excel_path   = os.path.join(healing_utils.output_xpath_validate, "validated_xpath.xlsx")
page_folder  = page_folder_path

# ─── Title ─────────────────────────────────────────────────────────────────────
st.title("🤖🛠️ TigerQE Web Self-Healing (AI)")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Action File Input
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("### Step 1: Provide User Workflow")
st.markdown(
    "Enter an existing action file path **or** record a new workflow below. "
    "<span style='color:red;'>*</span>",
    unsafe_allow_html=True
)

action_file_input = st.text_input(
    "Action file location (.txt)",
    value=st.session_state.Action_file_Location or ""
)
if action_file_input:
    st.session_state.Action_file_Location = action_file_input

st.markdown("<span style='color:gray;'>— or record a new workflow —</span>", unsafe_allow_html=True)

with st.expander("🔴 User Workflow Recorder"):
    st.subheader("Record User Actions")
    page_url = st.text_input("Enter the URL to open:")
    st.session_state.page_url = page_url

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🌐 Open Browser"):
            if page_url:
                chrome_options = Options()
                chrome_options.add_argument("--remote-debugging-port=9222")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                st.session_state.driver = webdriver.Chrome(options=chrome_options)
                st.session_state.driver.get(page_url)
                st.session_state.driver.maximize_window()
                WebDriverWait(st.session_state.driver, 30).until(
                    lambda d: action_utils.is_page_loaded(d)
                )
                st.success("✅ Browser opened.")

    with col2:
        if not st.session_state.recording_started and st.button("🎥 Start Recording"):
            if st.session_state.driver:
                st.session_state.actions = []
                action_utils.clear_recorded_actions(st.session_state.driver)
                action_utils.start_recording(st.session_state.driver)
                st.session_state.recording_started = True
                st.session_state.stop_monitor = {"stop": False}
                st.session_state.monitor_thread = threading.Thread(
                    target=action_utils.monitor_url_changes_for_each_nav,
                    args=(st.session_state.driver, st.session_state.stop_monitor),
                    daemon=True
                )
                st.session_state.monitor_thread.start()
                st.success("🎥 Recording started.")

    with col3:
        if st.session_state.recording_started and st.button("🛑 Stop Recording"):
            st.session_state.actions = action_utils.get_recorded_actions(st.session_state.driver)
            st.session_state.recording_started = False
            st.session_state.stop_monitor["stop"] = True
            if st.session_state.monitor_thread:
                st.session_state.monitor_thread.join()
            st.success(f"✅ Captured {len(st.session_state.actions)} actions.")

    if st.session_state.actions:
        page_name = st.text_input("Workflow name (used as filename):")
        if st.button("💾 Save Workflow"):
            if page_name:
                workflow_text = action_utils.generate_workflow(st.session_state.actions)
                filename = os.path.join(healing_utils.Action_collection, f"{page_name}_actions.txt")
                with open(filename, "w") as f:
                    f.write("\n".join(workflow_text))
                st.session_state.Action_file_Location = filename
                st.success(f"✅ Workflow saved: {filename}")
                st.download_button(
                    "⬇ Download Workflow",
                    data="\n".join(workflow_text),
                    file_name=f"{page_name}_actions.txt"
                )
                st.session_state.actions = []

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Page Files Location
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("### Step 2: Page Files Location")
st.markdown(
    "Enter the local folder or GitLab path containing your framework page files. "
    "<span style='color:red;'>*</span>",
    unsafe_allow_html=True
)
git_pages_input = st.text_input(
    "Pages location (local folder or GitLab path)",
    value=st.session_state.Git_pages_Location or ""
)
if git_pages_input:
    st.session_state.Git_pages_Location = git_pages_input

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Run Self-Healing
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("### Step 3: Run Self-Healing")

if st.button("🚀 Start Self-Healing", type="primary"):
    if not st.session_state.Action_file_Location or not st.session_state.Git_pages_Location:
        st.error("❌ Please provide both the action file and pages location.")
    else:
        st.session_state.healing_done   = False
        st.session_state.validated_df   = None
        st.session_state.approved_xpaths = set()

        # ── 3a. Extract XPaths from framework ──────────────────────────────────
        with st.spinner("🔍 Extracting XPaths from framework page files..."):
            if source == "local":
                healing_framework_utils.generate_xpath_doc(
                    xpath_file_path, st.session_state.Git_pages_Location
                )
            else:
                healing_git_utils.generate_xpath_doc(
                    git_repo_url=git_repo_url,
                    git_branch_name=git_branch_name,
                    git_page_folder=st.session_state.Git_pages_Location
                )
        st.success("✅ XPaths extracted from framework.")

        # ── 3b. Generate Playwright DOM collector from action file (no feature file) ──
        with st.spinner("🤖 Generating DOM collector via MCP (direct from action file)..."):
            asyncio.run(healing_utils.main_from_actions(st.session_state.Action_file_Location))
        st.success("✅ Playwright DOM collector script generated.")

        # ── 3c. Run Node.js script to collect live DOM ──────────────────────────
        with st.spinner("🌐 Navigating pages and collecting live DOM..."):
            subprocess.run(['node', healing_utils.SCRIPT_PATH_execution], check=True)
        st.success(f"✅ DOM collected: {healing_utils.dom_file_path}")

        # ── 3d. Load and normalize collected data ───────────────────────────────
        xpath_content_all = healing_utils.read_json_file(healing_utils.xpath_file_path)
        dom_content_all   = healing_utils.read_json_file(healing_utils.dom_file_path)
        xpath_content_dict = healing_utils.normalize_content(xpath_content_all, details_key="xpath_details")
        dom_content_dict   = healing_utils.normalize_content(dom_content_all,   details_key="dom_details")

        # ── 3e. LLM XPath validation per page ──────────────────────────────────
        total_pages  = len(xpath_content_dict)
        progress_bar = st.progress(0)
        progress_txt = st.empty()
        response     = []

        for i, (xpath_page, xpath_details) in enumerate(xpath_content_dict.items(), start=1):
            for dom_page, dom_details in dom_content_dict.items():
                if healing_utils.has_partial_word_match(xpath_page, dom_page):
                    response.append(
                        healing_utils.compare_xpathdetails_dom(xpath_details, dom_details)
                    )
                    break
            progress_bar.progress(i / total_pages)
            progress_txt.text(f"Validating page {i}/{total_pages}: {xpath_page}")

        st.session_state.self_healing_response = response
        progress_txt.text("✅ LLM validation complete.")

        # ── 3f. Save LLM response to Excel ─────────────────────────────────────
        with st.spinner("💾 Saving validation results..."):
            healing_utils.save_ai_response_to_excel(response)

        # ── 3g. Re-verify alternative XPaths programmatically ──────────────────
        with st.spinner("🔬 Re-verifying alternative XPaths against live DOM..."):
            validated_df = healing_utils.verify_alternative_xpaths(excel_path, dom_content_dict)

        st.session_state.validated_df = validated_df
        st.session_state.healing_done = True
        st.success("✅ Self-healing analysis complete. Review results below.")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Review & Approve
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.healing_done and st.session_state.validated_df is not None:
    st.markdown("---")
    st.markdown("### Step 4: Review & Approve Fixes")

    df = st.session_state.validated_df

    # Summary counts
    total   = len(df)
    invalid = len(df[df['Status'].str.lower() == 'invalid'])
    verified = len(df[(df['Status'].str.lower() == 'invalid') & (df['Verified'] == 'Yes')])

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total XPaths",     total)
    col_b.metric("Invalid XPaths",   invalid)
    col_c.metric("Verified Fixes",   f"{verified}/{invalid}")

    st.markdown("**Review invalid XPaths below. Select which fixes to apply.**")

    invalid_df = df[df['Status'].str.lower() == 'invalid'].copy().reset_index(drop=True)

    if invalid_df.empty:
        st.info("ℹ️ No invalid XPaths found — framework is healthy!")
    else:
        # Show colour-coded table
        def highlight_verified(row):
            if row.get("Verified") == "Yes":
                return ['background-color: #d4edda'] * len(row)
            elif row.get("Verified") == "No":
                return ['background-color: #f8d7da'] * len(row)
            return [''] * len(row)

        st.dataframe(
            invalid_df.style.apply(highlight_verified, axis=1),
            use_container_width=True
        )

        st.markdown("**Select fixes to apply:**")

        approved = set()
        for idx, row in invalid_df.iterrows():
            old_xpath = str(row.get("Xpath", "")).strip()
            alt_xpath = str(row.get("Alternative Xpath", "")).strip()
            verified  = row.get("Verified", "N/A")
            page      = row.get("Page", "")
            match_cnt = row.get("Match Count", 0)

            verified_badge = "✅ Verified" if verified == "Yes" else ("⚠️ Unverified" if verified == "No" else "—")
            label = (
                f"**[{page}]** `{old_xpath[:60]}...`  →  `{alt_xpath[:60]}...`  "
                f"{verified_badge} (matches: {match_cnt})"
            )
            if st.checkbox(label, key=f"approve_{idx}", value=(verified == "Yes")):
                approved.add(old_xpath)

        st.session_state.approved_xpaths = approved

        # ── Apply button ────────────────────────────────────────────────────────
        st.markdown("---")
        if approved:
            st.markdown(f"**{len(approved)} fix(es) selected for application.**")
            if st.button("✅ Apply Approved Fixes to Repository", type="primary"):
                with st.spinner("🔧 Applying approved XPath replacements..."):
                    if source == "local":
                        healing_utils.replace_invalid_xpaths(
                            excel_path,
                            page_folder=page_folder,
                            approved_xpaths=approved
                        )
                    else:
                        healing_git_utils.replace_invalid_xpaths(
                            excel_path=excel_path,
                            git_repo_url=git_repo_url,
                            git_branch_name=git_branch_name,
                            git_file_path=st.session_state.Git_pages_Location,
                            approved_xpaths=approved
                        )
                st.success(f"✅ {len(approved)} XPath(s) updated in repository.")
                st.balloons()
        else:
            st.warning("No fixes selected. Tick the checkboxes above to approve fixes.")

    # Full results download
    st.markdown("---")
    with open(excel_path, "rb") as f:
        st.download_button(
            "⬇ Download Full Validation Report (Excel)",
            data=f,
            file_name="validated_xpath.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ─── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
### Contact Us
- Reach us at [QE Core Team](mailto:sahil.gupta@tigeranalytics.com)
""")
