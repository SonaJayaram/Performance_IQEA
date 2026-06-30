import os
import json
import tempfile
import subprocess
import shutil
import time  # Allowed network sockets to bind cleanly
from datetime import datetime
import configparser
import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------------------------------
# Import API utilities
# -------------------------------------------
from utilities.API_Utils import api_core_model as api_utils
from utilities.API_Utils import swaggerhub as swagger_utils
import utilitymodule
import allure

# Safe initialization of allure results using absolute project root hierarchy
root_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) if "__file__" in locals() else os.getcwd()
allure_dir = os.path.join(root_dir, "allure-results")
if os.path.exists(allure_dir):
    for filename in os.listdir(allure_dir):
        file_path = os.path.join(allure_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception:
            pass
else:
    os.makedirs(allure_dir, exist_ok=True)

# Initialize Session States
state_vars = [
    "swagger_apis", "api_response_analysis", "api_performance_analysis",
    "locust_convert_response", "generated_jmx", "generated_jmx_path"
]
for var in state_vars:
    if var not in st.session_state:
        st.session_state[var] = [] if "analysis" in var or "response" in var or "apis" in var else ""

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
            type=["xlsx"],
            key="api_excel_uploader"
        )

    with col2:
        with open(api_template_file, "rb") as f:
            st.download_button("⬇ Download Template", f, file_name="API_Test_Template.xlsx")

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
            api_list = st.session_state.api_data
            progress = st.progress(0)

            for i, api_data in enumerate(api_list):
                if not str(api_data.get("Validate?")):
                    continue

                api_response, combined_url, http_method = api_utils.Apicore().makeapicall(api_data, "file")

                if not api_response:
                    results.append({
                        "Method": http_method, "Endpoint": combined_url, "Status": "NO RESPONSE",
                        "Actual Response": "", "Expected Response": "", "Result": "FAIL"
                    })
                    continue

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
                    "Actual Response": api_response.text[:200] + "..." if len(
                        api_response.text) > 200 else api_response.text,
                    "Expected Response": api_data.get("expected_message", ""),
                    "Result": result
                })

                progress.progress((i + 1) / len(api_list))

            df = pd.DataFrame(results)


            def color_rows(row):
                return ["background-color: #c8f7c5" if row["Result"] == "PASS" else "background-color: #f7c5c5"] * len(
                    row)


            st.success("API Functional Testing Completed")
            st.dataframe(df.style.apply(color_rows, axis=1), width="stretch")

    # ==============================================================================
    # 📊 JMETER CONTROLLER MATRIX WITH VM-TO-VM DISTRIBUTED MATRIX SETUP
    # ==============================================================================
    if performance_flag and perf_engine == "JMeter (v5.6.3)":
        st.markdown("---")
        st.subheader("🏁 JMeter Test Plan Provisioning Selection")

        jmx_source_mode = st.radio(
            "Select Script Method",
            ["Upload Existing JMX Script File", "Generate with AI Engine Blueprint Matrix"],
            index=0, horizontal=True
        )

        if jmx_source_mode == "Upload Existing JMX Script File":
            uploaded_jmx = st.file_uploader("Upload your operational target .jmx file", type=["jmx"],
                                            key="direct_jmx_uploader")
            if uploaded_jmx:
                jmx_string_content = uploaded_jmx.getvalue().decode("utf-8")
                st.session_state.generated_jmx = jmx_string_content
                saved_uploaded_path = os.path.join(JMX_FOLDER, "runtime_api_execution.jmx")
                with open(saved_uploaded_path, "w", encoding="utf-8") as f:
                    f.write(jmx_string_content)
                st.session_state.generated_jmx_path = saved_uploaded_path
                st.success(f"📂 Operational script cached locally.")
        else:
            if st.button("📦 Build Script Matrix Plan via AI"):
                if not uploaded_file:
                    st.error("Please upload the baseline API Excel Document at the top first.")
                else:
                    st.info("📦 Compiling performance blueprint specs directly into JMeter structure...")
                    try:
                        excel_sheets = pd.read_excel(uploaded_file, sheet_name=None)
                        compiled_template_data = ""
                        for sheet, df_sheet in excel_sheets.items():
                            compiled_template_data += f"\n--- Sheet Data Profile: {sheet} ---\n{df_sheet.to_string(index=False)}\n"

                        ai_generation_instruction = (
                            "Generate a COMPLETE, VALID, EXECUTABLE JMeter JMX file for version 5.6.3 utilizing this structured matrix:\n"
                            f"{compiled_template_data}\n"
                            "CRITICAL INSTRUCTION: Do NOT use 'localhost' inside the Server Name / IP configurations "
                            "for your HTTP Samplers or HTTP Request Defaults. Instead, use the dynamic property token: ${__P(target_host,10.0.0.4)}"
                        )
                        response = utilitymodule.get_output_from_ai(ai_generation_instruction)

                        if response and not str(response).strip().startswith("<!DOCTYPE html>"):
                            st.session_state.generated_jmx = str(response)
                            file_path = os.path.join(JMX_FOLDER, "runtime_api_execution.jmx")
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(str(response))
                            st.session_state.generated_jmx_path = file_path
                            st.success("✅ JMeter JMX Performance Blueprint saved successfully.")
                        else:
                            st.error("❌ Unexpected script parsing error. Check system keys.")
                    except Exception as e:
                        st.error(f"❌ Error compiling automated JMX template: {e}")

        if st.session_state.generated_jmx:
            st.markdown("---")
            st.subheader("⚙️ Execution Configuration Engine")

            execution_profile = st.selectbox(
                "Choose Test Execution Profile",
                ["Local Dry Run / Smoke Test (Your Machine Only)",
                 "Actual Load Test (Distributed Master-Slave Config)"],
                index=0
            )

            st.markdown("##### ⚙️ Adjust Runtime Thread Group Parameters")
            col_t1, col_t2, col_t3, col_t4 = st.columns(4)

            if "Local Dry Run" in execution_profile:
                runtime_threads = col_t1.number_input("Number of Users (Threads)", min_value=1, value=1, step=1)
                runtime_rampup = col_t2.number_input("Ramp-up Period (seconds)", min_value=1, value=1, step=1)
                runtime_loops = col_t3.number_input("Loop Count (-1 for Infinite)", min_value=-1, value=1, step=1)
                runtime_duration = col_t4.number_input("Duration (seconds; 0 to disable)", min_value=0, value=5, step=1)
            else:
                runtime_threads = col_t1.number_input("Number of Users (Threads)", min_value=1, value=10, step=1)
                runtime_rampup = col_t2.number_input("Ramp-up Period (seconds)", min_value=1, value=5, step=1)
                runtime_loops = col_t3.number_input("Loop Count (-1 for Infinite)", min_value=-1, value=-1, step=1)
                runtime_duration = col_t4.number_input("Duration (seconds)", min_value=1, value=120, step=1)

            jmeter_path = st.text_input("Local JMeter Executable Path",
                                        value=r"F:\Sona_Performance\apache-jmeter-5.6.3\apache-jmeter-5.6.3\bin\jmeter.bat",
                                        key="api_exec_jmeter_path")

            st.markdown("---")
            st.subheader("📊 Live Telemetry Metric Redirection")

            grafana_url = st.text_input(
                "Your Grafana Dashboard URL",
                value="http://localhost:3000/d/adrjwwj/iqeadashboard?orgId=1&refresh=5s&panelId=1"
            )

            if "http" in grafana_url:
                st.link_button("📈 Open Live Grafana Monitor Dashboard", grafana_url, type="primary",
                               use_container_width=True)

            if "Actual Load Test" in execution_profile:
                local_master_ip = st.text_input("Master VM Infrastructure IP", value="10.0.0.4", disabled=True)
                remote_slave_ip = st.text_input("Slave VM Target Node IP", value="10.0.0.5", disabled=True)

            if st.button("🚀 Fire Performance Execution Plan", key="btn_run_api_jmeter"):
                jmx_full_path = st.session_state.generated_jmx_path

                if not jmx_full_path or not os.path.exists(jmx_full_path):
                    st.error("❌ Execution target configuration missing.")
                else:
                    base_name = "api_runtime_run"
                    report_base_dir = os.path.join(current_path, "jmeter_reports", base_name)
                    output_jtl = os.path.join(report_base_dir, f"{base_name}_log.jtl")
                    html_report_dir = os.path.join(report_base_dir, "html_dashboard")

                    if os.path.exists(report_base_dir):
                        try:
                            shutil.rmtree(report_base_dir)
                        except OSError:
                            pass
                    os.makedirs(report_base_dir, exist_ok=True)

                    # Scan and drop any orphan connections before binding sockets
                    if "Actual Load Test" in execution_profile:
                        try:
                            find_port_cmd = 'netstat -ano | findstr :60000'
                            port_check = subprocess.run(find_port_cmd, shell=True, capture_output=True, text=True)
                            if port_check.stdout:
                                for line in port_check.stdout.strip().split('\n'):
                                    if "LISTENING" in line or "TIME_WAIT" in line:
                                        zombie_pid = line.split()[-1]
                                        subprocess.run(f"taskkill /F /PID {zombie_pid}", shell=True,
                                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                time.sleep(2)
                        except Exception:
                            pass

                    runtime_config = {
                        "threads": int(runtime_threads),
                        "rampup": int(runtime_rampup),
                        "loops": int(runtime_loops),
                        "duration": int(runtime_duration)
                    }
                    updated_jmx_str = utilitymodule.update_jmx_file(st.session_state.generated_jmx, runtime_config)

                    updated_jmx_str = updated_jmx_str.replace("localhost:8086", "10.0.0.4:8086")
                    updated_jmx_str = updated_jmx_str.replace("127.0.0.1:8086", "10.0.0.4:8086")
                    updated_jmx_str = updated_jmx_str.replace("172.173.226.74:8086", "10.0.0.4:8086")

                    with open(jmx_full_path, "w", encoding="utf-8") as f:
                        f.write(updated_jmx_str)

                    jmeter_bin_directory = os.path.dirname(jmeter_path)

                    # -------------------------------------------------------------
                    # 🚀 SYSTEM RESOLUTION OVERRIDES (FORCES INTERNAL RMI ENGINE)
                    # -------------------------------------------------------------
                    custom_env = os.environ.copy()
                    if jmeter_bin_directory:
                        custom_env["JMETER_HOME"] = os.path.dirname(jmeter_bin_directory)

                    # Directly inject core JVM networking properties into the environment layout
                    custom_env[
                        "JVM_ARGS"] = "-Djava.rmi.server.hostname=10.0.0.4 -Dclient.rmi.localport=60000 -Dserver.rmi.ssl.disable=true"

                    if "Local Dry Run" in execution_profile:
                        st.info("🏃‍♂️ Running standalone local smoke iteration...")
                        cmd_args = [
                            jmeter_path,
                            "-Jtarget_host=localhost",
                            "-n", "-t", jmx_full_path,
                            "-l", output_jtl,
                            "-Jsummariser.name=summary"
                        ]
                    else:
                        st.info(
                            "🌐 Triggering Distributed Infrastructure Load Layout across Private Virtual Machines...")
                        cmd_args = [
                            jmeter_path,
                            "-Jjmeter.reportgenerator.ignore_bad_lines=true",
                            "-Jjmeter.save.saveservice.output_format=csv",
                            "-Jtarget_host=10.0.0.4",
                            "-n", "-t", jmx_full_path,
                            "-R", "10.0.0.5:1099",
                            "-l", output_jtl,
                            "-Jsummariser.name=summary"
                        ]

                    try:
                        st.caption(f"Executing Stream Stack: {' '.join(cmd_args)}")

                        process = subprocess.Popen(
                            cmd_args, shell=False, env=custom_env, cwd=jmeter_bin_directory,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
                        )

                        log_stdout_box = st.empty()
                        accumulated_logs = ""

                        # Dynamically align loops to test runtime context + give a clean 60s environment cushion
                        max_allowed_seconds = int(runtime_duration) + 60 if int(runtime_duration) > 0 else 720
                        start_time = datetime.now()

                        # =============================================================
                        # 🔄 LOG-STREAMING LOOP
                        # =============================================================
                        while True:
                            line = process.stdout.readline()
                            if line:
                                accumulated_logs += line
                                log_stdout_box.code(accumulated_logs[-3000:])

                            if process.poll() is not None:
                                break

                            elapsed_seconds = (datetime.now() - start_time).total_seconds()
                            if elapsed_seconds > max_allowed_seconds:
                                st.warning("⚠️ Workload threshold or test duration completed. Finalizing log sync...")
                                break

                        # Explicitly terminate local master process instance to release JTL file locks
                        if process.poll() is None:
                            try:
                                subprocess.run(f"taskkill /F /T /PID {process.pid}", shell=True,
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            except Exception:
                                process.terminate()

                        # Ensure system resources are unblocked cleanly
                        process.wait()
                        st.info("⏳ Giving data buffers a brief moment to settle down...")
                        time.sleep(3)

                        # =============================================================
                        # 📊 HTML DASHBOARD GENERATION PHASE
                        # =============================================================
                        if os.path.exists(output_jtl) and os.path.getsize(output_jtl) > 100:
                            st.success("🎉 Performance test workflow compiled completely!")

                            # 🛠️ Sanitize JTL file by removing truncated/incomplete last lines
                            try:
                                with open(output_jtl, "r", encoding="utf-8", errors="ignore") as f:
                                    lines = f.readlines()

                                if lines:
                                    # Find the header column count to use as our validation blueprint
                                    expected_columns = len(lines[0].split(','))
                                    # Inspect the very last line written before the taskkill
                                    last_line_columns = len(lines[-1].split(','))

                                    # If the last line is truncated, slice it off safely
                                    if last_line_columns < expected_columns:
                                        with open(output_jtl, "w", encoding="utf-8") as f:
                                            f.writelines(lines[:-1])
                                        st.caption(
                                            "🔧 Sanitized incomplete trailing log artifacts from hard-stop sequence.")
                            except Exception as e:
                                st.warning(f"⚠️ Log pre-check optimization bypassed: {e}")

                            # Completely remove target folder to satisfy JMeter's generation rule
                            if os.path.exists(html_report_dir):
                                try:
                                    shutil.rmtree(html_report_dir)
                                except Exception:
                                    pass

                            st.info("📊 Generating JMeter HTML Dashboard...")
                            report_cmd = [
                                jmeter_path,
                                "-g", output_jtl,
                                "-o", html_report_dir
                            ]

                            report_process = subprocess.run(
                                report_cmd,
                                shell=False,
                                cwd=jmeter_bin_directory,
                                env=custom_env,
                                capture_output=True,
                                text=True
                            )

                            if report_process.returncode == 0:
                                st.success("✅ HTML Report generated successfully.")
                                st.info(f"📊 Dashboard Location: {html_report_dir}")
                            else:
                                st.error("❌ HTML Report generation failed.")
                                st.code(report_process.stdout)
                                st.code(report_process.stderr)
                        else:
                            st.error(
                                "❌ Log data was completely empty due to a hard connection block from the slave machine. No metrics were returned.")

                    except Exception as ex:
                        st.error(f"❌ Core runtime engine crash: {ex}")

# ==============================
# SWAGGER INPUT MODE
# ==============================
if mode == "Swagger":
    st.subheader("Swagger API Flow")
    swagger_url = st.text_input("Swagger / OpenAPI URL",
                                placeholder="https://virtserver.swaggerhub.com/xxx/1.0.0/swagger.json")

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

st.divider()
st.markdown("### 📞 Contact\nQE Core Team  \n📧 sahil.gupta@tigeranalytics.com")