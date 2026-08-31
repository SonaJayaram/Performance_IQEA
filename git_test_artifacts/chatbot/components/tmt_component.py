"""TMT knowledge-base fetch — mirrors the panel's Test Management Integration UI
exactly (Azure Test Plans: direct Test Cases fetch OR Test Plan → suite; and
Jira by project key). Fetches existing test cases so the flow can gap-analyse.

Uses `chat_tmt_*` session keys so it never clashes with the panel's `tmt_*`.
Returns {"done": True, "existing": [...], "tool": "Azure Test Plans"|"Jira"|None}.
"""
import streamlit as st

from utilities.TMT_Connection import Test_management_tool_utils as tmt_utils


def _init():
    ss = st.session_state
    ss.setdefault("chat_tmt_connected", False)
    ss.setdefault("chat_tmt_plans", [])
    ss.setdefault("chat_tmt_suites", [])
    ss.setdefault("chat_tmt_plan_id", None)
    ss.setdefault("chat_tmt_suite_id", None)
    ss.setdefault("chat_tmt_tcs", None)


def render_tmt_fetch(key_prefix="tmt", slots=None):
    _init()
    ss = st.session_state
    k = key_prefix

    st.caption("Connect Azure Test Plans or Jira and fetch existing test cases — "
               "I'll gap-analyse and only add what's missing.")

    tool = st.radio("Test Management Tool", ["Azure Test Plans", "Jira"],
                    horizontal=True, key=f"{k}_tool")

    # ---------- Azure Test Plans ----------
    if tool == "Azure Test Plans":
        c1, c2 = st.columns(2)
        c1.text_input("Organization URL", value="https://dev.azure.com/QE-Practice-team",
                      key=f"{k}_org", disabled=True)
        c2.text_input("Project", value="qe-practice", key=f"{k}_proj", disabled=True)

        fetch_type = st.selectbox(
            "Fetch Type", ["Test Cases", "Test Plan"], key=f"{k}_ftype",
            help="'Test Cases' = direct fetch (no Test Plans licence needed). "
                 "'Test Plan' = fetch via a specific plan and suite.")

        if fetch_type == "Test Cases":
            if st.button("📥 Fetch Test Cases Directly", key=f"{k}_fa"):
                with st.spinner("Fetching test cases from project..."):
                    try:
                        ss.chat_tmt_tcs = tmt_utils.get_all_testcases_direct()
                        st.success(f"✅ Fetched {len(ss.chat_tmt_tcs)} test case(s).")
                    except Exception as e:
                        st.error(f"❌ Fetch failed: {e}")
        else:
            if st.button("🔌 Connect & Fetch Test Plans", key=f"{k}_cp"):
                with st.spinner("Fetching test plans..."):
                    try:
                        ss.chat_tmt_plans = tmt_utils.get_test_plans()
                        ss.chat_tmt_connected = True
                        st.success(f"✅ Connected — {len(ss.chat_tmt_plans)} plan(s).")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {e}")
                        ss.chat_tmt_connected = False

            if ss.chat_tmt_connected and ss.chat_tmt_plans:
                plan_opts = {p["name"]: p["id"] for p in ss.chat_tmt_plans}
                plan_name = st.selectbox("Select Test Plan", list(plan_opts.keys()), key=f"{k}_plan")
                ss.chat_tmt_plan_id = plan_opts[plan_name]

                scope = st.radio("Scope", ["All Suites", "Specific Suite"], horizontal=True, key=f"{k}_scope")
                if scope == "Specific Suite":
                    if st.button("Load Suites", key=f"{k}_ls"):
                        ss.chat_tmt_suites = tmt_utils.get_test_suites(ss.chat_tmt_plan_id)
                    if ss.chat_tmt_suites:
                        suite_opts = {s["name"]: s["id"] for s in ss.chat_tmt_suites}
                        suite_name = st.selectbox("Select Suite", list(suite_opts.keys()), key=f"{k}_suite")
                        ss.chat_tmt_suite_id = suite_opts[suite_name]
                else:
                    ss.chat_tmt_suite_id = None

                if st.button("📥 Fetch Existing Test Cases", key=f"{k}_fp"):
                    with st.spinner("Fetching existing test cases..."):
                        try:
                            if ss.chat_tmt_suite_id:
                                ss.chat_tmt_tcs = tmt_utils.get_testcases_from_suite(
                                    ss.chat_tmt_plan_id, ss.chat_tmt_suite_id)
                            else:
                                ss.chat_tmt_tcs = tmt_utils.get_all_testcases_from_plan(ss.chat_tmt_plan_id)
                            st.success(f"✅ Fetched {len(ss.chat_tmt_tcs)} test case(s).")
                        except Exception as e:
                            st.error(f"❌ Failed to fetch: {e}")

    # ---------- Jira ----------
    else:
        project = st.text_input("Jira Project Key (e.g. QA)", key=f"{k}_jproj")
        if st.button("📥 Fetch Jira Test Cases", key=f"{k}_fj"):
            with st.spinner("Fetching Jira test cases..."):
                try:
                    ss.chat_tmt_tcs = tmt_utils.get_jira_testcases((project or "").strip())
                    st.success(f"✅ Fetched {len(ss.chat_tmt_tcs)} Jira test case(s).")
                except Exception as e:
                    st.error(f"❌ Jira fetch failed: {e}")

    # ---------- confirm / skip ----------
    tcs = ss.chat_tmt_tcs
    if tcs is not None:
        st.info(f"📋 {len(tcs)} existing test case(s) loaded — gap analysis will run before generation.")
        with st.expander("Preview existing test cases", expanded=False):
            for tc in tcs[:10]:
                st.write(f"**{tc.get('id')}** — {tc.get('title')}")
            if len(tcs) > 10:
                st.caption(f"…and {len(tcs) - 10} more")
        b1, b2 = st.columns(2)
        if b1.button("Use these ✅", key=f"{k}_use", type="primary"):
            existing = list(tcs)
            _reset(ss)
            return {"done": True, "existing": existing, "tool": tool,
                    "summary": f"Using {len(existing)} existing test case(s) as knowledge base."}
        if b2.button("Skip", key=f"{k}_skip"):
            _reset(ss)
            return {"done": True, "existing": [], "tool": None, "summary": "Skipped TMT knowledge base."}
    else:
        if st.button("Skip — no knowledge base", key=f"{k}_skip0"):
            _reset(ss)
            return {"done": True, "existing": [], "tool": None, "summary": "Skipped TMT knowledge base."}

    return {"done": False}


def _reset(ss):
    for key in ("chat_tmt_connected", "chat_tmt_plans", "chat_tmt_suites",
                "chat_tmt_plan_id", "chat_tmt_suite_id", "chat_tmt_tcs"):
        ss.pop(key, None)
