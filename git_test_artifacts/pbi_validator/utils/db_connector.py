import urllib.parse

import pandas as pd
from sqlalchemy import create_engine, text

_DRIVERS = {
    "postgresql": "postgresql+psycopg2",
    "mysql":      "mysql+pymysql",
    "mssql":      "mssql+pyodbc",
    "sqlite":     "sqlite",
}

# ── Connection string builders ─────────────────────────────────────────────────

def build_connection_string(db_type: str, host: str, port: str,
                             dbname: str, user: str, password: str,
                             http_path: str = "", catalog: str = "",
                             schema: str = "") -> str:
    """
    Build a connection string for the given DB type.
    For Databricks, host = server hostname, password = access token.
    http_path / catalog / schema are Databricks-only fields.
    """
    dt = db_type.lower()

    if dt == "databricks":
        # Encode token in case it contains special chars
        token = urllib.parse.quote(password, safe="")
        conn = f"databricks://{host}?http_path={urllib.parse.quote(http_path, safe='/')}&token={token}"
        if catalog:
            conn += f"&catalog={urllib.parse.quote(catalog, safe='')}"
        if schema:
            conn += f"&schema={urllib.parse.quote(schema, safe='')}"
        print(conn)
        return conn

    if dt == "sqlite":
        return f"sqlite:///{dbname}"

    if dt == "mssql":
        return (
            f"mssql+pyodbc://{user}:{password}@{host}:{port}/{dbname}"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        )

    driver = _DRIVERS.get(dt, "postgresql+psycopg2")
    return f"{driver}://{user}:{password}@{host}:{port}/{dbname}"


def _parse_databricks_url(conn_string: str) -> dict:
    """Extract Databricks connection params from the internal URL format."""
    parsed = urllib.parse.urlparse(conn_string)
    qs = urllib.parse.parse_qs(parsed.query)
    return {
        "server_hostname": parsed.hostname,
        "http_path":       urllib.parse.unquote(qs.get("http_path",  [""])[0]),
        "access_token":    urllib.parse.unquote(qs.get("token",      [""])[0]),
        "catalog":         urllib.parse.unquote(qs.get("catalog",    [""])[0]) or None,
        "schema":          urllib.parse.unquote(qs.get("schema",     [""])[0]) or None,
    }


# ── Public helpers ─────────────────────────────────────────────────────────────

def test_connection(conn_string: str) -> tuple:
    """Returns (success: bool, message: str)."""
    try:
        if conn_string.startswith("databricks://"):
            from databricks import sql as dbsql
            params = _parse_databricks_url(conn_string)
            # Remove None values so the connector uses its defaults
            params = {k: v for k, v in params.items() if v is not None}
            with dbsql.connect(**params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
        else:
            # connect_timeout is not supported by SQLite
            connect_args = {} if conn_string.startswith("sqlite:") else {"connect_timeout": 5}
            engine = create_engine(conn_string, connect_args=connect_args)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        return True, "Connection successful"
    except FileNotFoundError:
        return False, "Database file not found. For SQLite, provide a valid path to an existing .db file."
    except Exception as exc:
        err = str(exc)
        low = err.lower()
        if "connection refused" in low:
            return False, "Connection refused — the server may not be running or the host/port is wrong."
        if "could not connect" in low or "no route to host" in low or "timed out" in low:
            return False, "Could not reach the database server. Check the host and port."
        if "password authentication failed" in low or "access denied" in low or "login failed" in low:
            return False, "Authentication failed — check your username and password."
        if "database" in low and ("does not exist" in low or "unknown database" in low):
            return False, "Database not found — check the database name."
        if "no such file or directory" in low:
            return False, "Database file not found — check the database name or file path."
        return False, f"Could not connect: {err}"


def execute_query(conn_string: str, sql: str) -> tuple:
    """
    Run a SQL query and return (success, result, error_message).
    result is a scalar when the query returns a single cell, otherwise a DataFrame.
    """
    try:
        if conn_string.startswith("databricks://"):
            from databricks import sql as dbsql
            params = _parse_databricks_url(conn_string)
            params = {k: v for k, v in params.items() if v is not None}
            with dbsql.connect(**params) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    rows    = cur.fetchall()
                    columns = [d[0] for d in cur.description] if cur.description else []
            df = pd.DataFrame(rows, columns=columns)
        else:
            engine = create_engine(conn_string)
            with engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)

        if df.empty:
            return True, None, "Query returned no rows"

        if df.shape == (1, 1):
            return True, df.iloc[0, 0], ""

        return True, df, ""

    except Exception as exc:
        return False, None, str(exc)
