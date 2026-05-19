
import os
import json
import pandas as pd
import streamlit as st
import urllib3
import configparser
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------------------------------
# Import API utilities
# -------------------------------------------
from utilities.API_Utils import api_core_model as api_utils
from utilities.API_Utils import swaggerhub as swagger_utils
import allure

swagger_utils.init_allure_results()

if "swagger_apis" not in st.session_state:
    st.session_state.swagger_apis = []
if "api_response_analysis" not in st.session_state:
    st.session_state.api_response_analysis=[]
if "api_performance_analysis" not in st.session_state:
    st.session_state.api_performance_analysis=[]
if "locust_convert_response" not in st.session_state:
    st.session_state.locust_convert_response=[]
# -------------------------------------------
# FOLDER CONFIG
# -------------------------------------------
current_path = os.getcwd()
input_folder = os.path.join(current_path, "Input")
output_folder = os.path.join(current_path, "output")
api_template_file = os.path.join(input_folder, "Api_template.xlsx")
REPORT_DIR = os.path.join(os.getcwd(), "tests_results", "Api_llm_results")
os.makedirs(REPORT_DIR, exist_ok=True)

os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)
ini_file_path = os.path.join(input_folder, "locust_config.ini")
locust_config = configparser.ConfigParser()
locust_config.read(ini_file_path)
performance_config = {
    "ramp_users": locust_config.get("api-performance", "ramp_users"),
    "spawn_rate": locust_config.get("api-performance", "spawn_rate"),
    "run_time": locust_config.get("api-performance", "run_time"),
    "stop_time": locust_config.get("api-performance", "stop_time")
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
if mode is "Document":
    performance_flag = st.checkbox("Performance Required?")

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

                # ----------------------------
                # Validation
                # ----------------------------
                http_method = http_method.upper()

                if http_method == "GET":
                    expected_output = api_data.get("expected_message", "")
                    result = api_utils.Apicore().validate_api_result(
                        api_response, expected_output
                    )

                elif http_method in ["POST", "PUT"]:
                    print("check api_data",api_data)
                    request_payload = api_data.get("payload", {})
                    if isinstance(request_payload, str):
                        request_payload = json.loads(request_payload)

                    result = api_utils.Apicore().validate_post_response(
                        api_response, request_payload
                    )

                elif http_method in ["PATCH", "DELETE"]:
                    result = "PASS" if api_response.status_code < 400 else "FAIL"

                else:
                    result = "FAIL"

                results.append({
                    "Method": http_method,
                    "Endpoint": combined_url,
                    "Status": api_response.status_code,
                    "Actual Response": api_response.text,
                    "Expected Response": api_data.get("expected_message", ""),
                    "Result": result
                })

                # ----------------------------
                # Performance
                # ----------------------------
                if performance_flag and str(api_data.get("Performance?")):
                    report_path,locust_csv_path = api_utils.Apicore().makeperformancecall(
                        api_data, "file"
                    )
                    performance_result.append(report_path)

                progress.progress((i + 1) / len(api_list))

            df = pd.DataFrame(results)
            api_response_analysis_prompt=swagger_utils.api_response_prompt(results)
            st.session_state.api_response_analysis=swagger_utils.get_queries_from_ai_updated(api_response_analysis_prompt)
            api_response_html=swagger_utils.save_html_report(st.session_state.api_response_analysis,REPORT_DIR,"Api_Response")
            performance_extracted_data=swagger_utils.collect_locust_csv_from_paths(performance_result)

            print("******performance_extracted_data****",performance_extracted_data)
            locust_covert_prompt=swagger_utils.locust_convert_prompt(performance_extracted_data,performance_config)
            print("******locust_covert_prompt****", locust_covert_prompt)
            st.session_state.locust_convert_response=swagger_utils.get_queries_from_ai_updated(locust_covert_prompt)
            print("******locust_convert_response****", st.session_state.locust_convert_response)
            # api_performance_analysis_prompt=swagger_utils.api_performace_reponse_prompt(st.session_state.locust_convert_response,performance_config)
            # print("******api_performance_analysis_prompt****", api_performance_analysis_prompt)
            # st.session_state.api_performance_analysis=swagger_utils.get_queries_from_ai_updated(api_performance_analysis_prompt)
            # print("******api_performance_analysis****", st.session_state.api_performance_analysis)
            api_performance_response_html = swagger_utils.save_html_report(st.session_state.locust_convert_response, REPORT_DIR,
                                                               "Api_Performance_Response")

            def color_rows(row):
                return [
                    "background-color: #c8f7c5" if row["Result"] == "PASS"
                    else "background-color: #f7c5c5"
                ] * len(row)

            st.success("API Testing Completed")
            st.dataframe(df.style.apply(color_rows, axis=1), use_container_width=True)

            api_utils.Apicore().show_locust_report(performance_result)
            api_utils.Apicore().show_llm_response(api_response_html,"API_response")
            api_utils.Apicore().show_llm_response(api_performance_response_html,"Performance_response")


# ==============================
# SESSION STATE INIT
# ==============================
if mode == "Swagger":
    if "swagger_apis" not in st.session_state:
        st.session_state.swagger_apis = []

    # ==============================
    # SWAGGER INPUT
    # ==============================
    st.subheader("Swagger API Flow")

    swagger_url = st.text_input(
        "Swagger / OpenAPI URL",
        placeholder="https://virtserver.swaggerhub.com/xxx/1.0.0/swagger.json"
    )

    # ==============================
    # FETCH SWAGGER APIs
    # ==============================
    if st.button("Fetch APIs from Swagger"):
        if not swagger_url:
            st.error("Please enter Swagger URL")
        else:
            try:
                spec = swagger_utils.load_openapi_spec(swagger_url)
                api_details = swagger_utils.extract_api_details(spec)
                base_url = swagger_utils.get_base_url(api_details, spec)

                api_list = swagger_utils.build_data_dictionary(api_details, base_url,spec)

                for idx, api in enumerate(api_list):
                    api["Validate?"] = True
                    api["Performance?"] = False
                    api["__id__"] = f"{api['httpMethod']}_{api['endpoint']}_{idx}"

                st.session_state.swagger_apis = api_list
                st.success(f"Loaded {len(api_list)} APIs from Swagger")
                st.dataframe(api_list)

            except Exception as e:
                st.error(f"Failed to load Swagger APIs: {e}")
    # ==============================
    # DISPLAY API SELECTION UI
    # ==============================
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
                # Generate sample payload if POST/PUT and payload is empty
                if api["httpMethod"] in ["POST", "PUT"]:
                    print("*********Api_payload**********",api['payload'])
                    sample_payload =api['payload']
                        #swagger_utils.generate_example_payload(api.get("requestSchema", {}))
                    st.session_state[payload_key] = sample_payload
                    api["payload"] = sample_payload
                else:
                    st.session_state[payload_key] = {}

            api["Validate?"] = cols[1].checkbox("", key=validate_key)
            api["Performance?"] = cols[2].checkbox("", key=perf_key)

            # Editable payload textbox for POST/PUT
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

    if st.session_state.swagger_apis:
        st.markdown("---")

        if st.button("Run Selected Swagger APIs"):
            results = []
            performance_result = []
            print("swegger_api_data_core", st.session_state.swagger_apis)
            for api in st.session_state.swagger_apis:

                # ======================
                # VALIDATION FLOW
                # ======================
                if api.get("Validate?"):
                    response, combined_url, http_method = api_utils.Apicore().makeapicall(
                        api, "Swegger"
                    )

                    if response:
                        status = response.status_code

                        if http_method in ["POST", "PUT"]:
                            print("swegger_api_data",api)
                            request_payload = api.get("**********payload*************", {})
                            result = api_utils.Apicore().validate_post_response(
                                response, request_payload
                            )
                        else:
                            expected_output = api.get("expectedOutput", {})
                            try:
                                response_json = response.json()
                            except:
                                response_json = response.text

                            result = api_utils.Apicore().validate_api_result(
                                response_json, expected_output
                            )
                    else:
                        status = "NO RESPONSE"
                        result = "FAIL"

                    results.append({
                        "Method": http_method,
                        "Endpoint": combined_url,
                        "Status": status,
                        "Result": result
                    })

                # ======================
                # PERFORMANCE FLOW
                # ======================
                if api.get("Performance?"):
                    path,locust_csv_path = api_utils.Apicore().makeperformancecall(api, "Swegger")
                    if path:
                        performance_result.append(path)

            # ======================
            # SHOW VALIDATION RESULT
            # ======================
            if results:
                df = pd.DataFrame(results)

                def highlight_result(row):
                    return [
                        "background-color: #c8f7c5" if row["Result"] == "PASS"
                        else "background-color: #f7c5c5"
                    ] * len(row)

                st.subheader("Validation Results")
                st.dataframe(
                    df.style.apply(highlight_result, axis=1),
                    use_container_width=True
                )

            # ======================
            # SHOW PERFORMANCE REPORTS
            # ======================
            if performance_result:
                api_utils.Apicore().show_locust_report(performance_result)
            api_response_analysis_prompt = swagger_utils.api_response_prompt(results)
            st.session_state.api_response_analysis = swagger_utils.get_queries_from_ai_updated(api_response_analysis_prompt)
            api_response_html = swagger_utils.save_html_report(st.session_state.api_response_analysis, REPORT_DIR,
                                                               "Api_Response")
            if performance_result:
                performance_extracted_data = swagger_utils.collect_locust_csv_from_paths(performance_result)

                print("******performance_extracted_data****", performance_extracted_data)
                locust_covert_prompt = swagger_utils.locust_convert_prompt(performance_extracted_data)
                print("******locust_covert_prompt****", locust_covert_prompt)
                st.session_state.locust_convert_response = swagger_utils.get_queries_from_ai_updated(locust_covert_prompt)
                print("******locust_convert_response****", st.session_state.locust_convert_response)
            api_performance_analysis_prompt = swagger_utils.api_performace_reponse_prompt(
                st.session_state.locust_convert_response, performance_config)
            print("******api_performance_analysis_prompt****", api_performance_analysis_prompt)
            st.session_state.api_performance_analysis = swagger_utils.get_queries_from_ai_updated(
                api_performance_analysis_prompt)
            if performance_result:
                print("******api_performance_analysis****", st.session_state.api_performance_analysis)
                api_performance_response_html = swagger_utils.save_html_report(st.session_state.api_performance_analysis,
                                                                           REPORT_DIR,
                                                                           "Api_Performance_Response")

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.markdown("""
### 📞 Contact
QE Core Team  
📧 sahil.gupta@tigeranalytics.com
""")
