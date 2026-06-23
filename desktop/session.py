# desktop_session.py — IQEA Desktop Session v2.0
import time
from pywinauto import Application, Desktop
from pywinauto.timings import TimeoutError as PWTimeoutError


class DesktopSession:

    def __init__(self, app_path=None, backend="uia"):
        self.backend  = backend
        self.app      = None
        self.app_path = app_path

    def start(self, timeout=15):
        """
        Launch the application and wait until its main window is ready.
        FIX: v1 returned immediately after .start() — the window didn't
        exist yet, causing the first few recorded clicks to fail silently.
        """
        if not self.app_path:
            raise ValueError("Application path required")

        self.app = Application(backend=self.backend).start(self.app_path)

        # Wait for main window to appear and be ready (up to timeout seconds)
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                # Try to get the top window — raises if not ready yet
                win = self.app.top_window()
                win.wait("ready", timeout=2)
                print(f"  App ready: {win.window_text()}")
                return self.app
            except Exception:
                time.sleep(0.5)

        # Fallback — return app even if window check timed out
        print("  Warning: app window readiness timeout — proceeding anyway")
        return self.app

    def connect(self, title):
        self.app = Application(backend=self.backend).connect(title_re=title)
        return self.app
