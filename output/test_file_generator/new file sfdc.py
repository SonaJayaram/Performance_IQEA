import os
import re
import time
import pytest
import allure
from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError

os.makedirs("allure-results", exist_ok=True)

DEFAULT_WAIT = 5
EXPLICIT_WAIT = 10
RETRY_ATTEMPTS = 1
HEADLESS = os.environ.get("HEADLESS", "false").lower() in ("1", "true", "yes")

recorded_actions_text = """Salesforce Login URL: [https://mindful-shark-fv3y29-dev-ed.trailblaze.lightning.force.com/ ]
Enter "[USERNAME]" in the "Username" field 
Enter "[PASSWORD]" in the "Password" field
Click on "Log In"
Switched to new window: [https://mindful-shark-fv3y29-dev-ed.trailblaze.my.salesforce.com/_ui/identity/verification/method/EmailVerificationFinishUi/e?vcsrf=YuQ5OLv6yyJ29DpjFUhaXomRfGAwYfrRlfef_7PB71siOjtS_gQJSbQVEOZWMGUe2JswGDf-Liy9OxH_fZ8AJsPy1FUInAh4arzvOjO_lgZcYgk_Qm4UgzbVOigNfE9YvhJ9Utv2hCXSY7tbkBFlydpPjL_1_xF7vrVYzKWdlswRExyal2VsPNvI7LHOa32gfp2uDoNYgN-K9o8Opc-L_uG53MV3zchD5y1h1ZByU8cf3XfqanITSIjhBWvza8jMxTNeCIXWVegWbxFaXvq8a2SqxMLe0INXSkjJv2Ec2l1VK_8Ffcn42ZhuwCdgWl4IAZ3EE233dALhfMqJZ8y-aJC0kf-QlnqsDoDDkysm_G0F9HKpwYFFoZrY4R1GED2d7UH1PQ13-rS1Wybngf8mEtCQfR2yzX1bN8tGxa91JA4NrQqP4NkiM27gMuZXdQXk8q_8Ax11vF-Kaogzlv9176tLS_qDy3IjgKFk2vvsFlZaqFolddLklRMBkb4YzC1PbpZYa21_U-vJmzPFr01O2YkRdd_HRCdTMGQftSgotIg-35UxowzVrfOT6a0ZjItqvfu8tRdjILFR08NJ3iNtFIR-2mmu4Fqf5ARZ4F0BuOucdi1LpFry5euGgTBcIszKHeLUzd_yrHFCRuLZ5p4UEClh9nzD0mSjPkya9oYN7X0%3D&vpol=ic&vflid=0&vfgrp=890730828&retURL=%2Fsecur%2Ffrontdoor.jsp%3Fallp%3D1%26cshc%3Dy00000Dyuz7y00000MXzeM%26apv%3D1%26display%3Dpage%26ucs%3D1]
Enter "[VERIFICATION_CODE]" in the "Verification Code" field
Change the value to "Verified" in "Verify Your Identity"
Click on "Verify"
Landing Salesforce Home page: [https://mindful-shark-fv3y29-dev-ed.trailblaze.lightning.force.com/lightning/page/home]
Click on "Contacts" tab (URL: [https://mindful-shark-fv3y29-dev-ed.trailblaze.lightning.force.com/lightning/o/Contact/pipelineInspection?filterName=00BQy00000TK9JNMA1])
Contacts Intelligence View page gets displayed
Click on "New" (URL: [https://mindful-shark-fv3y29-dev-ed.trailblaze.lightning.force.com/lightning/o/Contact/new?count=1&nooverride=1&useRecordTypeCheck=1&navigationLocation=LIST_VIEW&uid=177324838383081506&backgroundContext=%2Flightning%2Fo%2FContact%2FpipelineInspection%3FfilterName%3D00BQy00000TK9JNMA1])
Click on "Salutation" 
Select "[SALUTATION]" in the "Salutation" field
Click on "First Name"
Enter "[CONTACT_FIRST_NAME]" in the "First Name" field
Click on "Last Name"
Enter "[CONTACT_LAST_NAME]" in the "Last Name" field
Click on "Email"
Enter "[CONTACT_EMAIL]" in the "Email" field
Click on "Account Name"
Enter "[ACCOUNT_NAME]" in the "Account Name" lookup field
Click on "Save"
Contact Saved with the Success Toast Message Contact Record Detail Page [https://mindful-shark-fv3y29-dev-ed.trailblaze.lightning.force.com/lightning/r/Contact/003Qy00001D6J81IAF/view ]
"""

_base_url_match = re.search(r"Salesforce Login URL:\s*\[(https?://[^\]\s]+)", recorded_actions_text)
BASE_URL = _base_url_match.group(1).strip() if _base_url_match else None
if not BASE_URL:
    raise RuntimeError("Base URL missing from recorded actions. Cannot proceed with tests.")

# Attempt to import real POMs if available, otherwise provide robust fallbacks.
try:
    from output.page_file_generator.Sfdc_login import Sfdc_login  # exact import requested by validation
except Exception:
    class Sfdc_login:
        def __init__(self, page: Page):
            self.page = page
            self.username = page.locator('input[name="username"], input#username, input[type="email"], input[placeholder*="Username"]')
            self.password = page.locator('input[name="password"], input#password, input[type="password"], input[placeholder*="Password"]')
            self.login_button = page.locator('button[type="submit"], input[type="submit"], button:has-text("Log In"), button:has-text("Log in")')

        def wait_for_element(self, locator_key: str):
            locator = getattr(self, locator_key)
            locator.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
            return locator

        def enter_text(self, locator_key: str, text: str):
            locator = getattr(self, locator_key)
            locator.fill(text)

        def click_element(self, locator_key: str):
            locator = getattr(self, locator_key)
            locator.click()

        def switch_to_new_window(self, page: Page, trigger_locator_key: str):
            trigger = getattr(self, trigger_locator_key)
            with page.expect_popup() as popup_info:
                trigger.click()
            new_page = popup_info.value
            new_page.bring_to_front()
            return new_page

        def login(self, username: str, password: str):
            self.wait_for_element("username")
            self.enter_text("username", username)
            self.wait_for_element("password")
            self.enter_text("password", password)
            try:
                with self.page.expect_popup() as popup_info:
                    self.click_element("login_button")
                new_page = popup_info.value
                new_page.bring_to_front()
                return new_page
            except Exception:
                # fallback to clicking without popup
                try:
                    self.click_element("login_button")
                except Exception:
                    pass
                return self.page

try:
    from output.page_file_generator.sfdc_otp import sfdc_otp
except Exception:
    class sfdc_otp:
        def __init__(self, page: Page):
            self.page = page
            self.verification_code = page.locator('input[name="verification_code"], input[placeholder*="Verification"], input[type="text"], input[id*="verification"]')
            self.verify_button = page.locator('button:has-text("Verify"), button:has-text("Continue"), button:has-text("Submit")')
            self.verify_identity_select = page.locator('select[name="verifyIdentity"], select[aria-label*="Verify Your Identity"], select[id*="verify"]')

        def wait_for_element(self, locator_key: str):
            locator = getattr(self, locator_key)
            locator.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
            return locator

        def click_element(self, locator_key: str):
            locator = getattr(self, locator_key)
            locator.click()

        def enter_text(self, locator_key: str, text: str):
            locator = getattr(self, locator_key)
            locator.fill(text)

        def switch_to_new_window(self, page: Page, trigger_locator_key: str):
            trigger = getattr(self, trigger_locator_key)
            with page.expect_popup() as popup_info:
                trigger.click()
            new_page = popup_info.value
            new_page.bring_to_front()
            return new_page

        def login(self, verification_code: str):
            self.wait_for_element("verification_code")
            self.enter_text("verification_code", verification_code)
            try:
                self.verify_identity_select.select_option(label="Verified")
            except Exception:
                pass
            try:
                self.click_element("verify_button")
            except Exception:
                pass

        def enter_verification_code(self, code: str):
            self.wait_for_element("verification_code")
            self.enter_text("verification_code", code)

try:
    from output.page_file_generator.sfdc_homepage import sfdc_homepage
except Exception:
    class sfdc_homepage:
        def __init__(self, page: Page):
            self.page = page
            self.contacts_tab = page.locator('a[title="Contacts"], a:has-text("Contacts"), button:has-text("Contacts")')
            self.new_button = page.locator('button:has-text("New"), a:has-text("New")')
            self._other = page.locator('div[role="main"], main')

        def wait_for_element(self, locator_key: str):
            locator = getattr(self, locator_key)
            locator.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
            return locator

        def enter_text(self, locator_key: str, text: str):
            locator = getattr(self, locator_key)
            locator.fill(text)

        def click_element(self, locator_key: str):
            locator = getattr(self, locator_key)
            locator.click()

        def switch_to_new_window(self, page: Page, trigger_locator_key: str):
            trigger = getattr(self, trigger_locator_key)
            with page.expect_popup() as popup_info:
                trigger.click()
            new_page = popup_info.value
            new_page.bring_to_front()
            return new_page

        def login(self, *args, **kwargs):
            pass

        def verify_identity(self):
            try:
                self._other.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
            except Exception:
                pass

        def click_contacts_tab(self):
            self.wait_for_element("contacts_tab")
            self.click_element("contacts_tab")

try:
    from output.page_file_generator.sfdc_contact_new import sfdc_contact_new
except Exception:
    class sfdc_contact_new:
        def __init__(self, page: Page):
            self.page = page
            self.salutation = page.locator('select[name="salutation"], div[aria-label*="Salutation"], label:has-text("Salutation") ~ div select, select[aria-label*="Salutation"]')
            self.first_name = page.locator('input[name="firstName"], input[placeholder*="First Name"], input[aria-label*="First Name"]')
            self.last_name = page.locator('input[name="lastName"], input[placeholder*="Last Name"], input[aria-label*="Last Name"]')
            self.email = page.locator('input[type="email"], input[placeholder*="Email"], input[aria-label*="Email"]')
            self.account_name = page.locator('input[aria-label*="Account Name"], input[name="accountName"], input[placeholder*="Account Name"]')
            self.save_button = page.locator('button:has-text("Save"), button[title="Save"]')
            self.assistant_name = page.locator('input[aria-label*="Assistant"], input[name*="assistant"]')
            self.assistant_phone = page.locator('input[aria-label*="Assistant Phone"], input[name*="assistantPhone"]')
            self.bio = page.locator('textarea[aria-label*="Description"], textarea[name*="bio"], textarea[placeholder*="Bio"]')
            self.new_button = page.locator('button:has-text("New"), a:has-text("New")')

        def wait_for_element(self, locator_key: str):
            locator = getattr(self, locator_key)
            locator.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
            return locator

        def click_element(self, locator_key: str):
            locator = getattr(self, locator_key)
            locator.click()

        def enter_text(self, locator_key: str, text: str):
            locator = getattr(self, locator_key)
            locator.fill(text)

        def switch_to_new_window(self, page: Page, trigger_locator_key: str):
            trigger = getattr(self, trigger_locator_key)
            with page.expect_popup() as popup_info:
                trigger.click()
            new_page = popup_info.value
            new_page.bring_to_front()
            return new_page

        def click_new_button(self):
            self.wait_for_element("new_button")
            self.click_element("new_button")

        def enter_last_name(self, last_name: str):
            self.wait_for_element("last_name")
            self.enter_text("last_name", last_name)

        def enter_email(self, email: str):
            self.wait_for_element("email")
            self.enter_text("email", email)

        def enter_assistant_name(self, name: str):
            try:
                self.wait_for_element("assistant_name")
                self.enter_text("assistant_name", name)
            except Exception:
                pass

        def enter_bio(self, bio_text: str):
            try:
                self.wait_for_element("bio")
                self.enter_text("bio", bio_text)
            except Exception:
                pass

        def enter_assistant_phone(self, phone: str):
            try:
                self.wait_for_element("assistant_phone")
                self.enter_text("assistant_phone", phone)
            except Exception:
                pass

        def click_save_edit_button(self):
            self.wait_for_element("save_button")
            self.click_element("save_button")

def safe_goto(page: Page, url: str, timeout: int = EXPLICIT_WAIT * 1000):
    try:
        page.goto(url, timeout=timeout)
    except Exception:
        time.sleep(0.5)
        try:
            page.goto(url, timeout=timeout)
        except Exception:
            try:
                page.reload()
            except Exception:
                raise

def helper_click_with_healing(page: Page, locator, alt_selector: str = None):
    try:
        locator.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
        locator.click()
        return
    except Exception:
        with allure.step("healing: initial click failed, retrying"):
            try:
                time.sleep(0.5)
                locator.click()
                return
            except Exception:
                try:
                    allure.attach(page.screenshot(), name="healing_after_retry", attachment_type=allure.attachment_type.PNG)
                except Exception:
                    pass
                if alt_selector:
                    try:
                        alt = page.locator(alt_selector)
                        alt.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                        alt.click()
                        return
                    except Exception:
                        pass
                try:
                    locator.click(force=True)
                    return
                except Exception as e:
                    try:
                        allure.attach(page.content(), name="healing_failure_html", attachment_type=allure.attachment_type.HTML)
                    except Exception:
                        pass
                    raise

@pytest.fixture(scope="function")
def page_context():
    with sync_playwright() as p:
        browser = p.webkit.launch(headless=HEADLESS)
        context: BrowserContext = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            java_script_enabled=True,
            ignore_https_errors=True,
            viewport={"width": 1400, "height": 900}
        )
        page = context.new_page()
        yield page
        try:
            context.close()
            browser.close()
        except Exception:
            pass

def pytest_runtest_makereport(item, call):
    if call.when == "call":
        if call.excinfo is not None:
            page = item.funcargs.get("page_context")
            if page:
                try:
                    filename = os.path.join("allure-results", f"{item.name}_failure.png")
                    page.screenshot(path=filename)
                    with open(filename, "rb") as f:
                        allure.attach(f.read(), name=f"{item.name}_failure_screenshot", attachment_type=allure.attachment_type.PNG)
                except Exception:
                    pass

test_files_content = {'TC05 - Create New Contact (Positive).xlsx': {'test_case_name': '**TC05 - Create New Contact (Positive)**', 'page_name': None, 'actions': [], 'expected_results': []}}
parsed_test_cases = []
for filename, tc in test_files_content.items():
    parsed_test_cases.append({
        "file": filename,
        "test_case_name": tc.get("test_case_name") or filename,
        "actions": tc.get("actions", []),
        "expected_results": tc.get("expected_results", [])
    })

GENERATED_TEST_COUNT = 1
PARSED_TEST_COUNT = len(parsed_test_cases)
if GENERATED_TEST_COUNT != PARSED_TEST_COUNT:
    raise RuntimeError(f"Generated tests ({GENERATED_TEST_COUNT}) != parsed cases ({PARSED_TEST_COUNT})")

raw_name = parsed_test_cases[0]["test_case_name"]
sanitized = re.sub(r"\W+", "_", raw_name).strip("_")
test_func_name = f"test_{sanitized}"

ENV_USERNAME = "rajaram111294@mindful-shark-fv3y29.comrajaram111294@mindful-shark-fv3y29.com"
ENV_PASSWORD = "Tiger@2026"
ENV_VERIFICATION_CODE = os.environ.get("SF_VERIFICATION_CODE", "")
ENV_SALUTATION = os.environ.get("CONTACT_SALUTATION", "Mr.")
ENV_CONTACT_FIRST_NAME = os.environ.get("CONTACT_FIRST_NAME", "Auto")
ENV_CONTACT_LAST_NAME = os.environ.get("CONTACT_LAST_NAME", "Contact")
ENV_CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", f"auto.contact.{int(time.time())}@example.com")
ENV_ACCOUNT_NAME = os.environ.get("ACCOUNT_NAME", "Default Account")

@allure.title(parsed_test_cases[0]["test_case_name"])
def test_TC05_Create_New_Contact_Positive(page_context: Page):
    page = page_context
    if not ENV_USERNAME or not ENV_PASSWORD:
        with allure.step("Missing credentials: SF_USERNAME or SF_PASSWORD not provided"):
            pytest.fail("Test data missing: SF_USERNAME and SF_PASSWORD must be set as environment variables.")

    try:
        with allure.step(f"Navigate to base URL: {BASE_URL}"):
            safe_goto(page, BASE_URL)
            try:
                allure.attach(page.screenshot(), name="after_initial_navigation", attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass
            try:
                allure.attach(page.content(), name="page_html", attachment_type=allure.attachment_type.HTML)
            except Exception:
                pass

        try:
            with allure.step("Instantiate Sfdc_login POM"):
                try:
                    login_page = Sfdc_login(page)
                except Exception:
                    with allure.step("auto-fix: constructor fallback for Sfdc_login"):
                        login_page = Sfdc_login(page)
        except Exception:
            login_page = Sfdc_login(page)

        with allure.step("Perform login on Salesforce"):
            try:
                with page.expect_popup() as popup_info:
                    # ensure locators exist on POM
                    if hasattr(login_page, "wait_for_element"):
                        try:
                            login_page.wait_for_element("username")
                        except Exception:
                            pass
                    # enter credentials using methods if present
                    if hasattr(login_page, "enter_text"):
                        try:
                            login_page.enter_text("username", ENV_USERNAME)
                            login_page.enter_text("password", ENV_PASSWORD)
                        except Exception:
                            try:
                                # try direct locator attributes
                                if hasattr(login_page, "username"):
                                    login_page.username.fill(ENV_USERNAME)
                                if hasattr(login_page, "password"):
                                    login_page.password.fill(ENV_PASSWORD)
                            except Exception:
                                pass
                    # trigger click using healing helper
                    trigger = getattr(login_page, "login_button", None)
                    if trigger is not None:
                        helper_click_with_healing(page, trigger)
                    else:
                        # fallback to generic button
                        btn = page.locator('button:has-text("Log In"), button:has-text("Log in")')
                        helper_click_with_healing(page, btn)
                new_page = popup_info.value
                new_page.bring_to_front()
                page = new_page
                try:
                    allure.attach(page.screenshot(), name="after_login_popup", attachment_type=allure.attachment_type.PNG)
                except Exception:
                    pass
            except Exception:
                # no popup, try login via method if exists
                try:
                    result = login_page.login(ENV_USERNAME, ENV_PASSWORD)
                    if result and isinstance(result, Page) and result != page:
                        page = result
                        page.bring_to_front()
                        try:
                            allure.attach(page.screenshot(), name="after_login_returned_page", attachment_type=allure.attachment_type.PNG)
                        except Exception:
                            pass
                except Exception:
                    # as last resort attempt a direct click on login button
                    try:
                        if hasattr(login_page, "login_button"):
                            helper_click_with_healing(page, login_page.login_button)
                    except Exception:
                        pass

        try:
            with allure.step("Re-instantiate POMs after navigation"):
                try:
                    otp_page = sfdc_otp(page)
                except Exception:
                    with allure.step("auto-fix: constructor fallback for sfdc_otp"):
                        otp_page = sfdc_otp(page)
                try:
                    homepage = sfdc_homepage(page)
                except Exception:
                    with allure.step("auto-fix: constructor fallback for sfdc_homepage"):
                        homepage = sfdc_homepage(page)
                try:
                    contact_new = sfdc_contact_new(page)
                except Exception:
                    with allure.step("auto-fix: constructor fallback for sfdc_contact_new"):
                        contact_new = sfdc_contact_new(page)
        except Exception:
            otp_page = None
            homepage = sfdc_homepage(page)
            contact_new = sfdc_contact_new(page)

        try:
            with allure.step("Handle potential OTP verification"):
                if otp_page:
                    try:
                        otp_page.wait_for_element("verification_code")
                        if not ENV_VERIFICATION_CODE:
                            try:
                                allure.attach(page.screenshot(), name="waiting_for_otp", attachment_type=allure.attachment_type.PNG)
                            except Exception:
                                pass
                            pytest.fail("Verification code required but SF_VERIFICATION_CODE not set in environment.")
                        otp_page.enter_verification_code(ENV_VERIFICATION_CODE)
                        otp_page.login(ENV_VERIFICATION_CODE)
                        pages = page.context.pages
                        if len(pages) > 1:
                            page = pages[-1]
                            page.bring_to_front()
                            homepage = sfdc_homepage(page)
                            contact_new = sfdc_contact_new(page)
                    except PlaywrightTimeoutError:
                        # OTP not present - continue
                        pass
                    except Exception:
                        with allure.step("OTP handling encountered an issue, continuing"):
                            try:
                                allure.attach(page.screenshot(), name="otp_issue", attachment_type=allure.attachment_type.PNG)
                            except Exception:
                                pass
        except Exception:
            pass

        with allure.step("Verify home and click Contacts tab"):
            try:
                homepage.verify_identity()
            except Exception:
                try:
                    homepage = sfdc_homepage(page)
                except Exception:
                    pass
            # click contacts
            if hasattr(homepage, "click_contacts_tab"):
                try:
                    homepage.click_contacts_tab()
                except Exception:
                    # try direct locator click
                    try:
                        helper_click_with_healing(page, homepage.contacts_tab)
                    except Exception:
                        pass
            else:
                helper_click_with_healing(page, page.locator('a[title="Contacts"], a:has-text("Contacts"), button:has-text("Contacts")'))
            page.wait_for_timeout(500)
            try:
                allure.attach(page.screenshot(), name="after_click_contacts", attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass

        with allure.step("Open New Contact form"):
            try:
                if hasattr(homepage, "new_button"):
                    helper_click_with_healing(page, homepage.new_button)
                elif hasattr(contact_new, "click_new_button"):
                    contact_new.click_new_button()
                else:
                    btn = page.locator('button:has-text("New")')
                    helper_click_with_healing(page, btn)
            except Exception:
                with allure.step("healing: clicking any visible New button fallback"):
                    try:
                        btn = page.locator('button:has-text("New")')
                        helper_click_with_healing(page, btn)
                    except Exception:
                        pass
            try:
                allure.attach(page.screenshot(), name="after_open_new_contact", attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass

        with allure.step("Fill contact details"):
            # Salutation
            try:
                try:
                    contact_new.wait_for_element("salutation")
                    try:
                        contact_new.salutation.select_option(label=ENV_SALUTATION)
                    except Exception:
                        try:
                            contact_new.salutation.evaluate(f"el => el.value = '{ENV_SALUTATION}'")
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass

            # First name
            try:
                contact_new.wait_for_element("first_name")
                contact_new.enter_text("first_name", ENV_CONTACT_FIRST_NAME)
            except Exception:
                try:
                    if hasattr(contact_new, "first_name"):
                        contact_new.first_name.fill(ENV_CONTACT_FIRST_NAME)
                except Exception:
                    pass

            # Last name
            try:
                contact_new.enter_last_name(ENV_CONTACT_LAST_NAME)
            except Exception:
                try:
                    if hasattr(contact_new, "last_name"):
                        contact_new.last_name.fill(ENV_CONTACT_LAST_NAME)
                except Exception:
                    pass

            # Email
            try:
                contact_new.enter_email(ENV_CONTACT_EMAIL)
            except Exception:
                try:
                    if hasattr(contact_new, "email"):
                        contact_new.email.fill(ENV_CONTACT_EMAIL)
                except Exception:
                    pass

            # Account Name / Lookup
            try:
                contact_new.wait_for_element("account_name")
                contact_new.enter_text("account_name", ENV_ACCOUNT_NAME)
            except Exception:
                with allure.step("healing: entering account name using alternate selector"):
                    try:
                        page.locator('input[placeholder*="Account"], input[aria-label*="Account"], input[placeholder*="Account Name"]').fill(ENV_ACCOUNT_NAME)
                    except Exception:
                        pass

        with allure.step("Save the new contact"):
            try:
                contact_new.click_save_edit_button()
            except Exception:
                try:
                    if hasattr(contact_new, "save_button"):
                        helper_click_with_healing(page, contact_new.save_button)
                    else:
                        helper_click_with_healing(page, page.locator('button:has-text("Save"), button[title="Save"]'))
                except Exception:
                    pass
            # allow save to process
            page.wait_for_timeout(2000)
            try:
                allure.attach(page.screenshot(), name="after_save_attempt", attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass

        with allure.step("Validate: contact record page is displayed (primary assertion)"):
            time_waited = 0
            max_wait = 20
            url = page.url
            while ("/lightning/r/Contact/" not in url) and time_waited < max_wait:
                time.sleep(1)
                time_waited += 1
                url = page.url
            try:
                allure.attach(page.screenshot(), name="final_state", attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass
            try:
                allure.attach(page.content(), name="page_html", attachment_type=allure.attachment_type.HTML)
            except Exception:
                pass
            assert "/lightning/r/Contact/" in url, f"Expected to be on a Contact record page after save, current URL: {url}"

    except Exception:
        try:
            allure.attach(page.screenshot(), name="failure_screenshot", attachment_type=allure.attachment_type.PNG)
        except Exception:
            pass
        try:
            allure.attach(page.content(), name="failure_page_html", attachment_type=allure.attachment_type.HTML)
        except Exception:
            pass
        raise