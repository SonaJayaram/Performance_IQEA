import os
import time
import sys as _sys
import pytest
import allure
from playwright.sync_api import sync_playwright, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

os.makedirs("allure-results", exist_ok=True)

DEFAULT_WAIT = 5
EXPLICIT_WAIT = 10
RETRY_ATTEMPTS = 1
HEADLESS = os.environ.get("HEADLESS", "false").lower() in ("1", "true", "yes")
BASE_URL = "https://mindful-shark-fv3y29-dev-ed.trailblaze.lightning.force.com/"

SF_USERNAME = os.environ.get("SF_USERNAME", "rajaram111294@mindful-shark-fv3y29.com")
SF_PASSWORD = os.environ.get("SF_PASSWORD", "Tiger@2026")
SF_VERIFICATION_CODE = os.environ.get("SF_VERIFICATION_CODE", "000000")
CONTACT_SALUTATION = os.environ.get("CONTACT_SALUTATION", "Mr.")
CONTACT_FIRST_NAME = os.environ.get("CONTACT_FIRST_NAME", "AutoFirst")
CONTACT_LAST_NAME = os.environ.get("CONTACT_LAST_NAME", "AutoLast")
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "auto@example.com")
ACCOUNT_NAME = os.environ.get("ACCOUNT_NAME", "AutoAccount")

try:
    from output.page_file_generator.Sfdc_login import Sfdc_login
except Exception:
    def helper_init_Sfdc_login(page):
        with allure.step("helper: initializing Sfdc_login interactions"):
            allure.attach(page.screenshot(), name="before_Sfdc_login_init",
                          attachment_type=allure.attachment_type.PNG)
            try:
                expect(page.locator("body")).to_be_visible(timeout=5000)
            except Exception:
                pass
            allure.attach(page.screenshot(), name="after_Sfdc_login_init",
                          attachment_type=allure.attachment_type.PNG)

try:
    from output.page_file_generator.sfdc_otp import sfdc_otp
except Exception:
    def helper_init_sfdc_otp(page):
        with allure.step("helper: initializing sfdc_otp interactions"):
            allure.attach(page.screenshot(), name="before_sfdc_otp_init",
                          attachment_type=allure.attachment_type.PNG)
            try:
                expect(page.locator("body")).to_be_visible(timeout=5000)
            except Exception:
                pass
            allure.attach(page.screenshot(), name="after_sfdc_otp_init",
                          attachment_type=allure.attachment_type.PNG)

try:
    from output.page_file_generator.sfdc_homepage import sfdc_homepage
except Exception:
    def helper_init_sfdc_homepage(page):
        with allure.step("helper: initializing sfdc_homepage interactions"):
            allure.attach(page.screenshot(), name="before_sfdc_homepage_init",
                          attachment_type=allure.attachment_type.PNG)
            try:
                expect(page.locator("body")).to_be_visible(timeout=5000)
            except Exception:
                pass
            allure.attach(page.screenshot(), name="after_sfdc_homepage_init",
                          attachment_type=allure.attachment_type.PNG)

try:
    from output.page_file_generator.sfdc_contact_new import sfdc_contact_new
except Exception:
    def helper_init_sfdc_contact_new(page):
        with allure.step("helper: initializing sfdc_contact_new interactions"):
            allure.attach(page.screenshot(), name="before_sfdc_contact_new_init",
                          attachment_type=allure.attachment_type.PNG)
            try:
                expect(page.locator("body")).to_be_visible(timeout=5000)
            except Exception:
                pass
            allure.attach(page.screenshot(), name="after_sfdc_contact_new_init",
                          attachment_type=allure.attachment_type.PNG)

def helper_click_Sfdc_login(page_obj, locator_key: str, page, fallback_selector=None):
    with allure.step(f"click {locator_key} on Sfdc_login (with healing)"):
        for attempt in range(RETRY_ATTEMPTS + 1):
            try:
                page_obj.wait_for_element(locator_key)
                page_obj.click_element(locator_key)
                allure.attach(page.screenshot(), name=f"after_click_{locator_key}",
                              attachment_type=allure.attachment_type.PNG)
                return
            except Exception:
                if attempt < RETRY_ATTEMPTS:
                    with allure.step(f"healing: retry attempt {attempt+1} — {locator_key}"):
                        time.sleep(0.5)
                        try:
                            getattr(page_obj, locator_key).wait_for(
                                state="visible", timeout=EXPLICIT_WAIT * 1000)
                        except Exception:
                            pass
                        try:
                            page_obj.click_element(locator_key)
                            return
                        except Exception:
                            pass
                else:
                    with allure.step(f"healing: fallback selector — {locator_key}"):
                        if fallback_selector:
                            try:
                                _fb = page.locator(fallback_selector)
                                _fb.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                                _fb.click()
                                allure.attach(page.screenshot(),
                                              name=f"after_fallback_{locator_key}",
                                              attachment_type=allure.attachment_type.PNG)
                                return
                            except Exception:
                                pass
                    with allure.step(f"healing: auto stable selector — {locator_key}"):
                        _stable = page.locator(f"[id*='{locator_key}'], [name*='{locator_key}']")
                        _stable.first.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                        _stable.first.click()
                        allure.attach(page.screenshot(), name="healing_final_fallback",
                                      attachment_type=allure.attachment_type.PNG)

def helper_fill_Sfdc_login(page_obj, locator_key: str, text: str, page, fallback_selector=None):
    with allure.step(f"fill {locator_key} on Sfdc_login (with healing)"):
        for attempt in range(RETRY_ATTEMPTS + 1):
            try:
                page_obj.wait_for_element(locator_key)
                page_obj.enter_text(locator_key, text)
                allure.attach(page.screenshot(), name=f"after_fill_{locator_key}",
                              attachment_type=allure.attachment_type.PNG)
                return
            except Exception:
                if attempt < RETRY_ATTEMPTS:
                    with allure.step(f"healing: retry attempt {attempt+1} — {locator_key}"):
                        time.sleep(0.5)
                        try:
                            getattr(page_obj, locator_key).wait_for(
                                state="visible", timeout=EXPLICIT_WAIT * 1000)
                        except Exception:
                            pass
                        try:
                            page_obj.enter_text(locator_key, text)
                            return
                        except Exception:
                            pass
                else:
                    with allure.step(f"healing: fallback selector — {locator_key}"):
                        if fallback_selector:
                            try:
                                _fb = page.locator(fallback_selector)
                                _fb.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                                _fb.fill(text)
                                allure.attach(page.screenshot(),
                                              name=f"after_fallback_{locator_key}",
                                              attachment_type=allure.attachment_type.PNG)
                                return
                            except Exception:
                                pass
                    with allure.step(f"healing: auto stable selector — {locator_key}"):
                        _stable = page.locator(f"[id*='{locator_key}'], [name*='{locator_key}']")
                        _stable.first.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                        _stable.first.fill(text)
                        allure.attach(page.screenshot(), name="healing_final_fallback",
                                      attachment_type=allure.attachment_type.PNG)

def helper_click_sfdc_otp(page_obj, locator_key: str, page, fallback_selector=None):
    with allure.step(f"click {locator_key} on sfdc_otp (with healing)"):
        for attempt in range(RETRY_ATTEMPTS + 1):
            try:
                page_obj.wait_for_element(locator_key)
                page_obj.click_element(locator_key)
                allure.attach(page.screenshot(), name=f"after_click_{locator_key}",
                              attachment_type=allure.attachment_type.PNG)
                return
            except Exception:
                if attempt < RETRY_ATTEMPTS:
                    with allure.step(f"healing: retry attempt {attempt+1} — {locator_key}"):
                        time.sleep(0.5)
                        try:
                            getattr(page_obj, locator_key).wait_for(
                                state="visible", timeout=EXPLICIT_WAIT * 1000)
                        except Exception:
                            pass
                        try:
                            page_obj.click_element(locator_key)
                            return
                        except Exception:
                            pass
                else:
                    with allure.step(f"healing: fallback selector — {locator_key}"):
                        if fallback_selector:
                            try:
                                _fb = page.locator(fallback_selector)
                                _fb.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                                _fb.click()
                                allure.attach(page.screenshot(),
                                              name=f"after_fallback_{locator_key}",
                                              attachment_type=allure.attachment_type.PNG)
                                return
                            except Exception:
                                pass
                    with allure.step(f"healing: auto stable selector — {locator_key}"):
                        _stable = page.locator(f"[id*='{locator_key}'], [name*='{locator_key}']")
                        _stable.first.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                        _stable.first.click()
                        allure.attach(page.screenshot(), name="healing_final_fallback",
                                      attachment_type=allure.attachment_type.PNG)

def helper_fill_sfdc_otp(page_obj, locator_key: str, text: str, page, fallback_selector=None):
    with allure.step(f"fill {locator_key} on sfdc_otp (with healing)"):
        for attempt in range(RETRY_ATTEMPTS + 1):
            try:
                page_obj.wait_for_element(locator_key)
                if hasattr(page_obj, "enter_verification_code") and locator_key.lower().startswith("verification"):
                    page_obj.enter_verification_code(text)
                    time.sleep(10)  # allow any dynamic changes post text entry
                else:
                    page_obj.enter_text(locator_key, text)
                    time.sleep(10)  # allow any dynamic changes post text entry
                allure.attach(page.screenshot(), name=f"after_fill_{locator_key}",
                              attachment_type=allure.attachment_type.PNG)
                return
            except Exception:
                if attempt < RETRY_ATTEMPTS:
                    with allure.step(f"healing: retry attempt {attempt+1} — {locator_key}"):
                        time.sleep(0.5)
                        try:
                            getattr(page_obj, locator_key).wait_for(
                                state="visible", timeout=EXPLICIT_WAIT * 1000)
                        except Exception:
                            pass
                        try:
                            if hasattr(page_obj, "enter_verification_code") and locator_key.lower().startswith("verification"):
                                page_obj.enter_verification_code(text)
                            else:
                                page_obj.enter_text(locator_key, text)
                            return
                        except Exception:
                            pass
                else:
                    with allure.step(f"healing: fallback selector — {locator_key}"):
                        if fallback_selector:
                            try:
                                _fb = page.locator(fallback_selector)
                                _fb.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                                _fb.fill(text)
                                allure.attach(page.screenshot(),
                                              name=f"after_fallback_{locator_key}",
                                              attachment_type=allure.attachment_type.PNG)
                                return
                            except Exception:
                                pass
                    with allure.step(f"healing: auto stable selector — {locator_key}"):
                        _stable = page.locator(f"[id*='{locator_key}'], [name*='{locator_key}']")
                        _stable.first.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                        _stable.first.fill(text)
                        allure.attach(page.screenshot(), name="healing_final_fallback",
                                      attachment_type=allure.attachment_type.PNG)

def helper_click_sfdc_homepage(page_obj, locator_key: str, page, fallback_selector=None):
    with allure.step(f"click {locator_key} on sfdc_homepage (with healing)"):
        for attempt in range(RETRY_ATTEMPTS + 1):
            try:
                page_obj.wait_for_element(locator_key)
                page_obj.click_element(locator_key)
                allure.attach(page.screenshot(), name=f"after_click_{locator_key}",
                              attachment_type=allure.attachment_type.PNG)
                return
            except Exception:
                if attempt < RETRY_ATTEMPTS:
                    with allure.step(f"healing: retry attempt {attempt+1} — {locator_key}"):
                        time.sleep(0.5)
                        try:
                            getattr(page_obj, locator_key).wait_for(
                                state="visible", timeout=EXPLICIT_WAIT * 1000)
                        except Exception:
                            pass
                        try:
                            page_obj.click_element(locator_key)
                            return
                        except Exception:
                            pass
                else:
                    with allure.step(f"healing: fallback selector — {locator_key}"):
                        if fallback_selector:
                            try:
                                _fb = page.locator(fallback_selector)
                                _fb.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                                _fb.click()
                                allure.attach(page.screenshot(),
                                              name=f"after_fallback_{locator_key}",
                                              attachment_type=allure.attachment_type.PNG)
                                return
                            except Exception:
                                pass
                    with allure.step(f"healing: auto stable selector — {locator_key}"):
                        _stable = page.locator(f"[id*='{locator_key}'], [name*='{locator_key}']")
                        _stable.first.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                        _stable.first.click()
                        allure.attach(page.screenshot(), name="healing_final_fallback",
                                      attachment_type=allure.attachment_type.PNG)

def helper_fill_sfdc_contact_new(page_obj, locator_key: str, text: str, page, fallback_selector=None):
    with allure.step(f"fill {locator_key} on sfdc_contact_new (with healing)"):
        for attempt in range(RETRY_ATTEMPTS + 1):
            try:
                page_obj.wait_for_element(locator_key)
                # prefer dedicated methods
                if locator_key.lower().startswith("last"):
                    page_obj.enter_last_name(text)
                elif locator_key.lower().startswith("email"):
                    page_obj.enter_email(text)
                else:
                    page_obj.enter_text(locator_key, text)
                allure.attach(page.screenshot(), name=f"after_fill_{locator_key}",
                              attachment_type=allure.attachment_type.PNG)
                return
            except Exception:
                if attempt < RETRY_ATTEMPTS:
                    with allure.step(f"healing: retry attempt {attempt+1} — {locator_key}"):
                        time.sleep(0.5)
                        try:
                            getattr(page_obj, locator_key).wait_for(
                                state="visible", timeout=EXPLICIT_WAIT * 1000)
                        except Exception:
                            pass
                        try:
                            if locator_key.lower().startswith("last"):
                                page_obj.enter_last_name(text)
                            elif locator_key.lower().startswith("email"):
                                page_obj.enter_email(text)
                            else:
                                page_obj.enter_text(locator_key, text)
                            return
                        except Exception:
                            pass
                else:
                    with allure.step(f"healing: fallback selector — {locator_key}"):
                        if fallback_selector:
                            try:
                                _fb = page.locator(fallback_selector)
                                _fb.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                                _fb.fill(text)
                                allure.attach(page.screenshot(),
                                              name=f"after_fallback_{locator_key}",
                                              attachment_type=allure.attachment_type.PNG)
                                return
                            except Exception:
                                pass
                    with allure.step(f"healing: auto stable selector — {locator_key}"):
                        _stable = page.locator(f"[id*='{locator_key}'], [name*='{locator_key}']")
                        _stable.first.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                        _stable.first.fill(text)
                        allure.attach(page.screenshot(), name="healing_final_fallback",
                                      attachment_type=allure.attachment_type.PNG)

def _common_flow_execute(page, test_case: dict):
    expected_fragment = test_case.get("expected_url_contains", "/lightning/r/Contact/")
    # PAGE-1: Login
    with allure.step("Open Salesforce Login URL"):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        allure.attach(page.screenshot(), name="after_open_login", attachment_type=allure.attachment_type.PNG)
    # instantiate login pom
    try:
        login_pom = Sfdc_login(page)
    except NameError:
        helper_init_Sfdc_login(page)
        # cannot instantiate POM, raise
        pytest.fail("Missing POM: Sfdc_login")
    except TypeError:
        with allure.step("auto-fix: constructor adaptation for Sfdc_login"):
            try:
                login_pom = Sfdc_login(page, 10)
            except TypeError:
                login_pom = Sfdc_login(page, EXPLICIT_WAIT, DEFAULT_WAIT)
    # Enter username
    with allure.step('Enter username in the "Username" field'):
        try:
            helper_fill_Sfdc_login(login_pom, "Username", SF_USERNAME, page)
        except Exception as e:
            allure.attach(str(e), name="username_entry_exception", attachment_type=allure.attachment_type.TEXT)
            raise
    # Enter password
    with allure.step('Enter password in the "Password" field'):
        try:
            helper_fill_Sfdc_login(login_pom, "Password", SF_PASSWORD, page)
        except Exception as e:
            allure.attach(str(e), name="password_entry_exception", attachment_type=allure.attachment_type.TEXT)
            raise
    # Click Log In and handle popup
    with allure.step("Handle popup / new tab"):
        allure.attach(page.screenshot(), name="before_login_click", attachment_type=allure.attachment_type.PNG)
        try:
            with page.expect_popup() as popup_info:
                # wait then click
                login_pom.wait_for_element("Log In")
                login_pom.click_element("Log In")
            new_page = popup_info.value
            new_page.bring_to_front()
            new_page.wait_for_load_state("networkidle")
            allure.attach(new_page.screenshot(), name="after_popup_open", attachment_type=allure.attachment_type.PNG)
        except PlaywrightTimeoutError:
            pages = page.context.pages
            if len(pages) > 1:
                new_page = pages[-1]
                new_page.bring_to_front()
                new_page.wait_for_load_state("networkidle")
            else:
                new_page = page
        except Exception:
            pages = page.context.pages
            if len(pages) > 1:
                new_page = pages[-1]
                new_page.bring_to_front()
                new_page.wait_for_load_state("networkidle")
            else:
                new_page = page
    # Re-instantiate OTP POM on new_page
    try:
        otp_pom = sfdc_otp(new_page)
    except NameError:
        helper_init_sfdc_otp(new_page)
        pytest.fail("Missing POM: sfdc_otp")
    except TypeError:
        with allure.step("auto-fix: constructor adaptation for sfdc_otp"):
            try:
                otp_pom = sfdc_otp(new_page, 10)
            except TypeError:
                otp_pom = sfdc_otp(new_page, EXPLICIT_WAIT, DEFAULT_WAIT)
    # Enter verification code
    with allure.step('Enter verification code in the "Verification Code" field'):
        try:
            helper_fill_sfdc_otp(otp_pom, "Verification Code", SF_VERIFICATION_CODE, new_page)
        except Exception as e:
            allure.attach(str(e), name="verification_entry_exception", attachment_type=allure.attachment_type.TEXT)
            raise
    # Change value to Verified in Verify Your Identity (dropdown)
    with allure.step('Change the value to "Verified" in "Verify Your Identity"'):
        try:
            try:
                otp_pom.wait_for_element("Verify Your Identity")
                otp_pom.click_element("Verify Your Identity")
            except Exception:
                pass
            try:
                new_page.click(f"text=Verified")
            except Exception:
                try:
                    new_page.select_option("select[name='Verify Your Identity']", label="Verified")
                except Exception:
                    pass
            allure.attach(new_page.screenshot(), name="after_select_verified", attachment_type=allure.attachment_type.PNG)
        except Exception:
            allure.attach(new_page.screenshot(), name="after_select_verified_error", attachment_type=allure.attachment_type.PNG)
    # Click Verify
    with allure.step('Click on "Verify"'):
        try:
            otp_pom.wait_for_element("Verify")
            otp_pom.click_element("Verify")
            new_page.wait_for_load_state("networkidle")
            allure.attach(new_page.screenshot(), name="after_click_verify", attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(new_page.screenshot(), name="verify_click_exception", attachment_type=allure.attachment_type.PNG)
            raise
    # Resolve active page to home
    target_page = None
    expected_home_fragment = "/lightning/page/home"
    for _p in page.context.pages:
        if expected_home_fragment in _p.url:
            target_page = _p
            break
    if not target_page:
        target_page = page
    target_page.bring_to_front()
    target_page.wait_for_load_state("networkidle")
    allure.attach(target_page.screenshot(), name="resolved_active_page", attachment_type=allure.attachment_type.PNG)
    # Re-instantiate homepage POM
    try:
        home_pom = sfdc_homepage(target_page)
    except NameError:
        helper_init_sfdc_homepage(target_page)
        pytest.fail("Missing POM: sfdc_homepage")
    except TypeError:
        with allure.step("auto-fix: constructor adaptation for sfdc_homepage"):
            try:
                home_pom = sfdc_homepage(target_page, 10)
            except TypeError:
                home_pom = sfdc_homepage(target_page, EXPLICIT_WAIT, DEFAULT_WAIT)
    # Click Contacts tab
    with allure.step('Click on "Contacts" tab'):
        try:
            home_pom.wait_for_element("Contacts")
            # prefer dedicated method if exists
            if hasattr(home_pom, "click_contacts_tab"):
                home_pom.click_contacts_tab()
            else:
                home_pom.click_element("Contacts")
            target_page.wait_for_load_state("networkidle")
            allure.attach(target_page.screenshot(), name="after_click_contacts", attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(target_page.screenshot(), name="contacts_click_exception", attachment_type=allure.attachment_type.PNG)
            raise
    # Click New
    with allure.step('Click on "New"'):
        try:
            home_pom.wait_for_element("New")
            # if homepage has no click_new_button, fallback to click_element
            try:
                home_pom.click_element("New")
            except Exception:
                try:
                    home_pom.click_new_button()
                except Exception:
                    target_page.click("text=New")
            target_page.wait_for_load_state("networkidle")
            allure.attach(target_page.screenshot(), name="after_click_new", attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(target_page.screenshot(), name="new_click_exception", attachment_type=allure.attachment_type.PNG)
            raise
    # Re-instantiate contact new POM
    try:
        contact_pom = sfdc_contact_new(target_page)
    except NameError:
        helper_init_sfdc_contact_new(target_page)
        pytest.fail("Missing POM: sfdc_contact_new")
    except TypeError:
        with allure.step("auto-fix: constructor adaptation for sfdc_contact_new"):
            try:
                contact_pom = sfdc_contact_new(target_page, 10)
            except TypeError:
                contact_pom = sfdc_contact_new(target_page, EXPLICIT_WAIT, DEFAULT_WAIT)
    # Fill Salutation (dropdown)
    with allure.step('Select salutation in "Salutation" field'):
        try:
            contact_pom.wait_for_element("Salutation")
            contact_pom.click_element("Salutation")
            try:
                target_page.click(f"text={CONTACT_SALUTATION}")
            except Exception:
                try:
                    target_page.select_option("select[name='Salutation']", label=CONTACT_SALUTATION)
                except Exception:
                    pass
            allure.attach(target_page.screenshot(), name="after_select_salutation", attachment_type=allure.attachment_type.PNG)
        except Exception:
            allure.attach(target_page.screenshot(), name="salutation_exception", attachment_type=allure.attachment_type.PNG)
    # Enter First Name
    with allure.step('Enter first name in the "First Name" field'):
        try:
            contact_pom.wait_for_element("First Name")
            contact_pom.enter_text("First Name", CONTACT_FIRST_NAME)
            allure.attach(target_page.screenshot(), name="after_first_name", attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(target_page.screenshot(), name="first_name_exception", attachment_type=allure.attachment_type.PNG)
            raise
    # Enter Last Name
    with allure.step('Enter last name in the "Last Name" field'):
        try:
            contact_pom.wait_for_element("Last Name")
            if hasattr(contact_pom, "enter_last_name"):
                contact_pom.enter_last_name(CONTACT_LAST_NAME)
            else:
                contact_pom.enter_text("Last Name", CONTACT_LAST_NAME)
            allure.attach(target_page.screenshot(), name="after_last_name", attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(target_page.screenshot(), name="last_name_exception", attachment_type=allure.attachment_type.PNG)
            raise
    # Enter Email
    with allure.step('Enter email in the "Email" field'):
        try:
            contact_pom.wait_for_element("Email")
            if hasattr(contact_pom, "enter_email"):
                contact_pom.enter_email(CONTACT_EMAIL)
            else:
                contact_pom.enter_text("Email", CONTACT_EMAIL)
            allure.attach(target_page.screenshot(), name="after_email", attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(target_page.screenshot(), name="email_exception", attachment_type=allure.attachment_type.PNG)
            raise
    # Account Name lookup
    with allure.step('Enter account name in the "Account Name" lookup field'):
        try:
            contact_pom.wait_for_element("Account Name")
            try:
                contact_pom.enter_text("Account Name", ACCOUNT_NAME)
            except Exception:
                contact_pom.enter_text("AccountName", ACCOUNT_NAME)
            try:
                target_page.wait_for_selector("div[role='option'], li[role='option']", timeout=EXPLICIT_WAIT * 1000)
                target_page.locator("div[role='option'], li[role='option']").first.click()
            except Exception:
                pass
            allure.attach(target_page.screenshot(), name="after_account_lookup", attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(target_page.screenshot(), name="account_lookup_exception", attachment_type=allure.attachment_type.PNG)
    # Click Save
    with allure.step('Click on "Save"'):
        try:
            contact_pom.wait_for_element("Save")
            try:
                contact_pom.click_save_edit_button()
            except Exception:
                try:
                    contact_pom.click_element("Save")
                except Exception:
                    target_page.click("text=Save")
            # post-save stabilization
            time.sleep(1.5)
            target_page.wait_for_load_state("networkidle")
            allure.attach(target_page.screenshot(), name="after_save", attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(target_page.screenshot(), name="save_exception", attachment_type=allure.attachment_type.PNG)
            raise
    # Primary assertion
    with allure.step("Assert contact saved and navigated to contact detail"):
        allure.attach(target_page.screenshot(), name="before_assertion", attachment_type=allure.attachment_type.PNG)
        assert expected_fragment in target_page.url, f"Expected '{expected_fragment}' in URL after contact save"

@pytest.fixture(scope="function")
def browser_page():
    with sync_playwright() as pw:
        browser = pw.webkit.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            java_script_enabled=True,
            ignore_https_errors=True,
            viewport={"width": 1400, "height": 900}
        )
        pg = context.new_page()
        try:
            yield pg
        finally:
            try:
                context.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass

@allure.title("**TC05 - Create New Contact (Positive)**")
@allure.description("**TC05 - Create New Contact (Positive)**")
def test_tc05_create_new_contact_positive(browser_page):
    try:
        _common_flow_execute(browser_page, {
            "test_case_name": "**TC05 - Create New Contact (Positive)**",
            "expected_url_contains": "/lightning/r/Contact/"
        })
    except AssertionError:
        try:
            allure.attach(browser_page.screenshot(), name="assertion_failure",
                          attachment_type=allure.attachment_type.PNG)
            allure.attach(browser_page.content(), name="page_html",
                          attachment_type=allure.attachment_type.HTML)
        except Exception:
            pass
        raise
    except Exception as e:
        try:
            allure.attach(browser_page.screenshot(), name="unexpected_failure",
                          attachment_type=allure.attachment_type.PNG)
            allure.attach(browser_page.content(), name="page_html",
                          attachment_type=allure.attachment_type.HTML)
        except Exception:
            pass
        allure.attach(str(e), name="exception_detail",
                      attachment_type=allure.attachment_type.TEXT)
        pytest.fail(f"Test failed: {e}")

_test_fns = [n for n in dir(_sys.modules[__name__]) if n.startswith("test_")]
assert len(_test_fns) == 1, (
    f"Test count mismatch: expected 1, found {len(_test_fns)}"
)