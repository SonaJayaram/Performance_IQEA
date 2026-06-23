import os
import json
import tempfile
import subprocess
import shutil
import pandas as pd
import streamlit as st
import urllib3
import configparser
import xml.etree.ElementTree as ET
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------------------------------
# Import API utilities
# -------------------------------------------
from utilities.API_Utils import api_core_model as api_utils
from utilities.API_Utils import swaggerhub as swagger_utils
import utilitymodule  # From your uploaded utility module for JMX compilation
import allure

swagger_utils.init_allure_results()

# Initialize Session States
state_vars = [
    "swagger_apis", "api_response_analysis", "api_performance_analysis",
    "locust_convert_response", "generated_jmx", "generated_jmx_path"
]
for var in state_vars:
    if var not in st.session_state:
        st.session_state[var] = [] if "analysis" in var or "response" in var or "apis" in var else ""

# Fix page refresh issue: Ensure runtime configurations are registered in session state
if "runtime_threads" not in st.session_state:
    st.session_state.runtime_threads = 1
if "runtime_rampup" not in st.session_state:
    st.session_state.runtime_rampup = 1
if "runtime_loops" not in st.session_state:
    st.session_state.runtime_loops = 1
if "runtime_duration" not in st.session_state:
    st.session_state.runtime_duration = 0

# -------------------------------------------
# FOLDER CONFIG
# -------------------------------------------
current_path = os.getcwd()
input_folder = os.path.join(current_path, "Input")
output_folder = os.path.join(current_path, "output")
JMX_FOLDER = os.path.join(current_path, "generated_jmx_files")
REPORT_DIR = os.path.join(os.getcwd(), "tests_results", "Api_llm_results")

os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)
os.makedirs(JMX_FOLDER, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

api_template_file = os.path.join(input_folder, "Api_template.xlsx")
ini_file_path = os.path.join(input_folder, "locust_config.ini")

locust_config = configparser.ConfigParser()
locust_config.read(ini_file_path)

# Default Fallbacks for performance config mapping
performance_config = {
    "ramp_users": locust_config.get("api-performance", "ramp_users") if locust_config.has_section(
        "api-performance") else "1",
    "spawn_rate": locust_config.get("api-performance", "spawn_rate") if locust_config.has_section(
        "api-performance") else "1",
    "run_time": locust_config.get("api-performance", "run_time") if locust_config.has_section(
        "api-performance") else "60",
    "stop_time": locust_config.get("api-performance", "stop_time") if locust_config.has_section(
        "api-performance") else "10"
}

# -------------------------------------------
# STREAMLIT CONFIG
# -------------------------------------------
st.set_page_config(
    page_title="TigerQE AI iQEA",
    page_icon="🤖",
    layout="centered"
)

if "api_data" not in st.session_state:
    st.session_state.api_data = None

st.title("🤖 TigerQE AI Platform - API Validator")

# ============================================================
# INPUT MODE
# ============================================================
st.subheader("Select Input Mode")
mode = st.radio("Choose API Source", ["Document", "Swagger"])

performance_flag = False
perf_engine = "Locust"

if mode == "Document":
    performance_flag = st.checkbox("Performance Required?")
    if performance_flag:
        perf_engine = st.radio("Select Performance Engine", ["Locust", "JMeter (v5.6.3)"], index=0, horizontal=True)

# ============================================================
# DOCUMENT MODE
# ============================================================
if mode == "Document":

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Upload API Details Excel document",
            type=["xlsx"]
        )

    with col2:
        with open(api_template_file, "rb") as f:
            st.download_button(
                "⬇ Download Template",
                f,
                file_name="API_Test_Template.xlsx"
            )

    if uploaded_file:
        api_list = swagger_utils.read_excel_input(uploaded_file)
        st.session_state.api_data = api_list
        st.success("API file uploaded successfully")
        st.dataframe(pd.DataFrame(api_list))

    if st.button("Validate APIs"):
        if not st.session_state.api_data:
            st.error("Upload API Excel file")
        else:
            results = []
            performance_result = []
            api_list = st.session_state.api_data
            progress = st.progress(0)

            # --- JMeter JMX Compilation Flow Hook ---
            if performance_flag and perf_engine == "JMeter (v5.6.3)":
                st.info("📦 Compiling performance blueprint specs directly into JMeter structure...")
                try:
                    excel_sheets = pd.read_excel(uploaded_file, sheet_name=None)
                    compiled_template_data = ""
                    for sheet, df_sheet in excel_sheets.items():
                        compiled_template_data += f"\n--- Sheet Data Profile: {sheet} ---\n{df_sheet.to_string(index=False)}\n"

                    # Call utility module generation structure
                    ai_generation_instruction = f"Generate a COMPLETE, VALID, EXECUTABLE JMeter JMX file for version 5.6.3 utilizing this structured matrix:\n{compiled_template_data}"
                    response = utilitymodule.get_output_from_ai(ai_generation_instruction)

                    if response:
                        if response and not str(response).strip().startswith("<!DOCTYPE html>"):
                            st.session_state.generated_jmx = str(response)
                        file_path = os.path.join(JMX_FOLDER, "api_generated_test_plan.jmx")
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(str(response))
                        st.session_state.generated_jmx_path = file_path
                        st.success("✅ JMeter JMX Performance Blueprint saved successfully.")
                    else:
                        st.error(
                            "❌ Received an unexpected HTML response layout from the server instead of script configurations. Please check your API access keys or network route endpoints.")
                except Exception as e:
                    st.error(f"❌ Error compiling automated JMX template: {e}")

            for i, api_data in enumerate(api_list):
                if not str(api_data.get("Validate?")):
                    continue

                api_response, combined_url, http_method = api_utils.Apicore().makeapicall(
                    api_data, "file"
                )

                if not api_response:
                    results.append({
                        "Method": http_method,
                        "Endpoint": combined_url,
                        "Status": "NO RESPONSE",
                        "Actual Response": "",
                        "Expected Response": "",
                        "Result": "FAIL"
                    })
                    continue

                # Validation Logic Engine
                http_method = http_method.upper()
                if http_method == "GET":
                    expected_output = api_data.get("expected_message", "")
                    result = api_utils.Apicore().validate_api_result(api_response, expected_output)
                elif http_method in ["POST", "PUT"]:
                    request_payload = api_data.get("payload", {})
                    if isinstance(request_payload, str):
                        try:
                            request_payload = json.loads(request_payload)
                        except Exception:
                            pass
                    result = api_utils.Apicore().validate_post_response(api_response, request_payload)
                elif http_method in ["PATCH", "DELETE"]:
                    result = "PASS" if api_response.status_code < 400 else "FAIL"
                else:
                    result = "FAIL"

                results.append({
                    "Method": http_method,
                    "Endpoint": combined_url,
                    "Status": api_response.status_code,
                    "Actual Response": api_response.text[:200] + "..." if len(api_response.text) > 200 else api_response.text,
                    "Expected Response": api_data.get("expected_message", ""),
                    "Result": result
                })

                # Performance Call Hook (Only routes to Locust if selected)
                if performance_flag and str(api_data.get("Performance?")) and perf_engine == "Locust":
                    report_path, locust_csv_path = api_utils.Apicore().makeperformancecall(api_data, "file")
                    performance_result.append(report_path)

                progress.progress((i + 1) / len(api_list))

            # Render UI Dataframes
            df = pd.DataFrame(results)

            def color_rows(row):
                return ["background-color: #c8f7c5" if row["Result"] == "PASS" else "background-color: #f7c5c5"] * len(row)

            st.success("API Functional Testing Completed")
            st.dataframe(df.style.apply(color_rows, axis=1), width="stretch")

            # Process Reports depending on underlying Engine choices
            if performance_flag and perf_engine == "Locust" and performance_result:
                api_response_analysis_prompt = swagger_utils.api_response_prompt(results)
                st.session_state.api_response_analysis = swagger_utils.get_queries_from_ai_updated(api_response_analysis_prompt)
                api_response_html = swagger_utils.save_html_report(st.session_state.api_response_analysis, REPORT_DIR, "Api_Response")

                performance_extracted_data = swagger_utils.collect_locust_csv_from_paths(performance_result)
                locust_covert_prompt = swagger_utils.locust_convert_prompt(performance_extracted_data, performance_config)
                st.session_state.locust_convert_response = swagger_utils.get_queries_from_ai_updated(locust_covert_prompt)

                api_performance_response_html = swagger_utils.save_html_report(st.session_state.locust_convert_response, REPORT_DIR, "Api_Performance_Response")

                api_utils.Apicore().show_locust_report(performance_result)
                api_utils.Apicore().show_llm_response(api_response_html, "API_response")
                api_utils.Apicore().show_llm_response(api_performance_response_html, "Performance_response")

if performance_flag and perf_engine == "JMeter (v5.6.3)" and st.session_state.generated_jmx:
    st.markdown("---")
    st.subheader("📊 Generated JMeter Script Output")
    st.text_area("Raw JMX Test Plan", value=st.session_state.generated_jmx, height=250)

    st.download_button(
        label="⬇ Download 5.6.3 JMX File",
        data=st.session_state.generated_jmx,
        file_name="api_generated_test_plan.jmx",
        mime="application/xml"
    )

    # ==============================================================================
    # 🚀 INTEGRATED LIVE JMETER EXECUTION CONSOLE
    # ==============================================================================
    st.markdown("---")
    st.subheader("🚀 Active Test Execution & Live Telemetry Monitoring Console")

    jmeter_path = st.text_input(
        "JMeter Executable Path / Command",
        value="jmeter",
        help="Update this with the absolute path to your jmeter.bat/jmeter if it is not added to your system Environment PATH variables.",
        key="api_exec_jmeter_path"
    )

    # Dynamic Runtime Parameter Tuning (Bound directly to user session variables to stop reset glitches)
    st.markdown("##### ⚙️ Adjust Runtime Thread Group Parameters")
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)

    runtime_threads = col_t1.number_input("Number of Users (Threads)", min_value=1, step=1, key="runtime_threads")
    runtime_rampup = col_t2.number_input("Ramp-up Period (seconds)", min_value=1, step=1, key="runtime_rampup")
    runtime_loops = col_t3.number_input("Loop Count (-1 for Infinite)", min_value=-1, step=1, key="runtime_loops")
    runtime_duration = col_t4.number_input("Duration (seconds; 0 to disable)", min_value=0, step=1, key="runtime_duration")

    if st.button("🚀 Run Live Test Script", key="btn_run_api_jmeter"):
        jmx_full_path = st.session_state.generated_jmx_path

        if not jmx_full_path or not os.path.exists(jmx_full_path):
            st.error("❌ Blueprint configuration template error: JMX target not found locally.")
        else:
            with st.spinner("🔧 Re-calibrating Thread Groups with user-defined overrides..."):
                runtime_config = {
                    "threads": runtime_threads,
                    "rampup": runtime_rampup,
                    "loops": runtime_loops,
                    "duration": runtime_duration if runtime_duration > 0 else None
                }

                updated_jmx_str = utilitymodule.update_jmx_file(st.session_state.generated_jmx, runtime_config)
                temp_dir = tempfile.gettempdir()
                runtime_jmx_path = os.path.join(temp_dir, "runtime_api_execution.jmx")
                with open(runtime_jmx_path, "w", encoding="utf-8") as f:
                    f.write(updated_jmx_str)

            base_name = "api_runtime_run"
            report_base_dir = os.path.join(current_path, "jmeter_reports", base_name)
            output_jtl = os.path.join(report_base_dir, f"{base_name}_log.jtl")
            html_report_dir = os.path.join(report_base_dir, "html_dashboard")

            os.makedirs(report_base_dir, exist_ok=True)

            if os.path.exists(output_jtl):
                try: os.remove(output_jtl)
                except OSError: pass

            if os.path.exists(html_report_dir):
                try: shutil.rmtree(html_report_dir)
                except OSError: pass

            command = [
                jmeter_path, "-n",
                "-t", runtime_jmx_path,
                "-l", output_jtl,
                "-e", "-o", html_report_dir,
                "-Jsummariser.name=summary"
            ]

            st.subheader("📺 Live JMeter Console Stream")
            log_stdout_box = st.empty()
            accumulated_logs = ""

            with st.spinner("Spawning JMeter background instance process thread..."):
                try:
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        shell=True
                    )

                    while True:
                        line = process.stdout.readline()
                        if not line and process.poll() is not None:
                            break
                        if line:
                            accumulated_logs += line
                            log_stdout_box.code(accumulated_logs[-4000:])

                    return_code = process.poll()
                    if return_code == 0:
                        st.success("✅ JMeter test cycle completed successfully!")
                        st.info(f"📊 HTML Dashboard Directory created at: {html_report_dir}")
                    else:
                        st.error(f"❌ JMeter engine process exited with an error code: {return_code}")
                        st.info("Review the terminal streaming log output box above to diagnose runtime anomalies.")
                except Exception as ex:
                    st.error(f"❌ Automation runtime failure: Failed to spawn thread process execution: {ex}")

# ==============================
# SWAGGER INPUT MODE
# ==============================
if mode == "Swagger":
    st.subheader("Swagger API Flow")
    swagger_url = st.text_input(
        "Swagger / OpenAPI URL",
        placeholder="https://virtserver.swaggerhub.com/xxx/1.0.0/swagger.json"
    )

    if st.button("Fetch APIs from Swagger"):
        if not swagger_url:
            st.error("Please enter Swagger URL")
        else:
            try:
                spec = swagger_utils.load_openapi_spec(swagger_url)
                api_details = swagger_utils.extract_api_details(spec)
                base_url = swagger_utils.get_base_url(api_details, spec)
                api_list = swagger_utils.build_data_dictionary(api_details, base_url, spec)

                for idx, api in enumerate(api_list):
                    api["Validate?"] = True
                    api["Performance?"] = False
                    api["__id__"] = f"{api['httpMethod']}_{api['endpoint']}_{idx}"

                st.session_state.swagger_apis = api_list
                st.success(f"Loaded {len(api_list)} APIs from Swagger")
                st.dataframe(api_list)
            except Exception as e:
                st.error(f"Failed to load Swagger APIs: {e}")

    if st.session_state.swagger_apis:
        st.markdown("---")
        st.subheader("API Selection")

        header = st.columns([4, 2, 2, 4])
        header[0].markdown("**Endpoint**")
        header[1].markdown("**Validate**")
        header[2].markdown("**Performance**")
        header[3].markdown("**Payload (for POST/PUT)**")

        for api in st.session_state.swagger_apis:
            cols = st.columns([4, 2, 2, 4])
            cols[0].write(f"{api['httpMethod']} {api['endpoint']}")

            validate_key = f"swagger_validate_{api['__id__']}"
            perf_key = f"swagger_perf_{api['__id__']}"
            payload_key = f"swagger_payload_{api['__id__']}"

            if validate_key not in st.session_state:
                st.session_state[validate_key] = api["Validate?"]
            if perf_key not in st.session_state:
                st.session_state[perf_key] = api["Performance?"]
            if payload_key not in st.session_state:
                if api["httpMethod"] in ["POST", "PUT"]:
                    st.session_state[payload_key] = api['payload']
                    api["payload"] = api['payload']
                else:
                    st.session_state[payload_key] = {}

            api["Validate?"] = cols[1].checkbox("", key=validate_key)
            api["Performance?"] = cols[2].checkbox("", key=perf_key)

            if api["httpMethod"] in ["POST", "PUT"]:
                updated_payload = cols[3].text_area(
                    "Edit Payload",
                    value=json.dumps(st.session_state[payload_key], indent=2),
                    height=150,
                    key=f"payload_text_{api['__id__']}"
                )
                try:
                    api["payload"] = json.loads(updated_payload)
                    st.session_state[payload_key] = api["payload"]
                except Exception as e:
                    st.warning(f"Invalid JSON payload: {e}")

        st.markdown("---")
        if st.button("Run Selected Swagger APIs"):
            results = []
            performance_result = []

            for api in st.session_state.swagger_apis:
                if api.get("Validate?"):
                    response, combined_url, http_method = api_utils.Apicore().makeapicall(api, "Swegger")
                    if response:
                        status = response.status_code
                        if http_method in ["POST", "PUT"]:
                            request_payload = api.get("payload", {})
                            result = api_utils.Apicore().validate_post_response(response, request_payload)
                        else:
                            expected_output = api.get("expectedOutput", {})
                            try:
                                response_json = response.json()
                            except:
                                response_json = response.text
                            result = api_utils.Apicore().validate_api_result(response_json, expected_output)
                    else:
                        status = "NO RESPONSE"
                        result = "FAIL"

                    results.append(
                        {"Method": http_method, "Endpoint": combined_url, "Status": status, "Result": result})

                if api.get("Performance?"):
                    path, locust_csv_path = api_utils.Apicore().makeperformancecall(api, "Swegger")
                    if path:
                        performance_result.append(path)

            if results:
                df = pd.DataFrame(results)

                def highlight_result(row):
                    return ["background-color: #c8f7c5" if row["Result"] == "PASS" else "background-color: #f7c5c5"] * len(row)

                st.subheader("Validation Results")
                st.dataframe(df.style.apply(highlight_result, axis=1), width="stretch")

            if performance_result:
                api_utils.Apicore().show_locust_report(performance_result)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.markdown("""
### 📞 Contact
QE Core Team  
📧 sahil.gupta@tigeranalytics.com
""")