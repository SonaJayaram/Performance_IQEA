import mouse
import keyboard
import os
import mss
import mss.tools
import psutil
from pywinauto import Desktop
from datetime import datetime


class UltimateDesktopRecorder:

    def __init__(self):

        self.actions = []
        self.is_recording = False
        self.text_buffer = ""
        self.step = 1

        self.screenshot_dir = "recorded_steps"

        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

        self.last_app = None

    # -----------------------------
    # Detect Active Application
    # -----------------------------
    def get_active_application(self):

        try:

            element = Desktop(backend="uia").get_active()

            process_id = element.process_id

            process = psutil.Process(process_id)

            return process.name()

        except:
            return "UnknownApp"

    # -----------------------------
    # Screenshot Capture
    # -----------------------------
    def capture_screenshot(self):

        filename = f"{self.screenshot_dir}/step_{self.step:03}.png"

        with mss.mss() as sct:

            monitor = sct.monitors[1]

            img = sct.grab(monitor)

            mss.tools.to_png(img.rgb, img.size, output=filename)

        print("Screenshot:", filename)

    # -----------------------------
    # Keyboard Capture
    # -----------------------------
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
            self.text_buffer += "\n"

    def flush_text(self):

        if self.text_buffer.strip():

            app = self.get_active_application()

            action = f'TYPE_TEXT application="{app}" text="{self.text_buffer}"'

            print("Captured:", action)

            self.actions.append(action)

            self.capture_screenshot()

            self.step += 1

        self.text_buffer = ""

    # -----------------------------
    # Click Capture
    # -----------------------------
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

            app = self.get_active_application()

            menu_path = self.build_menu_path(target)

            if menu_path:

                action = f'MENU_CLICK application="{app}" path="{menu_path}"'

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

            print("Capture error:", e)

    # -----------------------------
    # Find Clickable Parent
    # -----------------------------
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

    # -----------------------------
    # Menu Path Builder
    # -----------------------------
    def build_menu_path(self, element):

        names = []

        current = element

        while current:

            try:

                control = current.element_info.control_type
                name = current.element_info.name

                if control == "MenuItem" and name:

                    names.append(name)

                current = current.parent()

            except:

                break

        if names:

            names.reverse()

            return "->".join(names)

        return None

    # -----------------------------
    # Start Recording
    # -----------------------------
    def start(self):

        print("Recording started...")

        self.is_recording = True

        mouse.on_button(self.handle_click, buttons=("left",), types=("down",))

        keyboard.hook(self.handle_key)

    # -----------------------------
    # Stop Recording
    # -----------------------------
    def stop(self):

        print("Recording stopped")

        self.flush_text()

        self.is_recording = False

        mouse.unhook_all()

        keyboard.unhook_all()

    # -----------------------------
    # Save Action File
    # -----------------------------
    def save(self, filename):

        with open(filename, "w", encoding="utf-8") as f:

            for action in self.actions:

                f.write(f"STEP {self.step}: {action}\n")

        print("Saved:", filename)