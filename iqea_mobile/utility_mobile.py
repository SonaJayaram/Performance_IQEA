"""
IQEA Mobile Automation — utility_mobile.py
==========================================
Pure backend utility layer. Zero Streamlit imports.

Key capability: ActionRecorder
  - Background thread polls Appium every 1.5s during recording
  - Diffs page source XML to detect what user tapped / typed
  - Extracts XPath of changed element automatically
  - Takes screenshot at moment of each action
  - Stores structured action dicts with screenshot_b64

ScriptExecutor
  - Replays recorded actions on connected device step by step
  - Streams pass/fail + screenshot per step back to UI
"""

import json
import os
import random
import shutil
import string
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import requests


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

APPIUM_DEFAULT_URL  = "http://localhost:4723"
APPIUM_DEFAULT_PORT = 4723
BS_DEVICES_API      = "https://api.browserstack.com/app-automate/devices.json"
BS_SESSION_API      = "https://api-cloud.browserstack.com/app-automate/sessions"
POLL_INTERVAL_SEC   = 1.5

FRAMEWORKS = {
    "Python + Appium (pytest)":        {"ext": "py",    "install": "pip install Appium-Python-Client pytest"},
    "Python + Playwright Mobile":      {"ext": "py",    "install": "pip install playwright pytest-playwright\nplaywright install chromium"},
    "Java + Appium (TestNG)":          {"ext": "java",  "install": "<dependency>io.appium:java-client:8.x</dependency>"},
    "JavaScript + WebdriverIO":        {"ext": "js",    "install": "npm init wdio@latest"},
    "Robot Framework + AppiumLibrary": {"ext": "robot", "install": "pip install robotframework AppiumLibrary"},
}

# Elements that are layout containers — skip when detecting actions
SKIP_TAGS = {
    "android.widget.FrameLayout", "android.widget.LinearLayout",
    "android.widget.RelativeLayout", "android.widget.ScrollView",
    "android.view.ViewGroup", "android.widget.ListView",
    "android.widget.RecyclerView", "XCUIElementTypeOther",
    "XCUIElementTypeWindow", "XCUIElementTypeApplication",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. LOGGER
# ═══════════════════════════════════════════════════════════════════════════════

class MobileLogger:
    def __init__(self, max_entries: int = 300):
        self.entries: list[dict] = []
        self.max_entries = max_entries
        self._lock = threading.Lock()

    def log(self, msg: str, level: str = "info") -> dict:
        entry = {"ts": datetime.now().strftime("%H:%M:%S.%f")[:-3], "msg": msg, "level": level}
        with self._lock:
            self.entries.append(entry)
            if len(self.entries) > self.max_entries:
                self.entries = self.entries[-self.max_entries:]
        return entry

    def ok(self,   msg: str) -> dict: return self.log(msg, "ok")
    def err(self,  msg: str) -> dict: return self.log(msg, "err")
    def warn(self, msg: str) -> dict: return self.log(msg, "warn")
    def info(self, msg: str) -> dict: return self.log(msg, "info")

    def clear(self):
        with self._lock:
            self.entries = []

    def tail(self, n: int = 60) -> list[dict]:
        with self._lock:
            return list(reversed(self.entries[-n:]))


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ADB MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ADBManager:
    def __init__(self, logger: Optional[MobileLogger] = None):
        self.logger   = logger or MobileLogger()
        self.adb_path = shutil.which("adb") or "adb"

    @staticmethod
    def is_adb_available() -> bool:
        try:
            p = shutil.which("adb") or "adb"
            subprocess.run([p, "version"], capture_output=True, timeout=4)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def scan_android(self) -> list[dict]:
        devices = []
        if not self.is_adb_available():
            self.logger.err("adb not found. Install Android SDK Platform Tools.")
            return devices
        try:
            result = subprocess.run(
                [self.adb_path, "devices", "-l"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.strip().splitlines()[1:]:
                line = line.strip()
                if not line or "offline" in line or "unauthorized" in line:
                    continue
                parts = line.split()
                if len(parts) < 2 or parts[1] != "device":
                    continue
                serial = parts[0]
                source = "emulator" if serial.startswith("emulator") else "usb"
                model  = self._adb_prop(serial, "ro.product.model")
                mfr    = self._adb_prop(serial, "ro.product.manufacturer")
                os_ver = self._adb_prop(serial, "ro.build.version.release")
                devices.append({
                    "serial": serial, "model": f"{mfr} {model}".strip(),
                    "os": f"Android {os_ver}", "platform": "Android", "source": source,
                })
            self.logger.ok(f"ADB scan — {len(devices)} device(s) found")
        except subprocess.TimeoutExpired:
            self.logger.err("ADB scan timed out")
        except Exception as exc:
            self.logger.err(f"ADB scan error: {exc}")
        return devices

    def _adb_prop(self, serial: str, prop: str, timeout: int = 5) -> str:
        try:
            r = subprocess.run(
                [self.adb_path, "-s", serial, "shell", "getprop", prop],
                capture_output=True, text=True, timeout=timeout
            )
            return r.stdout.strip()
        except Exception:
            return ""

    def scan_ios(self) -> list[dict]:
        devices = []
        try:
            result = subprocess.run(["idevice_id", "-l"], capture_output=True, text=True, timeout=8)
            for udid in result.stdout.strip().splitlines():
                udid = udid.strip()
                if not udid:
                    continue
                name    = self._idevice_info(udid, "DeviceName")
                ios_ver = self._idevice_info(udid, "ProductVersion")
                model   = self._idevice_info(udid, "ProductType")
                devices.append({
                    "serial": udid, "model": name or model or "iPhone",
                    "os": f"iOS {ios_ver}", "platform": "iOS", "source": "usb",
                })
            if devices:
                self.logger.ok(f"iOS USB scan — {len(devices)} device(s) found")
        except FileNotFoundError:
            self.logger.info("libimobiledevice not installed — iOS USB detection unavailable")
        except Exception as exc:
            self.logger.warn(f"iOS detect error: {exc}")
        return devices

    def _idevice_info(self, udid: str, key: str, timeout: int = 5) -> str:
        try:
            r = subprocess.run(["ideviceinfo", "-u", udid, "-k", key], capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip()
        except Exception:
            return ""

    def scan_all(self) -> list[dict]:
        return self.scan_android() + self.scan_ios()

    @staticmethod
    def make_emulator_entry(serial="emulator-5554", model="Android Emulator (AVD)", os_ver="Android 14") -> dict:
        return {"serial": serial, "model": model, "os": os_ver, "platform": "Android", "source": "emulator"}

    def restart_adb_server(self) -> bool:
        try:
            subprocess.run([self.adb_path, "kill-server"], capture_output=True, timeout=6)
            time.sleep(1)
            subprocess.run([self.adb_path, "start-server"], capture_output=True, timeout=8)
            self.logger.ok("ADB server restarted")
            return True
        except Exception as exc:
            self.logger.err(f"ADB restart failed: {exc}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# 3. BROWSERSTACK MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

BS_HUB_URL       = "https://hub.browserstack.com/wd/hub"
BS_UPLOAD_API    = "https://api-cloud.browserstack.com/app-automate/upload"
BS_PLAN_API      = "https://api.browserstack.com/automate/plan.json"
BS_APP_AUTOMATE_PLAN_API = "https://api-cloud.browserstack.com/app-automate/plan.json"


class BrowserStackManager:
    def __init__(self, username="", access_key="", logger=None):
        self.username   = username
        self.access_key = access_key
        self.logger     = logger or MobileLogger()
        self.uploaded_app_url: str = ""   # bs:// URL after upload

    @property
    def auth(self): return (self.username, self.access_key)

    def set_credentials(self, username, access_key):
        self.username   = username
        self.access_key = access_key

    def validate_credentials(self) -> dict:
        """Validate credentials and return plan info dict."""
        if not self.username or not self.access_key:
            self.logger.warn("BrowserStack credentials not set")
            return {"valid": False, "error": "Credentials missing"}
        try:
            resp = requests.get(BS_APP_AUTOMATE_PLAN_API, auth=self.auth, timeout=8)
            if resp.status_code == 200:
                plan = resp.json()
                self.logger.ok("BrowserStack credentials valid")
                return {"valid": True, "plan": plan}
            self.logger.err(f"BS auth failed ({resp.status_code})")
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
        except Exception as exc:
            self.logger.err(f"BS validation error: {exc}")
            return {"valid": False, "error": str(exc)}

    def upload_app(self, file_path: str, custom_id: str = "") -> dict:
        """
        Upload APK/IPA to BrowserStack App Automate.
        Returns dict with 'app_url' (bs://...) on success.
        """
        if not self.username or not self.access_key:
            return {"ok": False, "error": "Credentials not set"}
        if not os.path.exists(file_path):
            return {"ok": False, "error": f"File not found: {file_path}"}
        try:
            self.logger.info(f"Uploading {os.path.basename(file_path)} to BrowserStack…")
            data = {}
            if custom_id:
                data["custom_id"] = custom_id
            with open(file_path, "rb") as f:
                resp = requests.post(
                    BS_UPLOAD_API,
                    auth=self.auth,
                    files={"file": (os.path.basename(file_path), f)},
                    data=data,
                    timeout=120,
                )
            if resp.status_code == 200:
                app_url = resp.json().get("app_url", "")
                self.uploaded_app_url = app_url
                self.logger.ok(f"Upload success: {app_url}")
                return {"ok": True, "app_url": app_url}
            msg = resp.text[:300]
            self.logger.err(f"Upload failed ({resp.status_code}): {msg}")
            return {"ok": False, "error": msg}
        except Exception as exc:
            self.logger.err(f"Upload error: {exc}")
            return {"ok": False, "error": str(exc)}

    def get_devices(self, platform_filter=None) -> list:
        if not self.username or not self.access_key:
            self.logger.warn("BS credentials required")
            return []
        try:
            resp = requests.get(BS_DEVICES_API, auth=self.auth, timeout=12)
            if resp.status_code != 200:
                self.logger.err(f"BS devices API error ({resp.status_code})")
                return []
            devices = []
            for d in resp.json():
                plat = d.get("os", "Android")
                if platform_filter and plat.lower() != platform_filter.lower():
                    continue
                devices.append({
                    "serial":        f"bs_{d.get('device','').replace(' ','_')}_{d.get('os_version','')}",
                    "model":         d.get("device", "Unknown"),
                    "os":            f"{plat} {d.get('os_version','')}",
                    "platform":      plat,
                    "source":        "browserstack",
                    "bs_os_version": d.get("os_version", ""),
                })
            self.logger.ok(f"BrowserStack: {len(devices)} device(s) available")
            return devices
        except Exception as exc:
            self.logger.err(f"BS API error: {exc}")
            return []


# ═══════════════════════════════════════════════════════════════════════════════
# 4. AVD MANAGER  (Android Studio / SDK emulators)
# ═══════════════════════════════════════════════════════════════════════════════

class AVDManager:
    """
    Manages Android Virtual Devices via the `emulator` CLI from Android Studio
    or the Android SDK command-line tools. Auto-discovers the binary from common
    SDK install paths so the user doesn't need `emulator` on their PATH.
    """

    _SDK_CANDIDATES = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk"),
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "Android", "Sdk"),
        os.path.join(os.path.expanduser("~"), "Library", "Android", "sdk"),
        os.path.join(os.path.expanduser("~"), "Android", "Sdk"),
        os.environ.get("ANDROID_HOME", ""),
        os.environ.get("ANDROID_SDK_ROOT", ""),
    ]

    def __init__(self, logger=None):
        self.logger    = logger or MobileLogger()
        self._emulator = self._find("emulator")
        self._adb      = shutil.which("adb") or "adb"
        self._procs: dict = {}   # avd_name → Popen

    def _find(self, binary: str) -> str:
        found = shutil.which(binary)
        if found:
            return found
        for sdk in self._SDK_CANDIDATES:
            if not sdk:
                continue
            for candidate in [
                os.path.join(sdk, "emulator", binary),
                os.path.join(sdk, "emulator", binary + ".exe"),
            ]:
                if os.path.exists(candidate):
                    return candidate
        return binary

    @property
    def sdk_path(self) -> str:
        for sdk in self._SDK_CANDIDATES:
            if sdk and os.path.isdir(os.path.join(sdk, "emulator")):
                return sdk
        return ""

    def is_available(self) -> bool:
        try:
            subprocess.run([self._emulator, "-version"], capture_output=True, timeout=6)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def list_avds(self) -> list[str]:
        try:
            result = subprocess.run(
                [self._emulator, "-list-avds"],
                capture_output=True, text=True, timeout=10,
            )
            avds = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            self.logger.info(f"AVDs found: {avds or 'none'}")
            return avds
        except Exception as exc:
            self.logger.err(f"list_avds: {exc}")
            return []

    def launch_avd(self, avd_name: str) -> bool:
        proc = self._procs.get(avd_name)
        if proc and proc.poll() is None:
            self.logger.info(f"{avd_name} already running")
            return True
        try:
            proc = subprocess.Popen(
                [self._emulator, "-avd", avd_name, "-no-audio"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            self._procs[avd_name] = proc
            self.logger.ok(f"AVD '{avd_name}' launched (PID {proc.pid})")
            return True
        except Exception as exc:
            self.logger.err(f"Launch '{avd_name}': {exc}")
            return False

    def get_running_serials(self) -> list[str]:
        try:
            result = subprocess.run(
                [self._adb, "devices"], capture_output=True, text=True, timeout=8,
            )
            serials = []
            for line in result.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device" and parts[0].startswith("emulator"):
                    serials.append(parts[0])
            return serials
        except Exception:
            return []

    def is_booted(self, serial: str) -> bool:
        try:
            r = subprocess.run(
                [self._adb, "-s", serial, "shell", "getprop", "sys.boot_completed"],
                capture_output=True, text=True, timeout=5,
            )
            return r.stdout.strip() == "1"
        except Exception:
            return False

    def get_avd_name(self, serial: str) -> str:
        try:
            r = subprocess.run(
                [self._adb, "-s", serial, "emu", "avd", "name"],
                capture_output=True, text=True, timeout=5,
            )
            lines = [l.strip() for l in r.stdout.splitlines()
                     if l.strip() and "OK" not in l]
            return lines[0] if lines else ""
        except Exception:
            return ""

    def get_device_info(self, serial: str) -> dict:
        def prop(p):
            try:
                r = subprocess.run(
                    [self._adb, "-s", serial, "shell", "getprop", p],
                    capture_output=True, text=True, timeout=5,
                )
                return r.stdout.strip()
            except Exception:
                return ""
        avd_name = self.get_avd_name(serial)
        model    = prop("ro.product.model") or avd_name or "Android Emulator"
        mfr      = prop("ro.product.manufacturer") or "Google"
        os_ver   = prop("ro.build.version.release") or "?"
        return {
            "serial":   serial,
            "model":    f"{mfr} {model}".strip(),
            "os":       f"Android {os_ver}",
            "platform": "Android",
            "source":   "emulator",
            "avd_name": avd_name,
        }

    def stop(self, serial: str) -> bool:
        try:
            subprocess.run(
                [self._adb, "-s", serial, "emu", "kill"],
                capture_output=True, timeout=6,
            )
            self.logger.ok(f"Emulator {serial} stopped")
            return True
        except Exception as exc:
            self.logger.err(f"Stop {serial}: {exc}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# 5. APPIUM MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class AppiumManager:
    def __init__(self, base_url=APPIUM_DEFAULT_URL, logger=None):
        self.base_url   = base_url.rstrip("/")
        self.session_id: Optional[str] = None
        self.logger     = logger or MobileLogger()
        self._server_proc = None

    def start_server(self, port=APPIUM_DEFAULT_PORT) -> bool:
        try:
            self._server_proc = subprocess.Popen(
                ["appium", "--port", str(port)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            time.sleep(2.5)
            if self._server_proc.poll() is None:
                self.logger.ok(f"Appium server started on port {port}")
                return True
            self.logger.err("Appium server exited immediately")
            return False
        except FileNotFoundError:
            self.logger.err("Appium not found. Run: npm install -g appium")
            return False
        except Exception as exc:
            self.logger.err(f"Appium start error: {exc}")
            return False

    def is_server_running(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/status", timeout=4)
            return r.status_code == 200
        except Exception:
            return False

    def create_session(self, device, app_path="", app_type="native",
                       bs_user="", bs_key="", automation="", extra_caps=None,
                       bs_project="IQEA Mobile", bs_build="Build 1", bs_session_name="") -> dict:
        platform   = device.get("platform", "Android")
        model      = device.get("model",    "Device")
        source     = device.get("source",   "usb")
        automation = automation or ("UIAutomator2" if platform == "Android" else "XCUITest")

        # ── BrowserStack: use hub URL, no local Appium needed ──────────────────
        if source == "browserstack":
            url = BS_HUB_URL
            caps = {
                "platformName":             platform,
                "appium:deviceName":        model,
                "appium:platformVersion":   device.get("bs_os_version", ""),
                "appium:automationName":    automation,
                "appium:noReset":           True,
                "appium:newCommandTimeout": 300,
                "bstack:options": {
                    "userName":    bs_user,
                    "accessKey":   bs_key,
                    "projectName": bs_project,
                    "buildName":   bs_build,
                    "sessionName": bs_session_name or model,
                    "debug":       True,
                    "networkLogs": True,
                    "deviceLogs":  True,
                },
            }
            if app_type == "native" and app_path:
                caps["appium:app"] = app_path   # must be bs:// URL
            elif app_type == "browser":
                caps["browserName"] = "Chrome" if platform == "Android" else "Safari"
        else:
            # ── Local USB / Emulator ───────────────────────────────────────────
            url = self.base_url
            caps = {
                "platformName":             platform,
                "appium:deviceName":        model,
                "appium:automationName":    automation,
                "appium:noReset":           True,
                "appium:newCommandTimeout": 300,
            }
            if app_type == "native" and app_path:
                if app_path.endswith((".apk", ".ipa")):
                    caps["appium:app"] = app_path
                else:
                    caps["appium:appPackage"]  = app_path
                    caps["appium:appActivity"] = ".MainActivity"
            elif app_type == "browser":
                caps["browserName"] = "Chrome" if platform == "Android" else "Safari"
            if device.get("serial"):
                caps["appium:udid"] = device["serial"]
            # Emulator-specific extras — help Appium wait for the AVD to boot
            if source == "emulator":
                caps["appium:avdLaunchTimeout"]  = 120000
                caps["appium:avdReadyTimeout"]   = 120000
                caps["appium:autoGrantPermissions"] = True
                if device.get("avd_name"):
                    caps["appium:avd"] = device["avd_name"]

        if extra_caps:
            caps.update(extra_caps)

        try:
            self.logger.info(f"Creating session — {model} ({platform}) [{source}] → {url}")
            resp = requests.post(
                f"{url}/session",
                json={"capabilities": {"alwaysMatch": caps}},
                timeout=120,   # BS can be slow to provision
            )
            data = resp.json()
            sid  = data.get("value", {}).get("sessionId") or data.get("sessionId")
            if sid:
                self.session_id = sid
                self.logger.ok(f"Session created: {sid}")
                return {"ok": True, "session_id": sid, "caps": caps}
            msg = str(data.get("value", {}).get("message", data))[:300]
            self.logger.err(f"Session failed: {msg}")
            return {"ok": False, "error": msg}
        except requests.exceptions.ConnectionError:
            msg = f"Cannot connect to {url}"
            self.logger.err(msg)
            return {"ok": False, "error": msg}
        except Exception as exc:
            self.logger.err(f"Session exception: {exc}")
            return {"ok": False, "error": str(exc)}

    def delete_session(self, session_id=None) -> bool:
        sid = session_id or self.session_id
        if not sid:
            return False
        try:
            requests.delete(f"{self.base_url}/session/{sid}", timeout=10)
            self.logger.ok(f"Session {sid} deleted")
            if sid == self.session_id:
                self.session_id = None
            return True
        except Exception as exc:
            self.logger.warn(f"Delete session warning: {exc}")
            return False

    def get_screenshot(self, session_id=None) -> Optional[str]:
        sid = session_id or self.session_id
        if not sid:
            return None
        try:
            resp = requests.get(f"{self.base_url}/session/{sid}/screenshot", timeout=12)
            return resp.json().get("value")
        except Exception:
            return None

    def get_page_source(self, session_id=None) -> str:
        sid = session_id or self.session_id
        if not sid:
            return ""
        try:
            resp = requests.get(f"{self.base_url}/session/{sid}/source", timeout=15)
            return resp.json().get("value", "")
        except Exception:
            return ""

    def find_element(self, xpath, session_id=None) -> Optional[str]:
        sid = session_id or self.session_id
        if not sid:
            return None
        try:
            resp = requests.post(
                f"{self.base_url}/session/{sid}/element",
                json={"using": "xpath", "value": xpath}, timeout=12
            )
            val = resp.json().get("value", {})
            return val.get("ELEMENT") or val.get("element-6066-11e4-a52e-4f735466cecf")
        except Exception:
            return None

    def tap_element(self, xpath, session_id=None) -> dict:
        sid   = session_id or self.session_id
        el_id = self.find_element(xpath, sid)
        if not el_id:
            return {"ok": False, "error": f"Element not found: {xpath}"}
        try:
            requests.post(f"{self.base_url}/session/{sid}/element/{el_id}/click", timeout=10)
            self.logger.ok(f"Tapped: {xpath}")
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def send_keys(self, xpath, value, session_id=None) -> dict:
        sid   = session_id or self.session_id
        el_id = self.find_element(xpath, sid)
        if not el_id:
            return {"ok": False, "error": f"Element not found: {xpath}"}
        try:
            requests.post(f"{self.base_url}/session/{sid}/element/{el_id}/clear", timeout=8)
            requests.post(
                f"{self.base_url}/session/{sid}/element/{el_id}/value",
                json={"text": value, "value": list(value)}, timeout=10
            )
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def swipe(self, start_x, start_y, end_x, end_y, duration_ms=500, session_id=None) -> dict:
        sid = session_id or self.session_id
        if not sid:
            return {"ok": False, "error": "No active session"}
        try:
            requests.post(
                f"{self.base_url}/session/{sid}/touch/perform",
                json={"actions": [
                    {"action": "press",  "options": {"x": start_x, "y": start_y}},
                    {"action": "wait",   "options": {"ms": duration_ms}},
                    {"action": "moveTo", "options": {"x": end_x,   "y": end_y}},
                    {"action": "release","options": {}},
                ]}, timeout=12
            )
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def execute_script_on_device(self, script, args=None, session_id=None) -> dict:
        sid = session_id or self.session_id
        if not sid:
            return {"ok": False, "error": "No active session"}
        try:
            resp = requests.post(
                f"{self.base_url}/session/{sid}/execute/sync",
                json={"script": script, "args": args or []}, timeout=15
            )
            return {"ok": True, "value": resp.json().get("value")}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. XPATH UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def build_xpath(node: ET.Element) -> str:
    """Build best unique XPath for an XML element."""
    tag = node.tag
    a   = node.attrib
    if a.get("resource-id"):  return f'//{tag}[@resource-id="{a["resource-id"]}"]'
    if a.get("content-desc"): return f'//{tag}[@content-desc="{a["content-desc"]}"]'
    if a.get("text"):         return f'//{tag}[@text="{a["text"]}"]'
    if a.get("name"):         return f'//{tag}[@name="{a["name"]}"]'
    if a.get("label"):        return f'//{tag}[@label="{a["label"]}"]'
    return f'//{tag}[@index="{a.get("index","0")}"]'

def infer_action_type(node: ET.Element) -> str:
    combined = (node.tag + node.attrib.get("class", "")).lower()
    if "edittext" in combined or "textfield" in combined: return "input"
    if "scrollview" in combined or "recyclerview" in combined: return "scroll"
    return "tap"

def infer_label(node: ET.Element) -> str:
    a = node.attrib
    for key in ("content-desc", "text", "name", "label", "resource-id"):
        val = a.get(key, "").strip()
        if val:
            if key == "resource-id" and "/" in val:
                val = val.split("/")[-1]
            return val[:60]
    return node.tag.split(".")[-1]

def diff_page_sources(prev_xml: str, curr_xml: str) -> list[ET.Element]:
    """Return list of XML elements that changed between two page source snapshots."""
    if not prev_xml or not curr_xml or prev_xml == curr_xml:
        return []
    try:
        prev_root = ET.fromstring(prev_xml)
        curr_root = ET.fromstring(curr_xml)
    except ET.ParseError:
        return []

    prev_map: dict[str, dict] = {}
    curr_map: dict[str, dict] = {}
    curr_nodes: dict[str, ET.Element] = {}

    def index_tree(root, amap, nmap=None, path=""):
        for i, child in enumerate(root):
            key = f"{path}/{child.tag}[{i}]"
            amap[key] = dict(child.attrib)
            if nmap is not None:
                nmap[key] = child
            index_tree(child, amap, nmap, key)

    index_tree(prev_root, prev_map)
    index_tree(curr_root, curr_map, curr_nodes)

    changed = []
    for key, curr_attribs in curr_map.items():
        if curr_attribs != prev_map.get(key, {}):
            node = curr_nodes.get(key)
            if node is not None:
                changed.append(node)

    return changed

def pick_best_node(nodes: list[ET.Element]) -> Optional[ET.Element]:
    """Pick the most actionable element from a list of changed nodes."""
    candidates = [n for n in nodes if n.tag not in SKIP_TAGS] or nodes

    def score(n: ET.Element) -> int:
        a = n.attrib
        s = 0
        if a.get("resource-id"):          s += 4
        if a.get("content-desc"):         s += 3
        if a.get("text"):                 s += 2
        if a.get("clickable") == "true":  s += 2
        if a.get("focused")   == "true":  s += 2
        if a.get("selected")  == "true":  s += 1
        return s

    candidates.sort(key=score, reverse=True)
    return candidates[0] if candidates else None


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ACTION RECORDER  ← real auto-detection
# ═══════════════════════════════════════════════════════════════════════════════

class ActionRecorder:
    """
    Auto-detects user actions on connected device via Appium page-source diffing.

    Flow:
      recorder.start()          → spawns background poll thread
        [user taps phone]       → thread detects XML change → stores action + screenshot
        [user taps again]       → same
      recorder.stop()           → stops thread, returns action list
      recorder.to_dict(device)  → serialisable payload for JSON save
    """

    def __init__(self, appium: Optional[AppiumManager] = None,
                 logger: Optional[MobileLogger] = None):
        self.appium    = appium
        self.logger    = logger or MobileLogger()
        self.actions:  list[dict]   = []
        self.recording = False
        self.latest_screenshot: Optional[str] = None

        self._prev_source = ""
        self._poll_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    # ── Control ───────────────────────────────────────────────────
    def start(self):
        with self._lock:
            self.actions        = []
            self.recording      = True
            self._prev_source   = ""
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
        self.logger.ok("Recording started — interact with your device")

    def stop(self) -> list[dict]:
        self.recording = False
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=6)
        self.logger.ok(f"Recording stopped — {len(self.actions)} action(s) captured")
        return list(self.actions)

    def clear(self):
        with self._lock:
            self.actions           = []
            self._prev_source      = ""
            self.latest_screenshot = None
        self.logger.info("Actions cleared")

    # ── Poll loop (background thread) ─────────────────────────────
    def _poll_loop(self):
        while self.recording:
            try:
                self._poll_once()
            except Exception as exc:
                self.logger.warn(f"Poll error: {exc}")
            time.sleep(POLL_INTERVAL_SEC)

    def _poll_once(self):
        if not self.appium or not self.appium.session_id:
            return

        # Fetch current state
        curr_source = self.appium.get_page_source()
        screenshot  = self.appium.get_screenshot()
        if screenshot:
            self.latest_screenshot = screenshot

        if not curr_source:
            return

        # First poll → just set baseline
        if not self._prev_source:
            self._prev_source = curr_source
            return

        # Nothing changed
        if curr_source == self._prev_source:
            return

        # Detect changed elements
        changed = diff_page_sources(self._prev_source, curr_source)
        self._prev_source = curr_source

        if not changed:
            return

        target = pick_best_node(changed)
        if target is None:
            return

        xpath  = build_xpath(target)
        atype  = infer_action_type(target)
        label  = infer_label(target)
        value  = target.attrib.get("text", "") if atype == "input" else ""

        action = {
            "seq":            len(self.actions) + 1,
            "ts":             datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "type":           atype,
            "label":          label,
            "xpath":          xpath,
            "value":          value,
            "start":          [0, 0],
            "end":            [0, 0],
            "screenshot_b64": screenshot or "",
        }

        with self._lock:
            self.actions.append(action)

        self.logger.ok(f"#{action['seq']:02d} detected — {atype.upper()} '{label}'")

    # ── Persistence ───────────────────────────────────────────────
    def to_dict(self, device: dict, session_id: str = "") -> dict:
        # Strip screenshots from JSON — keep file small
        clean = [{k: v for k, v in a.items() if k != "screenshot_b64"}
                 for a in self.actions]
        return {
            "iqea_version":  "2.0",
            "session_id":    session_id,
            "device":        device.get("model",    ""),
            "platform":      device.get("platform", ""),
            "os":            device.get("os",       ""),
            "source":        device.get("source",   ""),
            "recorded_at":   datetime.now().isoformat(),
            "action_count":  len(clean),
            "actions":       clean,
        }

    def load_dict(self, data: dict) -> list[dict]:
        self.actions = data.get("actions", [])
        self.logger.ok(f"Loaded {len(self.actions)} action(s) from file")
        return self.actions


# ═══════════════════════════════════════════════════════════════════════════════
# 7. SCRIPT EXECUTOR  ← replay on device + stream results
# ═══════════════════════════════════════════════════════════════════════════════

class ScriptExecutor:
    """
    Replays recorded actions on the connected device step by step.
    Calls on_step(result) after each action so the UI can update live.
    """

    def __init__(self, appium: AppiumManager, logger: Optional[MobileLogger] = None):
        self.appium  = appium
        self.logger  = logger or MobileLogger()
        self.running = False
        self.results: list[dict] = []

    def execute(self, actions: list[dict],
                on_step: Optional[callable] = None,
                delay_sec: float = 1.2) -> list[dict]:
        self.running = True
        self.results = []

        for action in actions:
            if not self.running:
                break

            seq   = action.get("seq",   "?")
            atype = action.get("type",  "tap")
            xpath = action.get("xpath", "")
            value = action.get("value", "")
            label = action.get("label", "")
            start = action.get("start", [0, 0])
            end   = action.get("end",   [0, 0])

            self.logger.info(f"Executing #{seq} {atype.upper()} — {label}")

            if   atype == "tap"   and xpath: res = self.appium.tap_element(xpath)
            elif atype == "input" and xpath: res = self.appium.send_keys(xpath, value)
            elif atype == "swipe":           res = self.appium.swipe(start[0], start[1], end[0], end[1])
            elif atype == "scroll":          res = self.appium.execute_script_on_device("mobile: scroll", [{"direction": "down"}])
            else:                            res = {"ok": False, "error": f"Unknown type: {atype}"}

            screenshot = self.appium.get_screenshot()

            step_result = {
                "seq":            seq,
                "label":          label,
                "type":           atype,
                "xpath":          xpath,
                "ok":             res.get("ok", False),
                "error":          res.get("error", ""),
                "screenshot_b64": screenshot or "",
                "ts":             datetime.now().strftime("%H:%M:%S.%f")[:-3],
            }
            self.results.append(step_result)

            if res.get("ok"): self.logger.ok(f"  ✓ #{seq} {label}")
            else:             self.logger.err(f"  ✗ #{seq} {label} — {res.get('error','')}")

            if on_step:
                on_step(step_result)

            time.sleep(delay_sec)

        self.running = False
        passed = sum(1 for r in self.results if r["ok"])
        self.logger.ok(f"Execution complete — {passed}/{len(self.results)} passed")
        return self.results

    def stop(self):
        self.running = False
        self.logger.warn("Execution stopped by user")


# ═══════════════════════════════════════════════════════════════════════════════
# 8. SCRIPT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class ScriptGenerator:
    def __init__(self, logger: Optional[MobileLogger] = None):
        self.logger = logger or MobileLogger()

    def generate(self, actions, device, framework,
                 app_path="", app_type="native",
                 add_waits=True, add_asserts=False, add_logging=True) -> str:
        platform = device.get("platform", "Android")
        model    = device.get("model",    "Device")
        os_ver   = device.get("os",       "Unknown")
        source   = device.get("source",   "usb")
        ext      = FRAMEWORKS.get(framework, {}).get("ext", "py")
        c        = "#" if ext in ("py", "robot") else "//"

        header = (
            f"{c} {'='*62}\n"
            f"{c} IQEA Auto-Generated Mobile Test Script\n"
            f"{c} Device   : {model}\n"
            f"{c} Platform : {platform} ({os_ver})\n"
            f"{c} Source   : {'BrowserStack' if source=='browserstack' else 'USB/Local'}\n"
            f"{c} App      : {app_path or 'browser'}\n"
            f"{c} Framework: {framework}\n"
            f"{c} Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{c} {'='*62}\n"
        )

        if   "Python + Appium" in framework: body = self._python_appium(actions, platform, model, app_path, app_type, source, add_waits, add_asserts, add_logging)
        elif "Playwright"      in framework: body = self._python_playwright(actions, model, add_waits, add_logging)
        elif "Java"            in framework: body = self._java_testng(actions, platform, model, app_path, add_waits, add_logging)
        elif "WebdriverIO"     in framework: body = self._js_wdio(actions, platform, model, app_path, add_waits, add_logging)
        elif "Robot"           in framework: body = self._robot_framework(actions, platform, model, app_path, add_waits)
        else:                                body = f"{c} Unknown framework"

        script = header + "\n" + body
        self.logger.ok(f"Script generated — {framework} — {len(script.splitlines())} lines")
        return script

    def _python_appium(self, actions, platform, model, app_path, app_type, source, add_waits, add_asserts, add_logging):
        auto = "UIAutomator2" if platform == "Android" else "XCUITest"
        L = [
            "import pytest, logging",
            "from appium import webdriver",
            "from appium.options import AppiumOptions",
            "from appium.webdriver.common.appiumby import AppiumBy",
            "from selenium.webdriver.support.ui import WebDriverWait",
            "from selenium.webdriver.support import expected_conditions as EC",
            "", "logging.basicConfig(level=logging.INFO)",
            "log = logging.getLogger('IQEA')", "",
            "@pytest.fixture(scope='module')",
            "def driver():",
            "    opts = AppiumOptions()",
            f'    opts.platform_name     = "{platform}"',
            f'    opts.automation_name   = "{auto}"',
            f'    opts.set_capability("appium:deviceName", "{model}")',
            '    opts.set_capability("appium:noReset", True)',
        ]
        if app_type == "native" and app_path:
            L.append(f'    opts.set_capability("appium:app", "{app_path}")')
        else:
            L.append('    opts.browser_name = "Chrome"')
        L += [
            '    d = webdriver.Remote("http://localhost:4723", options=opts)',
            "    yield d", "    d.quit()", "",
            "def test_recorded_flow(driver):",
            "    wait = WebDriverWait(driver, 10)", "",
        ]
        for i, a in enumerate(actions):
            L += self._py_action(a, i, add_waits, add_asserts, add_logging)
        return "\n".join(L)

    def _py_action(self, a, idx, add_waits, add_asserts, add_logging):
        L = []
        xpath = a.get("xpath",""); label = a.get("label",f"step_{idx+1}")
        atype = a.get("type","tap"); value = a.get("value","")
        sx,sy = a.get("start",[0,0]); ex,ey = a.get("end",[0,0])
        if add_logging: L.append(f'    log.info("Step {idx+1}: {label}")')
        if add_waits and xpath: L.append(f'    wait.until(EC.presence_of_element_located((AppiumBy.XPATH, "{xpath}")))  # {label}')
        if   atype=="tap"   and xpath: L.append(f'    driver.find_element(AppiumBy.XPATH, "{xpath}").click()  # {label}')
        elif atype=="input" and xpath:
            L.append(f'    driver.find_element(AppiumBy.XPATH, "{xpath}").clear()')
            L.append(f'    driver.find_element(AppiumBy.XPATH, "{xpath}").send_keys("{value}")  # {label}')
        elif atype=="swipe":  L.append(f'    driver.swipe({sx}, {sy}, {ex}, {ey}, 500)  # {label}')
        elif atype=="scroll": L.append(f'    driver.execute_script("mobile: scroll", {{"direction": "down"}})')
        if add_asserts and atype=="tap" and xpath: L.append(f'    assert driver.find_element(AppiumBy.XPATH, "{xpath}").is_displayed()')
        L.append("")
        return L

    def _python_playwright(self, actions, model, add_waits, add_logging):
        L = [
            "import pytest, logging",
            "from playwright.sync_api import sync_playwright",
            "", "log = logging.getLogger('IQEA')", "",
            "def test_recorded_mobile():",
            "    with sync_playwright() as p:",
            "        browser = p.chromium.launch(headless=False)",
            f'        ctx  = browser.new_context(**p.devices["{model}"])',
            "        page = ctx.new_page()", "",
        ]
        for i, a in enumerate(actions):
            xpath=a.get("xpath",""); label=a.get("label",f"step_{i+1}")
            atype=a.get("type","tap"); value=a.get("value","")
            sx,sy=a.get("start",[0,0]); ex,ey=a.get("end",[0,0])
            if add_logging: L.append(f'        log.info("Step {i+1}: {label}")')
            if add_waits and xpath: L.append(f"        page.locator('xpath={xpath}').wait_for()")
            if   atype=="tap"   and xpath: L.append(f"        page.locator('xpath={xpath}').click()  # {label}")
            elif atype=="input" and xpath: L.append(f"        page.locator('xpath={xpath}').fill('{value}')  # {label}")
            elif atype=="swipe":
                L += [f"        page.mouse.move({sx},{sy})","        page.mouse.down()",f"        page.mouse.move({ex},{ey})","        page.mouse.up()"]
            L.append("")
        L += ["        ctx.close()", "        browser.close()"]
        return "\n".join(L)

    def _java_testng(self, actions, platform, model, app_path, add_waits, add_logging):
        L = [
            "import io.appium.java_client.AppiumDriver;",
            "import io.appium.java_client.android.AndroidDriver;",
            "import io.appium.java_client.android.options.UiAutomator2Options;",
            "import org.openqa.selenium.By;",
            "import org.openqa.selenium.support.ui.ExpectedConditions;",
            "import org.openqa.selenium.support.ui.WebDriverWait;",
            "import org.testng.annotations.*;",
            "import java.net.URL; import java.time.Duration; import java.util.logging.Logger;","",
            "public class IQEAMobileTest {",
            "    private AppiumDriver driver;",
            "    private static final Logger log = Logger.getLogger(IQEAMobileTest.class.getName());","",
            "    @BeforeClass public void setUp() throws Exception {",
            f'        var opts = new UiAutomator2Options().setDeviceName("{model}").setApp("{app_path}");',
            '        driver = new AndroidDriver(new URL("http://localhost:4723"), opts);',
            "    }","","    @Test public void testRecordedFlow() {",
            "        var wait = new WebDriverWait(driver, Duration.ofSeconds(10));","",
        ]
        for i, a in enumerate(actions):
            xpath=a.get("xpath",""); label=a.get("label",f"step_{i+1}")
            atype=a.get("type","tap"); value=a.get("value","")
            if add_logging: L.append(f'        log.info("Step {i+1}: {label}");')
            if add_waits and xpath: L.append(f'        wait.until(ExpectedConditions.presenceOfElementLocated(By.xpath("{xpath}")));')
            if   atype=="tap"   and xpath: L.append(f'        driver.findElement(By.xpath("{xpath}")).click();  // {label}')
            elif atype=="input" and xpath:
                L.append(f'        driver.findElement(By.xpath("{xpath}")).clear();')
                L.append(f'        driver.findElement(By.xpath("{xpath}")).sendKeys("{value}");  // {label}')
            L.append("")
        L += ["    }","    @AfterClass public void tearDown() { if(driver!=null) driver.quit(); }","}"]
        return "\n".join(L)

    def _js_wdio(self, actions, platform, model, app_path, add_waits, add_logging):
        auto = "UIAutomator2" if platform == "Android" else "XCUITest"
        L = [
            "const { remote } = require('webdriverio');","",
            "describe('IQEA Recorded Flow', () => {","    let driver;","",
            "    before(async () => { driver = await remote({ path:'/wd/hub', port:4723,",
            "        capabilities: {",
            f"            platformName: '{platform}', 'appium:deviceName': '{model}',",
            f"            'appium:automationName': '{auto}', 'appium:app': '{app_path}'",
            "        }}); });","","    it('replays recorded actions', async () => {",
        ]
        for i, a in enumerate(actions):
            xpath=a.get("xpath",""); label=a.get("label",f"step_{i+1}")
            atype=a.get("type","tap"); value=a.get("value","")
            if add_logging: L.append(f"        console.log('Step {i+1}: {label}');")
            if add_waits and xpath: L.append(f"        await $('{xpath}').waitForExist({{timeout:10000}});")
            if   atype=="tap"   and xpath: L.append(f"        await $('{xpath}').click();  // {label}")
            elif atype=="input" and xpath: L.append(f"        await $('{xpath}').setValue('{value}');  // {label}")
            L.append("")
        L += ["    });","    after(() => driver.deleteSession());","});"]
        return "\n".join(L)

    def _robot_framework(self, actions, platform, model, app_path, add_waits):
        auto = "UIAutomator2" if platform == "Android" else "XCUITest"
        L = [
            "*** Settings ***","Library    AppiumLibrary","",
            "*** Variables ***",
            f"${{PLATFORM}}   {platform}", f"${{DEVICE}}     {model}",
            f"${{APP}}        {app_path}", f"${{AUTO}}       {auto}","",
            "*** Test Cases ***","IQEA Recorded Mobile Flow",
            "    [Documentation]    Auto-generated by IQEA","    Open Mobile App",
        ]
        for a in actions:
            xpath=a.get("xpath",""); label=a.get("label","")
            atype=a.get("type","tap"); value=a.get("value","")
            sx,sy=a.get("start",[0,0]); ex,ey=a.get("end",[0,0])
            if add_waits and xpath: L.append(f"    Wait Until Element Is Visible    xpath={xpath}")
            if   atype=="tap"   and xpath: L.append(f"    Click Element    xpath={xpath}    # {label}")
            elif atype=="input" and xpath:
                L.append(f"    Clear Text    xpath={xpath}")
                L.append(f"    Input Text    xpath={xpath}    {value}    # {label}")
            elif atype=="swipe":  L.append(f"    Swipe    {sx}    {sy}    {ex}    {ey}    500")
            elif atype=="scroll": L.append("    Scroll Down")
        L += [
            "","*** Keywords ***","Open Mobile App",
            "    Open Application    http://localhost:4723",
            "    ...    platformName=${PLATFORM}",
            "    ...    appium:deviceName=${DEVICE}",
            "    ...    appium:app=${APP}",
            "    ...    appium:automationName=${AUTO}",
            "    ...    appium:noReset=True",
        ]
        return "\n".join(L)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. SCRCPY MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ScrcpyManager:
    def __init__(self, logger=None):
        self.logger = logger or MobileLogger()
        self._procs: dict[str, subprocess.Popen] = {}

    @staticmethod
    def is_available() -> bool:
        try:
            subprocess.run(["scrcpy", "--version"], capture_output=True, timeout=4)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def start(self, serial, max_size=720, bit_rate="4M", title=None) -> bool:
        if serial in self._procs and self._procs[serial].poll() is None:
            return True
        if not self.is_available():
            self.logger.err("scrcpy not installed. Download: https://github.com/Genymobile/scrcpy/releases")
            return False
        try:
            proc = subprocess.Popen(
                ["scrcpy", "--serial", serial,
                 "--window-title", title or f"IQEA — {serial}",
                 "--max-size", str(max_size), "--bit-rate", bit_rate],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            time.sleep(1.8)
            if proc.poll() is None:
                self._procs[serial] = proc
                self.logger.ok(f"scrcpy started for {serial}")
                return True
            self.logger.err("scrcpy exited immediately")
            return False
        except Exception as exc:
            self.logger.err(f"scrcpy error: {exc}")
            return False

    def stop(self, serial) -> bool:
        proc = self._procs.get(serial)
        if proc and proc.poll() is None:
            proc.terminate()
            self._procs.pop(serial, None)
            return True
        return False

    def is_running(self, serial) -> bool:
        p = self._procs.get(serial)
        return p is not None and p.poll() is None

    def running_serials(self) -> list[str]:
        return [s for s, p in self._procs.items() if p.poll() is None]


# ═══════════════════════════════════════════════════════════════════════════════
# 10. HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_session_id() -> str:
    return "SES-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def device_label(device: dict) -> str:
    src = {"usb": "USB", "emulator": "EMU", "browserstack": "BS"}.get(device.get("source","usb"), "?")
    return f"{device.get('model','Unknown')} [{src}]"

def framework_extension(framework: str) -> str:
    return FRAMEWORKS.get(framework, {}).get("ext", "py")

def framework_install_cmd(framework: str) -> str:
    return FRAMEWORKS.get(framework, {}).get("install", "")