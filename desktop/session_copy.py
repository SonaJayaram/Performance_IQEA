from pywinauto import Application


class DesktopSession:

    def __init__(self, app_path=None, backend="uia"):
        self.backend = backend
        self.app = None
        self.app_path = app_path

    def start(self):
        if not self.app_path:
            raise ValueError("Application path required")

        self.app = Application(backend=self.backend).start(self.app_path)
        return self.app

    def connect(self, title):
        self.app = Application(backend=self.backend).connect(title_re=title)
        return self.app