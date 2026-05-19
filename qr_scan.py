import time
import base64
import pytest
from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ─── Configuration ─────────────────────────────────────────────────────────────

QR_PAGE_URL        = "https://your-app-url.com/qr-page"   # ← replace with actual URL
GENERATE_BTN_XPATH = "//button[contains(text(),'Generate')]"  # ← replace with actual XPath
QR_IMAGE_XPATH     = "//img[contains(@id,'qr')]"              # ← replace with actual XPath

# The known/expected Google Wallet URL encoded in the static QR code.
# Run Scenario 2 once manually to discover it, then paste it here.
EXPECTED_QR_URL    = "https://pay.google.com/gp/v/save/YOUR_TOKEN_HERE"  # ← replace


# ─── Browser Setup ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def driver():
    """Shared Chrome driver for the entire test module."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--remote-allow-origins=*")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless=new")  # ← uncomment for CI/headless runs
    d = webdriver.Chrome(options=chrome_options)
    d.maximize_window()
    yield d
    d.quit()


# ─── QR Scan Helpers (from shared library) ─────────────────────────────────────

def _scan_element_screenshot(driver, xpath):
    element = driver.find_element(By.XPATH, xpath)
    image   = Image.open(BytesIO(element.screenshot_as_png))
    results = decode(image)
    if not results:
        raise ValueError("No QR decoded from element screenshot.")
    return results[0].data.decode("utf-8")


def _scan_image_src(driver, xpath):
    element = driver.find_element(By.XPATH, xpath)
    src     = element.get_attribute("src")
    if not src:
        raise ValueError("Element has no src attribute.")

    if src.startswith("data:image"):
        _, b64 = src.split(",", 1)
        image  = Image.open(BytesIO(base64.b64decode(b64)))
    else:
        js = """
            var img = arguments[0];
            var c = document.createElement('canvas');
            c.width = img.naturalWidth; c.height = img.naturalHeight;
            c.getContext('2d').drawImage(img, 0, 0);
            return c.toDataURL('image/png').split(',')[1];
        """
        image = Image.open(BytesIO(base64.b64decode(driver.execute_script(js, element))))

    results = decode(image)
    if not results:
        raise ValueError("No QR decoded from image src.")
    return results[0].data.decode("utf-8")


def _scan_canvas(driver, xpath):
    canvas  = driver.find_element(By.XPATH, xpath)
    b64     = driver.execute_script("return arguments[0].toDataURL('image/png').split(',')[1];", canvas)
    results = decode(Image.open(BytesIO(base64.b64decode(b64))))
    if not results:
        raise ValueError("No QR decoded from canvas.")
    return results[0].data.decode("utf-8")


def _scan_fullpage(driver):
    results = decode(Image.open(BytesIO(driver.get_screenshot_as_png())))
    if not results:
        raise ValueError("No QR decoded from full-page screenshot.")
    return results[0].data.decode("utf-8")


def scan_qr(driver, xpath=None, retries=3, wait=2):
    """
    Auto-fallback QR scanner. Tries in order:
      1. Element screenshot  (precise — needs xpath)
      2. Image src extract   (zero render dependency — needs xpath to <img>)
      3. Canvas extract      (for JS-drawn QR — needs xpath to <canvas>)
      4. Full page screenshot (universal fallback)
    """
    for attempt in range(1, retries + 1):
        print(f"\n  [QR Scan] Attempt {attempt}/{retries}")
        try:
            if xpath:
                for strategy, fn in [
                    ("element-screenshot", lambda: _scan_element_screenshot(driver, xpath)),
                    ("image-src",          lambda: _scan_image_src(driver, xpath)),
                    ("canvas",             lambda: _scan_canvas(driver, xpath)),
                ]:
                    try:
                        result = fn()
                        print(f"  [QR Scan] Success via {strategy}: {result}")
                        return result
                    except Exception as e:
                        print(f"  [QR Scan] {strategy} failed: {e}")

            result = _scan_fullpage(driver)
            print(f"  [QR Scan] Success via full-page screenshot: {result}")
            return result

        except Exception as e:
            print(f"  [QR Scan] All strategies failed: {e}")
            if attempt < retries:
                time.sleep(wait)

    raise ValueError("QR scan failed after all retries.")


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO 1 — Validate QR code is successfully generated after button click
# ═══════════════════════════════════════════════════════════════════════════════

class TestScenario1_QRGeneration:
    """
    Tests that clicking the 'Generate QR' button causes a QR code
    image to appear on the page — i.e. generation succeeded.
    """

    def test_qr_not_visible_before_click(self, driver):
        """
        Pre-condition: QR element should NOT be present before the button is clicked.
        Skip this test if your app shows the QR on page load instead.
        """
        driver.get(QR_PAGE_URL)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        qr_elements = driver.find_elements(By.XPATH, QR_IMAGE_XPATH)
        visible_before = any(el.is_displayed() for el in qr_elements)

        assert not visible_before, (
            "QR code is already visible before clicking Generate — "
            "adjust the test or the pre-condition check."
        )

    def test_generate_button_is_clickable(self, driver):
        """The Generate button must exist and be enabled."""
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, GENERATE_BTN_XPATH))
        )
        assert btn.is_enabled(), "Generate button is present but disabled."

    def test_qr_appears_after_button_click(self, driver):
        """
        Core scenario 1 test:
        Click Generate → wait → assert QR image is now visible in the DOM.
        """
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, GENERATE_BTN_XPATH))
        )
        btn.click()
        print("\n  [S1] Generate button clicked.")

        # Wait up to 15s for the QR element to become visible
        qr_element = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, QR_IMAGE_XPATH))
        )

        assert qr_element.is_displayed(), "QR element found but not visible after clicking Generate."
        print("  [S1] QR element is visible on page ✓")

    def test_qr_image_has_nonzero_dimensions(self, driver):
        """
        The QR image must have a real rendered size — rules out a 0×0 invisible element.
        """
        qr_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, QR_IMAGE_XPATH))
        )
        width  = qr_element.size["width"]
        height = qr_element.size["height"]
        print(f"\n  [S1] QR element size: {width}×{height}px")
        assert width  > 0, f"QR image width is 0 — element may not have rendered."
        assert height > 0, f"QR image height is 0 — element may not have rendered."

    def test_qr_is_decodable_after_generation(self, driver):
        """
        The rendered QR must actually be scannable — i.e. contains valid QR data.
        Decoding failure means the image rendered incorrectly or is corrupt.
        """
        qr_data = scan_qr(driver, xpath=QR_IMAGE_XPATH)
        assert qr_data, "QR decoded successfully but returned empty string."
        print(f"\n  [S1] QR decoded content: {qr_data}")


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO 2 — Extract URL from QR and validate against expected Google Wallet URL
# ═══════════════════════════════════════════════════════════════════════════════

class TestScenario2_QRUrlValidation:
    """
    Decodes the static QR code image and validates its embedded URL
    matches the expected Google Wallet link.
    Since the QR is static, these tests are stable across runs.
    """

    @pytest.fixture(autouse=True)
    def navigate_and_trigger(self, driver):
        """Ensure we're on the QR page and the QR is visible before each test."""
        driver.get(QR_PAGE_URL)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Click generate if needed to surface the QR
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, GENERATE_BTN_XPATH))
            )
            btn.click()
        except Exception:
            pass  # Button may not exist if QR is shown on load

        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, QR_IMAGE_XPATH))
        )

    def test_qr_decodes_to_a_url(self, driver):
        """
        The QR content must be a valid URL (starts with http/https).
        Fails if QR encodes plain text, key-value pairs, or empty data.
        """
        qr_data = scan_qr(driver, xpath=QR_IMAGE_XPATH)
        print(f"\n  [S2] Decoded QR data: {qr_data}")
        assert qr_data.startswith("http://") or qr_data.startswith("https://"), (
            f"QR data is not a URL. Got: {qr_data!r}"
        )

    def test_qr_url_matches_expected(self, driver):
        """
        Core scenario 2 test:
        The decoded URL must exactly match EXPECTED_QR_URL.
        """
        qr_data = scan_qr(driver, xpath=QR_IMAGE_XPATH)
        print(f"\n  [S2] Decoded  : {qr_data}")
        print(f"  [S2] Expected : {EXPECTED_QR_URL}")
        assert qr_data == EXPECTED_QR_URL, (
            f"\nQR URL mismatch!\n"
            f"  Expected : {EXPECTED_QR_URL}\n"
            f"  Got      : {qr_data}"
        )

    def test_qr_url_is_google_wallet_domain(self, driver):
        """
        Domain-level check — confirms the URL belongs to Google Wallet,
        even if the token/path changes between environments.
        """
        qr_data = scan_qr(driver, xpath=QR_IMAGE_XPATH)
        google_wallet_domains = (
            "pay.google.com",
            "wallet.google.com",
            "google.com/wallet",
        )
        assert any(domain in qr_data for domain in google_wallet_domains), (
            f"URL does not belong to a Google Wallet domain.\n"
            f"  Got: {qr_data}\n"
            f"  Expected one of: {google_wallet_domains}"
        )

    def test_qr_url_is_consistent_across_scans(self, driver):
        """
        Since the QR is static, two consecutive scans must return identical URLs.
        A mismatch here indicates a dynamic/rotating QR — update your test strategy.
        """
        first_scan  = scan_qr(driver, xpath=QR_IMAGE_XPATH)
        time.sleep(1)
        second_scan = scan_qr(driver, xpath=QR_IMAGE_XPATH)

        assert first_scan == second_scan, (
            f"QR URL changed between scans — QR may not be truly static!\n"
            f"  Scan 1: {first_scan}\n"
            f"  Scan 2: {second_scan}"
        )
        print(f"\n  [S2] Consistency check passed: both scans returned {first_scan}")