# desktop_recorder.py — IQEA Desktop Action Recorder v2.0
#
# Fixes over v1:
#   1. Click resolved on mouse UP (not down) — element state is stable
#   2. UIA element lookup moved to background thread — no blocking on click
#   3. Full keyboard handling: shift combos, backspace, shortcuts (Ctrl+S etc.)
#   4. Expanded control type whitelist covering Excel, Office, Win32 apps
#   5. Right-click recording
#   6. Scroll recording (mouse wheel)
#   7. Keyboard shortcuts recorded as named actions (SHORTCUT, not TYPE_TEXT)
#   8. Duplicate action suppression (same action within 300ms)
#   9. Active window title captured alongside process name
#  10. Timestamped screenshots with page/step naming
#  11. Thread-safe action list

import os
import time
import threading
import queue
import mss
import mss.tools
import mouse
import keyboard
import win32gui
import win32process
import psutil
from datetime import datetime
from pywinauto import Desktop


# ─── Control types that are meaningful to record ──────────────────────────────
# Expanded to cover Excel cells, Office ribbon, tree views, list items, etc.
RECORDABLE_CONTROLS = {
    "MenuItem", "Button", "Edit", "TabItem",
    "CheckBox", "RadioButton", "ComboBox", "ListItem",
    "TreeItem", "Hyperlink", "DataItem", "Custom",
    "Cell", "Header", "HeaderItem", "ToolBar",
    "SplitButton", "ToggleButton", "Spinner"
}

# ─── Keyboard shortcuts to record as named actions ────────────────────────────
SHORTCUT_MAP = {
    ("ctrl", "s"):    "Save",
    ("ctrl", "z"):    "Undo",
    ("ctrl", "y"):    "Redo",
    ("ctrl", "c"):    "Copy",
    ("ctrl", "v"):    "Paste",
    ("ctrl", "x"):    "Cut",
    ("ctrl", "a"):    "Select All",
    ("ctrl", "n"):    "New",
    ("ctrl", "o"):    "Open",
    ("ctrl", "w"):    "Close Tab",
    ("ctrl", "p"):    "Print",
    ("ctrl", "f"):    "Find",
    ("ctrl", "home"): "Go to Start",
    ("ctrl", "end"):  "Go to End",
    ("alt", "f4"):    "Close Window",
    ("alt", "tab"):   "Switch Window",
    ("f1",):          "Help",
    ("f2",):          "Rename / Edit Cell",
    ("f5",):          "Refresh / Go To",
    ("f12",):         "Save As",
    ("delete",):      "Delete",
    ("escape",):      "Escape / Cancel",
}

# Shift map for producing correct characters
SHIFT_MAP = {
    "1":"!", "2":"@", "3":"#", "4":"$", "5":"%",
    "6":"^", "7":"&", "8":"*", "9":"(", "0":")",
    "`":"~", "-":"_", "=":"+", "[":"{", "]":"}",
    "\\":"|", ";":":", "'":'"', ",":"<", ".":">", "/":"?",
}


class DesktopRecorder:

    def __init__(self, screenshot_folder="recorded_steps"):
        self.actions        = []
        self._lock          = threading.Lock()          # thread-safe action list
        self.is_recording   = False
        self.text_buffer    = ""
        self.step           = 1
        self.screenshot_folder = screenshot_folder
        self._last_action_key  = None                   # for duplicate suppression
        self._last_action_ts   = 0.0
        self._lookup_queue     = queue.Queue()          # async UIA lookups
        self._lookup_thread    = None

        # Track currently pressed modifier keys
        self._pressed = set()

        os.makedirs(self.screenshot_folder, exist_ok=True)

    # ─── Active window info ───────────────────────────────────────────────────
    def get_active_app(self):
        """Returns (process_name, window_title) for the foreground window."""
        try:
            hwnd  = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc  = psutil.Process(pid)
            return proc.name(), title or "Unknown Window"
        except Exception:
            return "UnknownApp", "Unknown Window"

    # ─── Screenshot ───────────────────────────────────────────────────────────
    def capture_screenshot(self):
        ts       = datetime.now().strftime("%H%M%S_%f")[:9]
        filename = os.path.join(
            self.screenshot_folder, f"step_{self.step:03}_{ts}.png"
        )
        with mss.mss() as sct:
            img = sct.grab(sct.monitors[1])
            mss.tools.to_png(img.rgb, img.size, output=filename)
        return filename

    # ─── Duplicate suppression ────────────────────────────────────────────────
    def _is_duplicate(self, key):
        now = time.time()
        if key == self._last_action_key and (now - self._last_action_ts) < 0.3:
            return True
        self._last_action_key = key
        self._last_action_ts  = now
        return False

    # ─── Append action thread-safely ─────────────────────────────────────────
    def _append(self, action_str, screenshot=True):
        if self._is_duplicate(action_str):
            return
        with self._lock:
            self.actions.append(action_str)
            print(f"  Captured: {action_str}")
        if screenshot:
            self.capture_screenshot()
        self.step += 1

    # ─── Flush accumulated typed text ─────────────────────────────────────────
    def flush_text(self):
        text = self.text_buffer.strip()
        self.text_buffer = ""
        if not text:
            return
        app, title = self.get_active_app()
        self._append(f'TYPE_TEXT app="{app}" window="{title}" text="{text}"')

    # ─── Keyboard handler ─────────────────────────────────────────────────────
    def handle_key(self, event):
        if not self.is_recording:
            return
        if event.event_type == "up":
            self._pressed.discard(event.name.lower())
            return

        # event_type == "down"
        key = event.name.lower()
        self._pressed.add(key)

        # ── Check for named shortcuts first ───────────────────────────────────
        pressed = frozenset(self._pressed)
        for combo, label in SHORTCUT_MAP.items():
            if frozenset(combo) == pressed:
                self.flush_text()
                app, title = self.get_active_app()
                combo_str = "+".join(k.capitalize() for k in combo)
                self._append(
                    f'SHORTCUT app="{app}" window="{title}" '
                    f'keys="{combo_str}" action="{label}"'
                )
                return

        # ── Special non-printable keys ────────────────────────────────────────
        if key == "enter":
            self.flush_text()
            app, title = self.get_active_app()
            self._append(f'KEY_PRESS app="{app}" window="{title}" key="Enter"',
                         screenshot=False)
            return

        if key == "tab":
            self.flush_text()
            return

        if key == "backspace":
            # Remove last character from buffer (correct text capture)
            if self.text_buffer:
                self.text_buffer = self.text_buffer[:-1]
            return

        if key in ("left", "right", "up", "down", "home", "end",
                   "page up", "page down"):
            # Navigation keys — flush current text, don't add to buffer
            self.flush_text()
            return

        if key in ("shift", "ctrl", "alt", "caps lock", "win",
                   "left shift", "right shift", "left ctrl", "right ctrl",
                   "left alt", "right alt"):
            # Pure modifier — don't record alone
            return

        # ── Printable character ───────────────────────────────────────────────
        shift_held = "shift" in self._pressed or \
                     "left shift" in self._pressed or \
                     "right shift" in self._pressed

        if len(key) == 1:
            if shift_held:
                # Produce correct shifted character
                char = SHIFT_MAP.get(key, key.upper())
            else:
                char = key
            self.text_buffer += char

        elif key == "space":
            self.text_buffer += " "

    # ─── Mouse click handler (resolved on UP for stable UIA state) ────────────
    def handle_click(self, button="left"):
        if not self.is_recording:
            return

        self.flush_text()
        x, y = mouse.get_position()

        # FIX: put UIA lookup on a background thread so the mouse hook
        # doesn't block. The lookup can take 200–800ms on complex UIs.
        self._lookup_queue.put((x, y, button, time.time()))

    # ─── Background UIA lookup thread ─────────────────────────────────────────
    def _uia_lookup_worker(self):
        """
        Processes click events asynchronously.
        Resolves element info without blocking the mouse hook.
        """
        while self.is_recording or not self._lookup_queue.empty():
            try:
                x, y, button, ts = self._lookup_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            # Small delay so element activates before UIA query
            elapsed = time.time() - ts
            if elapsed < 0.15:
                time.sleep(0.15 - elapsed)

            app_name, win_title = self.get_active_app()

            try:
                element = Desktop(backend="uia").from_point(x, y)
                target  = self._find_recordable(element)

                if target:
                    name    = (target.element_info.name or "").strip()
                    control = target.element_info.control_type
                    menu    = self._build_menu_path(target)

                    if menu:
                        action = (f'MENU_CLICK app="{app_name}" '
                                  f'window="{win_title}" path="{menu}"')
                    elif control == "Button":
                        action = (f'CLICK_BUTTON app="{app_name}" '
                                  f'window="{win_title}" name="{name}"')
                    elif control in ("Edit", "Cell", "DataItem"):
                        verb = "RIGHT_CLICK_FIELD" if button == "right" else "CLICK_FIELD"
                        action = (f'{verb} app="{app_name}" '
                                  f'window="{win_title}" name="{name}"')
                    elif control == "CheckBox":
                        action = (f'TOGGLE_CHECKBOX app="{app_name}" '
                                  f'window="{win_title}" name="{name}"')
                    elif control == "ComboBox":
                        action = (f'OPEN_DROPDOWN app="{app_name}" '
                                  f'window="{win_title}" name="{name}"')
                    elif control == "ListItem":
                        action = (f'SELECT_ITEM app="{app_name}" '
                                  f'window="{win_title}" name="{name}"')
                    elif control == "TabItem":
                        action = (f'SELECT_TAB app="{app_name}" '
                                  f'window="{win_title}" name="{name}"')
                    else:
                        verb = "RIGHT_CLICK" if button == "right" else "CLICK"
                        action = (f'{verb} app="{app_name}" '
                                  f'window="{win_title}" '
                                  f'name="{name}" type="{control}"')

                else:
                    # No UIA element found — record coordinates as fallback
                    verb = "RIGHT_CLICK" if button == "right" else "CLICK"
                    action = (f'{verb} app="{app_name}" '
                              f'window="{win_title}" coords="({x},{y})"')

            except Exception as e:
                print(f"  UIA lookup failed: {e}")
                verb = "RIGHT_CLICK" if button == "right" else "CLICK"
                action = (f'{verb} app="{app_name}" '
                          f'window="{win_title}" coords="({x},{y})"')

            self._append(action)

    # ─── Find first recordable ancestor ──────────────────────────────────────
    def _find_recordable(self, element):
        current = element
        depth   = 0
        while current and depth < 10:
            try:
                ctrl = current.element_info.control_type
                if ctrl in RECORDABLE_CONTROLS:
                    return current
                current = current.parent()
                depth  += 1
            except Exception:
                break
        return None

    # ─── Build menu path for MenuItem chains ─────────────────────────────────
    def _build_menu_path(self, element):
        names   = []
        current = element
        depth   = 0
        while current and depth < 8:
            try:
                name = current.element_info.name
                ctrl = current.element_info.control_type
                if ctrl == "MenuItem" and name:
                    names.append(name)
                current = current.parent()
                depth  += 1
            except Exception:
                break
        if names:
            names.reverse()
            return " -> ".join(names)
        return None

    # ─── Scroll handler ───────────────────────────────────────────────────────
    def handle_scroll(self, event):
        if not self.is_recording:
            return
        direction = "down" if event.delta < 0 else "up"
        app, title = self.get_active_app()
        self._append(
            f'SCROLL app="{app}" window="{title}" direction="{direction}"',
            screenshot=False
        )

    # ─── Start recording ──────────────────────────────────────────────────────
    def start(self):
        print("  IQEA Desktop Recorder started...")
        self.is_recording  = True
        self._pressed      = set()
        self.text_buffer   = ""
        self.actions       = []
        self.step          = 1

        # Start background UIA lookup thread
        self._lookup_thread = threading.Thread(
            target=self._uia_lookup_worker, daemon=True
        )
        self._lookup_thread.start()

        # Hook mouse — left click on UP (stable UIA state), right click on UP
        mouse.on_button(
            lambda: self.handle_click("left"),
            buttons=("left",), types=("up",)
        )
        mouse.on_button(
            lambda: self.handle_click("right"),
            buttons=("right",), types=("up",)
        )
        mouse.on_button(
            self.handle_scroll,
            buttons=("middle",), types=("down",)
        )
        # Scroll wheel
        try:
            mouse.hook(self._mouse_hook)
        except Exception:
            pass

        keyboard.hook(self.handle_key)

    def _mouse_hook(self, event):
        """Catches WheelEvent for scroll recording."""
        if not self.is_recording:
            return
        if hasattr(event, "delta") and event.delta != 0:
            self.handle_scroll(event)

    # ─── Stop recording ───────────────────────────────────────────────────────
    def stop(self):
        print("  IQEA Desktop Recorder stopped.")
        self.flush_text()
        self.is_recording = False

        mouse.unhook_all()
        keyboard.unhook_all()

        # Wait for any pending UIA lookups to finish (max 3s)
        if self._lookup_thread and self._lookup_thread.is_alive():
            self._lookup_thread.join(timeout=3)

    # ─── Save workflow ────────────────────────────────────────────────────────
    def save(self, filename):
        """Save recorded actions to a numbered text file."""
        with self._lock:
            actions_copy = list(self.actions)

        # with open(filename, "w", encoding="utf-8") as f:
        #     for i, action in enumerate(actions_copy, start=1):
        #         f.write(f"STEP {i}: {action}\n")
        #
        # print(f"  Saved {len(actions_copy)} actions to {filename}")
        return actions_copy

    # ─── Get actions as list (for Streamlit / AI consumption) ────────────────
    def get_actions(self) -> list:
        with self._lock:
            return list(self.actions)
