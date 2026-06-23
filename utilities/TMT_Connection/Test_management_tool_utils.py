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

def create_test_case(parent_id, title="IQEA_Testcases"):
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

# # Test call
# get_user_story_by_id(37)
# test_case_id=create_test_case(37,"IQEA_Testcases")
# file_path=r"C:\Users\sathanantham.aru\PycharmProjects\ai-accelerator\output\Test_Cases_collection\SauceDemolblPYTCc.xlsx"
# upload_attachment_to_testcase(test_case_id,file_path)


# ─────────────────────────────────────────────────────────────────────────────
# Azure Test Plans — fetch plans / suites / test cases
# ─────────────────────────────────────────────────────────────────────────────

def get_all_testcases_direct(max_results=500):
    """Fetch all Test Case work items directly via WIQL — no test plan required."""
    wiql_query = {
        "query": (
            "SELECT [System.Id], [System.Title] FROM WorkItems "
            "WHERE [System.WorkItemType] = 'Test Case' "
            "ORDER BY [System.Id]"
        )
    }
    response = requests.post(base_url, json=wiql_query, auth=auth, verify=False)
    print(f"WIQL status: {response.status_code}")
    print(f"WIQL response: {response.text[:500]}")
    if response.status_code != 200:
        print(f"❌ WIQL query failed: {response.status_code} {response.text}")
        return []

    work_items = response.json().get("workItems", [])
    print(f"Work items found: {len(work_items)}")
    ids = [item["id"] for item in work_items][:max_results]
    if not ids:
        return []

    # Batch fetch titles (up to 200 per request)
    result = []
    batch_size = 200
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i: i + batch_size]
        ids_str = ",".join(str(x) for x in batch_ids)
        url = (
            f"https://dev.azure.com/{organization}/_apis/wit/workitems"
            f"?ids={ids_str}&fields=System.Id,System.Title&api-version=7.0"
        )
        batch_response = requests.get(url, auth=auth, verify=False)
        if batch_response.status_code != 200:
            print(f"❌ Batch fetch failed: {batch_response.status_code}")
            continue
        for item in batch_response.json().get("value", []):
            fields = item.get("fields", {})
            tc_id = fields.get("System.Id", item.get("id", ""))
            title = fields.get("System.Title", "")
            steps_summary = _extract_steps_summary(tc_id)
            result.append({"id": tc_id, "title": title, "steps_summary": steps_summary})

    print(f"✅ Fetched {len(result)} test cases directly.")
    return result


def get_test_plans():
    """Return list of {id, name} for all test plans in the project."""
    url = f"https://dev.azure.com/{organization}/{project}/_apis/testplan/plans?api-version=7.0"
    response = requests.get(url, auth=auth, verify=False)
    if response.status_code != 200:
        print(f"❌ Failed to fetch test plans: {response.status_code} {response.text}")
        return []
    plans = response.json().get("value", [])
    return [{"id": p["id"], "name": p["name"]} for p in plans]


def get_test_suites(plan_id):
    """Return list of {id, name} for all suites under a test plan."""
    url = (
        f"https://dev.azure.com/{organization}/{project}"
        f"/_apis/testplan/plans/{plan_id}/suites?api-version=7.0"
    )
    response = requests.get(url, auth=auth, verify=False)
    if response.status_code != 200:
        print(f"❌ Failed to fetch suites for plan {plan_id}: {response.status_code}")
        return []
    suites = response.json().get("value", [])
    return [{"id": s["id"], "name": s["name"]} for s in suites]


def get_testcases_from_suite(plan_id, suite_id):
    """Return list of {id, title, steps_summary} for all test cases in a suite."""
    url = (
        f"https://dev.azure.com/{organization}/{project}"
        f"/_apis/testplan/plans/{plan_id}/suites/{suite_id}/testcases?api-version=7.0"
    )
    response = requests.get(url, auth=auth, verify=False)
    if response.status_code != 200:
        print(f"❌ Failed to fetch test cases: {response.status_code} {response.text}")
        return []

    items = response.json().get("value", [])
    result = []
    for item in items:
        wi = item.get("workItem", {})
        tc_id = wi.get("id", "")
        title = wi.get("name", "")
        # Fetch steps from the work item fields
        steps_summary = _extract_steps_summary(tc_id)
        result.append({"id": tc_id, "title": title, "steps_summary": steps_summary})
    return result


def get_all_testcases_from_plan(plan_id):
    """Fetch test cases from every suite in the plan. Returns combined list."""
    suites = get_test_suites(plan_id)
    all_tcs = []
    seen_ids = set()
    for suite in suites:
        for tc in get_testcases_from_suite(plan_id, suite["id"]):
            if tc["id"] not in seen_ids:
                seen_ids.add(tc["id"])
                all_tcs.append(tc)
    return all_tcs


def _extract_steps_summary(tc_id):
    """Pull Microsoft.VSTS.TCM.Steps field and return plain-text summary (max 300 chars)."""
    if not tc_id:
        return ""
    url = (
        f"https://dev.azure.com/{organization}/_apis/wit/workitems/{tc_id}"
        f"?fields=Microsoft.VSTS.TCM.Steps&api-version=7.0"
    )
    response = requests.get(url, auth=auth, verify=False)
    if response.status_code != 200:
        return ""
    fields = response.json().get("fields", {})
    raw_steps = fields.get("Microsoft.VSTS.TCM.Steps", "") or ""
    # Strip XML tags (steps are stored as XML)
    import re
    plain = re.sub(r"<[^>]+>", " ", raw_steps).strip()
    plain = re.sub(r"\s+", " ", plain)
    return plain[:300]


def build_steps_xml(steps_rows):
    """
    Convert a list of step dicts into Azure DevOps TCM steps XML.
    Each dict: {step_number, description, expected}
    """
    import xml.etree.ElementTree as ET
    root = ET.Element("steps", id="0", last=str(len(steps_rows)))
    for i, row in enumerate(steps_rows, 1):
        step = ET.SubElement(root, "step", id=str(i), type="ActionStep")
        action = ET.SubElement(step, "parameterizedString", isformatted="true")
        action.text = row.get("description", "")
        expected = ET.SubElement(step, "parameterizedString", isformatted="true")
        expected.text = row.get("expected", "")
        ET.SubElement(step, "description")
    return ET.tostring(root, encoding="unicode")


def create_testcase_with_steps(title, steps_xml, parent_id=None):
    """
    Create an Azure DevOps Test Case work item with steps.
    If parent_id is provided, links it as a child of that work item.
    Returns the new work item ID.
    """
    url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/$Test%20Case?api-version=7.0"

    patch_document = [
        {"op": "add", "path": "/fields/System.Title", "value": title},
        {"op": "add", "path": "/fields/Microsoft.VSTS.TCM.Steps", "value": steps_xml},
    ]

    if parent_id:
        patch_document.append({
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"https://dev.azure.com/{organization}/_apis/wit/workitems/{parent_id}"
            }
        })

    headers = {"Content-Type": "application/json-patch+json"}
    response = requests.patch(url, headers=headers, data=json.dumps(patch_document), auth=auth, verify=False)

    if response.status_code not in (200, 201):
        print(f"❌ Failed to create test case '{title}': {response.text}")
        return None

    tc_id = response.json()["id"]
    print(f"✅ Created Test Case '{title}' — ID: {tc_id}")
    return tc_id


def update_testcase_title(tc_id, new_title):
    """Patch the title of an existing test case work item."""
    url = f"https://dev.azure.com/{organization}/_apis/wit/workitems/{tc_id}?api-version=7.0"
    patch = [{"op": "replace", "path": "/fields/System.Title", "value": new_title}]
    headers = {"Content-Type": "application/json-patch+json"}
    response = requests.patch(url, headers=headers, data=json.dumps(patch), auth=auth, verify=False)
    if response.status_code in (200, 201):
        print(f"✅ Updated test case {tc_id} title.")
    else:
        print(f"❌ Failed to update test case {tc_id}: {response.text}")
    return response.status_code


# ─────────────────────────────────────────────────────────────────────────────
# Jira Xray — fetch folders / test cases  (basic REST, no Xray plugin required)
# ─────────────────────────────────────────────────────────────────────────────

jira_url = os.getenv("JIRA_URL", "")
jira_user = os.getenv("JIRA_USER", "")
jira_token = os.getenv("JIRA_TOKEN", "")


def get_jira_test_projects():
    """Return list of Jira projects (id, key, name)."""
    if not jira_url:
        return []
    url = f"{jira_url}/rest/api/3/project"
    response = requests.get(url, auth=HTTPBasicAuth(jira_user, jira_token), verify=False)
    if response.status_code != 200:
        return []
    return [{"id": p["id"], "key": p["key"], "name": p["name"]} for p in response.json()]


def get_jira_testcases(project_key, max_results=200):
    """Fetch issues of type 'Test' from a Jira project via JQL."""
    if not jira_url:
        return []
    jql = f'project = "{project_key}" AND issuetype = Test ORDER BY created DESC'
    url = f"{jira_url}/rest/api/3/search"
    params = {"jql": jql, "maxResults": max_results, "fields": "summary,description"}
    response = requests.get(
        url, params=params,
        auth=HTTPBasicAuth(jira_user, jira_token),
        verify=False
    )
    if response.status_code != 200:
        print(f"❌ Jira fetch failed: {response.status_code} {response.text}")
        return []
    issues = response.json().get("issues", [])
    result = []
    for issue in issues:
        fields = issue.get("fields", {})
        desc = fields.get("description") or {}
        desc_text = ""
        if isinstance(desc, dict):
            for block in desc.get("content", []):
                for item in block.get("content", []):
                    desc_text += item.get("text", "") + " "
        result.append({
            "id": issue["key"],
            "title": fields.get("summary", ""),
            "steps_summary": desc_text.strip()[:300]
        })
    return result
