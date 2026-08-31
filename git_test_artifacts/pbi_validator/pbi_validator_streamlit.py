import io
import json
import os
import re
import sys
import time
import zipfile
from datetime import datetime

import openai
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ── Path setup so sibling utilities are importable ────────────────────────────
_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)
for _p in (_THIS_DIR, _PARENT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

load_dotenv(os.path.join(_PARENT_DIR, ".env"))

from utils.pbi_browser   import (apply_combination, extract_kpis_via_llm,
                                  extract_slicers_via_dom, get_slicer_options,
                                  is_driver_alive, start_browser, take_screenshot,
                                  try_show_as_table)
from utils.combinations   import (build_combinations, combo_filename, combo_label,
                                   total_possible)
from utils.sql_generator  import (generate_reference_queries, read_requirements_file,
                                   reference_queries_to_df, df_to_reference_queries,
                                   build_combination_queries, adapt_sql_dialect,
                                   qualify_table_names)
from utils.db_connector   import build_connection_string, execute_query, test_connection
from utils.comparator     import (build_validation_df, compare_values, export_to_excel,
                                  export_visuals_workbook, parse_kpi_name,
                                  match_kpi_to_query, match_kpi_to_queries,
                                  extract_db_value, llm_match_fallback, tables_to_kpis)
from utils               import pipeline, script_gen

# ── Output folder ─────────────────────────────────────────────────────────────
_OUTPUT_DIR = os.path.join(_THIS_DIR, "output", "reports")
os.makedirs(_OUTPUT_DIR, exist_ok=True)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="PBI Validator", page_icon="📊", layout="wide")

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS = {
    "pbi_driver":             None,
    "pbi_extracted_kpis":     [],
    "pbi_table_results":      [],
    "pbi_slicers":            [],
    "pbi_slicer_options":     {},
    "pbi_sweep_manifest":     [],
    "pbi_sweep_zip":          None,
    "pbi_sweep_run_dir":      "",
    "pbi_sweep_data":         [],
    "pbi_slicer_col_map":     {},
    "pbi_combo_val_results":  [],
    "pbi_screenshot_b64":     None,
    "pbi_screenshot_bytes":   None,
    "pbi_reference_queries":  [],       # KPI-driven (visual-wise) set — Tab 3 "Run Validation"
    "pbi_slicer_base_queries": [],      # placeholder base queries — Tab 3 "Run Combination Validation"
    "pbi_validation_results": [],
    "pbi_conn_string":        "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── LLM factory ───────────────────────────────────────────────────────────────
def _get_llm():
    return openai.OpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )


def _visuals_from_extracted(table_results, extracted_kpis):
    """
    Build a [{name, headers}] visuals list to ground the KPI-driven (visual-wise)
    SQL generation in what was actually extracted in Step 1.

    Prefers the raw per-visual table structure (headers as scraped); otherwise
    reconstructs one "visual" per visual_name by collecting its KPI metric names
    as pseudo-headers. This keeps generation to ONE query per visual — covering
    all of that visual's KPI values — instead of one query per value.
    """
    visuals = []
    if table_results:
        for t in table_results:
            hdrs = t.get("headers") or t.get("columns", [])
            visuals.append({"name": t.get("visual_title", "Table"),
                            "headers": [str(h) for h in hdrs]})
        return visuals

    # Fallback: group extracted KPIs by visual_name, headers = metric names
    grouped = {}
    for k in (extracted_kpis or []):
        vt = (k.get("visual_type") or "").lower()
        if vt in ("slicer", "filter"):
            continue
        vname = k.get("visual_name", "") or "Visual"
        metric, _dim = parse_kpi_name(k.get("kpi_name", ""))
        grouped.setdefault(vname, [])
        if metric and metric not in grouped[vname]:
            grouped[vname].append(metric)
    return [{"name": name, "headers": hdrs} for name, hdrs in grouped.items()]


# Validation orchestration now lives in utils.pipeline — the single source of
# truth shared with the generated standalone scripts (kept as this alias so the
# existing call sites don't change).
_validate_kpi_list = pipeline.validate_kpi_list


# ── Tab-2 helpers (shared by both query generators) ───────────────────────────
def _read_requirements(uploaded_req, manual_req):
    """Combine an uploaded requirements doc and pasted text into one string."""
    text = ""
    if uploaded_req:
        try:
            text = read_requirements_file(uploaded_req)
        except Exception as exc:
            st.error(f"Could not read requirements file: {exc}")
    if manual_req and manual_req.strip():
        text += "\n" + manual_req
    return text


def _split_csv(val):
    s = str(val).strip()
    if not s or s == "nan":
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


# Bound-parameter / placeholder tokens (:name, {{name}}, ${name}) that the KPI
# flow must NOT contain — they are unbindable at execution → UNBOUND_SQL_PARAMETER.
_SQL_PARAM_RE = re.compile(r"(?<![:\w]):[A-Za-z_]\w*|\{\{\s*\w+\s*\}\}|\$\{\s*\w+\s*\}")


def _find_sql_params(queries):
    """Return {query_name: [param_tokens]} for any query carrying bound params."""
    flagged = {}
    for q in queries or []:
        toks = sorted(set(_SQL_PARAM_RE.findall(q.get("sql_query", "") or "")))
        if toks:
            flagged[q.get("query_name", "?")] = toks
    return flagged


def _render_query_editor(session_key, key_prefix, dl_filename, save_msg):
    """
    Render the shared review/edit/save/download editor for a list of reference
    queries held in st.session_state[session_key]. Used by BOTH the KPI-driven
    set and the slicer base-query set so they stay independent but look alike.
    """
    queries = st.session_state.get(session_key) or []
    if not queries:
        return
    st.caption(
        "Edit any field directly. metric_columns and kpi_patterns use comma-separated "
        "values. card→one row result; table→result grouped by dimension_column."
    )
    _display_rows = []
    for _q in queries:
        mc = _q.get("metric_columns", [])
        kp = _q.get("kpi_patterns", [])
        _display_rows.append({
            "query_name":       _q.get("query_name", ""),
            "visual_type":      _q.get("visual_type", "card"),
            "sql_query":        _q.get("sql_query", ""),
            "dimension_column": _q.get("dimension_column") or "",
            "metric_columns":   ", ".join(mc) if isinstance(mc, list) else str(mc),
            "kpi_patterns":     ", ".join(kp) if isinstance(kp, list) else str(kp),
            "description":      _q.get("description", ""),
        })
    edited_ref = st.data_editor(
        pd.DataFrame(_display_rows),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "query_name":       st.column_config.TextColumn("Query Name",    width="medium"),
            "visual_type":      st.column_config.TextColumn("Type",          width="small"),
            "sql_query":        st.column_config.TextColumn("SQL Query",      width="large"),
            "dimension_column": st.column_config.TextColumn("Dimension Col",  width="medium"),
            "metric_columns":   st.column_config.TextColumn("Metric Columns", width="medium"),
            "kpi_patterns":     st.column_config.TextColumn("KPI Patterns",   width="medium"),
            "description":      st.column_config.TextColumn("Description",    width="medium"),
        },
        key=f"{key_prefix}_editor",
    )
    col_save_sql, col_dl_sql, _ = st.columns([1, 1, 3])
    with col_save_sql:
        if st.button("💾 Save Queries", type="primary",
                     use_container_width=True, key=f"{key_prefix}_save"):
            updated = []
            for _, row in edited_ref.iterrows():
                updated.append({
                    "query_name":       str(row.get("query_name", "")),
                    "visual_type":      str(row.get("visual_type", "card")),
                    "sql_query":        str(row.get("sql_query", "")),
                    "dimension_column": str(row.get("dimension_column", "")) or None,
                    "metric_columns":   _split_csv(row.get("metric_columns", "")),
                    "kpi_patterns":     _split_csv(row.get("kpi_patterns", "")),
                    "description":      str(row.get("description", "")),
                })
            st.session_state[session_key] = updated
            st.success(save_msg)
    with col_dl_sql:
        _ref_df = reference_queries_to_df(st.session_state[session_key])
        st.download_button(
            "📥 Save as CSV",
            data=_ref_df.to_csv(index=False).encode("utf-8"),
            file_name=dl_filename,
            mime="text/csv",
            use_container_width=True,
            key=f"{key_prefix}_dl",
        )


# ── Slicer-flow session bundle (save / load whole sweep as one JSON file) ──────
# The sweep flow's inputs live only in session_state (per-combo tables, slicers,
# slicer→column map, base queries). A single self-describing JSON bundle lets a
# user reload an entire sweep session next time and go straight to Step 3.
_BUNDLE_KEYS = (
    "pbi_extracted_kpis",
    "pbi_table_results",
    "pbi_slicers",
    "pbi_sweep_data",
    "pbi_slicer_col_map",
    "pbi_slicer_base_queries",
)


def _build_session_bundle() -> bytes:
    payload = {"version": 1,
               "data": {k: st.session_state.get(k) for k in _BUNDLE_KEYS}}
    return json.dumps(payload, default=str, indent=2).encode("utf-8")


def _restore_session_bundle(raw) -> int:
    payload = json.loads(raw)
    data = payload.get("data", payload)  # tolerate a bare {key: value} map
    restored = 0
    for k in _BUNDLE_KEYS:
        if k in data and data[k] is not None:
            st.session_state[k] = data[k]
            restored += 1
    return restored


# ── Script generation helpers ─────────────────────────────────────────────────
_SCRIPT_README = (
    "PBI Validator — generated scripts ({flow} flow)\n"
    "================================================\n\n"
    "Run order (all headless, no Streamlit, no LLM):\n"
    "  1. python step1_extract.py  extract_inputs.xlsx\n"
    "  2. (step2_queries.py holds your reviewed queries — imported by step 3)\n"
    "  3. python step3_validate.py validate_inputs.xlsx\n\n"
    "Before running: open step1_extract.py and fill in the login() stub with your\n"
    "Power BI authentication. Edit the *_inputs.xlsx workbooks for URL / DB creds\n"
    "and (Flow 2) the Combinations sheet — one row per test case.\n"
)


def _default_flow():
    return "slicer" if st.session_state.get("pbi_sweep_data") else "kpi"


def _db_settings_from_session():
    return {
        "db_type":   st.session_state.get("pbi_db_type", "databricks"),
        "host":      st.session_state.get("pbi_db_host", ""),
        "port":      st.session_state.get("pbi_db_port", ""),
        "database":  st.session_state.get("pbi_db_name", ""),
        "user":      st.session_state.get("pbi_db_user", ""),
        "password":  st.session_state.get("pbi_db_pass", ""),
        "http_path": st.session_state.get("pbi_db_http_path", ""),
        "catalog":   st.session_state.get("pbi_db_catalog", ""),
        "schema":    st.session_state.get("pbi_db_schema_name", ""),
        "tolerance": st.session_state.get("pbi_tolerance", 0.1),
    }


def _combos_from_sweep():
    return [cd.get("combo") for cd in (st.session_state.get("pbi_sweep_data") or [])
            if cd.get("combo")]


def _script_bundle_zip(flow):
    """All 3 scripts + input workbooks + README for `flow`, as a ZIP."""
    url = st.session_state.get("pbi_url_input", "")
    if flow == "slicer":
        s2 = script_gen.build_queries_script(
            "slicer", st.session_state.get("pbi_slicer_base_queries", []),
            st.session_state.get("pbi_slicer_col_map", {}))
        ecfg, ecombos = script_gen.extract_inputs("slicer", url, _combos_from_sweep())
    else:
        s2 = script_gen.build_queries_script(
            "kpi", st.session_state.get("pbi_reference_queries", []))
        ecfg, ecombos = script_gen.extract_inputs("kpi", url)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("step1_extract.py",  script_gen.build_extract_script(flow))
        z.writestr("step2_queries.py",  s2)
        z.writestr("step3_validate.py", script_gen.build_validate_script(flow))
        z.writestr("extract_inputs.xlsx",  pipeline.inputs_to_bytes(ecfg, ecombos))
        z.writestr("validate_inputs.xlsx",
                   pipeline.inputs_to_bytes(script_gen.validate_inputs(_db_settings_from_session())))
        z.writestr("README.txt", _SCRIPT_README.format(flow=flow))
    return buf.getvalue()


_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _render_script_expander(step):
    """Per-tab 'Generate Script' section. step ∈ {extract, queries, validate}."""
    titles = {"extract": "Step 1 · Extraction",
              "queries": "Step 2 · Reviewed queries (direct copy)",
              "validate": "Step 3 · Validation"}
    with st.expander(f"🧩 Generate script — {titles[step]}", expanded=False):
        st.caption("Standalone, runnable script — no Streamlit, no LLM. Inputs come "
                   "from an Excel workbook you edit (URL / DB creds / test cases).")
        flow_label = st.radio(
            "Flow", ["Flow 1 · KPI (unfiltered)", "Flow 2 · Slicer (combinations)"],
            index=0 if _default_flow() == "kpi" else 1,
            horizontal=True, key=f"scriptflow_{step}",
        )
        flow = "kpi" if flow_label.startswith("Flow 1") else "slicer"
        url  = st.session_state.get("pbi_url_input", "")

        if step == "extract":
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "📄 step1_extract.py", data=script_gen.build_extract_script(flow),
                    file_name="step1_extract.py", mime="text/x-python",
                    use_container_width=True, key="dl_s1")
            with c2:
                cfg, combos = (script_gen.extract_inputs("slicer", url, _combos_from_sweep())
                               if flow == "slicer" else script_gen.extract_inputs("kpi", url))
                st.download_button(
                    "📊 extract_inputs.xlsx", data=pipeline.inputs_to_bytes(cfg, combos),
                    file_name="extract_inputs.xlsx", mime=_XLSX_MIME,
                    use_container_width=True, key="dl_s1cfg")
            if flow == "slicer":
                st.caption(f"Combinations sheet pre-filled with "
                           f"{len(_combos_from_sweep())} test case(s) from your sweep.")

        elif step == "queries":
            if flow == "slicer":
                queries = st.session_state.get("pbi_slicer_base_queries", [])
                s2 = script_gen.build_queries_script(
                    "slicer", queries, st.session_state.get("pbi_slicer_col_map", {}))
            else:
                queries = st.session_state.get("pbi_reference_queries", [])
                s2 = script_gen.build_queries_script("kpi", queries)
            if not queries:
                st.warning("No reviewed queries for this flow yet — generate & save them "
                           "in Step 2 first.")
            st.download_button(
                "📄 step2_queries.py", data=s2, file_name="step2_queries.py",
                mime="text/x-python", use_container_width=True, key="dl_s2",
                disabled=not queries)

        else:  # validate
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "📄 step3_validate.py", data=script_gen.build_validate_script(flow),
                    file_name="step3_validate.py", mime="text/x-python",
                    use_container_width=True, key="dl_s3")
            with c2:
                st.download_button(
                    "📊 validate_inputs.xlsx",
                    data=pipeline.inputs_to_bytes(script_gen.validate_inputs(_db_settings_from_session())),
                    file_name="validate_inputs.xlsx", mime=_XLSX_MIME,
                    use_container_width=True, key="dl_s3cfg")
            st.markdown("---")
            st.download_button(
                "📦 Download all 3 scripts + inputs (ZIP)", data=_script_bundle_zip(flow),
                file_name=f"pbi_scripts_{flow}.zip", mime="application/zip",
                type="primary", use_container_width=True, key="dl_bundle")


# ── Shared styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
.pbi-header {
    padding: 20px 0 14px 0;
}
.pbi-header h1 {
    font-size: 30px;
    font-weight: 900;
    color: #1B2A4A;
    margin-bottom: 4px;
}
.pbi-header p {
    font-size: 15px;
    color: #666;
    font-weight: 500;
    margin: 0;
}
.step-badge {
    display: inline-block;
    background: #F47B20;
    color: white;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    line-height: 28px;
    text-align: center;
    font-weight: 800;
    font-size: 14px;
    margin-right: 8px;
}
.section-title {
    font-size: 18px;
    font-weight: 700;
    color: #1B2A4A;
    margin: 16px 0 8px 0;
}
.info-box {
    background: #FFF8F3;
    border-left: 4px solid #F47B20;
    padding: 10px 14px;
    border-radius: 4px;
    font-size: 14px;
    color: #444;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="pbi-header">
    <h1>📊 PBI Data Validator</h1>
    <p>Extract KPIs from Power BI UI &nbsp;→&nbsp; Generate SQL from Requirements
       &nbsp;→&nbsp; Validate UI vs Database</p>
    <hr style="border:2px solid #F47B20; width:60px; margin:10px 0 0 0;">
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🌐  Step 1 · Extract KPIs",
    "🧠  Step 2 · Generate SQL",
    "✅  Step 3 · Validate",
])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — EXTRACT KPIs
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    # ── Load KPIs from a previous session ─────────────────────────────────────
    with st.expander("📂 Load KPIs from a previous extraction", expanded=False):
        st.caption("Upload a CSV saved from an earlier session to skip re-extraction.")
        prev_kpi_file = st.file_uploader(
            "KPI CSV file",
            type=["csv"],
            key="pbi_prev_kpi_file",
            label_visibility="collapsed",
        )
        if prev_kpi_file is not None:
            try:
                df_prev = pd.read_csv(prev_kpi_file)
                st.dataframe(df_prev, use_container_width=True, height=180)
                if st.button("✅ Use this data", type="primary", key="pbi_load_prev_kpis_btn"):
                    st.session_state.pbi_extracted_kpis = df_prev.to_dict("records")
                    st.success(f"✅ Loaded {len(df_prev)} KPIs from file.")
                    st.rerun()
            except Exception as exc:
                st.error(f"Could not read file: {exc}")

    # ── Load a full slicer-sweep session (JSON bundle) ────────────────────────
    with st.expander("📂 Load a saved sweep session (JSON)", expanded=False):
        st.caption("Restore a whole filter-sweep session — extracted KPIs, per-combo "
                   "tables, slicers, slicer→column map and base queries — saved from "
                   "an earlier run. Populates Steps 1 & 2 so you can go straight to Step 3.")
        prev_bundle = st.file_uploader(
            "Sweep session JSON",
            type=["json"],
            key="pbi_prev_bundle_file",
            label_visibility="collapsed",
        )
        if prev_bundle is not None and st.button(
            "✅ Load session", type="primary", key="pbi_load_bundle_btn"
        ):
            try:
                n = _restore_session_bundle(prev_bundle.getvalue())
                st.success(f"✅ Restored {n} section(s) from the sweep session.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not read session file: {exc}")

    st.markdown('<p class="section-title">Open Power BI Report</p>', unsafe_allow_html=True)

    col_url, col_btn = st.columns([4, 1])
    with col_url:
        pbi_url = st.text_input(
            "Power BI Report URL",
            placeholder="https://app.powerbi.com/reportEmbed?reportId=...",
            label_visibility="collapsed",
            key="pbi_url_input",
        )
    with col_btn:
        open_btn = st.button("🌐 Open Browser", use_container_width=True)

    if open_btn:
        if not pbi_url:
            st.warning("Please enter a Power BI report URL first.")
        else:
            with st.spinner("Launching Chrome..."):
                try:
                    if st.session_state.pbi_driver and is_driver_alive(st.session_state.pbi_driver):
                        st.session_state.pbi_driver.quit()
                    st.session_state.pbi_driver = start_browser(pbi_url)
                    st.success(
                        "✅ Browser is open. **Log into Power BI** in the browser window, "
                        "navigate to the report page you want to validate, then come back here."
                    )
                except Exception as exc:
                    st.error(f"Could not open browser: {exc}")

    # Show status badge
    if st.session_state.pbi_driver and is_driver_alive(st.session_state.pbi_driver):
        st.markdown(
            '<div class="info-box">🟢 Browser is active. '
            'Make sure the report is fully loaded before extracting.</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown('<p class="section-title">Extract KPIs from Current View</p>',
                    unsafe_allow_html=True)

        extraction_mode = st.radio(
            "Extraction method",
            [
                "📸  Screenshot + LLM  (best for KPI cards & trend tiles)",
                "📋  Show as Table  (best for charts, bar graphs, tables)",
            ],
            horizontal=True,
            key="pbi_extraction_mode",
        )

        col_ext, col_ss = st.columns(2)
        with col_ext:
            extract_btn = st.button(
                "🔍 Extract KPIs Now", type="primary",
                use_container_width=True, key="pbi_extract_btn"
            )
        with col_ss:
            screenshot_btn = st.button(
                "📷 Refresh Screenshot Only",
                use_container_width=True, key="pbi_ss_btn"
            )

        if screenshot_btn:
            try:
                png, b64 = take_screenshot(st.session_state.pbi_driver)
                st.session_state.pbi_screenshot_b64   = b64
                st.session_state.pbi_screenshot_bytes = png
                st.rerun()
            except Exception as exc:
                st.error(f"Screenshot failed: {exc}")

        if extract_btn:
            try:
                with st.spinner("Taking screenshot..."):
                    png, b64 = take_screenshot(st.session_state.pbi_driver)
                    st.session_state.pbi_screenshot_b64   = b64
                    st.session_state.pbi_screenshot_bytes = png

                kpis    = []
                slicers = []

                if "Show as Table" in extraction_mode:
                    with st.spinner("Reading slicer selections from the report..."):
                        slicers = extract_slicers_via_dom(st.session_state.pbi_driver)

                    with st.spinner("Extracting tables from each visual (opens Focus Mode per visual)..."):
                        table_results = try_show_as_table(st.session_state.pbi_driver)

                    # Keep the raw per-visual table structure for visual-wise export
                    st.session_state.pbi_table_results = table_results or []

                    if table_results:
                        seen_kpi_names = set()  # dedup guard — skip KPIs already collected

                        for tbl in table_results:
                            cols           = tbl.get("headers") or tbl.get("columns", [])
                            rows           = tbl.get("rows", [])
                            visual_name    = tbl.get("visual_title", "Table")
                            has_row_header = tbl.get("has_row_header", True)

                            for row in rows:
                                if not row:
                                    continue

                                if has_row_header and len(cols) > 1:
                                    row_id = row[0] if row else ""
                                    for col_idx in range(1, len(cols)):
                                        if col_idx < len(row) and row[col_idx]:
                                            kpi_name = f"{cols[col_idx]} [{row_id}]"
                                            if kpi_name not in seen_kpi_names:
                                                seen_kpi_names.add(kpi_name)
                                                kpis.append({
                                                    "visual_name": visual_name,
                                                    "kpi_name":    kpi_name,
                                                    "value":       row[col_idx],
                                                    "value_type":  "number",
                                                    "visual_type": "table",
                                                })

                                elif not has_row_header and cols:
                                    for col_idx in range(len(cols)):
                                        if col_idx < len(row) and row[col_idx]:
                                            kpi_name = cols[col_idx]
                                            if kpi_name not in seen_kpi_names:
                                                seen_kpi_names.add(kpi_name)
                                                kpis.append({
                                                    "visual_name": visual_name,
                                                    "kpi_name":    kpi_name,
                                                    "value":       row[col_idx],
                                                    "value_type":  "number",
                                                    "visual_type": "card",
                                                })

                                else:
                                    kpi_name = cols[0] if cols else "Value"
                                    if kpi_name not in seen_kpi_names:
                                        seen_kpi_names.add(kpi_name)
                                        kpis.append({
                                            "visual_name": visual_name,
                                            "kpi_name":    kpi_name,
                                            "value":       row[0] if row else "",
                                            "value_type":  "number",
                                            "visual_type": "table",
                                        })

                        st.success(f"✅ Extracted {len(kpis)} KPIs from visual tables.")
                    else:
                        st.info("No 'Show as table' option found — falling back to Screenshot + LLM.")
                        with st.spinner("LLM reading KPIs from screenshot..."):
                            kpis, slicers = extract_kpis_via_llm(b64, _get_llm())
                        st.success(f"✅ LLM extracted {len(kpis)} KPIs from screenshot.")

                else:
                    with st.spinner("LLM reading KPIs from screenshot (this may take ~15 s)..."):
                        kpis, slicers = extract_kpis_via_llm(b64, _get_llm())
                    st.success(f"✅ LLM extracted {len(kpis)} KPIs from screenshot.")

                st.session_state.pbi_extracted_kpis = kpis
                st.session_state.pbi_slicers        = slicers
                st.rerun()

            except Exception as exc:
                st.error(f"Extraction failed: {exc}")

        # Show screenshot preview
        if st.session_state.pbi_screenshot_bytes:
            with st.expander("📷 Current Screenshot", expanded=False):
                st.image(st.session_state.pbi_screenshot_bytes, use_container_width=True)

        # Show / edit extracted KPIs
        if st.session_state.pbi_extracted_kpis:
            st.markdown("---")
            st.markdown(
                f'<p class="section-title">Review Extracted KPIs '
                f'({len(st.session_state.pbi_extracted_kpis)} found)</p>',
                unsafe_allow_html=True,
            )

            if st.session_state.pbi_slicers:
                slicer_tags = " &nbsp;|&nbsp; ".join(
                    f"<strong>{s['slicer_name']}</strong>: {s['selected_value']}"
                    for s in st.session_state.pbi_slicers
                )
                st.markdown(
                    f'<div class="info-box">🔍 Active Filters detected — '
                    f'these will be applied as WHERE conditions in the generated SQL: '
                    f'{slicer_tags}</div>',
                    unsafe_allow_html=True,
                )

            st.caption("Edit, add, or delete rows before proceeding to SQL generation.")

            edited_df = st.data_editor(
                pd.DataFrame(st.session_state.pbi_extracted_kpis),
                num_rows="dynamic",
                use_container_width=True,
                key="pbi_kpi_editor",
            )

            col_save, col_clear, col_dl, _ = st.columns([1, 1, 1, 1])
            with col_save:
                if st.button("💾 Save & Proceed →", type="primary",
                             use_container_width=True, key="pbi_save_kpis"):
                    st.session_state.pbi_extracted_kpis = edited_df.to_dict("records")
                    st.success("✅ KPIs saved. Head to **Step 2** to generate SQL.")
            with col_clear:
                if st.button("🗑️ Clear All", use_container_width=True, key="pbi_clear_kpis"):
                    st.session_state.pbi_extracted_kpis = []
                    st.rerun()
            with col_dl:
                csv_bytes = pd.DataFrame(
                    st.session_state.pbi_extracted_kpis
                ).to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Save as CSV",
                    data=csv_bytes,
                    file_name="kpi_extraction.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="pbi_dl_kpis",
                )
                st.success("✅ KPIs successfully downloaded as CSV.")

            # ── Visual-wise Excel workbook (one sheet per visual + Slicers) ──
            _tbls = st.session_state.pbi_table_results
            if _tbls:
                st.markdown("---")
                st.markdown(
                    f'<div class="info-box">📗 <strong>Visual-wise workbook</strong> — '
                    f'{len(_tbls)} visual sheet(s) + 1 Slicers sheet, each in the '
                    f'visual\'s native table shape.</div>',
                    unsafe_allow_html=True,
                )
                if st.session_state.pbi_slicers:
                    _slicer_tags = " &nbsp;|&nbsp; ".join(
                        f"<strong>{s.get('slicer_name','')}</strong>: "
                        f"{s.get('selected_value','')}"
                        for s in st.session_state.pbi_slicers
                    )
                    st.markdown(
                        f'<div class="info-box">🔍 Slicers captured: {_slicer_tags}</div>',
                        unsafe_allow_html=True,
                    )
                workbook_bytes = export_visuals_workbook(
                    _tbls, st.session_state.pbi_slicers
                )
                st.download_button(
                    "📗 Download Visual-wise Workbook (.xlsx)",
                    data=workbook_bytes,
                    file_name="pbi_visuals_extraction.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet"
                    ),
                    type="primary",
                    use_container_width=True,
                    key="pbi_dl_workbook",
                )

        # ══ Filter Combination Sweep (Phase 2) ═══════════════════════════════
        st.markdown("---")
        st.markdown('<p class="section-title">Filter Combination Sweep</p>',
                    unsafe_allow_html=True)
        st.markdown(
            '<div class="info-box">Extract the report under multiple slicer '
            'combinations. Detect slicer values → choose how many combinations to '
            'run → sweep. Each combination produces one visual-wise workbook; all '
            'are bundled with a manifest.</div>',
            unsafe_allow_html=True,
        )

        _sweep_ready = bool(st.session_state.pbi_extracted_kpis)
        if not _sweep_ready:
            st.caption("🔒 Extract & review KPIs above first — the sweep unlocks once "
                       "KPIs exist.")

        if st.button("🔎 Detect Slicer Options", use_container_width=True,
                     key="pbi_detect_slicers"):
            with st.spinner("Reading slicer values from the report..."):
                try:
                    st.session_state.pbi_slicer_options = get_slicer_options(
                        st.session_state.pbi_driver
                    )
                    st.success(
                        f"✅ Detected {len(st.session_state.pbi_slicer_options)} slicer(s)."
                    )
                except Exception as exc:
                    st.error(f"Slicer detection failed: {exc}")

        if st.session_state.pbi_slicer_options:
            st.caption(
                "Review / edit values per slicer (comma-separated). Add values for "
                "slicers that can't be auto-detected — e.g. Date."
            )
            _opt_rows = [
                {"slicer": k, "values": ", ".join(v)}
                for k, v in st.session_state.pbi_slicer_options.items()
            ]
            _edited_opts = st.data_editor(
                pd.DataFrame(_opt_rows),
                num_rows="dynamic",
                use_container_width=True,
                key="pbi_opts_editor",
            )

            # Rebuild the {slicer: [values]} dict from the edited table
            options = {}
            for _, r in _edited_opts.iterrows():
                name = str(r.get("slicer", "")).strip()
                if not name or name.lower() == "nan":
                    continue
                raw  = str(r.get("values", ""))
                vals = [x.strip() for x in raw.split(",")
                        if x.strip() and x.strip().lower() != "nan"]
                options[name] = vals

            _varyable = [k for k, v in options.items() if v]

            c1, c2, c3 = st.columns(3)
            with c1:
                vary = st.multiselect("Slicers to vary", _varyable,
                                      default=_varyable, key="pbi_vary")
            with c2:
                strategy = st.selectbox("Selection", ["diverse", "first"],
                                        key="pbi_strategy")
            with c3:
                count = st.number_input("Combination count", min_value=1,
                                        max_value=200, value=10, step=1,
                                        key="pbi_count")

            _vary_opts = {k: options[k] for k in vary}
            _tot       = total_possible(_vary_opts)
            combos     = build_combinations(_vary_opts, int(count), strategy)
            # The report's DEFAULT (no filter applied by us) is always extracted
            # first as its own baseline, so total = combinations + 1.
            st.info(
                f"{_tot} total possible combination(s) — this sweep will run "
                f"**{len(combos)} + 1 default = {len(combos) + 1}** extraction(s)."
            )
            with st.expander("👁️ Preview combinations", expanded=False):
                st.dataframe(
                    pd.DataFrame([{"combination": "Default (no filter)"}]
                                 + [{"combination": combo_label(c), **c} for c in combos]),
                    use_container_width=True,
                )

            if st.button("▶️ Run Sweep", type="primary", use_container_width=True,
                         key="pbi_run_sweep"):
                if not combos:
                    st.warning("No combinations to run — add slicer values first.")
                else:
                    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
                    run_dir  = os.path.join(_OUTPUT_DIR, f"sweep_{ts}")
                    os.makedirs(run_dir, exist_ok=True)
                    manifest = []

                    # Default baseline first (empty combo → no slicer changes),
                    # then every generated combination.
                    runs      = [{}] + combos
                    sweep_data = []          # per-combo tables for later validation
                    prog      = st.progress(0)
                    status    = st.empty()

                    for i, combo in enumerate(runs):        # i == 0 → default
                        is_default = not combo
                        label = "Default (no filter)" if is_default else combo_label(combo)
                        status.info(f"Run {i + 1}/{len(runs)} — {label}")
                        row = {"combination": label, **combo}
                        try:
                            # Default run captures the report as-loaded; combos
                            # apply their slicer values first.
                            applied = ({} if is_default
                                       else apply_combination(st.session_state.pbi_driver, combo))
                            tbls  = try_show_as_table(st.session_state.pbi_driver) or []
                            slic  = extract_slicers_via_dom(st.session_state.pbi_driver)
                            wb    = export_visuals_workbook(tbls, slic)
                            fname = "00_default.xlsx" if is_default else combo_filename(combo, i)
                            with open(os.path.join(run_dir, fname), "wb") as fh:
                                fh.write(wb)
                            row.update({
                                "applied_ok":    True if is_default else
                                                 (all(applied.values()) if applied else False),
                                "visual_sheets": len(tbls),
                                "file":          fname,
                                "error":         "",
                            })
                            # Keep the raw tables so Step 3 can validate this
                            # combination against the DB without re-reading xlsx.
                            sweep_data.append({
                                "label": label,
                                "combo": dict(combo),
                                "file":  fname,
                                "tables": tbls,
                            })
                        except Exception as exc:
                            row.update({"applied_ok": False, "visual_sheets": 0,
                                        "file": "", "error": str(exc)})
                        manifest.append(row)
                        prog.progress((i + 1) / len(runs))

                    pd.DataFrame(manifest).to_csv(
                        os.path.join(run_dir, "manifest.csv"), index=False
                    )

                    # Bundle the whole run folder into an in-memory ZIP
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                        for root, _, files in os.walk(run_dir):
                            for fn in files:
                                z.write(os.path.join(root, fn), arcname=fn)

                    st.session_state.pbi_sweep_zip      = buf.getvalue()
                    st.session_state.pbi_sweep_manifest = manifest
                    st.session_state.pbi_sweep_run_dir  = run_dir
                    st.session_state.pbi_sweep_data     = sweep_data
                    prog.empty()
                    status.empty()
                    st.success(f"✅ Sweep complete — {len(runs)} workbook(s) "
                               f"(1 default + {len(combos)} combinations) saved to {run_dir}")
                    # NOTE: no st.rerun() — results render below from session_state.

    else:
        st.markdown(
            '<div class="info-box">Enter a Power BI report URL above and click '
            '<strong>Open Browser</strong> to get started.</div>',
            unsafe_allow_html=True,
        )

    # ── Sweep results + bundle download ──────────────────────────────────────
    # Rendered OUTSIDE the driver-alive branch so it always shows once a sweep
    # has run, and wrapped in a fragment so clicking Download reruns ONLY this
    # block — not the whole app — which is what previously "restarted" the page
    # (the driver-alive check flickered false mid-navigation and hid everything).
    @st.fragment
    def _render_sweep_results():
        if not st.session_state.pbi_sweep_manifest:
            return
        st.markdown("---")
        st.markdown('<p class="section-title">Filter Sweep Results</p>',
                    unsafe_allow_html=True)
        if st.session_state.pbi_sweep_run_dir:
            st.caption(f"Saved to: {st.session_state.pbi_sweep_run_dir}")
        st.dataframe(
            pd.DataFrame(st.session_state.pbi_sweep_manifest),
            use_container_width=True,
        )
        col_zip, col_bundle = st.columns(2)
        with col_zip:
            if st.session_state.pbi_sweep_zip:
                st.download_button(
                    "📦 Download All Workbooks + Manifest (ZIP)",
                    data=st.session_state.pbi_sweep_zip,
                    file_name="pbi_filter_sweep.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                    key="pbi_dl_sweep",
                )
        with col_bundle:
            st.download_button(
                "💾 Save Sweep Session (JSON)",
                data=_build_session_bundle(),
                file_name="pbi_sweep_session.json",
                mime="application/json",
                use_container_width=True,
                key="pbi_dl_bundle",
                help="Reload later via '📂 Load a saved sweep session' at the top of "
                     "Step 1 to restore Steps 1 & 2 and jump to Step 3.",
            )

    _render_sweep_results()

    st.markdown("---")
    _render_script_expander("extract")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — GENERATE SQL
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    # ── Load reference queries from a previous session ────────────────────────
    with st.expander("📂 Load reference queries from a previous session", expanded=False):
        st.caption("Upload a reference queries CSV saved from an earlier session to skip re-generation.")
        prev_sql_file = st.file_uploader(
            "Reference queries CSV file",
            type=["csv"],
            key="pbi_prev_sql_file",
            label_visibility="collapsed",
        )
        if prev_sql_file is not None:
            try:
                df_sql_prev = pd.read_csv(prev_sql_file)
                st.dataframe(df_sql_prev, use_container_width=True, height=180)
                if st.button("✅ Use this data", type="primary", key="pbi_load_prev_sql_btn"):
                    queries = df_to_reference_queries(df_sql_prev)
                    st.session_state.pbi_reference_queries = queries
                    st.success(f"✅ Loaded {len(queries)} reference quer(ies) from file.")
                    st.rerun()
            except Exception as exc:
                st.error(f"Could not read file: {exc}")

    st.markdown("---")
    st.markdown('<p class="section-title">Upload Requirements Document</p>',
                unsafe_allow_html=True)

    col_file, col_text = st.columns(2)
    with col_file:
        uploaded_req = st.file_uploader(
            "Requirements file (Word / PDF / Excel / TXT)",
            type=["docx", "pdf", "xlsx", "xls", "txt"],
            key="pbi_req_upload",
        )
    with col_text:
        manual_req = st.text_area(
            "Or paste requirements directly",
            height=160,
            placeholder=(
                "Describe the KPIs, their business logic, and which tables/columns "
                "they come from…"
            ),
            key="pbi_manual_req",
        )

    st.markdown('<p class="section-title">Database Schema (optional but recommended)</p>',
                unsafe_allow_html=True)
    db_schema_text = st.text_area(
        "Paste relevant table and column definitions",
        height=110,
        placeholder="e.g.  sales(id, amount, date, region_id)  |  products(id, name, price)",
        key="pbi_db_schema",
    )

    st.markdown("---")
    # ── KPI-name summary from Step 1 ─────────────────────────────────────────
    _all_kpis  = st.session_state.pbi_extracted_kpis
    _slicers   = [k for k in _all_kpis
                  if (k.get("visual_type") or "").lower() in ("slicer", "filter")]
    _kpi_names = list(dict.fromkeys(
        k.get("kpi_name", "").strip()
        for k in _all_kpis
        if (k.get("visual_type") or "").lower() not in ("slicer", "filter")
        and k.get("kpi_name", "").strip()
    ))

    if _slicers:
        slicer_summary = " | ".join(
            f"**{s.get('kpi_name','')}** = {s.get('value','')}" for s in _slicers
        )
        st.info(f"Slicers detected: {slicer_summary}. **The KPI flow (Section A) "
                f"ignores these** — validate a filtered report via the slicer flow "
                f"(Section B + Step 1 sweep) instead.")
    if _kpi_names:
        st.caption(f"{len(_kpi_names)} unique KPI metric names from Step 1 will guide query generation.")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION A — KPI-driven (visual-wise) generation  [existing/restored flow]
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown('<p class="section-title">🅰️ KPI-driven generation (from Step 1 extraction)</p>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="info-box">Generates <strong>one unfiltered query per visual</strong> '
        '(one LLM call each), grounded in the KPIs extracted in Step 1 — covering every '
        'extracted value without a query-per-value token blow-up. <strong>No slicer '
        'filters are applied</strong> — use the slicer flow (Section B) for filtered '
        'reports. Validate via Step 3 → <em>Run Validation</em>.</div>',
        unsafe_allow_html=True,
    )
    _visuals_a = _visuals_from_extracted(st.session_state.pbi_table_results, _all_kpis)
    if _visuals_a:
        st.caption(f"{len(_visuals_a)} visual(s) detected from Step 1 → "
                   f"{len(_visuals_a)} query(ies), one LLM call each.")
    else:
        st.caption("No extracted KPIs yet — run Step 1 (or load a KPI CSV above) to "
                   "enable KPI-driven generation.")

    if st.button("🧠 Generate KPI-driven Queries", type="primary",
                 key="pbi_gen_kpi_sql", disabled=not _visuals_a):
        requirements_text = _read_requirements(uploaded_req, manual_req)

        # ONE LLM call per visual — small, reliable outputs. Orchestration lives
        # in utils.pipeline (shared with the generated scripts).
        prog   = st.progress(0)
        status = st.empty()

        def _gen_progress(i, n, label):
            status.info(f"Generating query {i + 1}/{n} — {label or 'visual'}")
            prog.progress(min((i + 1) / n, 1.0))

        ref_queries, failures = pipeline.generate_kpi_queries(
            st.session_state.pbi_table_results, _all_kpis,
            requirements_text, db_schema_text or "", progress=_gen_progress,
        )
        prog.empty()
        status.empty()

        st.session_state.pbi_reference_queries = ref_queries
        if ref_queries:
            st.success(f"✅ Generated {len(ref_queries)} query(ies) from "
                       f"{len(_visuals_a)} visual(s) — one LLM call per visual.")
        if failures:
            st.warning("Some visuals could not be generated:\n\n- "
                       + "\n- ".join(failures))
        # Safety net: the KPI flow must be filter-free. If the LLM slipped in a
        # bound parameter it would fail EVERY row with UNBOUND_SQL_PARAMETER, so
        # surface it now and let the user edit/regenerate rather than run blind.
        _flagged = _find_sql_params(ref_queries)
        if _flagged:
            _lines = "\n".join(f"- **{n}**: `{', '.join(t)}`"
                               for n, t in _flagged.items())
            st.error(
                "⚠️ These queries still contain bound parameters/placeholders, "
                "which fail on execution. Edit them below (remove the WHERE/"
                "parameter) or regenerate:\n\n" + _lines
            )
        # No st.rerun(): the editor below renders from the freshly-set state so
        # the success / per-visual failure messages stay visible.

    if st.session_state.pbi_reference_queries:
        st.markdown(
            f'<p class="section-title">Review & Edit KPI-driven Queries — '
            f'{len(st.session_state.pbi_reference_queries)} query(ies)</p>',
            unsafe_allow_html=True,
        )
        _render_query_editor(
            "pbi_reference_queries", "pbi_ref_query", "reference_queries.csv",
            "✅ Reference queries saved. Head to **Step 3 → Run Validation**.",
        )

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION B — Slicer / combination base queries  [separate flow]
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown('<p class="section-title">🅱️ Slicer / combination base queries</p>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="info-box">Generates <strong>base</strong> per-visual queries '
        'with a <code>{SLICER_CONDITIONS}</code> placeholder — each combination\'s '
        'filters are injected as WHERE at validation time. Use with a Filter '
        'Combination Sweep from Step 1 (Step 3 → <em>Run Combination Validation</em>).</div>',
        unsafe_allow_html=True,
    )

    with st.expander("📂 Load slicer base queries from a previous session", expanded=False):
        st.caption("Upload a slicer base-queries CSV saved earlier to skip re-generation.")
        prev_base_file = st.file_uploader(
            "Slicer base queries CSV", type=["csv"],
            key="pbi_prev_base_file", label_visibility="collapsed",
        )
        if prev_base_file is not None:
            try:
                _dfb = pd.read_csv(prev_base_file)
                st.dataframe(_dfb, use_container_width=True, height=160)
                if st.button("✅ Use this data", type="primary", key="pbi_load_prev_base_btn"):
                    st.session_state.pbi_slicer_base_queries = df_to_reference_queries(_dfb)
                    st.success(f"✅ Loaded {len(st.session_state.pbi_slicer_base_queries)} "
                               f"base query(ies).")
                    st.rerun()
            except Exception as exc:
                st.error(f"Could not read file: {exc}")

    _sweep_data = st.session_state.pbi_sweep_data
    if _sweep_data:
        # Slicer → DB column mapping (defaults slicer name → itself)
        _slicer_names = list(dict.fromkeys(
            k for d in _sweep_data for k in d.get("combo", {}).keys()
        ))
        if _slicer_names:
            st.caption("Map each slicer to its DB column (used to build WHERE "
                       "conditions per combination).")
            _existing = st.session_state.pbi_slicer_col_map or {}
            _map_rows = [{"slicer": s, "db_column": _existing.get(s, s.lower())}
                         for s in _slicer_names]
            _map_edit = st.data_editor(
                pd.DataFrame(_map_rows), use_container_width=True,
                key="pbi_slicer_map_editor", hide_index=True,
            )
            st.session_state.pbi_slicer_col_map = {
                str(r["slicer"]): str(r["db_column"]).strip()
                for _, r in _map_edit.iterrows()
                if str(r.get("slicer", "")).strip()
            }
        _visuals_b = [{"name": t.get("visual_title", ""),
                       "headers": t.get("headers") or t.get("columns", [])}
                      for t in _sweep_data[0].get("tables", [])]
        _combo_kpi_names = list(dict.fromkeys(
            parse_kpi_name(k["kpi_name"])[0]
            for k in tables_to_kpis(_sweep_data[0].get("tables", []))
        ))
    else:
        st.caption("No filter sweep captured in Step 1. You can still generate base "
                   "queries, but combination validation in Step 3 needs a sweep "
                   "(or a loaded sweep session).")
        _visuals_b = _visuals_from_extracted(st.session_state.pbi_table_results, _all_kpis)
        _combo_kpi_names = _kpi_names

    if st.button("🧠 Generate Slicer Base Queries", type="primary",
                 key="pbi_gen_base_sql"):
        requirements_text = _read_requirements(uploaded_req, manual_req)
        with st.spinner("LLM generating base SQL queries with slicer placeholder…"):
            try:
                base_queries = generate_reference_queries(
                    requirements_text, db_schema_text or "",
                    slicers=None, kpi_names=_combo_kpi_names,
                    use_slicer_placeholder=True, visuals=_visuals_b or None,
                )
                st.session_state.pbi_slicer_base_queries = base_queries
                st.success(f"✅ Generated {len(base_queries)} base query(ies).")
                st.rerun()
            except Exception as exc:
                st.error(f"Base SQL generation failed: {exc}")

    if st.session_state.pbi_slicer_base_queries:
        st.markdown(
            f'<p class="section-title">Review & Edit Slicer Base Queries — '
            f'{len(st.session_state.pbi_slicer_base_queries)} query(ies)</p>',
            unsafe_allow_html=True,
        )
        _render_query_editor(
            "pbi_slicer_base_queries", "pbi_base_query", "slicer_base_queries.csv",
            "✅ Base queries saved. Head to **Step 3 → Run Combination Validation**.",
        )

    st.markdown("---")
    _render_script_expander("queries")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — VALIDATE
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    if not st.session_state.pbi_reference_queries \
            and not st.session_state.pbi_slicer_base_queries:
        st.markdown(
            '<div class="info-box">⚠️ No reference queries found. '
            'Generate <strong>KPI-driven</strong> and/or <strong>slicer base</strong> '
            'queries in <strong>Step 2</strong> first.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<p class="section-title">Database Connection</p>',
                    unsafe_allow_html=True)

        col_db1, col_db2, col_db3 = st.columns(3)
        with col_db1:
            db_type = st.selectbox(
                "DB Type",
                ["postgresql", "mysql", "mssql", "sqlite", "databricks"],
                key="pbi_db_type",
            )

        is_databricks = db_type == "databricks"

        with col_db1:
            if is_databricks:
                db_host = st.text_input(
                    "Server Hostname",
                    placeholder="adb-1234567890.7.azuredatabricks.net",
                    key="pbi_db_host",
                )
            else:
                db_host = st.text_input("Host", value="localhost", key="pbi_db_host")
                db_port = st.text_input("Port", value="5432",      key="pbi_db_port")

        with col_db2:
            if is_databricks:
                db_http_path = st.text_input(
                    "HTTP Path",
                    placeholder="/sql/1.0/warehouses/abc123...",
                    key="pbi_db_http_path",
                )
                db_pass = st.text_input(
                    "Access Token",
                    type="password",
                    placeholder="dapi...",
                    key="pbi_db_pass",
                )
                db_catalog = st.text_input(
                    "Catalog (optional)",
                    placeholder="hive_metastore",
                    key="pbi_db_catalog",
                )
                db_schema  = st.text_input(
                    "Schema (optional)",
                    placeholder="default",
                    key="pbi_db_schema_name",
                )
                # unused for databricks but keep variables defined
                db_name = ""
                db_user = ""
                db_port = ""
            else:
                db_name = st.text_input("Database Name", key="pbi_db_name")
                db_user = st.text_input("Username",      key="pbi_db_user")
                db_pass = st.text_input("Password", type="password", key="pbi_db_pass")
                db_http_path = ""
                db_catalog   = ""
                db_schema    = ""

        with col_db3:
            tolerance = st.number_input(
                "Tolerance (%)",
                min_value=0.0, max_value=10.0, value=0.1, step=0.05,
                help="Max acceptable % difference between UI and DB value.",
                key="pbi_tolerance",
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔌 Test Connection", use_container_width=True, key="pbi_test_conn"):
                conn_str = build_connection_string(
                    db_type, db_host, db_port, db_name, db_user, db_pass,
                    http_path=db_http_path, catalog=db_catalog, schema=db_schema,
                )
                ok, msg = test_connection(conn_str)
                if ok:
                    st.session_state.pbi_conn_string = conn_str
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

        # ── KPI-driven (single-state) validation — uses pbi_reference_queries ──
        if st.session_state.pbi_reference_queries:
            _ready_kpis    = len(st.session_state.pbi_extracted_kpis)
            _ready_visuals = len(st.session_state.pbi_reference_queries)
            st.markdown("---")
            st.markdown(
                f'<p class="section-title">🅰️ KPI Validation — '
                f'{_ready_kpis} KPIs across {_ready_visuals} visual(s)</p>',
                unsafe_allow_html=True,
            )

            run_btn = st.button("▶️ Run Validation", type="primary", key="pbi_run_val")

            if run_btn:
                if not st.session_state.pbi_conn_string:
                    st.session_state.pbi_conn_string = build_connection_string(
                        db_type, db_host, db_port, db_name, db_user, db_pass,
                        http_path=db_http_path, catalog=db_catalog, schema=db_schema,
                    )

                with st.spinner("Matching KPIs, running queries, comparing…"):
                    results = _validate_kpi_list(
                        st.session_state.pbi_conn_string,
                        st.session_state.pbi_extracted_kpis,
                        st.session_state.pbi_reference_queries,
                        tolerance, _get_llm(), db_type=db_type,
                        catalog=db_catalog, schema=db_schema,
                    )
                st.session_state.pbi_validation_results = results
                # KPI validation and combination validation are separate flows —
                # showing one clears the other from view.
                st.session_state.pbi_combo_val_results = []
                st.rerun()

        # ── Combination (filter-sweep) validation ────────────────────────────
        _sweep_data = st.session_state.pbi_sweep_data
        if _sweep_data:
            st.markdown("---")
            st.markdown(
                f'<p class="section-title">Combination Validation — '
                f'{len(_sweep_data)} combination(s) from the sweep</p>',
                unsafe_allow_html=True,
            )
            _col_map = st.session_state.pbi_slicer_col_map or {}
            st.caption(
                "Each combination's slicer values are injected into the "
                "**slicer base queries** (Step 2 · Section B) at the "
                "{SLICER_CONDITIONS} placeholder. Slicer→column map: "
                f"{_col_map or '(defaults to slicer name)'}"
            )
            if not st.session_state.pbi_slicer_base_queries:
                st.warning("No slicer base queries yet — generate them in "
                           "**Step 2 · Section B** before running combination validation.")

            if st.button("▶️ Run Combination Validation", type="primary",
                         key="pbi_run_combo_val",
                         disabled=not st.session_state.pbi_slicer_base_queries):
                if not st.session_state.pbi_conn_string:
                    st.session_state.pbi_conn_string = build_connection_string(
                        db_type, db_host, db_port, db_name, db_user, db_pass,
                        http_path=db_http_path, catalog=db_catalog, schema=db_schema,
                    )
                prog   = st.progress(0)
                status = st.empty()

                def _combo_progress(i, n, label):
                    status.info(f"Validating {i + 1}/{n} — {label}")
                    prog.progress(min((i + 1) / n, 1.0))

                # Combination orchestration lives in utils.pipeline (shared with
                # the generated scripts).
                all_results = pipeline.validate_combinations(
                    st.session_state.pbi_conn_string, _sweep_data,
                    st.session_state.pbi_slicer_base_queries, _col_map,
                    tolerance, _get_llm(), db_type=db_type,
                    catalog=db_catalog, schema=db_schema, progress=_combo_progress,
                )
                prog.empty()
                status.empty()
                st.session_state.pbi_combo_val_results = all_results
                # Clear the KPI-validation view — the two flows are mutually exclusive.
                st.session_state.pbi_validation_results = []
                st.success(f"✅ Validated {len(_sweep_data)} combination(s) — "
                           f"{len(all_results)} KPI comparison(s).")

            # ── Combination results ──────────────────────────────────────────
            if st.session_state.pbi_combo_val_results:
                _cres = st.session_state.pbi_combo_val_results
                _p = sum(1 for r in _cres if r["status"] == "PASS")
                _f = sum(1 for r in _cres if r["status"] == "FAIL")
                _e = sum(1 for r in _cres if r["status"] == "ERROR")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total",     len(_cres))
                m2.metric("✅ Passed",  _p)
                m3.metric("❌ Failed",  _f)
                m4.metric("⚠️ Errors", _e)

                _cdf = pd.DataFrame([{
                    "Combination": r.get("combination", ""),
                    "Visual Name": r.get("visual_name", ""),
                    "KPI Name":    r.get("kpi_name", ""),
                    "UI Value":    r.get("ui_value", ""),
                    "DB Value":    r.get("db_value", ""),
                    "Status":      r.get("status", ""),
                    "Reason":      r.get("reason", ""),
                    "SQL Query":   r.get("sql_query", ""),
                } for r in _cres])
                st.dataframe(_cdf, use_container_width=True, height=420)
                st.download_button(
                    "📥 Download Combination Report (Excel)",
                    data=export_to_excel(_cdf),
                    file_name="pbi_combination_validation.xlsx",
                    mime=("application/vnd.openxmlformats-officedocument"
                          ".spreadsheetml.sheet"),
                    type="primary", key="pbi_dl_combo_val",
                )

        # ── Results ────────────────────────────────────────────────────────────
        if st.session_state.pbi_validation_results:
            results = st.session_state.pbi_validation_results
            total   = len(results)
            passed  = sum(1 for r in results if r["status"] == "PASS")
            failed  = sum(1 for r in results if r["status"] == "FAIL")
            errors  = sum(1 for r in results if r["status"] == "ERROR")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total KPIs",  total)
            m2.metric("✅ Passed",    passed)
            m3.metric("❌ Failed",    failed)
            m4.metric("⚠️ Errors",   errors)

            st.markdown("---")
            st.markdown('<p class="section-title">Validation Results</p>',
                        unsafe_allow_html=True)

            df_results = build_validation_df(results)

            def _row_color(row):
                s = row["Status"]
                color = (
                    "#C6EFCE" if s == "PASS" else
                    "#FFC7CE" if s == "FAIL" else
                    "#FFEB9C"
                )
                return [f"background-color: {color}"] * len(row)

            st.dataframe(
                df_results.style.apply(_row_color, axis=1),
                use_container_width=True,
                height=420,
            )

            st.markdown("---")
            col_dl, col_clear_res, _ = st.columns([1, 1, 3])
            with col_dl:
                excel_bytes = export_to_excel(df_results)
                st.download_button(
                    "📥 Download Excel Report",
                    data=excel_bytes,
                    file_name="pbi_validation_report.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet"
                    ),
                    type="primary",
                    key="pbi_download",
                )
            with col_clear_res:
                if st.button("🔄 Clear Results", use_container_width=True,
                             key="pbi_clear_results"):
                    st.session_state.pbi_validation_results = []
                    st.rerun()

        st.markdown("---")
        _render_script_expander("validate")
