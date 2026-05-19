from locust import HttpUser, task, between
import os
import json

base_uri = test_type = os.environ.get('BASE_URI')
#api_list = json.loads(os.environ.get("LOCUST_DATA", "[]"))
class LocustApiUser(HttpUser):
    wait_time = between(1, 3)  # Simulate real-user wait time

    # def on_start(self):
    #     """ Setup code when Locust starts (Optional) """
    #     self.base_url = base_uri # Default to localhost if no host provided

    @task()
    def make_api_request(self):
        """ Make API request using Locust """
        print("going inside the actual performance")
        endpoint = os.getenv("LOCUST_HOST")
        print(endpoint)# Default to root if no endpoint is given
        method = os.getenv("LOCUST_METHOD")
        print(method)# Default method is GET
        #header_deatils=os.getenv("LOCUST_AUTH")
        request_details = json.loads(os.getenv("LOCUST_DATA", "{}"))
        headers = json.loads(os.getenv("LOCUST_AUTH", "{}"))
        print("request_details", request_details)
        print("headers", headers)
        #data = os.getenv("LOCUST_DATA")  # Default to empty JSON
        # headers = {
        #     "Content-Type": "application/json"
        # }

        # for api in api_list:
        #     method = api.get("method", "GET").upper()
        #     url = api.get("url", "")
        #     headers = api.get("headers", {})
        #     body = api.get("body", {})
        #
        #     if not url:
        #         print("⚠️ No API URL provided. Skipping test.")
        #         continue  # Move to the next API
        #     if method == "GET":
        #         self.client.get(url, headers=headers)
        if method == "GET":
            self.client.get(endpoint, headers=headers, verify=False)
        elif method == "POST":
            self.client.post(endpoint, headers=headers, json=request_details["json"], verify=False)
        elif method == "PUT":
            self.client.put(endpoint, headers=headers, json=request_details["json"], verify=False)
        # elif method == "DELETE":
        #     self.client.delete(endpoint, headers=headers, verify=False)

        else:
            print(f"Unsupported method: {method}")

