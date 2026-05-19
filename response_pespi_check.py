import  json
import re
resp="""
| Test Case Name | Step Number | Test Step Description | Test Step Expected Result | Status | Type | Category |\n|----------------|-------------|------------------------|---------------------------|--------|------|----------|\n| Verify Login Functionality | 1 | Navigate to the login page. | Login page is displayed. | New | Manual | Positive |\n| Verify Login Functionality | 2 | Enter valid credentials and click login. | User is successfully logged in and redirected to the dashboard. | New | Manual | Positive |\n| Verify Logout Functionality | 1 | Click on the logout button. | User is logged out and redirected to the login page. | New | Manual | Positive |\n| Verify Forecast Tab Accessibility | 1 | Navigate to the Forecast Tab after login. | Forecast Tab is displayed. | New | Manual | Positive |\n| Verify Sector Level Forecast Input Fields | 1 | Navigate to the Forecast Tab for a Multi Sector Buy Plan. | Editable numeric input fields for each sector are displayed. | New | Manual | Positive |\n| Verify Total Forecast Auto-Calculation | 1 | Enter forecast values for all sectors. | Total Forecast field auto-calculates the sum of all sector forecasts. | New | Manual | Positive |\n| Verify Total Forecast Field Read-Only | 1 | Attempt to edit the Total Forecast field. | Total Forecast field remains read-only. | New | Manual | Negative |\n| Verify Year-Based View Structure | 1 | Navigate to the Forecast Tab. | Tabs for 2025, 2026, and 2027 are displayed. | New | Manual | Positive |\n| Verify Data Consistency with Coverage Tab | 1 | Compare sectors in the Forecast Tab with the Coverage Tab. | Sectors in both tabs match. | New | Manual | Positive |\n| Verify Database Persistence of Forecast Data | 1 | Enter forecast values and save the Buy Plan. | Forecast data is saved in the database. | New | Manual | Workflow |\n| Verify Copy-Paste Functionality | 1 | Copy forecast data from one tab and paste it into another. | Data is successfully pasted. | New | Manual | Positive |\n| Verify Read-Only Logic for Past Month Rows | 1 | Attempt to edit rows for past months. | Past month rows remain read-only. | New | Manual | Negative |\n| Verify Actuals Forecast Validation | 1 | Enter identical totals for Actuals and Forecast. | Validation error is triggered. | New | Manual | Negative |\n| Verify Variance Highlighting | 1 | Enter values causing MoM variance to be 10% or negative. | Variance is highlighted. | New | Manual | Positive |\n| Verify Forecast Total Reflection in Buy Plan Tab | 1 | Save the Buy Plan and navigate to the Buy Plan Tab. | Forecast total matches in Volume LE and Updated Forecast columns. | New | Manual | Workflow |\n| Verify Empty Input for Sector Forecast | 1 | Leave a sector forecast field empty and save. | Validation error is displayed. | New | Manual | Negative |\n| Verify Special Characters in Sector Forecast | 1 | Enter special characters in a sector forecast field. | Validation error is displayed. | New | Manual | Negative |\n| Verify Minimum Boundary Value for Sector Forecast | 1 | Enter the minimum allowed value in a sector forecast field. | Value is accepted and Total Forecast updates correctly. | New | Manual | Edge case |\n| Verify Maximum Boundary Value for Sector Forecast | 1 | Enter the maximum allowed value in a sector forecast field. | Value is accepted and Total Forecast updates correctly. | New | Manual | Edge case |\n| Verify Spinner Visibility During Save | 1 | Save the Buy Plan after entering forecast data. | Spinner appears during the save process and disappears after completion. | New | Manual | UI |\n| Verify Error Message for Invalid Forecast Data | 1 | Enter invalid data in a sector forecast field and save. | Error message is displayed near the invalid field. | New | Manual | UI |\n| Verify Responsiveness of Forecast Tab | 1 | Resize the browser window to different screen sizes. | Forecast Tab adjusts layout and remains usable. | New | Manual | UI |\n| Verify Navigation Between Year Tabs | 1 | Click on each year tab (2025, 2026, 2027). | Corresponding forecast data is displayed for each year. | New | Manual | Positive |\n| Verify Forecast Update View Accessibility | 1 | Navigate to the Forecast Update view. | Forecast Update view is displayed. | New | Manual | Positive |\n| Verify Previous Month Forecast View Accessibility | 1 | Navigate to the Previous Month Forecast view. | Previous Month Forecast view is displayed. | New | Manual | Positive |\n| Verify Error Handling for Database Save Failure | 1 | Simulate a database save failure during Buy Plan save. | Error message is displayed, and data is not saved. | New | Manual | Negative |\n| Verify UI Feedback for Successful Save | 1 | Save the Buy Plan after entering forecast data. | Success message is displayed, and data is saved. | New | Manual | Positive |\n| Verify Total Forecast with Zero Values | 1 | Enter zero for all sector forecasts. | Total Forecast updates to zero. | New | Manual | Edge case |\n| Verify Total Forecast with Negative Values | 1 | Enter negative values for sector forecasts. | Validation error is displayed. | New | Manual | Negative |\n| Verify Multi-Year Data Persistence | 1 | Enter forecast data for all three years and save. | Data for all years is saved in the database. | New | Manual | Workflow |\n| Verify Forecast Tab Accessibility for Unauthorized Users | 1 | Attempt to access the Forecast Tab without proper permissions. | Access is denied, and an error message is displayed. | New | Manual | Negative |\n| Verify UI Behavior for Disabled Buttons | 1 | Attempt to save without entering required data. | Save button remains disabled. | New | Manual | UI |\n| Verify Forecast Data Export Functionality | 1 | Export forecast data to a file. | Data is successfully exported. | New | Manual | Positive |\n| Verify Forecast Data Import Functionality | 1 | Import forecast data from a file. | Data is successfully imported and displayed. | New | Manual | Positive |\n| Verify Undo Functionality in Forecast Tab | 1 | Make changes to forecast data and click undo. | Changes are reverted. | New | Manual | Positive |\n| Verify Redo Functionality in Forecast Tab | 1 | Undo changes and then click redo. | Changes are reapplied. | New | Manual | Positive |\n| Verify Forecast Tab Loading Time | 1 | Navigate to the Forecast Tab. | Tab loads within acceptable time limits. | New | Manual | Performance |\n| Verify Forecast Tab Accessibility on Mobile | 1 | Access the Forecast Tab on a mobile device. | Tab is accessible and usable on mobile. | New | Manual | UI |\n| Verify Forecast Tab Accessibility on Tablet | 1 | Access the Forecast Tab on a tablet device. | Tab is accessible and usable on tablet. | New | Manual | UI |\n| Verify Forecast Tab Accessibility on Desktop | 1 | Access the Forecast Tab on a desktop device. | Tab is accessible and usable on desktop. | New | Manual | UI |\n| Verify Forecast Tab Accessibility for Different Roles | 1 | Access the Forecast Tab with different user roles. | Tab behaves as per role permissions. | New | Manual | Positive |\n| Verify Forecast Tab Accessibility for Disabled Users | 1 | Access the Forecast Tab using assistive technologies. | Tab is accessible and usable. | New | Manual | Accessibility |\n| Verify Forecast Tab Accessibility for Different Browsers | 1 | Access the Forecast Tab using different browsers. | Tab behaves consistently across browsers. | New | Manual | Compatibility |\n| Verify Forecast Tab Accessibility for Different Languages | 1 | Access the Forecast Tab in different languages. | Tab displays correctly in all supported languages. | New | Manual | Localization |\n| Verify Forecast Tab Accessibility for Different Time Zones | 1 | Access the Forecast Tab from different time zones. | Tab behaves consistently across time zones. | New | Manual | Edge case |\n| Verify Forecast Tab Accessibility for Different Network Speeds | 1 | Access the Forecast Tab on slow and fast networks. | Tab behaves consistently across network speeds. | New | Manual | Performance |\n| Verify Forecast Tab Accessibility for Different Screen Resolutions | 1 | Access the Forecast Tab on devices with different screen resolutions. | Tab behaves consistently across resolutions. | New | Manual | UI |\n| Verify Forecast Tab Accessibility for Different Operating Systems | 1 | Access the Forecast Tab on different operating systems. | Tab behaves consistently across operating systems. | New | Manual | Compatibility |
"""
def parse_testcases_from_markdown(md_text):
    """
    Parse a Markdown table into structured test case dicts.
    Handles multi-line cells and extra pipes in descriptions.
    Returns a list of dicts, each with test case name, step number, description, expected, status, type, category.
    """
    import re
    rows = []
    md_text = md_text.strip()

    # Remove header/separator lines
    lines = [line for line in md_text.splitlines() if line.strip() and not re.match(r'^\|\s*-', line)]

    buffer = ""
    for line in lines:
        if line.startswith("|"):
            buffer += line + "\n"
            # Count pipes in the line; a full row should have 8 '|' for 7 columns
            if buffer.count("|") >= 8:
                parts = re.split(r'\s*\|\s*', buffer.strip())
                parts = [p.strip() for p in parts[1:-1]]  # skip first and last empty split
                if len(parts) == 7:
                    rows.append({
                        "name": parts[0],
                        "step_number": parts[1],
                        "description": parts[2],
                        "expected": parts[3],
                        "status": parts[4],
                        "type": parts[5],
                        "category": parts[6],
                    })
                buffer = ""  # reset for next row

    return rows
def response_check(raw_response):
    """
        Cleans up LLM JSON-like response by removing unnecessary sections.
        Handles prompt, metadata, and markdown code fences.
        """

    # Ensure string
    if not isinstance(raw_response, str):
        raw_response = str(raw_response)

    cleaned = raw_response

    # 1️⃣ Remove from "prompt" to the next closing brace
    cleaned = re.sub(r'","prompt".*?}', '}', cleaned, flags=re.DOTALL)

    # 2️⃣ Remove from '{"response' to the first colon
    cleaned = re.sub(r'\{"response"\s*:\s*', '', cleaned, flags=re.DOTALL)

    # 3️⃣ Remove from "```" to "markdown" (if exists)
    cleaned = re.sub(r'```.*?markdown', '', cleaned, flags=re.IGNORECASE | re.DOTALL)

    # 4️⃣ Remove all "```" fences
    cleaned = cleaned.replace("```", "")

    # 5️⃣ Clean up trailing braces, quotes, and whitespace
    cleaned = cleaned.strip("} \n\t\"")
    seen_steps = set()
    all_raw_responses = ""
    attempt = 0
    all_testcases = []
    min_new_threshold=5
    max_testcases=20
    all_raw_responses = ""
    all_raw_responses += "\n" + cleaned
    # Parse test cases
    new_cases = parse_testcases_from_markdown(cleaned)
    new_added = 0
    for case in new_cases:
        # key = (case["name"], case["step_number"])
        key = case["name"].strip().lower()
        if key not in seen_steps:
            seen_steps.add(key)
            all_testcases.append(case)
            new_added += 1

    print(f"New unique test cases added: {new_added} | Total: {len(all_testcases)}")
    return cleaned.strip()
response_check(resp)

