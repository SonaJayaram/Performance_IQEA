import pytest
import allure
from playwright.sync_api import sync_playwright, Page
from output.page_file_generator.sfdc_homepage import sfdc_homepage
from output.page_file_generator.sfdc_contact_new import sfdc_contact_new


# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
BASE_URL          = "https://mindful-shark-fv3y29-dev-ed.trailblaze.my.salesforce.com/"
USERNAME          = "rajaram111294@mindful-shark-fv3y29.com"
PASSWORD          = "Tiger@2026"
VERIFICATION_CODE = "123456"   # Supply the live OTP when running

CONTACT_LAST_NAME       = "TestContact"
CONTACT_EMAIL           = "testcontact@example.com"
CONTACT_ASSISTANT_NAME  = "Assistant Smith"
CONTACT_BIO             = "Automation test contact bio"
CONTACT_ASSISTANT_PHONE = "9876543210"


# ──────────────────────────────────────────────
# Helper – attach a screenshot to the Allure report
# ──────────────────────────────────────────────
def attach_screenshot(page: Page, name: str = "screenshot"):
    allure.attach(
        page.screenshot(),
        name=name,
        attachment_type=allure.attachment_type.PNG,
    )


# ──────────────────────────────────────────────
# Fixture – WebKit browser, headed, slow_mo
# ──────────────────────────────────────────────
@pytest.fixture(scope="function")
def page():
    """Launch WebKit visibly, yield a Page, then close everything."""
    with sync_playwright() as p:
        browser = p.webkit.launch(headless=False, slow_mo=500)
        browser = p.Edge.launch(headless=False, slow_mo=500)# ← headed + slowed
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        pg      = context.new_page()
        yield pg
        context.close()
        browser.close()


# ──────────────────────────────────────────────
# Auto-screenshot on failure
# ──────────────────────────────────────────────
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report  = outcome.get_result()
    if report.when == "call" and report.failed:
        pg: Page = item.funcargs.get("page")
        if pg:
            allure.attach(
                pg.screenshot(full_page=True),
                name="FAILURE screenshot",
                attachment_type=allure.attachment_type.PNG,
            )


# ──────────────────────────────────────────────
# Test
# ──────────────────────────────────────────────
@allure.epic("Salesforce CRM")
@allure.feature("Contact Management")
@allure.story("Create a new Contact")
@allure.title("End-to-end: Login → OTP → Contacts → Create Contact")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("smoke", "regression", "contacts")
def test_create_sfdc_contact(page: Page):
    """
    End-to-end test:
      1. Navigate to Salesforce login page.
      2. Log in with username + password.
      3. Handle OTP verification.
      4. Navigate to the Contacts tab.
      5. Create a new Contact and save.
    """

    # ── Step 1: Open Salesforce ──────────────────────────────────────────────
    with allure.step("Navigate to Salesforce login page"):
        page.goto(BASE_URL)
        attach_screenshot(page, "01 - Login Page")

    # ── Step 2: Login ────────────────────────────────────────────────────────
    with allure.step(f"Login with username: {USERNAME}"):
        homepage = sfdc_homepage(page)
        homepage.login(USERNAME, PASSWORD)
        attach_screenshot(page, "02 - After Login Submit")

    # ── Step 3: OTP verification ─────────────────────────────────────────────
    with allure.step("Enter OTP verification code"):
        homepage.verify_identity(VERIFICATION_CODE)
        attach_screenshot(page, "03 - After OTP Verification")

    # Switch to the active page after auth and re-bind homepage
    active_page = homepage.switch_to_new_window()
    homepage    = sfdc_homepage(active_page)

    # ── Step 4: Navigate to Contacts tab ─────────────────────────────────────
    with allure.step("Click the Contacts tab"):
        homepage.click_contacts_tab()
        attach_screenshot(active_page, "04 - Contacts Tab")

    # ── Step 5: Open New Contact form ─────────────────────────────────────────
    contact_page = sfdc_contact_new(active_page)

    with allure.step("Click New button to open Contact form"):
        contact_page.click_new_button()
        attach_screenshot(active_page, "05 - New Contact Form")

    # ── Step 6: Fill in Contact details ──────────────────────────────────────
    with allure.step(f"Enter Last Name: {CONTACT_LAST_NAME}"):
        contact_page.enter_last_name(CONTACT_LAST_NAME)

    with allure.step(f"Enter Email: {CONTACT_EMAIL}"):
        contact_page.enter_email(CONTACT_EMAIL)

    with allure.step(f"Enter Assistant Name: {CONTACT_ASSISTANT_NAME}"):
        contact_page.enter_assistant_name(CONTACT_ASSISTANT_NAME)

    with allure.step(f"Enter Bio: {CONTACT_BIO}"):
        contact_page.enter_bio(CONTACT_BIO)

    with allure.step(f"Enter Assistant Phone: {CONTACT_ASSISTANT_PHONE}"):
        contact_page.enter_assistant_phone(CONTACT_ASSISTANT_PHONE)

    attach_screenshot(active_page, "06 - Filled Contact Form")

    # ── Step 7: Save the Contact ──────────────────────────────────────────────
    with allure.step("Click Save button"):
        contact_page.click_save_edit_button()
        active_page.wait_for_load_state("networkidle")
        attach_screenshot(active_page, "07 - After Save")

    # ── Step 8: Assert contact was created ────────────────────────────────────
    with allure.step(f"Verify contact '{CONTACT_LAST_NAME}' is visible on the detail page"):
        contact_visible = (
            CONTACT_LAST_NAME in active_page.title()
            or active_page.locator(
                f"xpath=//*[contains(text(),'{CONTACT_LAST_NAME}')]"
            ).is_visible()
        )
        attach_screenshot(active_page, "08 - Contact Detail Page")
        assert contact_visible, (
            f"Contact '{CONTACT_LAST_NAME}' was not found on the page after saving."
        )

    allure.attach(
        f"Last Name      : {CONTACT_LAST_NAME}\n"
        f"Email          : {CONTACT_EMAIL}\n"
        f"Assistant Name : {CONTACT_ASSISTANT_NAME}\n"
        f"Bio            : {CONTACT_BIO}\n"
        f"Assistant Phone: {CONTACT_ASSISTANT_PHONE}",
        name="Contact Details",
        attachment_type=allure.attachment_type.TEXT,
    )