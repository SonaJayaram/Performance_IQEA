import requests
import json
import openai
import csv
import allure
from bs4 import BeautifulSoup
import allure_commons
from allure_commons.logger import AllureFileLogger
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os
from datetime import datetime
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
client = openai.OpenAI(api_key =  os.environ["OPENAI_API_KEY"],
                       base_url = os.environ["OPENAI_API_BASE"])
# # Access the variables
# api_key = os.getenv("AZURE_OPENAI_API_KEY")
# endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
#
# # Set the environment variables explicitly if needed
# os.environ["AZURE_OPENAI_API_KEY"] = api_key
# os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint
def init_allure_results():
    allure_dir = "allure-results"

    import os, shutil
    if os.path.exists(allure_dir):
        shutil.rmtree(allure_dir)
    os.makedirs(allure_dir, exist_ok=True)

    plugin_name = "allure_file_logger"

    # Safe unregister if exists
    try:
        allure_commons.plugin_manager.unregister(name=plugin_name)
    except:
        pass

    # Fresh register
    file_logger = AllureFileLogger(allure_dir)
    allure_commons.plugin_manager.register(file_logger, name=plugin_name)
    print("✔ Allure logger registered cleanly")

import requests
swaggerhub_api_key= "3870e0b0-429d-45d8-8502-a85fafab4b51"
def load_openapi_spec(
    url: str
) -> dict:
    """
    Load OpenAPI/Swagger JSON from SwaggerHub apiproxy endpoint
    using API Key authentication.
    """

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {swaggerhub_api_key}",
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        verify=False,
        timeout=30
    )

    # Clear, user-friendly errors
    if response.status_code == 401:
        raise Exception("Unauthorized: Invalid SwaggerHub API Key")
    if response.status_code == 403:
        raise Exception("Forbidden: API Key has no access to this API")
    if response.status_code == 404:
        raise Exception(
            "API not found or requires authentication. "
            "Ensure the SwaggerHub URL and API key are correct."
        )

    response.raise_for_status()
    return response.json()

# def load_openapi_spec(url: str) -> dict:
#     """
#     Load OpenAPI/Swagger JSON from a given URL.
#     Works for SwaggerHub JSON endpoints.
#     """
#     response = requests.get(url, verify=False)
#     response.raise_for_status()
#     return response.json()


def extract_api_details(openapi_json: dict) -> dict:
    """
    Extracts endpoints, methods, parameters, headers, request bodies,
    responses, and authentication details.
    """
    extracted = {}

    paths = openapi_json.get("paths", {})
    components = openapi_json.get("components", {})

    for path, methods in paths.items():
        extracted[path] = {}

        for method, details in methods.items():
            method = method.lower()

            # Skip non-HTTP keys
            if method not in ["get", "post", "put", "delete", "patch", "options", "head"]:
                continue

            extracted[path][method] = {}

            # Basic info
            extracted[path][method]["summary"] = details.get("summary", "")
            extracted[path][method]["description"] = details.get("description", "")

            # -------------------------
            # Extract Parameters
            # -------------------------
            params = details.get("parameters", [])
            extracted[path][method]["parameters"] = []

            for param in params:
                extracted[path][method]["parameters"].append({
                    "name": param.get("name"),
                    "in": param.get("in"),              # query, path, header
                    "required": param.get("required", False),
                    "schema": param.get("schema", {})
                })

            # -------------------------
            # Extract Request Body
            # -------------------------
            request_body = details.get("requestBody", {})

            if request_body:
                content = request_body.get("content", {})
                extracted[path][method]["requestBody"] = content
            else:
                extracted[path][method]["requestBody"] = {}

            # -------------------------
            # Extract Responses
            # -------------------------
            responses = details.get("responses", {})
            extracted[path][method]["responses"] = responses

            # -------------------------
            # Extract Security
            # -------------------------
            security = details.get("security", [])
            extracted[path][method]["security"] = security

    # -------------------------
    # Global Security Schemes
    # -------------------------
    extracted["securitySchemes"] = components.get("securitySchemes", {})

    return extracted


def build_data_dictionary(swagger_api_details, base_url,spec):
    """
    Convert Swagger/OpenAPI extracted info into the format required by makeapicall().

    swagger_api_details = {
        "/users": {
            "get": {
                "summary": "...",
                "parameters": [...],
                "requestBody": {...},
                "responses": {...},
                "security": [...]
            }
        }
    }
    """
    data_dict_list = []

    for endpoint, methods in swagger_api_details.items():

        # Skip securitySchemes object
        if endpoint == "securitySchemes":
            continue

        for method, details in methods.items():
            print("swegger_details_to_build",details)
            http_method = method.upper()

            # ----------------------------
            # Collect Payload (if exists)
            # ----------------------------
            payload = {}
            request_body = details.get("requestBody", {})

            schema = {}

            # Case 1: OpenAPI 3 standard (content exists)
            if "content" in request_body:
                content = request_body.get("content", {})
                if content:
                    first_ct = next(iter(content))
                    schema = content[first_ct].get("schema", {})

            # Case 2: Your flattened structure (application/json directly)
            else:
                for ct, ct_val in request_body.items():
                    if isinstance(ct_val, dict) and "schema" in ct_val:
                        schema = ct_val.get("schema", {})
                        break

            if schema:
                payload = generate_sample_payload(schema, spec)

            print("*********Api_payload**********", payload)
            # ----------------------------
            # Collect Authentication Header
            # ----------------------------
            headers = {}
            security = details.get("security", [])
            security_schemes = swagger_api_details.get("securitySchemes", {})

            if security:
                for sec in security:
                    for scheme_name in sec.keys():
                        if scheme_name in security_schemes:
                            scheme = security_schemes[scheme_name]

                            if scheme["type"] == "apiKey":
                                headers[scheme["name"]] = "REPLACE_WITH_AUTH_KEY"

                            if scheme["type"] == "http" and scheme["scheme"] == "bearer":
                                headers["Authorization"] = "Bearer REPLACE_TOKEN"

            # Default header
            headers["Content-Type"] = "application/json"

            # ----------------------------
            # Expected Response
            # ----------------------------
            responses = details.get("responses", {})
            expected_output = {}
            expected_status = None

            # Pick first success response
            for status_code, resp_val in responses.items():
                if str(status_code).startswith("2"):
                    expected_status = int(status_code)
                    expected_output = {"expected_response_schema": resp_val}
                    break

            # ----------------------------
            # Create FINAL Data Dict
            # ----------------------------
            final_dict = {
                "baseUrl": base_url,
                "endpoint": endpoint,
                "httpMethod": http_method,
                "payload": payload,
                "headers": headers,
                "expectedOutput": expected_output,
                "Expected-StatusCode": expected_status,
            }

            data_dict_list.append(final_dict)

    return data_dict_list


# def generate_sample_payload(schema):
#     """
#     Converts a Swagger schema into a simple sample payload.
#     """
#     if "type" not in schema:
#         return {}
#
#     if schema["type"] == "object":
#         payload = {}
#         props = schema.get("properties", {})
#         for key, val in props.items():
#             if val.get("type") == "string":
#                 payload[key] = "string"
#             elif val.get("type") == "integer":
#                 payload[key] = 0
#             elif val.get("type") == "boolean":
#                 payload[key] = True
#             elif val.get("type") == "array":
#                 payload[key] = []
#             elif val.get("type") == "object":
#                 payload[key] = generate_sample_payload(val)
#         return payload
#
#     return {}
def resolve_ref(ref: str, swagger_spec: dict):
    """
    Resolve Swagger $ref paths
    Example: #/components/schemas/Pet
    """
    ref_path = ref.lstrip("#/").split("/")
    value = swagger_spec
    for key in ref_path:
        value = value.get(key, {})
    return value
def generate_sample_payload(schema: dict, swagger_spec: dict):
    """
    Generate sample JSON payload from Swagger schema
    """
    if not schema:
        return {}

    # Resolve $ref
    if "$ref" in schema:
        resolved = resolve_ref(schema["$ref"], swagger_spec)
        return generate_sample_payload(resolved, swagger_spec)

    # Use example if present
    if "example" in schema:
        return schema["example"]

    schema_type = schema.get("type", "object")

    if schema_type == "object":
        payload = {}
        properties = schema.get("properties", {})
        for prop, prop_schema in properties.items():
            payload[prop] = generate_sample_payload(prop_schema, swagger_spec)
        return payload

    if schema_type == "array":
        items = schema.get("items", {})
        return [generate_sample_payload(items, swagger_spec)]

    if schema_type == "string":
        return "string"

    if schema_type == "integer":
        return 0

    if schema_type == "number":
        return 0.0

    if schema_type == "boolean":
        return True

    return None

def get_base_url(swagger_url, spec):
    # 1. If API has servers[] block
    servers = spec.get("servers", [])
    if servers:
        if "url" in servers[0]:
            return servers[0]["url"]

    print("⚠ No Base URL found inside Swagger. Using SwaggerHub mock server.")

    # 2. Build SwaggerHub Mock URL
    # swagger_url: https://api.swaggerhub.com/apis/tiger-b7b/equifax_new/1.0.0?format=json
    parts = swagger_url.split("/apis/")[1]
    org, api, version_with_query = parts.split("/")
    version = version_with_query.split("?")[0]

    mock_url = f"https://virtserver.swaggerhub.com/{org}/{api}/{version}"
    return mock_url


def run_allure_test(api_dict, utils):
    test_name = f"{api_dict.get('httpMethod')} {api_dict.get('endpoint')}"

    with allure.step(f"Executing: {test_name}"):
        utils.makeapicall(api_dict)

import pandas as pd
import json


def read_excel_input(file_path: str):
    """
    Reads the API Excel file and returns a clean list of API dictionaries
    compatible with makeapicall() and makeperformancecall().
    """

    df = pd.read_excel(file_path)
    df.columns = [c.strip() for c in df.columns]

    # Normalize Yes/No fields
    def normalize_flag(val):
        if str(val).strip().upper() in ["Y", "YES", "TRUE", "1"]:
            return True
        return False

    api_list = []

    for _, row in df.iterrows():

        api_data = {
            "test_case_name": row.get("Test_Case_Name", ""),
            "method": row.get("httpMethod", "").upper(),
            "baseUrl": row.get("baseUrl", ""),
            "endpoint": row.get("endPoint", ""),

            # Headers
            "content_type": row.get("headers", "application/json"),
            "authorization": row.get("headers-Authorization", ""),

            # Request Body Inputs
            "body_format": row.get("BodyFormat", ""),             # JSON / FORM-DATA / NODATA
            "username": row.get("Request-username", ""),
            "password": row.get("Request-password", ""),
            #auth_type
            "auth_type": row.get("auth_type", ""),
            # Expected Output Details
            "expected_status": int(row.get("Expected-StatusCode", 200)),
            "expected_message": row.get("Expected-Message", ""),

            # Flags
            "validate": normalize_flag(row.get("Validate?", "Y")),
            "performance": normalize_flag(row.get("Performance?", "N")),

            # Extraction
            "extract_token": row.get("Extract-token", "")
        }

        api_list.append(api_data)

    return api_list
def generate_example_payload(schema: dict):
    """
    Generate sample payload from Swagger schema
    """
    if not schema:
        return {}

    if "$ref" in schema:
        return {"_ref": schema["$ref"]}

    payload = {}
    properties = schema.get("properties", {})

    for key, prop in properties.items():
        prop_type = prop.get("type", "string")

        if prop_type == "string":
            payload[key] = prop.get("example", "string")
        elif prop_type == "integer":
            payload[key] = prop.get("example", 0)
        elif prop_type == "boolean":
            payload[key] = prop.get("example", True)
        elif prop_type == "array":
            payload[key] = []
        elif prop_type == "object":
            payload[key] = generate_sample_payload(prop)
        else:
            payload[key] = None

    return payload


def api_response_prompt(api_response):
    formatted_summary = f"""You are a Senior API Quality Architect and Automation Expert.

    Your task is to analyze API execution results and provide a clear, structured
    QUALITY ANALYSIS REPORT in HTML format.

    You will be given API execution details including:
    - API name
    - HTTP method
    - Endpoint
    - Request payload (for POST/PUT)
    - Expected output (if provided)
    - Actual HTTP status code
    - Actual API response JSON

    Your responsibilities:
    1. Validate whether the HTTP status code matches expected behavior.
    2. Validate response correctness:
       - For GET APIs: verify expected fields and values.
       - For POST/PUT APIs: verify that request payload values are correctly reflected in the response.
    3. Identify missing fields, incorrect values, or contract mismatches.
    4. Detect potential functional risks or inconsistencies.
    5. Provide actionable recommendations to improve API quality.

    Rules:
    - Be precise and factual.
    - Do not invent data.
    - If information is missing, clearly state it.
    - Do NOT include raw JSON dumps unless required for explanation.

    ---

    ### INPUT DATA
    The following is the API execution data in JSON format:

    {api_response}

    ---

    ### OUTPUT FORMAT (STRICT)

    Generate a well-structured **HTML report** with the following sections:

    <h2>API Summary</h2>
    - Method
    - Endpoint
    - Status Code
    - Result (PASS / FAIL)

    <h2>Validation Results</h2>
    - Status code validation
    - Field/value validation details

    <h2>Issues Identified</h2>
    - List of defects or mismatches (if any)

    <h2>Risk Assessment</h2>
    - Low / Medium / High
    - Short justification

    <h2>Recommendations</h2>
    - Clear, actionable improvement points

    <h2>Overall Verdict</h2>
    - Final PASS or FAIL with reasoning

    Only return valid HTML.
    """
    return  formatted_summary

def api_performace_reponse_prompt(performance_response=None,performance_parameter=None):
    formatted_summary = f"""You are a Senior Performance Test Architect and Scalability Expert.

    Your task is to analyze performance test results generated by Locust
    and provide an insightful PERFORMANCE ANALYSIS REPORT in HTML format.

    You will be provided with:
    - API method and endpoint
    - Load test configuration (users, spawn rate, duration)
    - Raw Locust HTML report content

    Your responsibilities:
    1. Analyze key performance metrics:
       - Response times (avg, p95, p99)
       - Throughput (requests/sec)
       - Failure rate
    2. Identify performance bottlenecks and instability.
    3. Assess system scalability and reliability.
    4. Highlight SLA/SLO risks.
    5. Provide optimization and tuning recommendations.

    Rules:
    - Base analysis strictly on provided data.
    - Do not assume infrastructure details unless evident.
    - Be concise but insightful.
    - Avoid generic advice; tailor recommendations to observed metrics.

    ---

    ### INPUT DATA
    The following is the performance test data:

    {performance_response}
    {performance_parameter}
    ---
    
    ### OUTPUT FORMAT (STRICT)
    Do NOT wrap output in triple backticks like ```html,```java,```python,```.
    Generate a structured **HTML report** with the following sections:

    <h2>Test Overview</h2>
    - API Method & Endpoint
    - Load Configuration Summary

    <h2>Key Metrics Summary</h2>
    - Average Response Time
    - P95 / P99 Response Time
    - Throughput
    - Error Rate

    <h2>Performance Findings</h2>
    - Observed behavior under load
    - Bottlenecks or anomalies

    <h2>Risk Level</h2>
    - Low / Medium / High
    - Reasoning

    <h2>Recommendations</h2>
    - Performance optimizations
    - Configuration or architectural suggestions

    <h2>Production Readiness Verdict</h2>
    - Ready / Not Ready
    - Explanation

    Only return valid HTML.
    """
    return  formatted_summary
def locust_convert_prompt(Locust_extarcted_data=None,performance_config=None):
    formatted_summary = formatted_summary = f"""
You are a Senior Performance Test Architect with deep expertise in
analyzing Locust performance test results.

You will receive PERFORMANCE TEST OUTPUT extracted from Locust CSV files
AND the test execution configuration used to run the test.

---

### 📥 INPUT 1: Performance Test Configuration (Context Only)

The following configuration describes how the test was executed.
Use this information ONLY to provide contextual understanding of load,
NOT to infer or calculate performance metrics.

performance_config:
- ramp_users: total virtual users ramped
- spawn_rate: users started per second
- run_time: steady-state duration
- stop_time: graceful shutdown duration

{performance_config}

---

### 📥 INPUT 2: Extracted Locust CSV Data

The input contains performance data per API, including:
- stats.csv
- stats_history.csv
- failures.csv
- exceptions.csv

{Locust_extarcted_data}

---

### 🎯 YOUR OBJECTIVE

For EACH API present in the input:

1. Analyze performance metrics strictly from CSV-derived data.
2. Use the performance configuration ONLY to:
   - Describe load intensity
   - Explain observed behavior (e.g., latency under high load)
3. Generate a professional HTML performance report with:
   - Findings
   - Risks
   - Recommendations

---

### ⚠️ STRICT CONSTRAINTS

- Do NOT derive metrics from configuration values.
- Do NOT hallucinate numbers.
- If data is missing, display **"Not Available"**.
- Configuration values must never be treated as results.

---

### 📤 OUTPUT FORMAT (STRICT HTML ONLY)

Return ONLY valid HTML.

<!DOCTYPE html>
<html>
<head>
  <title>API Performance Test Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; }}
    h1, h2, h3 {{ color: #2c3e50; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background-color: #f4f6f8; }}
    .good {{ color: green; font-weight: bold; }}
    .moderate {{ color: orange; font-weight: bold; }}
    .poor {{ color: red; font-weight: bold; }}
    .na {{ color: gray; }}
  </style>
</head>

<body>

<h1>Test Execution Configuration</h1>
<table>
  <tr><th>Parameter</th><th>Value</th></tr>
  <tr><td>Ramp Users</td><td>{(performance_config or {}).get("ramp_users", "Not Available")}</td></tr>
  <tr><td>Spawn Rate (users/sec)</td><td>{(performance_config or {}).get("spawn_rate", "Not Available")}</td></tr>
  <tr><td>Run Time</td><td>{(performance_config or {}).get("run_time", "Not Available")}</td></tr>
  <tr><td>Stop Time</td><td>{(performance_config or {}).get("stop_time", "Not Available")}</td></tr>
</table>

<hr/>

<h1>Overall Performance Summary</h1>
<ul>
  <li><strong>Total APIs Tested:</strong> {{number}}</li>
  <li><strong>Overall Health:</strong> Good | Moderate | Poor | Not Available</li>
</ul>

<h2>Key Risks</h2>
<ul>
  <li>Risk 1</li>
  <li>Risk 2</li>
</ul>

<hr/>

<h1>API-wise Performance Analysis</h1>

<!-- One section per API -->
<section>
  <h2>API: &lt;endpoint or base_path&gt;</h2>

  <h3>Throughput</h3>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Requests / Second</td><td>value or Not Available</td></tr>
    <tr><td>Total Requests</td><td>value or Not Available</td></tr>
  </table>

  <h3>Latency</h3>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Average Response Time</td><td>value or Not Available</td></tr>
    <tr><td>P95 Response Time</td><td>value or Not Available</td></tr>
  </table>

  <h3>Reliability</h3>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Failure Count</td><td>value or Not Available</td></tr>
    <tr><td>Failure Rate</td><td>value or Not Available</td></tr>
    <tr><td>Observations</td><td>text or Not Available</td></tr>
  </table>

  <h3>Stability Assessment</h3>
  <p>Stable | Degrading | Unstable | Not Available</p>

  <h3>Recommendations</h3>
  <ul>
    <li>Recommendation 1</li>
    <li>Recommendation 2</li>
  </ul>
</section>

<hr/>

<h1>Final Recommendation</h1>
<p>Overall production readiness guidance.</p>

</body>
</html>

---

### ✅ QUALITY RULES

- Output ONLY HTML.Do NOT wrap output in triple backticks like ```html,```.
- Do NOT echo raw CSV data.
- Configuration is CONTEXT, not RESULT.
- Use precise engineering language.
"""


    return  formatted_summary
def get_queries_from_ai_updated(formatted_summary):
   print("going inside get_queries_from_ai_updated")
   model = "gpt-5-mini"
   try:
        response = client.chat.completions.create(model=model,
                                          messages=[{"role": "user",
                                                     "content": formatted_summary
                                                     }
                                                    ])
        print(response)
        return response.choices[0].message.content
   except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return None
# def get_queries_from_ai_updated(formatted_summary):
#     # Access the variables
#     api_key = os.getenv("AZURE_OPENAI_API_KEY")
#     endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
#
#     # Set the environment variables explicitly if needed
#     os.environ["AZURE_OPENAI_API_KEY"] = api_key
#     os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint
#     model = AzureChatOpenAI(
#         openai_api_version="2023-05-15",
#         azure_deployment="qepracticekey",
#     )
#     message = HumanMessage(content=formatted_summary)
#     output_value = model([message])
#     print(output_value)
#     return output_value.content



def collect_locust_reports_data(html_report_paths):
    """
    Reads Locust HTML reports and extracts ALL possible raw textual content
    (tables, labels, embedded JS text) for LLM-based interpretation.
    """

    collected_reports = []

    for report_path in html_report_paths:
        if not os.path.exists(report_path):
            continue

        with open(report_path, "r", encoding="utf-8", errors="ignore") as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # 1️⃣ Extract visible text
        visible_text = soup.get_text(separator=" ", strip=True)

        # 2️⃣ Extract script text (sometimes contains metric labels / values)
        script_texts = []
        for script in soup.find_all("script"):
            if script.string:
                script_texts.append(script.string)

        combined_raw_text = (
            visible_text[:8000] + "\n\n" +
            "\n".join(script_texts)[:8000]
        )

        collected_reports.append({
            "report_name": os.path.basename(report_path),
            "raw_text": combined_raw_text
        })

    return {
        "total_reports": len(collected_reports),
        "reports": collected_reports
    }

def save_html_report(html_content, report_dir, report_name_prefix):
    """
    Saves HTML content to a file and returns the file path.

    Args:
        html_content (str): HTML string content
        report_dir (str): Directory where report should be saved
        report_name_prefix (str): Logical name (api_analysis / performance_analysis)

    Returns:
        str: Full file path of saved HTML report
    """

    # Ensure directory exists
    os.makedirs(report_dir, exist_ok=True)

    # Timestamp to avoid overwrite
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # Build file name
    file_name = f"{report_name_prefix}_{timestamp}.html"
    file_path = os.path.join(report_dir, file_name)

    # Write HTML content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return file_path

if __name__ == "__main__":
    swagger_url = "https://api.swaggerhub.com/apis/tiger-b7b/equifax_new/1.0.0?format=json"

    openapi_spec = load_openapi_spec(swagger_url)
    api_details = extract_api_details(openapi_spec)

    # Extract Base URL from Swagger if exists, else ask user/UI
    base_url = get_base_url(openapi_spec)

    final_list = build_data_dictionary(api_details, base_url)

    print(json.dumps(final_list, indent=4))

def read_csv_safe(file_path):
    if not os.path.exists(file_path):
        return []

    with open(file_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
CSV_SUFFIXES = [
    "_stats.csv",
    "_stats_history.csv",
    "_failures.csv",
    "_exceptions.csv"
]
def collect_locust_csv_from_paths(paths):
    aggregated_result = []

    for base_path in paths:
        api_result = {
            "base_path": base_path,
            "stats": [],
            "stats_history": [],
            "failures": [],
            "exceptions": []
        }

        for suffix in CSV_SUFFIXES:
            full_path = base_path + suffix

            if suffix == "_stats.csv":
                api_result["stats"] = read_csv_safe(full_path)

            elif suffix == "_stats_history.csv":
                api_result["stats_history"] = read_csv_safe(full_path)

            elif suffix == "_failures.csv":
                api_result["failures"] = read_csv_safe(full_path)

            elif suffix == "_exceptions.csv":
                api_result["exceptions"] = read_csv_safe(full_path)

        aggregated_result.append(api_result)
    print("*******aggregated_result**********",aggregated_result)
    return aggregated_result
