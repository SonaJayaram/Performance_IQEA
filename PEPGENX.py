import requests
import uuid
import json
import os
from dotenv import load_dotenv
load_dotenv()


okta_metadata= os.getenv("okta_metadata")
okta_secret = os.getenv("okta_secret")
okta_client = os.getenv("okta_client")
team_id = os.getenv("team_id")
project_id  = os.getenv("project_id")
api_key = os.getenv("api_key")
pepgenx_url= os.getenv("pepgenx_url")


def pepgenx_authendication():
        bearer_token = requests.get(okta_metadata,verify=False)
        token_url = bearer_token.json()["token_endpoint"]
        token_response = requests.post(
                token_url,
                auth=requests.auth.HTTPBasicAuth(
                    okta_client, okta_secret
                ),  # Basic Auth with client_id and client_secret
                data={"grant_type": "client_credentials"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},verify=False
        )

        bearer_token = token_response.json()["access_token"]
        print(bearer_token)
        return bearer_token
prompt ="""Hi"""
def llm_pepgenx(prompt):
        headers = {
                'Authorization': f'Bearer {pepgenx_authendication}',
                'team_id': team_id,
                'project_id': project_id,
                'user_id': 'test-user',
                'transaction_id': str(uuid.uuid4()),
                'x-pepgenx-apikey': api_key,
                "Content-Type": "application/json",
        }
        test_data = {
                "prompt": prompt,
                "generation_model": "gpt-4o",
                "temperature": 0.1
        }

        # response = requests.request("POST", url3, headers=headers,data=json.dumps(data2))
        response = requests.request("POST", pepgenx_url, headers=headers, data=json.dumps(test_data),verify=False)

        print(response.text)

llm_pepgenx(prompt)