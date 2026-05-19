import mouse
import keyboard
import json
from pywinauto import Desktop


class DesktopRecorder:

    def __init__(self):
        self.actions = []
        self.is_recording = False
        self.text_buffer = ""
        self.last_menu_header = None
        self.current_app = None

    # ----------------------------
    # Detect Active Window
    # ----------------------------
    def _get_active_window(self):

        try:
            window = Desktop(backend="uia").get_active()
            title = window.window_text()

            if "Excel" in title:
                return "excel"

            elif "Notepad" in title:
                return "notepad"

            elif "Chrome" in title or "Edge" in title:
                return "browser"

            else:
                return "desktop"

        except:
            return "unknown"

    # ----------------------------
    # TEXT HANDLING
    # ----------------------------
    def _handle_key(self, event):

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

    def _flush_text_buffer(self):

        if self.text_buffer.strip():

            app = self._get_active_window()

            if app == "excel":
                action = {
                    "source": "excel",
                    "action": "enter_cell_text",
                    "value": self.text_buffer
                }

            else:
                action = {
                    "source": "desktop",
                    "action": "type",
                    "text": self.text_buffer
                }

            self.actions.append(action)

            print(f'Captured: {action}')

        self.text_buffer = ""

    # ----------------------------
    # CLICK HANDLING
    # ----------------------------
    def _handle_click(self):

        if not self.is_recording:
            return

        self._flush_text_buffer()

        x, y = mouse.get_position()

        try:

            element = Desktop(backend="uia").from_point(x, y)
            target = self._find_clickable_parent(element)

            if not target:
                return

            name = target.element_info.name
            control_type = target.element_info.control_type

            app = self._get_active_window()

            if app == "excel":

                action = {
                    "source": "excel",
                    "action": "click",
                    "element": name,
                    "control_type": control_type
                }

            else:

                menu_path = self._build_menu_path(target)

                if menu_path:
                    action = {
                        "source": "desktop",
                        "action": "menu_click",
                        "path": menu_path
                    }

                else:
                    action = {
                        "source": "desktop",
                        "action": "click",
                        "element_name": name,
                        "control_type": control_type
                    }

            self.actions.append(action)

            print("Captured:", action)

        except Exception as e:
            print("Capture failed:", e)

    # ----------------------------
    # Parent Finder
    # ----------------------------
    def _find_clickable_parent(self, element):

        current = element

        while current:

            try:

                name = current.element_info.name
                control_type = current.element_info.control_type

                if control_type in ["MenuItem", "Button", "Edit", "TabItem", "DataItem"]:
                    return current

                current = current.parent()

            except:
                break

        return None

    # ----------------------------
    # Menu Path Builder
    # ----------------------------
    def _build_menu_path(self, element):

        names = []
        current = element

        while current:

            try:

                control_type = current.element_info.control_type
                name = current.element_info.name

                if control_type == "MenuItem" and name:
                    names.append(name)

                current = current.parent()

            except:
                break

        if names:
            names.reverse()
            return " -> ".join(names)

        return None

    # ----------------------------
    # Start Recording
    # ----------------------------
    def start_recording(self):

        print("Recording started...")

        self.is_recording = True

        mouse.on_button(self._handle_click, buttons=("left",), types=("down",))
        keyboard.hook(self._handle_key)

    # ----------------------------
    # Stop Recording
    # ----------------------------
    def stop_recording(self):

        print("Recording stopped.")

        self._flush_text_buffer()

        self.is_recording = False

        mouse.unhook_all()
        keyboard.unhook_all()

    # ----------------------------
    # Save JSON
    # ----------------------------
    def save(self, file_name):

        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(self.actions, f, indent=4)

        print("Saved to", file_name)

    # ----------------------------
    # Save Text Workflow
    # ----------------------------
    def save_file(self, file_name):

        with open(file_name, "w", encoding="utf-8") as f:

            for action in self.actions:

                if action["source"] == "excel":

                    if action["action"] == "enter_cell_text":
                        f.write(f'Excel: Enter "{action["value"]}"\n')

                    elif action["action"] == "click":
                        f.write(f'Excel: Click {action["element"]}\n')

                elif action["source"] == "desktop":

                    if action["action"] == "type":
                        f.write(f'Enter text "{action["text"]}"\n')

                    elif action["action"] == "menu_click":
                        f.write(f'Menu: {action["path"]}\n')

                    elif action["action"] == "click":
                        f.write(f'Click {action["element_name"]}\n')

        print("Saved to", file_name)