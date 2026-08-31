import json
import re
from io import BytesIO
import os
import openai
import docx2txt
import pandas as pd
import PyPDF2
from dotenv import load_dotenv

load_dotenv()

def read_requirements_file(uploaded_file) -> str:
    filename = uploaded_file.name.lower()
    content = uploaded_file.read()
    if filename.endswith(".docx"):
        return docx2txt.process(BytesIO(content))
    if filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(content))
        return df.to_string(index=False)
    return content.decode("utf-8", errors="ignore")


# ── Budgets ────────────────────────────────────────────────────────────────────
# gpt-5-mini has a large context window, so we send the FULL schema — the LLM
# must see the exact table names (e.g. gold_orders) or it invents them ("Orders").
_MAX_TOKENS       = 400
_MAX_REQ_CHARS    = 4000
_MAX_SCHEMA_CHARS = 8000
_CHUNK_SIZE_CHARS = 400
_CHUNK_OVERLAP    = 40

_STOP_WORDS = {
    "the", "a", "an", "and", "or", "is", "are", "was", "were", "of", "in",
    "for", "to", "by", "at", "as", "be", "it", "its", "this", "that", "with",
    "on", "from", "all", "has", "have", "not", "but", "if", "then", "so",
}


# ── Chunking helpers ───────────────────────────────────────────────────────────

def _extract_keywords(names: list) -> set:
    keywords: set = set()
    for name in names:
        for word in re.sub(r"[^\w\s]", " ", name).lower().split():
            if len(word) >= 3 and word not in _STOP_WORDS:
                keywords.add(word)
    return keywords


def _split_chunks(text: str, chunk_size: int = _CHUNK_SIZE_CHARS,
                  overlap: int = _CHUNK_OVERLAP) -> list:
    if len(text) <= chunk_size:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            for sep in ("\n\n", "\n", ". "):
                pos = text.rfind(sep, start + chunk_size // 2, end)
                if pos != -1:
                    end = pos + len(sep)
                    break
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def _pick_relevant(text: str, keywords: set, budget: int) -> str:
    if not text or not text.strip():
        return ""
    if len(text) <= budget:
        return text
    chunks = _split_chunks(text)
    if not keywords:
        return text[:budget]
    scored = sorted(
        [(sum(1 for kw in keywords if kw in c.lower()), i, c)
         for i, c in enumerate(chunks)],
        key=lambda x: (-x[0], x[1]),
    )
    selected, used = [], 0
    for _, idx, chunk in scored:
        if used + len(chunk) > budget:
            if not selected:
                selected.append((idx, chunk[:budget]))
            break
        selected.append((idx, chunk))
        used += len(chunk)
    selected.sort(key=lambda x: x[0])
    note = "[Relevant excerpts]\n" if len(selected) < len(chunks) else ""
    return note + "\n...\n".join(c for _, c in selected)


# ── LLM call ──────────────────────────────────────────────────────────────────

def _call_llm(prompt: str) -> list:
    client = openai.OpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=25000,
        timeout=600,
    )
    raw    = response.choices[0].message.content or ""
    finish = response.choices[0].finish_reason

    if not raw.strip():
        raise ValueError(f"LLM returned empty response (finish_reason='{finish}').")

    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw).strip()

    if not raw:
        raise ValueError("LLM returned only code fences with no JSON.")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        last = raw.rfind("},")
        if last > 0:
            try:
                return json.loads("[" + raw.lstrip("[")[:last + 1] + "]")
            except json.JSONDecodeError:
                pass
        raise ValueError(f"LLM response was not valid JSON.\nFirst 300 chars: {raw[:300]}")


# ── Public API ─────────────────────────────────────────────────────────────────

_MAX_KPI_NAMES = 20


def generate_reference_queries(requirements_text: str, db_schema: str, client=None,
                                slicers: list = None, kpi_names: list = None,
                                use_slicer_placeholder: bool = False,
                                visuals: list = None) -> list:
    """
    Phase 2: Generate reference SQL queries from requirements + schema.

    slicers   — list of {kpi_name, value} dicts extracted from Phase 1 slicer visuals.
                Applied as WHERE conditions in every generated query so DB values
                match the filtered state shown in the Power BI UI.
    kpi_names — list of metric name strings extracted from Phase 1 (non-slicer KPIs).
                Guides the LLM to build kpi_patterns that match the real extracted names.

    Returns:
      [{query_name, sql_query, visual_type, dimension_column,
        metric_columns, kpi_patterns, description}]
      metric_columns and kpi_patterns are parallel lists (index i maps pattern→column).
    """
    keywords = _extract_keywords([
        "sales", "profit", "margin", "orders", "customers",
        "return", "rate", "total", "count", "region", "category",
    ])
    req_slice    = _pick_relevant(requirements_text or "", keywords, _MAX_REQ_CHARS)
    schema_slice = _pick_relevant(db_schema or "",         keywords, _MAX_SCHEMA_CHARS)

    schema_block = f"\nSchema:\n{schema_slice}" if schema_slice else ""

    # ── Filter handling ──────────────────────────────────────────────────────
    slicer_conds = []
    if use_slicer_placeholder:
        # Combination mode: filters injected later. Tell the LLM to emit the
        # literal placeholder wherever a filter belongs.
        slicer_block = (
            "\nEVERY query MUST include a WHERE clause using the EXACT literal "
            "placeholder {SLICER_CONDITIONS} where slicer filters apply. If a "
            "query has a fixed condition, combine as '<cond> AND {SLICER_CONDITIONS}'. "
            "In subqueries too, each WHERE must use {SLICER_CONDITIONS}. Never "
            "invent slicer values."
        )
    else:
        for s in (slicers or []):
            name = (s.get("kpi_name") or s.get("slicer_name") or "").strip()
            val  = str(s.get("value") or "").strip()
            if name and val and val.lower() not in ("all", "n/a", "", "nan"):
                slicer_conds.append(f"{name}='{val}'")
        if slicer_conds:
            slicer_block = (
                f"\nActive slicers — add as WHERE conditions in EVERY query: "
                f"{', '.join(slicer_conds)}"
            )
        else:
            # KPI flow: report is UNFILTERED. The LLM must not volunteer any
            # slicer/parameter filter (region/segment/date), or Databricks fails
            # with UNBOUND_SQL_PARAMETER on the unbound :region / {{start_date}} etc.
            slicer_block = (
                "\nThis report is UNFILTERED. Do NOT add any WHERE filter for "
                "region, segment, date or any slicer. Do NOT use bound parameters "
                "or placeholders of ANY kind — no :name, no {{name}}, no ${name}, "
                "no ? markers. Emit PLAIN queries that aggregate over the whole "
                "table. Only keep a WHERE that is intrinsic to the metric's own "
                "definition (e.g. status='returned' for a returns metric)."
            )

    # Include sample KPI names so LLM builds matching kpi_patterns
    kpi_block = ""
    if kpi_names:
        sample = [n.strip() for n in kpi_names if n.strip()][:_MAX_KPI_NAMES]
        if sample:
            kpi_block = f"\nKPI metric names to cover: {', '.join(sample)}"

    # List the actual visuals so the LLM emits ONE query per visual (coverage)
    visuals_block = ""
    if visuals:
        lines = []
        for v in visuals[:15]:
            hdrs = ", ".join(str(h) for h in (v.get("headers") or []))
            lines.append(f"- \"{v.get('name', '')}\": columns [{hdrs}]")
        if lines:
            visuals_block = (
                "\nVisuals — generate exactly ONE query per visual below, matching "
                "its columns (first column = dimension for tables):\n" + "\n".join(lines)
            )

    prompt = (
        "Generate SQL queries for a Power BI dashboard.\n"
        f"Requirements:\n{req_slice}"
        f"{schema_block}"
        f"{visuals_block}"
        f"{slicer_block}"
        f"{kpi_block}\n"
        "Return ONLY a JSON array (no markdown). One element per visual:\n"
        '[{"query_name":"","sql_query":"SELECT ...","visual_type":"card|table",'
        '"dimension_column":null,"metric_columns":["col_alias"],'
        '"kpi_patterns":["Metric Name"],"description":""}]\n'
        "Rules:\n"
        "- Use the EXACT fully-qualified table names from the schema "
        "(e.g. catalog.schema.gold_orders). NEVER invent or shorten names "
        "like 'Orders'. Use only columns that exist in the schema.\n"
        "- Qualify TABLES fully, but reference COLUMNS by their table ALIAS only "
        "(e.g. o.sales, o.order_date). NEVER write a column as "
        "catalog.schema.column — that is a table reference and will fail.\n"
        "- STRICT GROUP BY (Spark/Databricks): EVERY column in the outer SELECT "
        "that is not wrapped in an aggregate — INCLUDING columns coming from a "
        "joined subquery (e.g. r.return_orders) — MUST appear in GROUP BY, or be "
        "wrapped in an aggregate such as any_value(...), MAX(...) or SUM(...). "
        "Never select a raw non-grouped column.\n"
        "- When the query uses table aliases or JOINs, alias-qualify EVERY column "
        "reference (SELECT, WHERE, GROUP BY, ON, ORDER BY) so no reference is "
        "ambiguous. A bare `region` when both o.region and r.region exist will fail.\n"
        "- Emit ONE query object per visual listed above (do not merge or skip visuals)\n"
        "- metric_columns and kpi_patterns are parallel (index i maps pattern→column)\n"
        "- card: SELECT metric columns only, no GROUP BY, returns one row\n"
        "- table: SELECT dimension + metric columns, GROUP BY dimension\n"
        "- kpi_patterns must exactly match the KPI metric names / visual columns"
        + ("\n- Put {SLICER_CONDITIONS} in EVERY WHERE clause (incl. subqueries). "
           "The slicer columns are injected as bare `column = value`, so expose "
           "each filterable slicer column from ONE relation with a stable alias "
           "and make sure that column name is unambiguous where the placeholder sits."
           if use_slicer_placeholder else
           ("\n- Apply ALL active slicers as WHERE conditions in every query"
            if slicer_conds else
            "\n- NO filters and NO parameters/placeholders (:x, {{x}}, ${x}, ?) — "
            "emit plain unfiltered aggregate queries"))
    )

    return _call_llm(prompt)


# ── Phase 3: filter-combination injection ───────────────────────────────────────
#
#  Generate base per-visual SQL ONCE (no filters), then for each combination
#  inject that combination's slicer values as WHERE conditions — deterministic,
#  no extra LLM calls.

# Top-level clauses after which a WHERE cannot go — we insert before the first one.
_TAIL_CLAUSE_RE = re.compile(
    r"\b(group\s+by|order\s+by|having|limit|offset|window|"
    r"union|except|intersect|fetch\s+first)\b",
    re.IGNORECASE,
)


def _format_condition(column: str, value) -> str:
    """Build a single `col = value` predicate, quoting non-numeric values."""
    col = str(column).strip()
    val = str(value).strip()
    # Numeric → unquoted; everything else → quoted (with '' escaping)
    if re.fullmatch(r"-?\d+(\.\d+)?", val):
        return f"{col} = {val}"
    return f"{col} = '{val.replace(chr(39), chr(39) * 2)}'"


# Placeholder tokens the LLM is asked to emit where filters apply. We SUBSTITUTE
# these (works for multi-subquery SQL where a single injected WHERE would not).
_SLICER_TOKENS = (
    "{SLICER_CONDITIONS}", "{{SLICER_CONDITIONS}}", "{SLICER}",
    "{FILTERS}", "{FILTER_CONDITIONS}", "{WHERE}",
)


def apply_filters_to_sql(sql: str, filters: dict) -> str:
    """
    Apply `filters` ({column: value}) to a query.

    - If the SQL contains a {SLICER_CONDITIONS} placeholder (preferred — the LLM
      puts one in every WHERE), REPLACE every occurrence with the conditions,
      or '1=1' when there are no filters (e.g. the default run). This is correct
      even when the query has many subqueries.
    - Otherwise fall back to injecting a single WHERE before GROUP BY/ORDER BY,
      for simple flat queries.

    Empty / 'all' / 'nan' values are skipped.
    """
    sql = (sql or "").strip().rstrip(";")
    conds = [
        _format_condition(col, val)
        for col, val in (filters or {}).items()
        if str(val).strip() and str(val).strip().lower() not in ("all", "n/a", "nan", "")
    ]

    # ── Placeholder substitution (preferred) ─────────────────────────────────
    if any(tok in sql for tok in _SLICER_TOKENS):
        replacement = " AND ".join(conds) if conds else "1=1"
        for tok in _SLICER_TOKENS:
            sql = sql.replace(tok, replacement)
        return sql

    # ── Fallback: inject one WHERE (flat queries only) ───────────────────────
    if not conds:
        return sql
    cond_str = " AND ".join(conds)
    m = _TAIL_CLAUSE_RE.search(sql)
    pos = m.start() if m else len(sql)
    head, tail = sql[:pos], sql[pos:]
    if re.search(r"\bwhere\b", head, re.IGNORECASE):
        head = f"{head.rstrip()} AND {cond_str} "
    else:
        head = f"{head.rstrip()} WHERE {cond_str} "
    return (head + tail).strip()


def adapt_sql_dialect(sql: str, db_type: str) -> str:
    """
    Convert ANSI double-quoted identifiers (e.g. AS "Total Sales") to the target
    dialect's quoting so aliases with spaces parse:
      - databricks / mysql → backticks  `Total Sales`
      - mssql              → brackets    [Total Sales]
      - postgresql/sqlite  → unchanged (double quotes are valid identifiers)

    Filter values we inject use single quotes, so they are never affected.
    """
    t = (db_type or "").lower()
    if not sql:
        return sql
    if t in ("databricks", "mysql"):
        return re.sub(r'"([^"]*)"', r"`\1`", sql)
    if t == "mssql":
        return re.sub(r'"([^"]*)"', r"[\1]", sql)
    return sql


def qualify_table_names(sql: str, catalog: str = "", schema: str = "") -> str:
    """
    Prefix unqualified table names after FROM / JOIN with `catalog.schema.` so
    bare names like `Orders` resolve on Databricks. Skips subqueries `FROM (`
    and names that are already qualified (contain a dot).
    """
    prefix = ".".join(p for p in (str(catalog).strip(), str(schema).strip()) if p)
    if not prefix or not sql:
        return sql

    def _repl(m):
        kw, name = m.group(1), m.group(2)
        if "." in name:                 # already qualified — leave as-is
            return m.group(0)
        # Guard: `EXTRACT(YEAR FROM col)`, `SUBSTRING(x FROM y)` etc. are function
        # args, not table sources — the identifier is immediately followed by ')'.
        rest = sql[m.end():].lstrip()
        if rest.startswith(")"):
            return m.group(0)
        return f"{kw} {prefix}.{name}"

    # FROM/JOIN + a (possibly dotted) identifier; skip subqueries `FROM (`
    return re.sub(
        r"\b(FROM|JOIN)\s+(?!\()([A-Za-z_][\w.]*)",
        _repl, sql, flags=re.IGNORECASE,
    )


def build_combination_queries(base_queries: list, combo: dict,
                              slicer_to_column: dict = None) -> list:
    """
    Produce per-visual queries for ONE filter combination by injecting the
    combination's slicer values into each base query's SQL.

    Args:
        base_queries     — reference queries with unfiltered SQL (from
                           generate_reference_queries with no slicers).
        combo            — {slicer_name: value} for this combination.
        slicer_to_column — optional {slicer_name: db_column}. Defaults to using
                           the slicer name itself as the column.

    Returns a new list of query dicts (same shape) with combination-filtered SQL.
    """
    slicer_to_column = slicer_to_column or {}
    filters = {}
    for slicer_name, value in (combo or {}).items():
        column = slicer_to_column.get(slicer_name, slicer_name)
        filters[column] = value

    out = []
    for q in base_queries:
        nq = dict(q)
        nq["sql_query"] = apply_filters_to_sql(q.get("sql_query", ""), filters)
        out.append(nq)
    return out


# ── CSV round-trip ─────────────────────────────────────────────────────────────

def reference_queries_to_df(queries: list) -> pd.DataFrame:
    rows = []
    for q in queries:
        rows.append({
            "query_name":       q.get("query_name", ""),
            "visual_type":      q.get("visual_type", "card"),
            "sql_query":        q.get("sql_query", ""),
            "dimension_column": q.get("dimension_column") or "",
            "metric_columns":   json.dumps(q.get("metric_columns", [])),
            "kpi_patterns":     json.dumps(q.get("kpi_patterns", [])),
            "description":      q.get("description", ""),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def df_to_reference_queries(df: pd.DataFrame) -> list:
    def _parse_list(val):
        if isinstance(val, list):
            return val
        s = str(val).strip()
        if not s or s == "nan":
            return []
        try:
            return json.loads(s)
        except Exception:
            return [x.strip() for x in s.split(",") if x.strip()]

    queries = []
    for _, row in df.iterrows():
        queries.append({
            "query_name":       str(row.get("query_name", "")),
            "visual_type":      str(row.get("visual_type", "card")),
            "sql_query":        str(row.get("sql_query", "")),
            "dimension_column": str(row.get("dimension_column", "")) or None,
            "metric_columns":   _parse_list(row.get("metric_columns", "[]")),
            "kpi_patterns":     _parse_list(row.get("kpi_patterns", "[]")),
            "description":      str(row.get("description", "")),
        })
    return queries
