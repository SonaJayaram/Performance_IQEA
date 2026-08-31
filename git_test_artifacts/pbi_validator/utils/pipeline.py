"""
Shared orchestration for the PBI Validator — the SINGLE source of truth used by
both the Streamlit UI and the generated standalone scripts.

Stages, each supporting two flows:
    Flow 1 (kpi)    — unfiltered, one query per visual, value matched in comparison
    Flow 2 (slicer) — reviewed base queries + per-combination filter injection,
                      where every combination is a TEST CASE.

Every function here is UI-agnostic (no Streamlit imports). Long-running loops take
an optional ``progress(i, total, label)`` callback so the UI can show a bar while
scripts pass a plain print (or None).

NOTE ON THE LLM: query generation (``generate_*``) is a DESIGN-TIME activity used
only by the UI. The generated scripts embed the queries the user already reviewed
and never call the LLM at runtime.
"""

import os
import json
from io import BytesIO

import openai
import pandas as pd
from dotenv import load_dotenv

from .pbi_browser import (apply_combination, extract_kpis_via_llm,
                          extract_slicers_via_dom, get_slicer_options,
                          start_browser, take_screenshot, try_show_as_table)
from .combinations import build_combinations, combo_label
from .sql_generator import (adapt_sql_dialect, build_combination_queries,
                            generate_reference_queries, qualify_table_names)
from .db_connector import build_connection_string, execute_query, test_connection
from .comparator import (compare_values, extract_db_value, llm_match_fallback,
                         match_kpi_to_queries, parse_kpi_name, tables_to_kpis)

load_dotenv()

_SLICER_TYPES = ("slicer", "filter")


# ── LLM factory ─────────────────────────────────────────────────────────────
def make_llm():
    """Azure OpenAI client from env (AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT)."""
    return openai.OpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )


# ── Excel config IO ──────────────────────────────────────────────────────────
# Scripts read inputs from a workbook: a "Config" sheet (parameter | value) and,
# for Flow 2, a "Combinations" sheet (one row per TEST CASE, a column per slicer).
def read_config_xlsx(path, sheet="Config") -> dict:
    """Read a two-column (parameter | value) config sheet into a dict."""
    try:
        df = pd.read_excel(path, sheet_name=sheet)
    except Exception:
        df = pd.read_excel(path, sheet_name=0)
    cols = {str(c).lower(): c for c in df.columns}
    pcol = cols.get("parameter") or df.columns[0]
    vcol = cols.get("value") or df.columns[1]
    cfg = {}
    for _, r in df.iterrows():
        key = str(r.get(pcol, "")).strip()
        if not key or key.lower() == "nan":
            continue
        val = r.get(vcol)
        if isinstance(val, str):
            s = val.strip()
            if s.lower() == "nan":
                val = ""
            elif s[:1] in ("[", "{"):
                try:
                    val = json.loads(s)
                except Exception:
                    val = s
            else:
                val = s
        elif pd.isna(val):
            val = ""
        cfg[key] = val
    return cfg


def read_combinations_xlsx(path, sheet="Combinations") -> list:
    """Read the test-case sheet → [{slicer: value}] (empty cells dropped).

    Each row is one test case; each non-empty column contributes a slicer filter.
    """
    try:
        df = pd.read_excel(path, sheet_name=sheet)
    except Exception:
        return []
    combos = []
    for _, r in df.iterrows():
        combo = {}
        for col in df.columns:
            val = r.get(col)
            if pd.isna(val):
                continue
            s = str(val).strip()
            if s and s.lower() not in ("nan", "all"):
                combo[str(col).strip()] = s
        if combo:
            combos.append(combo)
    return combos


def inputs_to_bytes(config: dict, combinations: list = None) -> bytes:
    """Serialize an input workbook (Config sheet [+ Combinations sheet]) to xlsx bytes."""
    buf = BytesIO()
    rows = [{"parameter": k,
             "value": json.dumps(v) if isinstance(v, (list, dict)) else ("" if v is None else v)}
            for k, v in config.items()]
    with pd.ExcelWriter(buf) as xw:
        pd.DataFrame(rows).to_excel(xw, sheet_name="Config", index=False)
        if combinations is not None:
            # One row per test case; union of all slicer names as columns.
            keys = list(dict.fromkeys(k for c in combinations for k in c))
            data = [{k: c.get(k, "") for k in keys} for c in combinations]
            pd.DataFrame(data, columns=keys).to_excel(
                xw, sheet_name="Combinations", index=False)
    return buf.getvalue()


# ── Visual helpers ───────────────────────────────────────────────────────────
def visuals_from_extracted(table_results, extracted_kpis):
    """Build [{name, headers}] from the Step-1 extraction to ground generation."""
    visuals = []
    if table_results:
        for t in table_results:
            hdrs = t.get("headers") or t.get("columns", [])
            visuals.append({"name": t.get("visual_title", "Table"),
                            "headers": [str(h) for h in hdrs]})
        return visuals
    grouped = {}
    for k in (extracted_kpis or []):
        if (k.get("visual_type") or "").lower() in _SLICER_TYPES:
            continue
        vname = k.get("visual_name", "") or "Visual"
        metric, _ = parse_kpi_name(k.get("kpi_name", ""))
        grouped.setdefault(vname, [])
        if metric and metric not in grouped[vname]:
            grouped[vname].append(metric)
    return [{"name": n, "headers": h} for n, h in grouped.items()]


def _kpi_names_by_visual(extracted_kpis):
    out = {}
    for k in (extracted_kpis or []):
        if (k.get("visual_type") or "").lower() in _SLICER_TYPES:
            continue
        vn = k.get("visual_name", "") or "Visual"
        m, _ = parse_kpi_name(k.get("kpi_name", ""))
        out.setdefault(vn, [])
        if m and m not in out[vn]:
            out[vn].append(m)
    return out


def _all_kpi_names(extracted_kpis):
    return list(dict.fromkeys(
        k.get("kpi_name", "").strip() for k in (extracted_kpis or [])
        if (k.get("visual_type") or "").lower() not in _SLICER_TYPES
        and k.get("kpi_name", "").strip()
    ))


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════
def open_report(url, login=None):
    """Open the report in a browser and run the (user-supplied) login callback."""
    driver = start_browser(url)
    if login is not None:
        login(driver, url)
    return driver


def extract_flow1(driver, llm, mode="table"):
    """Flow 1 extraction. mode: 'table' (show-as-table) or 'screenshot'.

    Returns (kpis, table_results, slicers).
    """
    if mode == "table":
        slicers = extract_slicers_via_dom(driver)
        table_results = try_show_as_table(driver) or []
        if table_results:
            return tables_to_kpis(table_results), table_results, slicers
        _, b64 = take_screenshot(driver)
        kpis, slicers = extract_kpis_via_llm(b64, llm)
        return kpis, [], slicers
    _, b64 = take_screenshot(driver)
    kpis, slicers = extract_kpis_via_llm(b64, llm)
    return kpis, [], slicers


def detect_slicer_options(driver):
    """Flow 2: detect available slicer values → {slicer: [values]}."""
    return get_slicer_options(driver)


def run_sweep(driver, combos, progress=None):
    """Flow 2: extract the report under each combination (test case).

    A Default (no-filter) baseline is always run first. Returns
    [{label, combo, tables}] — one entry per test case.
    """
    runs = [{}] + list(combos or [])
    sweep = []
    for i, combo in enumerate(runs):
        is_default = not combo
        label = "Default (no filter)" if is_default else combo_label(combo)
        if progress:
            progress(i, len(runs), label)
        if not is_default:
            apply_combination(driver, combo)
        tbls = try_show_as_table(driver) or []
        sweep.append({"label": label, "combo": dict(combo), "tables": tbls})
    return sweep


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — SQL GENERATION  (DESIGN-TIME, UI ONLY — scripts never call these)
# ══════════════════════════════════════════════════════════════════════════════
def generate_kpi_queries(table_results, extracted_kpis, requirements, schema,
                         llm=None, progress=None):
    """Flow 1: ONE unfiltered query per visual (one LLM call each)."""
    visuals = visuals_from_extracted(table_results, extracted_kpis)
    by_visual = _kpi_names_by_visual(extracted_kpis)
    all_names = _all_kpi_names(extracted_kpis)
    out, failures = [], []
    for i, v in enumerate(visuals):
        name = v.get("name", "")
        if progress:
            progress(i, len(visuals), name)
        try:
            qs = generate_reference_queries(
                requirements, schema or "",
                slicers=None, kpi_names=by_visual.get(name, all_names),
                visuals=[v],
            )
            for q in (qs or []):
                q["visual_name"] = name
            out.extend(qs or [])
        except Exception as exc:            # noqa: BLE001 — surface per-visual
            failures.append(f"{name or 'visual'}: {exc}")
    return out, failures


def generate_slicer_base_queries(sweep_data, requirements, schema, llm=None):
    """Flow 2: base per-visual queries carrying a {SLICER_CONDITIONS} placeholder."""
    tables = sweep_data[0].get("tables", []) if sweep_data else []
    visuals = [{"name": t.get("visual_title", ""),
                "headers": t.get("headers") or t.get("columns", [])}
               for t in tables]
    combo_kpi_names = list(dict.fromkeys(
        parse_kpi_name(k["kpi_name"])[0] for k in tables_to_kpis(tables)
    ))
    return generate_reference_queries(
        requirements, schema or "",
        slicers=None, kpi_names=combo_kpi_names,
        use_slicer_placeholder=True, visuals=visuals or None,
    )


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — VALIDATION
# ══════════════════════════════════════════════════════════════════════════════
def validate_kpi_list(conn_str, kpi_list, ref_queries, tolerance, llm_client,
                      db_type=None, catalog="", schema=""):
    """Match each KPI to its query, run the unique queries, compare UI vs DB.

    Returns result dicts: visual_name, kpi_name, ui_value, sql_query, db_value,
    status, reason. Shared by single-state and per-combination validation.
    """
    if db_type:
        _t = db_type.lower()
        adapted = []
        for q in ref_queries:
            sql = adapt_sql_dialect(q.get("sql_query", ""), db_type)
            if _t == "databricks" and (catalog or schema):
                sql = qualify_table_names(sql, catalog, schema)
            adapted.append(dict(q, sql_query=sql))
        ref_queries = adapted

    results = []
    per_kpi, unmatched = [], []
    for kpi in kpi_list:
        metric, dim_value = parse_kpi_name(kpi.get("kpi_name", ""))
        vname = (kpi.get("visual_name") or "").strip().lower()
        # Route each KPI to ITS OWN visual's query first (per-visual generation),
        # so a metric shared across visuals isn't matched to the wrong visual.
        same_visual = [
            q for q in ref_queries
            if vname and (q.get("visual_name") or q.get("query_name") or "")
                         .strip().lower() == vname
        ]
        cands = match_kpi_to_queries(metric, same_visual) if same_visual else []
        if not cands:
            cands = match_kpi_to_queries(metric, ref_queries)
        if not cands and same_visual:
            cands = [(q, None) for q in same_visual]
        if cands:
            per_kpi.append({"kpi": kpi, "metric": metric,
                            "dim_value": dim_value, "cands": cands})
        else:
            unmatched.append(kpi)

    if unmatched:
        llm_matched = llm_match_fallback(unmatched, ref_queries, llm_client)
        matched_names = set()
        for m in llm_matched:
            if m.get("query"):
                per_kpi.append({"kpi": m["kpi"], "metric": m.get("metric", ""),
                                "dim_value": m.get("dim_value"),
                                "cands": [(m["query"], m.get("col_alias"))]})
                matched_names.add(m["kpi"].get("kpi_name"))
        still = {k["kpi_name"] for k in unmatched} - matched_names
        for kpi in kpi_list:
            if kpi.get("kpi_name") in still:
                results.append({
                    "visual_name": kpi.get("visual_name", ""),
                    "kpi_name":    kpi.get("kpi_name", ""),
                    "ui_value":    kpi.get("value", ""), "sql_query": "",
                    "db_value":    "", "status": "ERROR",
                    "reason":      "No matching reference query found",
                })

    cache = {}
    for e in per_kpi:
        for q, _ in e["cands"]:
            sql = q.get("sql_query", "")
            if sql and sql not in cache:
                cache[sql] = execute_query(conn_str, sql)

    for e in per_kpi:
        kpi, metric, dim_value = e["kpi"], e["metric"], e["dim_value"]
        uiv = kpi.get("value", "")
        chosen_sql, db_val, last_err = "", None, ""
        for q, col in e["cands"]:
            sql = q.get("sql_query", "")
            if not sql:
                continue
            ok, db_result, err = cache.get(sql, (False, None, "Not executed"))
            if not ok:
                last_err, chosen_sql = err, sql
                continue
            val = extract_db_value(metric, dim_value, q, db_result, col)
            chosen_sql = sql
            if val is not None:
                db_val = val
                break

        if db_val is None and last_err and not chosen_sql:
            status, reason = "ERROR", last_err
        elif db_val is None:
            status, reason = ("ERROR", last_err) if last_err else \
                             ("FAIL", "DB query returned no result")
        else:
            status, reason = compare_values(uiv, db_val, tolerance_pct=tolerance)

        results.append({"visual_name": kpi.get("visual_name", ""),
                        "kpi_name": kpi.get("kpi_name", ""), "ui_value": uiv,
                        "sql_query": chosen_sql,
                        "db_value": str(db_val) if db_val is not None else "",
                        "status": status, "reason": reason})
    return results


def validate_combinations(conn_str, sweep_data, base_queries, col_map, tolerance,
                          llm_client, db_type=None, catalog="", schema="",
                          progress=None):
    """Flow 2: inject each combination's slicer values then validate.

    Each combination (test case) yields its own block of result rows tagged with
    the combination label.
    """
    col_map = col_map or {}
    results = []
    for i, cd in enumerate(sweep_data or []):
        label = cd.get("label", f"combo {i}")
        if progress:
            progress(i, len(sweep_data), label)
        combo_queries = build_combination_queries(base_queries, cd.get("combo", {}), col_map)
        kpis = tables_to_kpis(cd.get("tables", []))
        res = validate_kpi_list(conn_str, kpis, combo_queries, tolerance, llm_client,
                                db_type=db_type, catalog=catalog, schema=schema)
        for r in res:
            r["combination"] = label
        results.extend(res)
    return results


def connection_from_config(cfg: dict) -> str:
    """Build a DB connection string from a config dict (script convenience)."""
    return build_connection_string(
        cfg.get("db_type", "postgresql"),
        cfg.get("host", ""), str(cfg.get("port", "")),
        cfg.get("database", ""), cfg.get("user", ""), cfg.get("password", ""),
        http_path=cfg.get("http_path", ""),
        catalog=cfg.get("catalog", ""), schema=cfg.get("schema", ""),
    )
