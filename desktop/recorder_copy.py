import mouse
import keyboard
import os
import time
import mss
import mss.tools
import win32gui
import win32process
import psutil
from pywinauto import Desktop


class DesktopRecorder:

    def __init__(self):

        self.actions = []
        self.is_recording = False
        self.text_buffer = ""

        self.step = 1
        self.screenshot_folder = "recorded_steps"

        if not os.path.exists(self.screenshot_folder):
            os.makedirs(self.screenshot_folder)

    # -------------------------------------------------
    # Get Active Application
    # -------------------------------------------------

    def get_active_app(self):

        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)

            return process.name()

        except:
            return "UnknownApp"

    # -------------------------------------------------
    # Screenshot
    # -------------------------------------------------

    def capture_screenshot(self):

        filename = f"{self.screenshot_folder}/step_{self.step:03}.png"

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            img = sct.grab(monitor)
            mss.tools.to_png(img.rgb, img.size, output=filename)

        return filename

    # -------------------------------------------------
    # Flush text
    # -------------------------------------------------

    def flush_text(self):

        if self.text_buffer.strip():

            app = self.get_active_app()

            action = f'TYPE_TEXT application="{app}" text="{self.text_buffer.strip()}"'

            print("Captured:", action)

            self.actions.append(action)

            self.capture_screenshot()

            self.step += 1

        self.text_buffer = ""

    # -------------------------------------------------
    # Keyboard Handler
    # -------------------------------------------------

    def handle_key(self, event):

        if not self.is_recording:
            return

        if event.event_type != "down":
            return

        if len(event.name) == 1:
            self.text_buffer += event.name

        elif event.name == "space":
            self.text_buffer += " "

        elif event.name == "enter":
            self.flush_text()

        elif event.name == "tab":
            self.flush_text()

    # -------------------------------------------------
    # Find clickable parent
    # -------------------------------------------------

    def find_clickable(self, element):

        current = element

        while current:

            try:
                control = current.element_info.control_type

                if control in ["MenuItem", "Button", "Edit", "TabItem"]:
                    return current

                current = current.parent()

            except:
                break

        return None

    # -------------------------------------------------
    # Build menu path
    # -------------------------------------------------

    def build_menu_path(self, element):

        names = []
        current = element

        while current:

            try:
                name = current.element_info.name
                control = current.element_info.control_type

                if control == "MenuItem" and name:
                    names.append(name)

                current = current.parent()

            except:
                break

        if names:
            names.reverse()
            return "->".join(names)

        return None

    # -------------------------------------------------
    # Mouse Click Handler
    # -------------------------------------------------

    def handle_click(self):

        if not self.is_recording:
            return

        self.flush_text()

        x, y = mouse.get_position()

        try:

            element = Desktop(backend="uia").from_point(x, y)

            target = self.find_clickable(element)

            if not target:
                return

            name = target.element_info.name
            control = target.element_info.control_type

            app = self.get_active_app()

            menu = self.build_menu_path(target)

            if menu:

                action = f'MENU_CLICK application="{app}" path="{menu}"'

            elif control == "Button":

                action = f'CLICK_BUTTON application="{app}" name="{name}"'

            elif control == "Edit":

                action = f'CLICK_FIELD application="{app}" name="{name}"'

            else:

                action = f'CLICK application="{app}" name="{name}" type="{control}"'

            print("Captured:", action)

            self.actions.append(action)

            self.capture_screenshot()

            self.step += 1

        except Exception as e:

            print("Capture failed:", e)

    # -------------------------------------------------
    # Start Recording
    # -------------------------------------------------

    def start(self):

        print("Recording started...")

        self.is_recording = True

        mouse.on_button(self.handle_click, buttons=("left",), types=("down",))

        keyboard.hook(self.handle_key)

    # -------------------------------------------------
    # Stop Recording
    # -------------------------------------------------

    def stop(self):

        print("Recording stopped.")

        self.flush_text()

        self.is_recording = False

        mouse.unhook_all()
        keyboard.unhook_all()

    # -------------------------------------------------
    # Save Action File
    # -------------------------------------------------

    def save(self, filename):

        step = 1

        with open(filename, "w", encoding="utf-8") as f:

            for action in self.actions:

                f.write(f"STEP {step}: {action}\n")

                step += 1

        print("Saved actions to", filename)