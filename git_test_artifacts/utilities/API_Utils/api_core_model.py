import configparser
import shutil

import streamlit as st
import json
import re
import subprocess
import allure
import requests
from datetime import datetime
import os
from jsonpath_ng import jsonpath, parse
import logging
import configparser
from .DBconnect import getvaluefromdatabse
current_path = os.getcwd()
input_folder = os.path.join(current_path, "Input")
DB_config = configparser.ConfigParser()
DB_config.read('DBconfig.ini')
class JSONUpdater:
    def update_nested_json(self, template, key, value):
        """
        Recursively check if a key exists in a nested dictionary and update it.
        If it doesn't exist, add it.
        """
        if isinstance(template, dict):
            # If the key exists at the current level, update its value
            if key in template:
                template[key] = value
                return True

            # Recursively check nested dictionaries
            for k, v in template.items():
                if isinstance(v, dict):
                    if self.update_nested_json(v, key, value):
                        return True

            # If the key was not found in the nested dictionaries, add it at the current level
            template[key] = value
            return True

        return False


updater = JSONUpdater()



class Apicore:

    def __int__(self):
        pass


    #description:contructing uri
    def getcompleteurl(self, data_dictionary):
        """
            Constructs a complete URL from the given data dictionary.
            This method extracts the base URI and endpoint from the provided data dictionary.
            It also identifies keys that start with "endPoint-" to extract specific endpoint values,
            which are then used to build the final URL.
            """
        #base_uri = "https://reqres.in/"
        base_uri=data_dictionary.get('baseUrl', '')

        # base_uri = data_dictionary.get('base_uri', '')
        endpoint = data_dictionary.get('endPoint', '')

        extracted_endpoint = {}
        endpoint_dash = None

        # Extract endpoint- values
        for key, value in data_dictionary.items():
            if key.startswith("endPoint-"):
                endpoint_dash = key.split("-", 1)[1]
                extracted_endpoint[endpoint_dash] = value

        # Construct the output based on extracted endpoint
        if endpoint_dash:
            # Convert extracted endpoint to JSON string and back to dictionary
            json_string = json.dumps(extracted_endpoint, ensure_ascii=False)
            extracted_endpoint = json.loads(json_string)
            return base_uri + endpoint + str(extracted_endpoint[endpoint_dash])
        else:
            return base_uri + endpoint


    def getheader(self,data_dictionary):
        """
            Extracts headers from the given data dictionary.
            This method scans through the provided data dictionary, identifies keys that start with "headers-",
            and extracts the corresponding values to form a dictionary of headers.
            """
        # Create an empty dictionary to store the extracted headers
        extracted_headers = {}

        # Iterate over the keys of the original dictionary
        for key, value in data_dictionary.items():
            # Check if the key starts with "headers-"
            if key.startswith("headers-"):
                # Extract the part after "headers-"
                header_key = key.split("-", 1)[1]
                # Add the extracted header to the new dictionary
                extracted_headers[header_key] = value

            json_string = json.dumps(extracted_headers, ensure_ascii=False)
            # Convert the JSON string back to a dictionary
            extracted_headers = json.loads(json_string)
        #Return Extracted Headers
        return extracted_headers

    def getexpectedoutput(self,data_dictionary):
        """
    Extracts expected output values from the given data dictionary.
    This method scans through the provided data dictionary, identifies keys that start with "Expected-",
    and extracts the corresponding values to form a dictionary of expected outputs.
    """
        extracted_expected_result = {}

        # Iterate over the keys of the original dictionary
        for key, value in data_dictionary.items():
            # Check if the key starts with "Expected-"
            if key.startswith("Expected-"):
                # Extract the part after "Expected-"
                expected_key = key.split("-", 1)[1]
                # Add the extracted key and value to the new dictionary
                extracted_expected_result[expected_key] = value

        # Return the extracted expected result dictionary
        return(extracted_expected_result)



    def get_value_from_path(self, data, path):
        """
        Retrieves the value from a nested data structure based on a dot-separated path.
    This method navigates through a nested dictionary or list structure to extract the value
    at the specified path. The path can include both dictionary keys and list indices."""
        keys = path.split('.')
        value = data
        for key in keys:
            if '[' in key and ']' in key:
                key, index = key[:-1].split('[')
                index = int(index)
                value = value[key][index]
            else:
                value = value.get(key)
        return value

    def allureresponsecapture(self,response):
        """
         Captures and attaches the API response to the Allure report.

    This method takes an API response, converts its body to a string, and attaches it to the Allure
    report for better visibility and debugging. The attachment is named "API Response" and is specified
    as a text attachment.
        """
        allure.attach(
            str(response.text),  # Attach response body as a string
            name="API Response",  # Name of the attachment
            attachment_type=allure.attachment_type.TEXT  # Specify attachment type as text
        )

    def convert_str_to_int_in_dict(self,data_dict):
        """
         Converts string values representing integers to actual integers within a dictionary.

    This method iterates through the given dictionary, checks if the values are strings that represent
    integers, and converts those string values to integers.
        """
        for key, value in data_dict.items():
            # Check if the value is a string and represents a number
            if isinstance(value, str) and value.isdigit():
                # Convert string to integer
                data_dict[key] = int(value)
        return data_dict

    def convert_bool_to_str_and_back(self,data_dict):
        """
        Converts boolean values to strings and string representations of booleans back to booleans within a dictionary.

    This method iterates through the given dictionary, converts boolean values to their string representations,
    and converts string representations of booleans back to boolean values.
        """
        for key, value in data_dict.items():
            if isinstance(value, bool):
                # Convert boolean to string
                data_dict[key] = str(value)
            elif isinstance(value, str):
                # Convert string to boolean if it represents a boolean value
                if value.lower() == "true":
                    data_dict[key] = True
                elif value.lower() == "false":
                    data_dict[key] = False
        return data_dict

    def returnupdatedjson(self, data_dictionary):
        """
        Constructs and returns an updated JSON template based on provided data.
    This method either loads a JSON template from a file specified in the `data_dictionary` or constructs
    a new JSON object from keys starting with "Request-". It replaces placeholders in the JSON template
    with corresponding values from the `data_dictionary` and converts boolean and integer strings to their
    respective types.

        """
        dir = os.path.dirname(os.path.dirname(__file__))
        json_template = {}
        pattern = r'\$(.*?)\$'
        # Check if JsonName is provided and the corresponding file exists
        if "JsonName" in data_dictionary:
            json_file_path = os.path.join(dir, "json", data_dictionary.get("JsonName"))
            if os.path.isfile(json_file_path):
                with open(json_file_path, 'r') as file:
                    json_template = file.read()
            else:
                print(
                    f"JSON file {json_file_path} not found. Constructing JSON from keys starting with 'Request-'.")

        # Process keys starting with "Request-" to construct JSON if not already loaded from file

        if not json_template:
            json_template = {}

        matches = re.findall(pattern, json.dumps(json_template))
        json_template_str = json.dumps(json_template)
        if "JsonName" in data_dictionary:
            for match in matches:
                if 'Request-' + match in data_dictionary:
                    json_template = json_template.replace(f'${match}$', data_dictionary['Request-' + match])

        for key, value in data_dictionary.items():
            if key.startswith("Request-"):
                json_key = key[len("Request-"):]
                if json_key not in json_template:
                    json_template[json_key]=value

        if "httpMethod" not in data_dictionary:
            UpdatedJsontemplate = json.loads(json_template)
            updated_dictionaryBool = self.convert_bool_to_str_and_back(UpdatedJsontemplate)
            updated_dictionary = self.convert_str_to_int_in_dict(updated_dictionaryBool)
            json_string = json.dumps(updated_dictionary, ensure_ascii=False)
        else:
            json_string = json.dumps(json_template, ensure_ascii=False)
            typee = type(json_string)
        # Convert the JSON string back to a dictionary
        json_template = json.loads(json_string)

        if isinstance(json_template,dict):
            json_template=json.dumps(json_template, ensure_ascii=False)
        return json_template

    def retunrparentschema(self,data_dictionary):
        """
            Loads and returns the parent schema from a JSON file specified in the `data_dictionary`.
            This method reads the parent schema from a JSON file whose name is provided in the `Parent_Schema`
            key of the `data_dictionary`. The schema is loaded and converted into a dictionary format.
        """
        dir = os.path.dirname(os.path.dirname(__file__))
        Schema_file_path = (os.path.join(dir, "json", data_dictionary.get("Parent_Schema")))
        with open(Schema_file_path, 'r') as file:
            Schema_template = file.read()
        Schema_string = json.dumps(Schema_template, ensure_ascii=False)
        Schema_template = json.loads(Schema_string)
        data_dictionary = json.loads(Schema_template)
        print(type(data_dictionary))
        return data_dictionary


    @allure.description("Check for Assertion")
    def statuscodeassertion(self,response,data_dictionary):
        """
        Asserts the status code of the API response against the expected status code provided in `data_dictionary`.
    This method uses the expected status code from `data_dictionary` to assert against the actual status code
    of the API response.
        """
        assert response.status_code == data_dictionary.get("Expected-StatusCode")


    def extract_value_from_json(self,response_json, json_path):
        """
        Extracts a value from a JSON response based on the specified JSON path.
        This method parses the JSON response and uses the JSON path to find and return the desired value.
        """
        try:
            response_json = json.loads(response_json)
            jsonpath_expr = parse(json_path)
            # Extract token value
            matches = [match.value for match in jsonpath_expr.find(response_json)]
            # Print token value
            value = (matches[0])
            return value
        except (KeyError, TypeError):
            return None

    # Function to extract the key from the pattern "Extract-***"
    def extract_key_from_pattern(self,pattern):
        """
            Extracts and returns the key from a pattern in the format "Extract-***".
            This method matches the input pattern against the format "Extract-***" and extracts the key part.
        """
        match = re.match(r'^Extract-(.*)$', pattern)
        if match:
            return match.group(1)
        else:
            return None

    # Function to store value in properties/INI file
    def store_value_in_file(self, key, value, data_dictionary):
        """
        Stores a key-value pair in an INI file.
        """
        key = data_dictionary.get("Test_Case_Name")[:6] + "_" + key
        config = configparser.ConfigParser()
        # Load existing INI file if it exists
        dir = os.path.dirname(os.path.dirname(__file__))
        ini_file_path = os.path.join(dir, "extracted_values.ini")
        if os.path.exists(ini_file_path):
            config.read(ini_file_path)
        # Check if the section exists, if not, create it
        if 'ExtractedValues' not in config:
            config['ExtractedValues'] = {}
        # Append the new key-value pair to the section in the INI file
        config['ExtractedValues'][key] = value
        # Write the updated content to the INI file
        with open(ini_file_path, 'w') as configfile:
            config.write(configfile)

    #
    def extractingdata(self, data_dictionary, response_json):
        """
        Extracts and returns the key from a pattern in the format "Extract-***".
        This method matches the input pattern against the format "Extract-***" and extracts the key part.
        """
        # Iterate over the data dictionary
        for key, value in data_dictionary.items():
            # Check if the key starts with "Extract-"
            if key.startswith("Extract-"):
                # Extract the JSON path from the value
                json_path = value

                # Extract the key from the pattern
                extracted_key = self.extract_key_from_pattern(key)

                if extracted_key:
                    # Extract value using JSON path
                    extracted_value = self.extract_value_from_json(response_json, json_path)

                    if extracted_value:
                        # Store value in properties/INI file
                        extracted_value = str(extracted_value)
                        self.store_value_in_file(extracted_key, extracted_value, data_dictionary)
                        print(f"Value '{extracted_value}' stored in file with key '{extracted_key}'")
                    else:
                        print(f"Failed to extract value from JSON using JSON path '{json_path}'")


    def Expectedoutputcompare(self,expectedoutputdict,response_json):
        """
        Compares expected output values with API response.
        """
        for key, value in expectedoutputdict.items():
            # Check if the key is not "StatusCode"
            if key.lower() != "statuscode":
                # Split the value by "||"
                texts = value.split(" || ")

                # Perform assertion
                text1, text2 = texts
                if "sqlvalidation" not in text2.lower():
                    pass
                elif  "sqlvalidation" not in text2.lower():
                    text1 = self.extract_value_from_json(response_json,text1 )
                    # Perform further assertions or operations as needed
                    assert text1 == text2

    def print_request_details(self, request_details):
        """
            Prints request details.
        """
        print("Request Details:", json.dumps(request_details, indent=4))

    def to_json_safe(self, resp):
        """Safely convert API response to dict/list."""
        if resp is None:
            return {}

        # Already JSON-parsed
        if isinstance(resp, (dict, list)):
            return resp

        # Convert to JSON if string
        if isinstance(resp, str):
            try:
                return json.loads(resp)
            except:
                return {"raw": resp}

        # Fallback
        return {"raw": str(resp)}

    def set_request_json_body(self, data_dictionary, request_details):
        """
        Sets the JSON body of the API request.
        """
        http_method = data_dictionary.get("httpMethod")
        if http_method in ["POST", "PUT"]:
            jsonbody = self.returnupdatedjson(data_dictionary)
            request_details["json"] = json.loads(jsonbody)
        return request_details

    # @allure.step("Perform API operation")
    # def makeapicall(self, data_dictionary):
    #     """
    #     Executes an API operation based on the provided data dictionary.
    #     """
    #     logger = logging.getLogger()
    #     logger.setLevel(logging.DEBUG)
    #
    #     if "httpMethod" in data_dictionary:
    #         http_method = data_dictionary.get("httpMethod").upper()
    #         combinedurl = data_dictionary.get("baseUrl")+data_dictionary.get("endpoint")
    #         extractedheaders = data_dictionary.get("headers")
    #         expectedresult = data_dictionary.get("expectedOutput")
    #         print("*********expectedresult**********",expectedresult)
    #         response = None
    #         request_details = {
    #             "method": http_method,
    #             "url": combinedurl,
    #             "headers": extractedheaders
    #         }
    #
    #         try:
    #             # Print request details
    #             self.print_request_details(request_details)
    #
    #             # Set request JSON body
    #             request_details = self.set_request_json_body(data_dictionary, request_details)
    #
    #             # Make API call based on HTTP method
    #             if http_method in ["GET", "READ"]:
    #                 response = requests.get(combinedurl, headers=extractedheaders, verify=False)
    #             elif http_method in ["POST", "CREATE"]:
    #                 response = requests.post(combinedurl, json=request_details["json"], headers=extractedheaders, verify=False)
    #             elif http_method in ["PUT", "UPDATE"]:
    #                 response = requests.put(combinedurl, headers=extractedheaders, json=request_details["json"], verify=False)
    #             elif http_method == "PATCH":
    #                 response = requests.patch(combinedurl, headers=extractedheaders, json=request_details["json"], verify=False)
    #             elif http_method == "DELETE":
    #                 response = requests.delete(combinedurl, headers=extractedheaders, verify=False)
    #             print("***************response************", response)
    #             # Process API response and validation
    #             print("***************response************",response.json())
    #             if response:
    #                 response_json = response.json()
    #                 print("Response JSON:", json.dumps(response_json, indent=4))
    #                 print("Response StatusCode:", json.dumps(response.status_code, indent=4))
    #                 logger.info(combinedurl + ' Request has been sent to the base URL ')
    #                 allure.attach(json.dumps(request_details, indent=4), name="Request Details",
    #                               attachment_type=allure.attachment_type.JSON)
    #                 allure.attach(json.dumps(response_json, indent=4), name="Response JSON",
    #                               attachment_type=allure.attachment_type.JSON)
    #                 allure.attach(json.dumps(response.status_code, indent=4), name="Response StatusCode",
    #                               attachment_type=allure.attachment_type.JSON)
    #                 with allure.step("Result: {}".format(response.text)):
    #                     pass
    #
    #                 self.allureresponsecapture(response)
    #                 self.extractingdata(data_dictionary, response.text)
    #                 if isinstance(expectedresult, str):
    #                     expectedresult = json.loads(expectedresult)
    #
    #                 # Separate status code from other expected output keys
    #                 expected_output = {k: v for k, v in expectedresult.items() if k != 'Expected-StatusCode'}
    #
    #                 response_dict = response_json if isinstance(response_json, dict) else json.loads(response_json)
    #
    #                 # Logging for debugging
    #                 print("Expected Output:", json.dumps(expected_output, indent=4))
    #                 print("Response Dict:", json.dumps(response_dict, indent=4))
    #
    #                 self.validate_response(expected_output, response_dict)
    #
    #         except Exception as e:
    #             logger.error(f"Error while making API call: {e}")
    #             allure.attach(str(e), name="Exception", attachment_type=allure.attachment_type.TEXT)
    #             raise e
    #
    # def makeperformancecall(self, data_dictionary):
    #     """
    #     Executes an perfomance operation based on the provided data dictionary.
    #     """
    #     logger = logging.getLogger()
    #     logger.setLevel(logging.DEBUG)
    #     currdir = os.path.dirname(os.path.dirname(__file__))
    #     ini_file_path = (os.path.join(currdir, "locust_config.ini"))
    #     locust_config = configparser.ConfigParser()
    #     locust_config.read(ini_file_path)
    #     run_performance = locust_config.get("api-performance", "execute_nft").upper()
    #
    #     if "httpMethod" in data_dictionary:
    #         base_uri = "https://reqres.in/"
    #         print("base_uri", base_uri)
    #         http_method = data_dictionary.get("httpMethod").upper()
    #         endpoint = data_dictionary.get('endPoint', '')
    #         combinedurl = self.getcompleteurl(data_dictionary)
    #         extractedheaders = self.getheader(data_dictionary)
    #         performance_required = data_dictionary.get("Execute?").upper()
    #         print("performance_required", performance_required)
    #         request_details = {
    #             "method": http_method,
    #             "url": combinedurl,
    #             "headers": extractedheaders
    #         }
    #
    #         # Set request JSON body
    #         request_details = self.set_request_json_body(data_dictionary, request_details)
    #
    #         os.environ["LOCUST_HOST"] = combinedurl
    #         # os.environ["LOCUST_ENDPOINT"] = data_dictionary.get("endpoint", "/")
    #         os.environ["LOCUST_METHOD"] = http_method
    #         # Store request details as a JSON string
    #         os.environ["LOCUST_DATA"] = json.dumps(request_details, ensure_ascii=False)
    #         print("request_details", os.environ["LOCUST_DATA"])
    #
    #         # Store headers separately as a JSON string
    #         os.environ["LOCUST_AUTH"] = json.dumps(extractedheaders, ensure_ascii=False)
    #         print("headers", os.environ["LOCUST_AUTH"])
    #         if performance_required == "Y" and run_performance == "Y":
    #             DEFAULT_REPORT_DIR = os.path.join(os.getcwd(), "tests_results", "locust_reports")
    #             REPORT_DIR = os.environ.get("PERFORMANCE_REPORT_DIR", DEFAULT_REPORT_DIR)
    #             # Ensure the directory exists
    #             os.makedirs(REPORT_DIR, exist_ok=True)
    #             # Construct API request dictionary dynamically
    #             # Extract and sanitize the filename
    #             sanitized_api = re.sub(r'[^a-zA-Z0-9_]', '_', endpoint)
    #             html_report_file = os.path.join(REPORT_DIR, f"locust_report_{http_method}_{sanitized_api}.html")
    #             locust_csv_path = os.path.join(REPORT_DIR, "locust_csv")
    #             locustfile_path = os.path.join(os.getcwd(), "locustfile.py")
    #
    #             print("Going inside to perform performance testing")
    #             command = [
    #                 "locust",
    #                 "-f", locustfile_path,
    #                 "--headless",
    #                 "--users", locust_config.get("api-performance", "ramp_users"),
    #                 "--spawn-rate", locust_config.get("api-performance", "spawn_rate"),
    #                 "--run-time", locust_config.get("api-performance", "run_time"),
    #                 "--host", base_uri,
    #                 "--stop-timeout", locust_config.get("api-performance", "stop_time"),
    #                 "--csv", locust_csv_path,  # Single CSV file
    #                 "--csv-full-history",  # ✅ Appends all endpoint results
    #                 "--html", html_report_file
    #             ]
    #             # try:
    #             # Run Locust test command
    #             logger.info("Running Locust test...")
    #             print("Starting Locust performance test...")
    #             # global locust_process
    #             # print(locust_process)
    #             locust_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    #             print(locust_process)
    #             print(locust_process.returncode)
    #             if locust_process.returncode != 0:
    #                 print(f"Error running Locust: {locust_process.stderr.decode()}")
    #                 logger.error(f"Locust test failed: {locust_process.stderr.decode('utf-8')}")
    #             else:
    #                 print("Performance report generated: report.html")
    #                 logger.info(f"Locust test completed: {locust_process.stdout.decode('utf-8')}")
    #             allure.attach(locust_process.stdout.decode('utf-8'), name=f"Locust Output - {combinedurl}",
    #                           attachment_type=allure.attachment_type.TEXT)
    #             # allure.attach(locust_process.stdout.decode('utf-8'), name=f"Locust Errors - {combinedurl}",
    #             #               attachment_type=allure.attachment_type.TEXT)
    #             if os.path.exists(html_report_file):
    #                 allure.attach.file(html_report_file, name=f"Locust Report - {combinedurl}",
    #                                    attachment_type=allure.attachment_type.HTML)
    #             else:
    #                 logger.error("Locust HTML report was not generated")
    #         else:
    #             print("No performance tests required. Skipping Locust execution.")
    #
    # @allure.step("Perform API operation")
    # def makeapicall(self, data_dictionary):
    #     logger = logging.getLogger()
    #     logger.setLevel(logging.DEBUG)
    #
    #     http_method = data_dictionary.get("httpMethod", "").upper()
    #     base_url = data_dictionary.get("baseUrl", "").rstrip("/")
    #     endpoint = data_dictionary.get("endpoint", "")
    #     combinedurl = f"{base_url}{endpoint}"
    #
    #     headers = data_dictionary.get("headers", {})
    #     expected_output = data_dictionary.get("expectedOutput", {})
    #
    #     print("********* Expected Output **********", expected_output)
    #
    #     response = None
    #
    #     try:
    #         # Build request body (if any)
    #         request_details = {
    #             "method": http_method,
    #             "url": combinedurl,
    #             "headers": headers
    #         }
    #         request_details = self.set_request_json_body(data_dictionary, request_details)
    #
    #         # --- API CALL ---
    #         if http_method == "GET":
    #             response = requests.get(combinedurl, headers=headers, verify=False)
    #         elif http_method == "POST":
    #             response = requests.post(combinedurl, json=request_details.get("json"), headers=headers, verify=False)
    #         elif http_method == "PUT":
    #             response = requests.put(combinedurl, json=request_details.get("json"), headers=headers, verify=False)
    #         elif http_method == "PATCH":
    #             response = requests.patch(combinedurl, json=request_details.get("json"), headers=headers, verify=False)
    #         elif http_method == "DELETE":
    #             response = requests.delete(combinedurl, headers=headers, verify=False)
    #
    #         print("*************** RAW Response ************", response)
    #
    #         # --- SAFE JSON PARSING ---
    #         try:
    #             response_json = response.json()
    #         except Exception:
    #             response_json = response.text
    #
    #         response_dict = self.to_json_safe(response_json)
    #
    #         print("Parsed Response:", json.dumps(response_dict, indent=4))
    #         print("Status Code:", response.status_code)
    #
    #         # --- Allure Attachments ---
    #         allure.attach(json.dumps(request_details, indent=4), "Request Details", allure.attachment_type.JSON)
    #         allure.attach(json.dumps(response_dict, indent=4), "Response JSON", allure.attachment_type.JSON)
    #         allure.attach(str(response.status_code), "Response Status Code", allure.attachment_type.TEXT)
    #
    #         # --- Validation ---
    #         if isinstance(expected_output, str):
    #             expected_output = json.loads(expected_output)
    #
    #         self.validate_response(expected_output, response_dict)
    #
    #     except Exception as e:
    #         logger.error(f"Error while making API call: {e}")
    #         allure.attach(str(e), "Exception", allure.attachment_type.TEXT)
    #         raise e
    #
    # def makeperformancecall(self, data_dictionary):
    #     logger = logging.getLogger()
    #     logger.setLevel(logging.DEBUG)
    #
    #     performance_required = str(data_dictionary.get("Performance?", "N")).upper()
    #     http_method = data_dictionary.get("httpMethod", "").upper()
    #
    #     if performance_required != "Y":
    #         print("Performance test not required.")
    #         return
    #
    #     base_url = data_dictionary.get("baseUrl", "").rstrip("/")
    #     endpoint = data_dictionary.get("endpoint", "")
    #     combinedurl = f"{base_url}{endpoint}"
    #
    #     headers = data_dictionary.get("headers", {})
    #
    #     # Prepare for Locust
    #     os.environ["LOCUST_HOST"] = base_url
    #     os.environ["LOCUST_METHOD"] = http_method
    #     os.environ["LOCUST_DATA"] = json.dumps({"url": combinedurl}, ensure_ascii=False)
    #     os.environ["LOCUST_AUTH"] = json.dumps(headers, ensure_ascii=False)
    #
    #     REPORT_DIR = os.path.join(os.getcwd(), "tests_results", "locust_reports")
    #     os.makedirs(REPORT_DIR, exist_ok=True)
    #
    #     locustfile_path = os.path.join(os.getcwd(), "locustfile.py")
    #
    #     command = [
    #         "locust",
    #         "-f", locustfile_path,
    #         "--headless",
    #         "--users", "5",
    #         "--spawn-rate", "2",
    #         "--run-time", "10s",
    #         "--host", base_url,
    #         "--html", os.path.join(REPORT_DIR, f"locust_{http_method}_{endpoint.replace('/', '_')}.html")
    #     ]
    #
    #     print("Running Locust:", command)
    #
    #     result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    #
    #     allure.attach(result.stdout.decode(), "Locust Output", allure.attachment_type.TEXT)
    def to_json_safe(self, resp):
        """Safely convert API response to dict/list."""
        if resp is None:
            return {}

        # Already JSON-parsed
        if isinstance(resp, (dict, list)):
            return resp

        # Convert to JSON if string
        if isinstance(resp, str):
            try:
                return json.loads(resp)
            except:
                return {"raw": resp}

        # Fallback
        return {"raw": str(resp)}

    def add_basic_auth_header(self, username, password, headers):
        import base64
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
        return headers
    def generate_bearer_token(self):
        config = configparser.ConfigParser()
        config.read("auth_config.ini")

        token_url = config.get("auth", "token_url")
        client_id = config.get("auth", "client_id")
        client_secret = config.get("auth", "client_secret")
        payload = {"client_id": client_id, "client_secret": client_secret}

        res = requests.post(token_url, json=payload, verify=False)
        return res.json().get("access_token")

    def get_auth_headers(self, data_dictionary):
        headers = data_dictionary.get("headers", {})
        auth_type = data_dictionary.get("auth_type", "NA").upper()

        # NA = No Auth
        if auth_type == "NA":
            return headers

        # Username (Basic Auth)
        if auth_type == "USERNAME":
            username = data_dictionary.get("username")
            password = data_dictionary.get("password")
            return self.add_basic_auth_header(username, password, headers)

        # API KEY coming from config file
        if auth_type == "API":
            # config = configparser.ConfigParser()
            # config.read("auth_config.ini")
            # api_key = config.get("auth", "api_key")
            headers["x-api-key"] = "reqres_77f2dcfc6bea46349bbc43b68dfc0436"
            return headers

        # Bearer token
        if auth_type == "BEARER":
            token = self.generate_bearer_token()
            headers["Authorization"] = f"Bearer {token}"
            return headers

        return headers
    def clear_allure(self):
        folder = "allure-results"
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

    def validate_api_result(self, response, expected_output_string):
        """
        Validates API response and expected output.
        expected_output_string example:
            "first_name:Janet"
            "first_name:Janet, age:30"
        """

        # -------------------------------
        # 1. Validate Status Code
        # -------------------------------
        status = getattr(response, "status_code", None)

        if status != 200:
            print(f"[FAIL] Status Code: Expected 200 but got {status}")
            return "FAIL"

        print("[PASS] Status Code matched: 200")

        # -------------------------------
        # 2. Convert response to JSON
        # -------------------------------
        try:
            response_json = response.json()
        except:
            try:
                response_json = json.loads(response.text)
            except:
                print("[FAIL] Response is not valid JSON")
                return "FAIL"

        # -------------------------------
        # 3. Parse expected string into dict
        # -------------------------------
        expected_pairs = {}

        for part in expected_output_string.split(","):
            part = part.strip()
            if ":" in part:
                key, value = part.split(":", 1)
                expected_pairs[key.strip()] = value.strip()

        # -------------------------------
        # 4. Validate values inside "data"
        # -------------------------------
        data_section = response_json.get("data", {})

        for key, expected_value in expected_pairs.items():
            actual_value = data_section.get(key)

            if str(actual_value) != str(expected_value):
                print(f"[FAIL] '{key}' mismatch → expected '{expected_value}' but got '{actual_value}'")
                return "FAIL"

            print(f"[PASS] {key}: {actual_value} == {expected_value}")

        print("All validations passed!")
        return "PASS"

    # @allure.step("API Call: Started")
    # def makeapicall(self, data_dictionary,api_input_type):
    #     logger = logging.getLogger()
    #     logger.setLevel(logging.DEBUG)
    #     with allure.step("Preparing API Request"):
    #         if api_input_type == "file":
    #             http_method = data_dictionary.get("method", "").upper()
    #             base_url = data_dictionary.get("baseUrl", "")
    #             endpoint = data_dictionary.get("endpoint", "")
    #             combinedurl = f"{base_url}{endpoint}"
    #
    #             # 🔥 Get final authentication headers
    #             headers = self.get_auth_headers(data_dictionary)
    #
    #
    #         else:
    #            http_method = data_dictionary.get("httpMethod", "").upper()
    #            base_url = data_dictionary.get("baseUrl", "")
    #            endpoint = data_dictionary.get("endpoint", "")
    #            combinedurl = f"{base_url}{endpoint}"
    #
    #            # 🔥 Get final authentication headers
    #            headers = data_dictionary.get("headers", "")
    #
    #            expected_output = data_dictionary.get("expectedOutput", {})
    #     response = None
    #
    #     try:
    #         # Build request body (if any)
    #         request_details = {
    #             "method": http_method,
    #             "url": combinedurl,
    #             "headers": headers
    #         }
    #         #request_details = self.set_request_json_body(data_dictionary, request_details)
    #         with allure.step(f"Sending Request: {http_method} {combinedurl}"):
    #             if http_method == "GET":
    #                 response = requests.get(combinedurl, headers=headers, verify=False)
    #
    #             elif http_method == "POST":
    #                 response = requests.post(
    #                     combinedurl,
    #                     json=request_details.get("json"),
    #                     headers=headers,
    #                     verify=False
    #                 )
    #
    #             elif http_method == "PUT":
    #                 response = requests.put(
    #                     combinedurl,
    #                     json=request_details.get("json"),
    #                     headers=headers,
    #                     verify=False
    #                 )
    #
    #             elif http_method == "PATCH":
    #                 response = requests.patch(
    #                     combinedurl,
    #                     json=request_details.get("json"),
    #                     headers=headers,
    #                     verify=False
    #                 )
    #
    #             elif http_method == "DELETE":
    #                 response = requests.delete(
    #                     combinedurl,
    #                     headers=headers,
    #                     verify=False
    #                 )
    #
    #         print("*************** RAW Response ************", response)
    #
    #
    #
    #         with allure.step("Response Details"):
    #             allure.attach(str(response.text), "Response Body", allure.attachment_type.TEXT)
    #             allure.attach(str(response.status_code), "Status Code", allure.attachment_type.TEXT)
    #         # Expected Output may be string
    #         # if isinstance(expected_output, str):
    #         #     expected_output = json.loads(expected_output)
    #
    #         #return self.validate_response(expected_output, response_dict)
    #         return response,combinedurl,http_method
    #     except Exception as e:
    #         logger.error(f"API Call Error: {e}")
    #         allure.attach(str(e), "Exception", allure.attachment_type.TEXT)
    #         raise e
    #
    # def makeperformancecall(self, data_dictionary,api_input_type):
    #     ini_file_path = (os.path.join(input_folder, "locust_config.ini"))
    #     locust_config = configparser.ConfigParser()
    #     locust_config.read(ini_file_path)
    #     logger = logging.getLogger()
    #     logger.setLevel(logging.DEBUG)
    #     if api_input_type == "file":
    #         performance_required = str(data_dictionary.get("performance"))
    #         if not performance_required:
    #             print("Skipping performance test.")
    #             return
    #     else:
    #         st.text("continues performance for all APIs from swegger")
    #
    #     if api_input_type == "file":
    #         http_method = data_dictionary.get("method", "").upper()
    #         base_url = data_dictionary.get("baseUrl", "")
    #         endpoint = data_dictionary.get("endpoint", "")
    #         combinedurl = f"{base_url}{endpoint}"
    #
    #         # 🔥 Get final authentication headers
    #         headers = self.get_auth_headers(data_dictionary)
    #
    #
    #     else:
    #         http_method = data_dictionary.get("httpMethod", "").upper()
    #         base_url = data_dictionary.get("baseUrl", "")
    #         endpoint = data_dictionary.get("endpoint", "")
    #         combinedurl = f"{base_url}{endpoint}"
    #
    #         # 🔥 Get final authentication headers
    #         headers = data_dictionary.get("headers", "")
    #
    #         expected_output = data_dictionary.get("expectedOutput", {})
    #
    #     # http_method = data_dictionary.get("method", "").upper()
    #     # base_url = data_dictionary.get("baseUrl", "")
    #     # endpoint = data_dictionary.get("endpoint", "")
    #     # combinedurl = f"{base_url}{endpoint}"
    #     #
    #     # # 🔥 Universal Auth Handler
    #     # headers = self.get_auth_headers(data_dictionary)
    #
    #     # Set Locust env vars
    #     os.environ["LOCUST_BASEURL"] = base_url
    #     os.environ["LOCUST_HOST"] = combinedurl
    #     os.environ["LOCUST_METHOD"] = http_method
    #     os.environ["LOCUST_DATA"] = json.dumps({"url": combinedurl}, ensure_ascii=False)
    #     os.environ["LOCUST_AUTH"] = json.dumps(headers, ensure_ascii=False)
    #
    #     # Prepare result folder
    #     REPORT_DIR = os.path.join(os.getcwd(), "tests_results", "locust_reports")
    #     os.makedirs(REPORT_DIR, exist_ok=True)
    #
    #     html_file = os.path.join(REPORT_DIR, f"locust_{http_method}_{endpoint.replace('/', '_')}.html")
    #     locustfile_path = os.path.join(os.getcwd(), "locustfile.py")
    #     sanitized_api = re.sub(r'[^a-zA-Z0-9_]', '_', endpoint)
    #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    #     html_report_file = os.path.join(REPORT_DIR, f"locust_report_{http_method}_{sanitized_api}_{timestamp}.html")
    #     locust_csv_path = os.path.join(REPORT_DIR, "locust_csv")
    #     command = [
    #         "locust",
    #         "-f", locustfile_path,
    #         "--headless",
    #         "--users", locust_config.get("api-performance", "ramp_users"),
    #         "--spawn-rate", locust_config.get("api-performance", "spawn_rate"),
    #         "--run-time", locust_config.get("api-performance", "run_time"),
    #         "--host", base_url,
    #         "--stop-timeout", locust_config.get("api-performance", "stop_time"),
    #         "--csv", locust_csv_path,  # Single CSV file
    #         "--csv-full-history",  # ✅ Appends all endpoint results
    #         "--html", html_report_file
    #     ]
    #     # command = [
    #     #     "locust", "-f", locustfile_path,
    #     #     "--headless",
    #     #     "--users", "5",
    #     #     "--spawn-rate", "2",
    #     #     "--run-time", "10s",
    #     #     "--host", base_url,
    #     #     "--html", html_file
    #     # ]
    #
    #     result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    #
    #     allure.attach(result.stdout.decode(), "Locust Output", allure.attachment_type.TEXT)
    #     return html_report_file

    @allure.step("API Call: Started")
    def makeapicall(self, data_dictionary, api_input_type):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # -------------------------------
        # 1. Resolve common inputs
        # -------------------------------
        if api_input_type == "file":
            http_method = data_dictionary.get("method", "").upper()
            base_url = data_dictionary.get("baseUrl", "")
            endpoint = data_dictionary.get("endpoint", "")
            headers = self.get_auth_headers(data_dictionary)

            # Excel payload (string JSON)
            raw_payload = data_dictionary.get("body_format")
            print("**********raw_payload_file***********", raw_payload)

        else:  # swagger
            http_method = data_dictionary.get("httpMethod", "").upper()

            base_url = data_dictionary.get("baseUrl", "")
            endpoint = data_dictionary.get("endpoint", "")
            headers = data_dictionary.get("headers", {})

            # Swagger payload (already dict)
            raw_payload = data_dictionary.get("payload")
            print("**********raw_payload_swegger***********",raw_payload)

        combinedurl = f"{base_url}{endpoint}"

        with allure.step("Preparing API Request"):
            allure.attach(http_method, "HTTP Method", allure.attachment_type.TEXT)
            allure.attach(combinedurl, "URL", allure.attachment_type.TEXT)
            allure.attach(json.dumps(headers), "Headers", allure.attachment_type.JSON)

        # -------------------------------
        # 2. Prepare request body
        # -------------------------------
        json_body = None

        if http_method in ["POST", "PUT", "PATCH"] and raw_payload:
            try:
                if api_input_type == "file":
                    # Excel → string → dict
                    print("make_api_call_rwa_payload", raw_payload)
                    json_body = json.loads(raw_payload)
                    print("make_api_call_json_body", json_body)
                else:
                    # Swagger → already dict
                    json_body = raw_payload
                    print("make_api_call_JSON_BODY",json_body)

                allure.attach(
                    json.dumps(json_body, indent=2),
                    "Request Body",
                    allure.attachment_type.JSON
                )

            except Exception as e:
                raise ValueError(f"Invalid request payload: {e}")

        # -------------------------------
        # 3. Send request
        # -------------------------------
        try:
            with allure.step(f"Sending {http_method} Request"):
                if http_method == "GET":
                    response = requests.get(combinedurl, headers=headers, verify=False)
                    print("Swegger GET Reposne",response)
                elif http_method == "POST":
                    print("Swegger_make_api_call_JSON_BODY", json_body)
                    response = requests.post(
                        combinedurl,
                        json=json_body,
                        headers=headers,
                        verify=False
                    )
                    print("Swegger_make_api_call_resposne", response.json)
                elif http_method == "PUT":
                    response = requests.put(
                        combinedurl,
                        json=json_body,
                        headers=headers,
                        verify=False
                    )

                elif http_method == "PATCH":
                    response = requests.patch(
                        combinedurl,
                        json=json_body,
                        headers=headers,
                        verify=False
                    )

                elif http_method == "DELETE":
                    response = requests.delete(
                        combinedurl,
                        headers=headers,
                        verify=False
                    )

                else:
                    raise ValueError(f"Unsupported HTTP method: {http_method}")

            with allure.step("Response Details"):
                allure.attach(str(response.status_code), "Status Code", allure.attachment_type.TEXT)
                allure.attach(response.text, "Response Body", allure.attachment_type.TEXT)

            return response, combinedurl, http_method

        except Exception as e:
            logger.error(f"API Call Error: {e}")
            allure.attach(str(e), "Exception", allure.attachment_type.TEXT)
            raise

    def makeperformancecall(self, data_dictionary, api_input_type):
        import configparser
        from datetime import datetime

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # -----------------------------------
        # 1. Read Locust config
        # -----------------------------------
        ini_file_path = os.path.join(input_folder, "locust_config.ini")
        locust_config = configparser.ConfigParser()
        locust_config.read(ini_file_path)

        # -----------------------------------
        # 2. Check performance flag (FILE only)
        # -----------------------------------
        if api_input_type == "file":
            performance_required = data_dictionary.get("performance")
            if not performance_required:
                print("Skipping performance test.")
                return None

        # -----------------------------------
        # 3. Resolve inputs
        # -----------------------------------
        if api_input_type == "file":
            http_method = data_dictionary.get("method", "").upper()
            base_url = data_dictionary.get("baseUrl", "")
            endpoint = data_dictionary.get("endpoint", "")
            headers = self.get_auth_headers(data_dictionary)
            # Excel payload (string JSON)
            print("**********raw_payload_file_performance_dictinary***********", data_dictionary)
            raw_payload = data_dictionary.get("body_format")
            print("**********raw_payload_file_performance***********", raw_payload)


        else:  # swagger
            http_method = data_dictionary.get("httpMethod", "").upper()
            base_url = data_dictionary.get("baseUrl", "")
            endpoint = data_dictionary.get("endpoint", "")
            headers = data_dictionary.get("headers", {})
            raw_payload = data_dictionary.get("payload")

        combinedurl = f"{base_url}{endpoint}"

        # -----------------------------------
        # 4. Prepare request body for Locust
        # -----------------------------------
        request_body = None
        if http_method in ["POST", "PUT", "PATCH"] and raw_payload:
            try:
                if api_input_type == "file":

                    request_body = raw_payload
                    print("**********raw_payload_file_performance_request_body***********", request_body)
                else:
                    request_body = raw_payload
            except Exception as e:
                raise ValueError(f"Invalid payload for performance test: {e}")

        # -----------------------------------
        # 5. Set Locust ENV variables
        # -----------------------------------
        os.environ["LOCUST_BASEURL"] = base_url
        os.environ["LOCUST_ENDPOINT"] = endpoint
        os.environ["LOCUST_METHOD"] = http_method
        os.environ["LOCUST_AUTH"] = json.dumps(headers)
        if http_method in ["POST", "PUT", "PATCH"] and raw_payload:
            if isinstance(raw_payload, str):
                os.environ["LOCUST_DATA"] = raw_payload
            else:
                os.environ["LOCUST_DATA"] = json.dumps(raw_payload)
        else:
            os.environ["LOCUST_DATA"] = ""
        # -----------------------------------
        # 6. Prepare report folder + filename
        # -----------------------------------
        REPORT_DIR = os.path.join(os.getcwd(), "tests_results", "locust_reports")
        os.makedirs(REPORT_DIR, exist_ok=True)

        sanitized_api = re.sub(r'[^a-zA-Z0-9_]', '_', endpoint)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        html_report_file = os.path.join(
            REPORT_DIR,
            f"locust_report_{http_method}_{sanitized_api}_{timestamp}.html"
        )

        locust_csv_path = os.path.join(REPORT_DIR, f"locust_csv_{http_method}_{sanitized_api}_{timestamp}")

        locustfile_path = os.path.join(os.getcwd(), "locustfile.py")

        # -----------------------------------
        # 7. Build Locust command
        # -----------------------------------
        command = [
            "locust",
            "-f", locustfile_path,
            "--headless",
            "--users", locust_config.get("api-performance", "ramp_users"),
            "--spawn-rate", locust_config.get("api-performance", "spawn_rate"),
            "--run-time", locust_config.get("api-performance", "run_time"),
            "--stop-timeout", locust_config.get("api-performance", "stop_time"),
            "--host", base_url,
            "--csv", locust_csv_path,
            "--csv-full-history",
            "--html", html_report_file
        ]

        # -----------------------------------
        # 8. Execute Locust
        # -----------------------------------
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        allure.attach(result.stdout.decode(), "Locust Output", allure.attachment_type.TEXT)
        allure.attach(result.stderr.decode(), "Locust Errors", allure.attachment_type.TEXT)

        print(f"Locust report generated: {html_report_file}")

        return html_report_file,locust_csv_path

    def show_locust_report(self, report_paths):
        if not report_paths or len(report_paths) == 0:
            st.error("No Locust reports generated.")
            return

        st.success("Locust performance tests completed!")

        # Loop through each generated report path
        for idx, report_path in enumerate(report_paths, start=1):

            if not os.path.exists(report_path):
                st.error(f"Report not found: {report_path}")
                continue

            # Accordion for each report
            with st.expander(f"📄 Locust Report {idx}", expanded=False):

                # Download/Open link
                st.markdown(f"[🔗 Open HTML Report]({report_path})", unsafe_allow_html=True)

                # Read HTML content
                with open(report_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()

                # Show inside Streamlit
                st.components.v1.html(html_content, height=900, scrolling=True)
    def show_llm_response(self, report_path,llm_types):
        # Accordion for each report
        with st.expander(f"📄 {llm_types}", expanded=False):

            # Download/Open link
            st.markdown(f"[🔗 Open HTML Report]({report_path})", unsafe_allow_html=True)

            # Read HTML content
            with open(report_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            # Show inside Streamlit
            st.components.v1.html(html_content, height=900, scrolling=True)

    # def validate_response(self, expected_output, response):
    #     """
    #     Validates the API response against expected output.
    #     """
    #     # Convert response to dictionary if it's a string
    #     if isinstance(response, str):
    #         response = json.loads(response)
    #
    #     # Log the structures for debugging
    #     print("Expected Output:", json.dumps(expected_output, indent=4))
    #     print("Actual Response:", json.dumps(response, indent=4))
    #
    #     # Keys to exclude from validation
    #     keys_to_exclude = ['statuscode']
    #
    #     def get_nested_value(data, key):
    #         parts = key.split('.')
    #         for part in parts:
    #             if '[' in part and ']' in part:
    #                 array_key = part.split('[')[0]
    #                 index = int(part.split('[')[1].split(']')[0])
    #                 data = data[array_key][index]
    #             else:
    #                 data = data.get(part)
    #             if data is None:
    #                 break
    #         return data
    #
    #     for key, key_value in expected_output.items():
    #         if key.lower() in keys_to_exclude:
    #             continue
    #
    #         if isinstance(key_value, str):
    #             if '||' in key_value:
    #                 nested_key, expected_value = key_value.split("||", 1)
    #                 nested_key = nested_key.strip()
    #                 expected_value = expected_value.strip()
    #                 actual_value = get_nested_value(response, nested_key)
    #                 print(f"Actual Value for {nested_key}: {actual_value}")  # Debugging print statement
    #                 assert actual_value == expected_value, \
    #                     f"Expected {nested_key} to be {expected_value}, but got {actual_value}"
    #             else:
    #                 actual_key = key.replace('expectedoutput-', '').strip()
    #                 actual_value = get_nested_value(response, actual_key)
    #                 print(f"Actual Value for {actual_key}: {actual_value}")  # Debugging print statement
    #                 assert actual_value == key_value.strip(), \
    #                     f"Expected {actual_key} to be {key_value}, but got {actual_value}"
    #         else:
    #             print(f"Skipping non-string key value pair: {key_value}")
    def validate_response(self, expected_output, response):
        """
        Validates the API response against expected output.
        expected_output: dict like {"Expected_Message": "data.first_name||Janet"}
        response: dict converted from API JSON response
        """

        if isinstance(response, str):
            response = json.loads(response)

        def get_nested_value(data, key_path):
            """Fetch value from nested dict using dot notation and array indices."""
            current = data
            for part in key_path.split('.'):
                if '[' in part and ']' in part:  # array indexing
                    arr_key = part.split('[')[0]
                    index = int(part.split('[')[1].split(']')[0])
                    current = current[arr_key][index]
                else:
                    current = current.get(part)
                if current is None:
                    break
            return current

        for col, val in expected_output.items():
            if isinstance(val, str) and "||" in val:
                nested_key, expected_value = val.split("||", 1)
                nested_key = nested_key.strip()
                expected_value = expected_value.strip()

                actual_value = get_nested_value(response, nested_key)

                print(f"Validating {nested_key}: expected={expected_value}, actual={actual_value}")

                assert str(actual_value) == expected_value, \
                    f"[FAIL] {nested_key}: expected={expected_value}, actual={actual_value}"

        print("All validations passed!")
        return True

    def replace_fetch_values(self, datadictionary):
        """
            Replaces fetch values in the data dictionary with actual values.
        """
        dir = os.path.dirname(os.path.dirname(__file__))
        ini_file_path = (os.path.join(dir, "extracted_values.ini"))
        config = configparser.ConfigParser()
        config.read(ini_file_path)
        for key, value in datadictionary.items():
            if isinstance(value, str) and "||" in value:
                parts = value.split("||")
                direct_value = parts[0].strip()
                fetch_key = parts[1].strip()
                if fetch_key.startswith("fetch-"):
                    fetch_key = fetch_key.split("-", 1)[1]  # Extract key after "fetch-"
                    if config.has_section('ExtractedValues') and fetch_key in config['ExtractedValues']:
                        fetched_value = config['ExtractedValues'][fetch_key]
                        # Replace the fetch value with the fetched value
                        datadictionary[key] = fetched_value
                    else:
                        print(f"Error: Key '{fetch_key}' not found in {ini_file_path}")
            elif isinstance(value, str) and value.startswith("fetch-"):
                fetch_key = value.split("-", 1)[1]  # Extract key after "fetch-"
                if config.has_section('ExtractedValues') and fetch_key in config['ExtractedValues']:
                    fetched_value = config['ExtractedValues'][fetch_key]
                    # Replace the fetch value with the fetched value
                    datadictionary[key] = fetched_value
                else:
                    print(f"Error: Key '{fetch_key}' not found in {ini_file_path}")

        return datadictionary



    def validation_with_database(self, response, data_dictionary):
        """
            Validates API response data with values fetched from a database using SQL queries.
        """
        sql_query = self.get_sql_query(data_dictionary)
        if sql_query:
            value_from_database = getvaluefromdatabse(sql_query)
            assert value_from_database == response["name"]
        else:
            raise ValueError("SQL query not found in data dictionary.")

    def get_sql_query(data_dictionary):
        """
            Retrieves the SQL query from the data dictionary.
        """
        sql_query = None
        for key, value in data_dictionary.items():
            if key.startswith("SQL-"):
                sql_query = value
                break
        return sql_query

    def parse_request_payload(self, payload_str):
        if not payload_str:
            return {}

        try:
            return json.loads(payload_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Request_payload: {e}")

    def set_request_json_body(self, data_dictionary, request_details):
        http_method = data_dictionary.get("httpMethod", "").upper()

        if http_method in ["POST", "PUT"]:
            payload_str = data_dictionary.get("Request_payload")
            if payload_str:
                request_details["json"] = self.parse_request_payload(payload_str)

        return request_details

    def validate_post_response(self, response, request_payload):
        try:
            print("validate_post_response-response", response.json())
        except Exception:
            print("validate_post_response-response (empty/non-JSON body)")
        print("validate_post_response-requestpayload", request_payload)
        if response.status_code not in [200, 201]:
            return "FAIL"

        try:
            response_json = response.json()
        except:
            return "FAIL"

        for key, expected_value in request_payload.items():
            actual_value = response_json.get(key)
            if str(actual_value) != str(expected_value):
                print(f"[FAIL] {key}: expected={expected_value}, actual={actual_value}")
                return "FAIL"

        return "PASS"
