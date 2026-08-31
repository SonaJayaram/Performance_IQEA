import os
import requests
import socket
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===========================================================
# Configuration (populate from client-provided values)
# ===========================================================
PEPGENX_TEAM_ID="dc2499e0-8e1f-46de-b2d2-1e98eac937c4"
PEPGENX_PROJECT_ID="4a249e4f-f770-4e6b-b8e7-ef084c4a6db3"
PEPGENX_API_KEY="a64e7f49-2779-49f5-abb2-cd46584807da"
PEPGENX_CLIENT_ID="0oa2bfeccjzx9OstR0h8"
PEPGENX_CLIENT_SECRET="4gim6NbfpI7m-LiFxYk-mqYbZICiPYQIqJxrb__CJrg5J5HTfWaZWmfC_dp190Og"
PEPGENX_MODEL="gpt-4o"

# Gateway URLs
APIGEE_URL = "https://apim-na.qa.mypepsico.com/cgf/pepgenx"
API_GATEWAY_URL = "https://pepgenx-apigateway-qa.global.gw01.aks01.eus.nonprod.azure.intra.pepsico.com"


# ===========================================================
# Utility – detect if VPN/internal network is reachable
# ===========================================================
def is_on_vpn():
    try:
        socket.gethostbyname("pepgenx-apigateway-qa.global.gw01.aks01.eus.nonprod.azure.intra.pepsico.com")
        return True
    except socket.gaierror:
        return False


# ===========================================================
# Function to get correct base URL
# ===========================================================
def get_pepgenx_base_url():
    if is_on_vpn():
        print("🔹 Detected VPN: Using internal API Gateway")
        return f"{API_GATEWAY_URL}/openai/deployments/{PEPGENX_MODEL}/chat/completions?api-version=2024-05-01-preview"
    else:
        print("🔹 Outside VPN: Using external Apigee endpoint")
        return f"{APIGEE_URL}/openai/deployments/{PEPGENX_MODEL}/chat/completions?api-version=2024-05-01-preview"


# ===========================================================
# Call PepGenX (Azure OpenAI–compatible)
# ===========================================================
def call_pepgenx(prompt_text):
    try:
        base_url = get_pepgenx_base_url()

        headers = {
            "Content-Type": "application/json",
            "api-key": PEPGENX_API_KEY,
            "x-client-id": PEPGENX_CLIENT_ID,
            "x-client-secret": PEPGENX_CLIENT_SECRET,
            "x-team-id": PEPGENX_TEAM_ID,
            "x-project-id": PEPGENX_PROJECT_ID,
        }

        payload = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_text}
            ],
            "max_tokens": 100
        }

        response = requests.post(base_url, headers=headers, json=payload, verify=False, timeout=30)

        if response.status_code == 200:
            data = response.json()
            message = data["choices"][0]["message"]["content"]
            print("✅ Response received from PepGenX:")
            print(message)
        else:
            print(f"❌ PepGenX request failed [{response.status_code}] → {response.text}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")


# ===========================================================
# Run a test call
# ===========================================================
if __name__ == "__main__":
    call_pepgenx("Hello! Please confirm if my PepGenX connection is active.")
