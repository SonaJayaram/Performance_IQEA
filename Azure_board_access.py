import requests
from requests.auth import HTTPBasicAuth
import urllib3
import os
import json
from dotenv import load_dotenv

load_dotenv()
pat = os.getenv("Azure_board_access")

organization = "QE-Practice-team"
project = "qe-practice"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/wiql?api-version=7.0"
auth = HTTPBasicAuth("", pat)


# -------------------------------------
# Function 1: Fetch work item full details
# -------------------------------------
def fetch_workitem_detail(id):
    url = f"https://dev.azure.com/{organization}/_apis/wit/workitems/{id}?api-version=7.0"
    print(f"Fetching details for WorkItem {id} → {url}")
    response = requests.get(url, auth=auth, verify=False)
    return response.json()


# -------------------------------------
# Function 2: Query Active Epics
# -------------------------------------
def get_active_epics():
    epic_query = {
        "query": """
            SELECT [System.Id], [System.Title], [System.State]
            FROM WorkItems
            WHERE 
                [System.WorkItemType] = 'Epic' 
                AND [System.State] = 'Active'
            ORDER BY [System.Id]
        """
    }

    print("\n=========== ACTIVE EPICS ===========")
    epic_response = requests.post(base_url, json=epic_query, auth=auth, verify=False).json()
    epic_ids = [item["id"] for item in epic_response.get("workItems", [])]

    for wid in epic_ids:
        detail = fetch_workitem_detail(wid)
        fields = detail.get("fields", {})
        print(f"\nEPIC ID: {wid}")
        print(f"Title: {fields.get('System.Title', 'N/A')}")
        print(f"State: {fields.get('System.State', 'N/A')}")
        print("--------------------------")


# -------------------------------------
# Function 3: Query a specific User Story by ID
# -------------------------------------
def get_user_story_by_id(workitem_id):
    userstory_query = {
        "query": f"""
            SELECT [System.Id], [System.Title], [System.State]
            FROM WorkItems
            WHERE 
                [System.WorkItemType] = 'User Story'
                AND [System.State] = 'Active'
                AND [System.Id] = {workitem_id}
        """
    }

    print("\n=========== USER STORY DETAILS ===========")
    us_response = requests.post(base_url, json=userstory_query, auth=auth, verify=False).json()
    us_ids = [item["id"] for item in us_response.get("workItems", [])]

    if not us_ids:
        print(f"No active user story found for ID {workitem_id}")
        return

    wid = us_ids[0]
    detail = fetch_workitem_detail(wid)
    fields = detail.get("fields", {})

    print(f"\nUSER STORY ID: {wid}")
    print(f"Title: {fields.get('System.Title', 'N/A')}")
    print(f"Description: {fields.get('System.Description', 'N/A')}")
    print(f"State: {fields.get('System.State', 'N/A')}")
    print("--------------------------")

def upload_attachment_to_testcase(workitem_id, file_path):
    filename = os.path.basename(file_path)

    # Step 1: Upload attachment
    upload_url = (
        f"https://dev.azure.com/{organization}/_apis/wit/attachments"
        f"?fileName={filename}&api-version=7.0"
    )

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    upload_response = requests.post(
        upload_url,
        headers={"Content-Type": "application/octet-stream"},
        data=file_bytes,
        auth=auth,
        verify=False
    )

    print("UPLOAD STATUS:", upload_response.status_code)
    print("RAW:", upload_response.text)

    if upload_response.status_code not in [200, 201]:
        print("❌ Attachment upload failed")
        return

    upload_json = upload_response.json()
    attachment_url = upload_json["url"]

    # Step 2: Attach uploaded file to test case
    patch_document = [
        {
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": "AttachedFile",
                "url": attachment_url,
                "attributes": {"comment": "Uploaded by automation"}
            }
        }
    ]

    patch_headers = {"Content-Type": "application/json-patch+json"}

    patch_response = requests.patch(
        f"https://dev.azure.com/{organization}/_apis/wit/workitems/{workitem_id}?api-version=7.0",
        headers=patch_headers,
        data=json.dumps(patch_document),
        auth=auth,
        verify=False
    )

    print(f"📎 Attachment '{filename}' uploaded to Test Case {workitem_id}")

def create_test_case(parent_id, title):
    url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/$Test%20Case?api-version=7.0"

    patch_document = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": title
        },
        {
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"https://dev.azure.com/{organization}/_apis/wit/workitems/{parent_id}"
            }
        }
    ]

    headers = {"Content-Type": "application/json-patch+json"}

    response = requests.patch(
        url,
        data=json.dumps(patch_document),
        headers=headers,
        auth=auth,
        verify=False
    )

    test_case = response.json()
    test_case_id = test_case["id"]

    print(f"✅ Test Case created under WorkItem {parent_id}: ID = {test_case_id}")
    return test_case_id


def validate_work_item_exists(workitem_id):
    url = f"https://dev.azure.com/{organization}/_apis/wit/workitems/{workitem_id}?api-version=7.0"
    res = requests.get(url, auth=auth, verify=False)

    # Case 1: Found
    if res.status_code == 200:
        return True, "OK"

    # Case 2: Azure sends JSON error
    try:
        error_json = res.json()
        msg = error_json.get("message", "")

        if f"No active user story found for ID {workitem_id}" in msg:
            return False, f"❌ Work item {workitem_id} does not exist."

        if f"Work item {workitem_id} does not exist" in msg:
            return False, f"❌ Work item {workitem_id} does not exist."

        # Permissions issue
        if "permissions" in msg.lower():
            return False, f"⚠ Work item exists but you do not have permission to read it."

        # Other Azure error
        return False, f"⚠ Azure Error: {msg}"

    except Exception:
        # Non-JSON response
        return False, f"⚠ Unexpected Azure response: {res.text}"
def create_direct_test_case(title="IQEA_Testcases_recorded"):
    url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/$Test%20Case?api-version=7.0"

    patch_document = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": title
        }
    ]

    headers = {"Content-Type": "application/json-patch+json"}

    response = requests.patch(
        url,
        data=json.dumps(patch_document),
        headers=headers,
        auth=auth,
        verify=False
    )

    if response.status_code >= 300:
        print("❌ Failed to create test case:", response.text)
        return None

    test_case = response.json()
    test_case_id = test_case["id"]

    print(f"✅ Direct Test Case created successfully: ID = {test_case_id}")
    return test_case_id
# Test call
get_user_story_by_id(4567)
# test_case_id=create_test_case(37,"IQEA_Testcases")
# file_path=r"C:\Users\sathanantham.aru\PycharmProjects\ai-accelerator\output\Test_Cases_collection\SauceDemolblPYTCc.xlsx"
# upload_attachment_to_testcase(test_case_id,file_path)
exists, message = validate_work_item_exists(4567)
if exists:
    print(message)
else:
    print(message)

create_direct_test_case()
