import os
import json
import pandas as pd
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------------------------------------------
# Import your actual utilities
# -------------------------------------------------------
from utilities.API_Utils import api_core_model as api_utils
from utilities.API_Utils import swaggerhub as swagger_utils

# -------------------------------------------------------
# FOLDER CONFIG
# -------------------------------------------------------
current_path = os.getcwd()
input_folder = os.path.join(current_path, "Input")
output_folder = os.path.join(current_path, "output")
api_template_file = os.path.join(input_folder, "Api_template.xlsx")

os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)


# =======================================================
# FUNCTION: DOCUMENT MODE (Excel Input)
# =======================================================
def run_document_mode():
    print("\n========== DOCUMENT MODE ==========")

    excel_path = os.path.join(input_folder, "Api_template.xlsx")

    if not os.path.exists(excel_path):
        print(f"❌ Input Excel missing: {excel_path}")
        return

    print(f"📘 Reading Excel: {excel_path}")

    api_list = swagger_utils.read_excel_input(excel_path)
    print(f"➡ Total APIs Loaded: {len(api_list)}")

    results = []

    for api_data in api_list:
        if str(api_data.get("Validate?")):

            print("\n-------------------------------------")
            print(f"🔵 Calling API: {api_data.get('Endpoint')}")
            print("-------------------------------------")

            # MAIN API CALL
            #api_result = api_utils.Apicore().makeapicall(api_data,"file")
            api_response = api_utils.Apicore().makeapicall(api_data, "file")
            if api_response:

                expected_output = api_data.get("expected_message", {})
                result = api_utils.Apicore().validate_api_result(api_response, expected_output)
                results.append(api_data.get("test_case_name", "") + "-" + result)

            # PERFORMANCE
            if str(api_data.get("Performance?")):
                print("⚡ Running performance test...")
                api_utils.Apicore().makeperformancecall(api_data)

    print("\n=========== FINAL RESULTS ===========")
    print(pd.DataFrame(results))


# =======================================================
# FUNCTION: SWAGGER MODE
# =======================================================
def run_swagger_mode(swagger_url):
    print("\n========== SWAGGER MODE ==========")

    try:
        print(f"📡 Loading Swagger: {swagger_url}")
        spec = swagger_utils.load_openapi_spec(swagger_url)

        api_details = swagger_utils.extract_api_details(spec)
        print(f"➡ Total API Definitions: {len(api_details)}")

        base_url = swagger_utils.get_base_url(api_details, spec)
        print(f"🔗 Base URL: {base_url}")

        api_list = swagger_utils.build_data_dictionary(api_details, base_url)

        print("\n🚀 Starting Swagger API Validation...")
        results = []

        for api_data in api_list:
            print(f"\n➡ Calling API: {api_data.get('Endpoint')}")
            api_result = api_utils.Apicore().makeapicall(api_data,"swegger")
            results.append(api_result)

        print("\n=========== FINAL RESULTS ===========")
        print(pd.DataFrame(results))

    except Exception as e:
        print(f"❌ ERROR loading Swagger → {e}")


# =======================================================
# MAIN EXECUTION
# =======================================================
if __name__ == "__main__":

    print("\n==============================================")
    print("        🔍 API VALIDATOR - RAW MODE")
    print("==============================================\n")

    print("Choose Mode:")
    print("1. Document (Excel)")
    print("2. Swagger URL\n")

    mode = input("Enter option (1 or 2): ").strip()

    if mode == "1":
        run_document_mode()

    elif mode == "2":
        swagger_url = input("\nEnter Swagger URL: ").strip()
        run_swagger_mode(swagger_url)

    else:
        print("❌ Invalid option. Please choose 1 or 2.")
