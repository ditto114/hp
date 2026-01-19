import json
import os
import tkinter as tk
from tkinter import ttk
import random
import time

import pyautogui
from pynput import keyboard

def normalize_pixel(pixel):
    return tuple(pixel[:3])


class RegionRatioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("색상 비율 측정기")
        self.region = None
        self.update_job = None
        self.selected_color = None
        self.hp_pixels = 0
        self.warning_start_time = None
        self.keyboard_listener = None
        self.key_timers = []
        self.timer_capture_window = None
        self.settings_path = os.path.join(os.path.dirname(__file__), "settings.json")

        self.status_var = tk.StringVar(value="영역과 픽셀을 선택하세요.")
        self.color_var = tk.StringVar(value="선택된 색상: 없음")
        self.hp_pixel_var = tk.StringVar(value="hp픽셀: 0")
        self.color_input_var = tk.StringVar(value="#")
        self.warning_threshold_var = tk.StringVar(value="30")
        self.warning_state_var = tk.StringVar(value="경고 상태: 정상")
        self.warning_duration_var = tk.StringVar(value="경고 지속시간: 0.00초")
        self.timer_key_var = tk.StringVar(value="")
        self.timer_seconds_var = tk.StringVar(value="5")
        self.keydown_shortcut_var = tk.StringVar(value="")
        self.keydown_key_primary_var = tk.StringVar(value="")
        self.keydown_key_secondary_var = tk.StringVar(value="")
        self.keydown_delay_min_var = tk.StringVar(value="0.1")
        self.keydown_delay_max_var = tk.StringVar(value="0.3")
        self.keydown_warning_reenable_var = tk.StringVar(value="5")
        self.keydown_state_var = tk.StringVar(value="키다운 상태: OFF")
        self.keydown_active = False
        self.keydown_shortcut_active = False
        self.pressed_keys = set()
        self.keydown_warning_triggered = False
        self.keydown_warning_job = None
        self.keydown_second_job = None
        self.keydown_second_pressed = False
        self.keydown_warning_restore = False
        self.overlay_enabled_var = tk.BooleanVar(value=False)
        self.overlay_window = None
        self.overlay_bg_window = None
        self.overlay_container = None
        self.overlay_drag_offset = {"x": 0, "y": 0}
        self.default_timer = None
        self.overlay_transparent_color = "#ff00ff"

        main_frame = ttk.Frame(root, padding=16)
        main_frame.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        style = ttk.Style(root)
        style.configure("Warning.TLabel", foreground="red")

        select_button = ttk.Button(main_frame, text="영역 선택", command=self.open_selector)
        select_button.grid(row=0, column=0, sticky="w")

        pixel_button = ttk.Button(main_frame, text="픽셀 선택", command=self.open_pixel_selector)
        pixel_button.grid(row=0, column=1, sticky="w", padx=(8, 0))

        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, sticky="w", pady=(12, 0))

        color_label = ttk.Label(main_frame, textvariable=self.color_var)
        color_label.grid(row=2, column=0, sticky="w", pady=(8, 0))

        color_input_label = ttk.Label(main_frame, text="색상 코드 입력(#RRGGBB):")
        color_input_label.grid(row=3, column=0, sticky="w", pady=(8, 0))

        color_input_entry = ttk.Entry(main_frame, textvariable=self.color_input_var, width=12)
        color_input_entry.grid(row=3, column=1, sticky="w", padx=(8, 0))

        color_input_button = ttk.Button(main_frame, text="적용", command=self.apply_color_input)
        color_input_button.grid(row=3, column=2, sticky="w", padx=(8, 0))

        hp_pixel_label = ttk.Label(main_frame, textvariable=self.hp_pixel_var, font=("Segoe UI", 14, "bold"))
        hp_pixel_label.grid(row=4, column=0, sticky="w", pady=(8, 0))

        warning_title = ttk.Label(main_frame, text="체력 경고", font=("Segoe UI", 12, "bold"))
        warning_title.grid(row=5, column=0, sticky="w", pady=(8, 0))

        warning_threshold_label = ttk.Label(main_frame, text="체력 경고 %:")
        warning_threshold_label.grid(row=6, column=0, sticky="w", pady=(8, 0))

        warning_threshold_entry = ttk.Entry(main_frame, textvariable=self.warning_threshold_var, width=10)
        warning_threshold_entry.grid(row=6, column=1, sticky="w", padx=(8, 0))

        self.warning_state_label = ttk.Label(main_frame, textvariable=self.warning_state_var)
        self.warning_state_label.grid(row=7, column=0, sticky="w", pady=(4, 0))

        warning_duration_label = ttk.Label(main_frame, textvariable=self.warning_duration_var)
        warning_duration_label.grid(row=8, column=0, sticky="w", pady=(4, 0))

        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.grid(row=9, column=0, columnspan=3, sticky="ew", pady=12)

        keydown_title = ttk.Label(main_frame, text="키다운 토글", font=("Segoe UI", 12, "bold"))
        keydown_title.grid(row=10, column=0, sticky="w")

        keydown_shortcut_label = ttk.Label(main_frame, text="단축키(+로 구분):")
        keydown_shortcut_label.grid(row=11, column=0, sticky="w", pady=(8, 0))

        keydown_shortcut_entry = ttk.Entry(
            main_frame,
            textvariable=self.keydown_shortcut_var,
            width=18,
            state="readonly"
        )
        keydown_shortcut_entry.grid(row=11, column=1, sticky="w", padx=(8, 0))

        keydown_shortcut_button = ttk.Button(
            main_frame,
            text="키 입력",
            command=self.capture_keydown_shortcut
        )
        keydown_shortcut_button.grid(row=11, column=2, sticky="w", padx=(8, 0))

        keydown_key_primary_label = ttk.Label(main_frame, text="키다운 키 1:")
        keydown_key_primary_label.grid(row=12, column=0, sticky="w", pady=(8, 0))

        keydown_key_primary_entry = ttk.Entry(
            main_frame,
            textvariable=self.keydown_key_primary_var,
            width=12,
            state="readonly"
        )
        keydown_key_primary_entry.grid(row=12, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        keydown_key_primary_button = ttk.Button(
            main_frame,
            text="키 입력",
            command=self.capture_keydown_key_primary
        )
        keydown_key_primary_button.grid(row=12, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

        keydown_key_secondary_label = ttk.Label(main_frame, text="키다운 키 2:")
        keydown_key_secondary_label.grid(row=13, column=0, sticky="w", pady=(8, 0))

        keydown_key_secondary_entry = ttk.Entry(
            main_frame,
            textvariable=self.keydown_key_secondary_var,
            width=12,
            state="readonly"
        )
        keydown_key_secondary_entry.grid(row=13, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        keydown_key_secondary_button = ttk.Button(
            main_frame,
            text="키 입력",
            command=self.capture_keydown_key_secondary
        )
        keydown_key_secondary_button.grid(row=13, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

        keydown_delay_label = ttk.Label(main_frame, text="랜덤 딜레이(초) 최소/최대:")
        keydown_delay_label.grid(row=14, column=0, sticky="w", pady=(8, 0))

        keydown_delay_min_entry = ttk.Entry(main_frame, textvariable=self.keydown_delay_min_var, width=6)
        keydown_delay_min_entry.grid(row=14, column=1, sticky="w", padx=(8, 0))

        keydown_delay_max_entry = ttk.Entry(main_frame, textvariable=self.keydown_delay_max_var, width=6)
        keydown_delay_max_entry.grid(row=14, column=2, sticky="w", padx=(8, 0))

        keydown_state_label = ttk.Label(main_frame, textvariable=self.keydown_state_var)
        keydown_state_label.grid(row=15, column=0, sticky="w", pady=(8, 0))

        keydown_warning_reenable_label = ttk.Label(main_frame, text="경고 후 토글 복귀 시간(초):")
        keydown_warning_reenable_label.grid(row=16, column=0, sticky="w", pady=(8, 0))

        keydown_warning_reenable_entry = ttk.Entry(
            main_frame,
            textvariable=self.keydown_warning_reenable_var,
            width=10
        )
        keydown_warning_reenable_entry.grid(row=16, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.grid(row=17, column=0, columnspan=3, sticky="ew", pady=12)

        timer_title = ttk.Label(main_frame, text="키 타이머", font=("Segoe UI", 12, "bold"))
        timer_title.grid(row=18, column=0, sticky="w")

        timer_key_label = ttk.Label(main_frame, text="키 입력:")
        timer_key_label.grid(row=19, column=0, sticky="w", pady=(8, 0))

        timer_key_entry = ttk.Entry(main_frame, textvariable=self.timer_key_var, width=12, state="readonly")
        timer_key_entry.grid(row=19, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        timer_key_button = ttk.Button(main_frame, text="키 입력", command=self.capture_timer_key)
        timer_key_button.grid(row=19, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

        timer_seconds_label = ttk.Label(main_frame, text="시간(초):")
        timer_seconds_label.grid(row=20, column=0, sticky="w", pady=(8, 0))

        timer_seconds_entry = ttk.Entry(main_frame, textvariable=self.timer_seconds_var, width=10)
        timer_seconds_entry.grid(row=20, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        timer_add_button = ttk.Button(main_frame, text="타이머 추가", command=self.add_key_timer)
        timer_add_button.grid(row=20, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

        timer_overlay_check = ttk.Checkbutton(
            main_frame,
            text="타이머 오버레이 표시",
            variable=self.overlay_enabled_var,
            command=self.toggle_timer_overlay
        )
        timer_overlay_check.grid(row=21, column=0, sticky="w", pady=(8, 0))

        self.timer_list_frame = ttk.Frame(main_frame)
        self.timer_list_frame.grid(row=22, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        self.initialize_default_timer()

        self.warning_threshold_var.trace_add("write", self.on_warning_threshold_change)
        self.timer_seconds_var.trace_add("write", self.on_timer_seconds_change)
        self.keydown_shortcut_var.trace_add("write", self.on_keydown_shortcut_change)
        self.keydown_key_primary_var.trace_add("write", self.on_keydown_key_change)
        self.keydown_key_secondary_var.trace_add("write", self.on_keydown_key_change)
        self.keydown_delay_min_var.trace_add("write", self.on_keydown_delay_change)
        self.keydown_delay_max_var.trace_add("write", self.on_keydown_delay_change)
        self.keydown_warning_reenable_var.trace_add("write", self.on_keydown_warning_reenable_change)
        self.overlay_enabled_var.trace_add("write", self.on_overlay_enabled_change)

        self.load_settings()
        self.start_keyboard_listener()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def open_selector(self):
        selector, canvas = self.create_selector_window(cursor="cross")

        start = {"x": 0, "y": 0}
        rect_id = {"id": None}

        def on_press(event):
            start["x"] = event.x
            start["y"] = event.y
            if rect_id["id"] is not None:
                canvas.delete(rect_id["id"])
                rect_id["id"] = None

        def on_drag(event):
            if rect_id["id"] is not None:
                canvas.delete(rect_id["id"])
            rect_id["id"] = canvas.create_rectangle(
                start["x"], start["y"], event.x, event.y,
                outline="red", width=2
            )

        def on_release(event):
            x1 = min(start["x"], event.x)
            y1 = min(start["y"], event.y)
            x2 = max(start["x"], event.x)
            y2 = max(start["y"], event.y)
            if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
                self.status_var.set("선택한 영역이 너무 작습니다.")
            else:
                offset_x = selector.winfo_rootx()
                offset_y = selector.winfo_rooty()
                self.region = (x1 + offset_x, y1 + offset_y, x2 + offset_x, y2 + offset_y)
                self.status_var.set("선택된 영역에서 색상 픽셀 수를 측정 중입니다.")
                self.start_updates()
                self.save_settings()
            selector.grab_release()
            selector.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)

    def open_pixel_selector(self):
        selector, canvas = self.create_selector_window(cursor="tcross")

        def on_click(event):
            from PIL import ImageGrab

            offset_x = selector.winfo_rootx()
            offset_y = selector.winfo_rooty()
            screen_x = event.x + offset_x
            screen_y = event.y + offset_y
            selector.withdraw()

            def capture_pixel():
                pixel = ImageGrab.grab(
                    bbox=(screen_x, screen_y, screen_x + 1, screen_y + 1)
                ).getpixel((0, 0))
                self.selected_color = normalize_pixel(pixel)
                color_hex = "#%02X%02X%02X" % self.selected_color
                self.color_var.set(f"선택된 색상: {color_hex}")
                self.status_var.set("선택된 색상 픽셀 수를 측정 중입니다.")
                self.start_updates()
                self.save_settings()
                selector.grab_release()
                selector.destroy()

            selector.after(10, capture_pixel)

        canvas.bind("<ButtonPress-1>", on_click)

    def create_selector_window(self, cursor):
        selector = tk.Toplevel(self.root)
        selector.attributes("-fullscreen", True)
        selector.attributes("-topmost", True)
        selector.attributes("-alpha", 0.01)
        selector.grab_set()

        selector.configure(background="black")
        canvas = tk.Canvas(selector, cursor=cursor, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        return selector, canvas

    def parse_color_input(self, value):
        value = value.strip()
        if not value:
            return None
        if value.startswith("#"):
            value = value[1:]
        if len(value) != 6:
            return None
        try:
            return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return None

    def apply_color_input(self):
        color = self.parse_color_input(self.color_input_var.get())
        if color is None:
            self.status_var.set("색상 코드를 다시 확인하세요.")
            return
        self.selected_color = normalize_pixel(color)
        color_hex = "#%02X%02X%02X" % self.selected_color
        self.color_var.set(f"선택된 색상: {color_hex}")
        self.status_var.set("선택된 색상 픽셀 수를 측정 중입니다.")
        self.start_updates()
        self.save_settings()

    def on_warning_threshold_change(self, *args):
        self.update_health_display()
        self.save_settings()

    def on_timer_seconds_change(self, *args):
        self.save_settings()

    def on_keydown_shortcut_change(self, *args):
        self.save_settings()

    def on_keydown_key_change(self, *args):
        self.save_settings()

    def on_keydown_delay_change(self, *args):
        self.save_settings()

    def on_keydown_warning_reenable_change(self, *args):
        self.save_settings()

    def on_overlay_enabled_change(self, *args):
        self.save_settings()

    def parse_warning_threshold(self):
        value = self.warning_threshold_var.get().strip()
        try:
            threshold = int(value)
        except ValueError:
            return 0
        return max(0, min(99, threshold))

    def parse_keydown_shortcut(self):
        raw_value = self.keydown_shortcut_var.get().strip()
        if not raw_value:
            return []
        keys = [key.strip().lower() for key in raw_value.split("+") if key.strip()]
        return keys

    def parse_keydown_keys(self):
        primary = self.keydown_key_primary_var.get().strip().lower()
        secondary = self.keydown_key_secondary_var.get().strip().lower()
        return [key for key in (primary, secondary) if key]

    def parse_keydown_delay_range(self):
        try:
            min_delay = float(self.keydown_delay_min_var.get().strip())
        except ValueError:
            min_delay = 0.0
        try:
            max_delay = float(self.keydown_delay_max_var.get().strip())
        except ValueError:
            max_delay = 0.0
        min_delay = max(0.0, min_delay)
        max_delay = max(0.0, max_delay)
        if max_delay < min_delay:
            min_delay, max_delay = max_delay, min_delay
        return min_delay, max_delay

    def parse_keydown_warning_reenable(self):
        value = self.keydown_warning_reenable_var.get().strip()
        try:
            duration = float(value)
        except ValueError:
            return 0.0
        return max(0.0, duration)

    def format_shortcut_from_event(self, event):
        modifier_keys = {
            "shift_l", "shift_r",
            "control_l", "control_r",
            "alt_l", "alt_r",
            "meta_l", "meta_r",
            "super_l", "super_r"
        }
        modifiers = []
        if event.state & 0x0004:
            modifiers.append("ctrl")
        if event.state & 0x0001:
            modifiers.append("shift")
        if event.state & 0x0008:
            modifiers.append("alt")

        keysym = event.keysym.lower()
        if keysym in modifier_keys:
            return None
        modifiers.append(keysym)
        return "+".join(modifiers)

    def capture_timer_key(self):
        if self.timer_capture_window is not None:
            self.timer_capture_window.lift()
            return

        self.timer_capture_window = tk.Toplevel(self.root)
        self.timer_capture_window.title("키 입력")
        self.timer_capture_window.attributes("-topmost", True)
        message = ttk.Label(self.timer_capture_window, text="타이머로 사용할 키를 누르세요.", padding=16)
        message.pack()

        def on_key(event):
            key_name = self.normalize_tk_key(event.keysym)
            if key_name:
                self.timer_key_var.set(key_name)
                self.timer_capture_window.destroy()
                self.timer_capture_window = None

        def on_close():
            self.timer_capture_window.destroy()
            self.timer_capture_window = None

        self.timer_capture_window.bind("<KeyPress>", on_key)
        self.timer_capture_window.protocol("WM_DELETE_WINDOW", on_close)
        self.timer_capture_window.focus_set()

    def capture_keydown_shortcut(self):
        if hasattr(self, "keydown_shortcut_capture_window") and self.keydown_shortcut_capture_window is not None:
            self.keydown_shortcut_capture_window.lift()
            return

        self.keydown_shortcut_capture_window = tk.Toplevel(self.root)
        self.keydown_shortcut_capture_window.title("단축키 입력")
        self.keydown_shortcut_capture_window.attributes("-topmost", True)
        message = ttk.Label(
            self.keydown_shortcut_capture_window,
            text="원하는 단축키를 누르세요.",
            padding=16
        )
        message.pack()

        def on_key(event):
            shortcut = self.format_shortcut_from_event(event)
            if shortcut:
                self.keydown_shortcut_var.set(shortcut)
                self.keydown_shortcut_capture_window.destroy()
                self.keydown_shortcut_capture_window = None

        def on_close():
            self.keydown_shortcut_capture_window.destroy()
            self.keydown_shortcut_capture_window = None

        self.keydown_shortcut_capture_window.bind("<KeyPress>", on_key)
        self.keydown_shortcut_capture_window.protocol("WM_DELETE_WINDOW", on_close)
        self.keydown_shortcut_capture_window.focus_set()

    def capture_keydown_key_primary(self):
        self.capture_keydown_key(self.keydown_key_primary_var, "키다운 키 1을 누르세요.")

    def capture_keydown_key_secondary(self):
        self.capture_keydown_key(self.keydown_key_secondary_var, "키다운 키 2를 누르세요.")

    def capture_keydown_key(self, target_var, message_text):
        if hasattr(self, "keydown_key_capture_window") and self.keydown_key_capture_window is not None:
            self.keydown_key_capture_window.lift()
            return

        self.keydown_key_capture_window = tk.Toplevel(self.root)
        self.keydown_key_capture_window.title("키 입력")
        self.keydown_key_capture_window.attributes("-topmost", True)
        message = ttk.Label(self.keydown_key_capture_window, text=message_text, padding=16)
        message.pack()

        def on_key(event):
            key_name = self.normalize_tk_key(event.keysym)
            if key_name:
                target_var.set(key_name)
                self.keydown_key_capture_window.destroy()
                self.keydown_key_capture_window = None

        def on_close():
            self.keydown_key_capture_window.destroy()
            self.keydown_key_capture_window = None

        self.keydown_key_capture_window.bind("<KeyPress>", on_key)
        self.keydown_key_capture_window.protocol("WM_DELETE_WINDOW", on_close)
        self.keydown_key_capture_window.focus_set()

    def normalize_tk_key(self, keysym):
        normalized = keysym.lower()
        special_map = {
            "space": "space",
            "return": "enter",
            "escape": "esc",
            "backspace": "backspace",
            "tab": "tab",
            "delete": "delete"
        }
        return special_map.get(normalized, normalized)

    def normalize_global_key(self, key):
        if isinstance(key, keyboard.KeyCode):
            if key.char is None:
                return None
            return key.char.lower()
        if isinstance(key, keyboard.Key):
            key_name = key.name.lower()
            modifier_map = {
                "ctrl_l": "ctrl",
                "ctrl_r": "ctrl",
                "shift_l": "shift",
                "shift_r": "shift",
                "alt_l": "alt",
                "alt_r": "alt",
                "cmd": "meta",
                "cmd_l": "meta",
                "cmd_r": "meta",
                "meta_l": "meta",
                "meta_r": "meta"
            }
            return modifier_map.get(key_name, key_name)
        return None

    def start_keyboard_listener(self):
        if self.keyboard_listener is not None:
            return
        self.keyboard_listener = keyboard.Listener(
            on_press=self.handle_global_key_press,
            on_release=self.handle_global_key_release
        )
        self.keyboard_listener.daemon = True
        self.keyboard_listener.start()

    def handle_global_key_press(self, key):
        key_name = self.normalize_global_key(key)
        if not key_name:
            return
        self.pressed_keys.add(key_name)
        self.root.after(0, lambda: self.process_global_key_press(key_name))

    def handle_global_key_release(self, key):
        key_name = self.normalize_global_key(key)
        if not key_name:
            return
        if key_name in self.pressed_keys:
            self.pressed_keys.remove(key_name)
        self.root.after(0, self.reset_keydown_shortcut_state)

    def process_global_key_press(self, key_name):
        if key_name == "right":
            self.reset_default_timer()
        self.trigger_key_timer(key_name)
        self.check_keydown_shortcut_toggle()

    def check_keydown_shortcut_toggle(self):
        shortcut_keys = self.parse_keydown_shortcut()
        if not shortcut_keys:
            return
        if all(key in self.pressed_keys for key in shortcut_keys):
            if not self.keydown_shortcut_active:
                self.keydown_shortcut_active = True
                self.toggle_keydown_state()

    def reset_keydown_shortcut_state(self):
        shortcut_keys = self.parse_keydown_shortcut()
        if not shortcut_keys:
            self.keydown_shortcut_active = False
            return
        if not all(key in self.pressed_keys for key in shortcut_keys):
            self.keydown_shortcut_active = False

    def add_key_timer(self):
        key_name = self.timer_key_var.get().strip().lower()
        if not key_name:
            self.status_var.set("타이머 키를 입력하세요.")
            return
        try:
            duration = int(self.timer_seconds_var.get())
        except ValueError:
            self.status_var.set("타이머 시간을 확인하세요.")
            return
        duration = max(1, duration)

        timer = self.create_timer_row(key_name, duration)
        self.key_timers.append(timer)
        if self.overlay_enabled_var.get():
            self.add_overlay_timer_row(timer)
        self.timer_key_var.set("")
        self.save_settings()

    def create_timer_row(self, key_name, duration, locked=False):
        row_frame = ttk.Frame(self.timer_list_frame)
        row_frame.pack(fill="x", pady=4)

        label = ttk.Label(row_frame, text=f"키: {key_name} ({duration}초)")
        label.pack(side="left")

        remaining_var = tk.StringVar(value=f"남은 시간: {duration}초")
        remaining_label = ttk.Label(row_frame, textvariable=remaining_var)
        remaining_label.pack(side="left", padx=12)

        progress = ttk.Progressbar(row_frame, orient="horizontal", length=200, mode="determinate")
        progress.pack(side="left", padx=8)
        progress["maximum"] = duration
        progress["value"] = duration

        if not locked:
            delete_button = ttk.Button(row_frame, text="삭제", command=lambda: self.remove_timer_row(timer))
            delete_button.pack(side="right")

        timer = {
            "key": key_name,
            "duration": duration,
            "remaining": duration,
            "job": None,
            "frame": row_frame,
            "remaining_var": remaining_var,
            "progress": progress,
            "overlay": None,
            "locked": locked
        }
        return timer

    def remove_timer_row(self, timer):
        if timer["job"] is not None:
            self.root.after_cancel(timer["job"])
        self.remove_overlay_timer_row(timer)
        timer["frame"].destroy()
        self.key_timers = [item for item in self.key_timers if item is not timer]
        self.save_settings()

    def trigger_key_timer(self, key_name):
        for timer in self.key_timers:
            if timer["key"] == key_name:
                self.start_timer(timer)

    def initialize_default_timer(self):
        if self.default_timer is not None:
            return
        timer = self.create_timer_row("키렉", 60, locked=True)
        self.key_timers.append(timer)
        self.default_timer = timer
        self.start_timer(timer)

    def reset_default_timer(self):
        if self.default_timer is None:
            return
        self.start_timer(self.default_timer)

    def start_timer(self, timer):
        timer["remaining"] = timer["duration"]
        timer["progress"]["maximum"] = timer["duration"]
        timer["progress"]["value"] = timer["duration"]
        timer["remaining_var"].set(f"남은 시간: {timer['remaining']}초")
        self.update_overlay_timer(timer)
        if timer["job"] is not None:
            self.root.after_cancel(timer["job"])
        timer["job"] = self.root.after(1000, lambda: self.tick_timer(timer))

    def tick_timer(self, timer):
        timer["remaining"] -= 1
        if timer["remaining"] <= 0:
            timer["remaining"] = 0
            timer["progress"]["value"] = 0
            timer["remaining_var"].set("남은 시간: 0초")
            self.update_overlay_timer(timer)
            timer["job"] = None
            return
        timer["progress"]["value"] = timer["remaining"]
        timer["remaining_var"].set(f"남은 시간: {timer['remaining']}초")
        self.update_overlay_timer(timer)
        timer["job"] = self.root.after(1000, lambda: self.tick_timer(timer))

    def toggle_timer_overlay(self):
        if self.overlay_enabled_var.get():
            self.open_timer_overlay()
        else:
            self.close_timer_overlay()
        self.save_settings()

    def open_timer_overlay(self):
        if self.overlay_window is not None or self.overlay_bg_window is not None:
            return
        self.overlay_bg_window = tk.Toplevel(self.root)
        self.overlay_bg_window.title("타이머 오버레이 배경")
        self.overlay_bg_window.attributes("-topmost", True)
        self.overlay_bg_window.overrideredirect(True)
        self.overlay_bg_window.configure(background="#FFFFFF")
        self.overlay_bg_window.attributes("-alpha", 0.1)
        self.overlay_bg_window.geometry("+20+20")

        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.title("타이머 오버레이")
        self.overlay_window.attributes("-topmost", True)
        self.overlay_window.overrideredirect(True)
        self.overlay_window.configure(background=self.overlay_transparent_color)
        self.overlay_window.geometry("+20+20")
        try:
            self.overlay_window.attributes("-transparentcolor", self.overlay_transparent_color)
        except tk.TclError:
            pass

        self.overlay_container = tk.Frame(
            self.overlay_window,
            bg=self.overlay_transparent_color,
            padx=8,
            pady=8
        )
        self.overlay_container.pack(fill="both", expand=True)
        self.bind_overlay_drag(self.overlay_window)
        self.bind_overlay_drag(self.overlay_container)
        self.bind_overlay_drag(self.overlay_bg_window)

        for timer in self.key_timers:
            self.add_overlay_timer_row(timer)
        self.sync_overlay_background()
        self.overlay_bg_window.lower(self.overlay_window)

    def close_timer_overlay(self):
        if self.overlay_window is None and self.overlay_bg_window is None:
            return
        for timer in self.key_timers:
            self.remove_overlay_timer_row(timer)
        if self.overlay_window is not None:
            self.overlay_window.destroy()
            self.overlay_window = None
        if self.overlay_bg_window is not None:
            self.overlay_bg_window.destroy()
            self.overlay_bg_window = None
        self.overlay_container = None

    def add_overlay_timer_row(self, timer):
        if self.overlay_window is None or self.overlay_container is None:
            return
        if timer.get("overlay") is not None:
            return

        row_frame = tk.Frame(self.overlay_container, bg=self.overlay_transparent_color)
        row_frame.pack(fill="x", pady=4)
        row_frame.columnconfigure(1, weight=1)

        bar_width = 100
        bar_height = 20
        canvas = tk.Canvas(
            row_frame,
            width=bar_width,
            height=bar_height,
            bg="#333333",
            highlightthickness=0
        )
        canvas.grid(row=0, column=0, sticky="w", padx=(0, 8))
        bar_rect = canvas.create_rectangle(0, 0, bar_width, bar_height, fill="#4caf50", width=0)
        text_item = canvas.create_text(
            bar_width // 2,
            bar_height // 2,
            text=f"{timer['remaining']}",
            fill="white"
        )

        key_label = tk.Label(
            row_frame,
            text=f"{timer['key']}",
            bg=self.overlay_transparent_color,
            anchor="e"
        )
        key_label.grid(row=0, column=1, sticky="e")

        self.bind_overlay_drag(row_frame)
        self.bind_overlay_drag(canvas)
        self.bind_overlay_drag(key_label)

        timer["overlay"] = {
            "frame": row_frame,
            "canvas": canvas,
            "rect": bar_rect,
            "text": text_item,
            "width": bar_width,
            "height": bar_height
        }
        self.update_overlay_timer(timer)
        self.sync_overlay_background()

    def remove_overlay_timer_row(self, timer):
        overlay = timer.get("overlay")
        if overlay is None:
            return
        overlay["frame"].destroy()
        timer["overlay"] = None
        self.sync_overlay_background()

    def update_overlay_timer(self, timer):
        overlay = timer.get("overlay")
        if overlay is None:
            return
        remaining = timer["remaining"]
        max_seconds = 180
        if remaining >= max_seconds:
            fill_width = overlay["width"]
        else:
            fill_width = int(overlay["width"] * max(0, remaining) / max_seconds)
        overlay["canvas"].coords(overlay["rect"], 0, 0, fill_width, overlay["height"])
        overlay["canvas"].itemconfig(overlay["text"], text=f"{remaining}")

    def bind_overlay_drag(self, widget):
        widget.bind("<ButtonPress-1>", self.on_overlay_drag_start, add="+")
        widget.bind("<B1-Motion>", self.on_overlay_drag_motion, add="+")

    def on_overlay_drag_start(self, event):
        if self.overlay_window is None:
            return
        self.overlay_drag_offset["x"] = event.x_root - self.overlay_window.winfo_x()
        self.overlay_drag_offset["y"] = event.y_root - self.overlay_window.winfo_y()

    def on_overlay_drag_motion(self, event):
        if self.overlay_window is None:
            return
        x = event.x_root - self.overlay_drag_offset["x"]
        y = event.y_root - self.overlay_drag_offset["y"]
        self.overlay_window.geometry(f"+{x}+{y}")
        if self.overlay_bg_window is not None:
            self.overlay_bg_window.geometry(f"+{x}+{y}")

    def sync_overlay_background(self):
        if self.overlay_window is None or self.overlay_bg_window is None:
            return
        self.overlay_window.update_idletasks()
        self.overlay_bg_window.geometry(self.overlay_window.geometry())

    def load_settings(self):
        if not os.path.exists(self.settings_path):
            return
        with open(self.settings_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.warning_threshold_var.set(str(data.get("warning_threshold", self.warning_threshold_var.get())))
        self.color_input_var.set(data.get("color_input", self.color_input_var.get()))
        self.keydown_shortcut_var.set(data.get("keydown_shortcut", self.keydown_shortcut_var.get()))
        self.keydown_key_primary_var.set(data.get("keydown_key_primary", self.keydown_key_primary_var.get()))
        self.keydown_key_secondary_var.set(data.get("keydown_key_secondary", self.keydown_key_secondary_var.get()))
        self.keydown_delay_min_var.set(str(data.get("keydown_delay_min", self.keydown_delay_min_var.get())))
        self.keydown_delay_max_var.set(str(data.get("keydown_delay_max", self.keydown_delay_max_var.get())))
        self.keydown_warning_reenable_var.set(str(
            data.get("keydown_warning_reenable", self.keydown_warning_reenable_var.get())
        ))
        timer_seconds = data.get("timer_seconds", self.timer_seconds_var.get())
        self.timer_seconds_var.set(str(timer_seconds))
        self.overlay_enabled_var.set(bool(data.get("overlay_enabled", self.overlay_enabled_var.get())))

        region = data.get("region")
        if region and len(region) == 4:
            self.region = tuple(region)
            self.status_var.set("선택된 영역에서 색상 픽셀 수를 측정 중입니다.")

        color_hex = data.get("selected_color")
        if color_hex:
            color = self.parse_color_input(color_hex)
            if color is not None:
                self.selected_color = normalize_pixel(color)
                self.color_var.set(f"선택된 색상: {color_hex.upper()}")
                self.status_var.set("선택된 색상 픽셀 수를 측정 중입니다.")

        timers = data.get("key_timers", [])
        for timer in timers:
            key_name = str(timer.get("key", "")).lower()
            duration = int(timer.get("duration", 0))
            if key_name and duration > 0:
                self.key_timers.append(self.create_timer_row(key_name, duration))

        if self.overlay_enabled_var.get():
            self.open_timer_overlay()
        if self.region is not None:
            self.start_updates()

    def save_settings(self):
        settings = {
            "region": list(self.region) if self.region else None,
            "selected_color": self.color_var.get().replace("선택된 색상: ", "").strip()
            if self.selected_color else None,
            "color_input": self.color_input_var.get(),
            "warning_threshold": self.warning_threshold_var.get(),
            "keydown_shortcut": self.keydown_shortcut_var.get(),
            "keydown_key_primary": self.keydown_key_primary_var.get(),
            "keydown_key_secondary": self.keydown_key_secondary_var.get(),
            "keydown_delay_min": self.keydown_delay_min_var.get(),
            "keydown_delay_max": self.keydown_delay_max_var.get(),
            "keydown_warning_reenable": self.keydown_warning_reenable_var.get(),
            "timer_seconds": self.timer_seconds_var.get(),
            "overlay_enabled": self.overlay_enabled_var.get(),
            "key_timers": [
                {"key": timer["key"], "duration": timer["duration"]}
                for timer in self.key_timers
                if not timer.get("locked")
            ]
        }
        with open(self.settings_path, "w", encoding="utf-8") as file:
            json.dump(settings, file, ensure_ascii=False, indent=2)

    def on_close(self):
        self.cancel_keydown_jobs()
        if self.keydown_active:
            self.release_keydown_keys()
        self.save_settings()
        self.close_timer_overlay()
        if self.keyboard_listener is not None:
            self.keyboard_listener.stop()
        self.root.destroy()

    def update_warning_state(self, health_percent):
        threshold = self.parse_warning_threshold()
        if health_percent < threshold:
            if self.warning_start_time is None:
                self.warning_start_time = time.monotonic()
                self.reset_default_timer()
            elapsed = time.monotonic() - self.warning_start_time
            elapsed = round(elapsed / 0.25) * 0.25
            self.warning_state_var.set("경고 상태: 경고")
            self.warning_duration_var.set(f"경고 지속시간: {elapsed:.2f}초")
            self.warning_state_label.configure(style="Warning.TLabel")
        else:
            self.warning_start_time = None
            self.warning_state_var.set("경고 상태: 정상")
            self.warning_duration_var.set("경고 지속시간: 0.00초")
            self.warning_state_label.configure(style="TLabel")
        self.handle_keydown_warning_logic(health_percent)

    def toggle_keydown_state(self):
        keydown_keys = self.parse_keydown_keys()
        if not keydown_keys:
            self.status_var.set("키다운 키를 입력하세요.")
            return
        if self.keydown_active:
            self.set_keydown_state(False)
            self.cancel_keydown_jobs()
        else:
            self.set_keydown_state(True)
            self.reset_keydown_warning_state()

    def press_keydown_keys(self):
        keydown_keys = self.parse_keydown_keys()
        if not keydown_keys:
            return
        self.keydown_second_pressed = False
        pyautogui.keyDown(keydown_keys[0])
        if len(keydown_keys) < 2:
            return
        min_delay, max_delay = self.parse_keydown_delay_range()
        delay = random.uniform(min_delay, max_delay) if max_delay > 0 else 0.0
        if delay <= 0:
            self.press_keydown_second_key(keydown_keys[1])
            return
        self.keydown_second_job = self.root.after(
            int(delay * 1000),
            lambda: self.press_keydown_second_key(keydown_keys[1])
        )

    def press_keydown_second_key(self, key_name):
        self.keydown_second_job = None
        if not self.keydown_active:
            return
        self.keydown_second_pressed = True
        pyautogui.keyDown(key_name)

    def release_keydown_keys(self):
        keydown_keys = self.parse_keydown_keys()
        if not keydown_keys:
            return
        if len(keydown_keys) > 1:
            pyautogui.keyUp(keydown_keys[1])
        pyautogui.keyUp(keydown_keys[0])
        self.keydown_second_pressed = False

    def cancel_keydown_jobs(self):
        if self.keydown_warning_job is not None:
            self.root.after_cancel(self.keydown_warning_job)
            self.keydown_warning_job = None
        if self.keydown_second_job is not None:
            self.root.after_cancel(self.keydown_second_job)
            self.keydown_second_job = None
        self.keydown_second_pressed = False
        self.keydown_warning_restore = False

    def handle_keydown_warning_logic(self, health_percent):
        threshold = self.parse_warning_threshold()
        if health_percent < threshold:
            if not self.keydown_warning_triggered:
                self.keydown_warning_triggered = True
                self.trigger_keydown_warning_toggle()
        else:
            self.reset_keydown_warning_state()

    def reset_keydown_warning_state(self):
        self.keydown_warning_triggered = False

    def set_keydown_state(self, active):
        self.keydown_active = active
        self.keydown_state_var.set(f"키다운 상태: {'ON' if active else 'OFF'}")
        if active:
            self.press_keydown_keys()
        else:
            if self.keydown_second_job is not None:
                self.root.after_cancel(self.keydown_second_job)
                self.keydown_second_job = None
            self.release_keydown_keys()

    def trigger_keydown_warning_toggle(self):
        if self.keydown_warning_job is not None:
            return
        delay = self.parse_keydown_warning_reenable()
        self.keydown_warning_restore = self.keydown_active
        if self.keydown_active:
            self.set_keydown_state(False)
        if delay <= 0:
            self.finish_keydown_warning_toggle()
            return
        self.keydown_warning_job = self.root.after(
            int(delay * 1000),
            self.finish_keydown_warning_toggle
        )

    def finish_keydown_warning_toggle(self):
        self.keydown_warning_job = None
        if self.keydown_warning_restore and not self.keydown_active:
            self.set_keydown_state(True)
        self.keydown_warning_restore = False

    def start_updates(self):
        if self.update_job is not None:
            self.root.after_cancel(self.update_job)
        self.update_job = self.root.after(100, self.update_ratio)

    def update_health_display(self):
        health_percent = (100 / 82) * ((self.hp_pixels / 2) + 3)
        rounded_percent = int(health_percent + 0.5)
        self.update_warning_state(rounded_percent)

    def update_ratio(self):
        if self.region is None:
            self.update_job = self.root.after(100, self.update_ratio)
            return

        from PIL import ImageGrab

        image = ImageGrab.grab(bbox=self.region)
        if self.selected_color is None:
            self.hp_pixels = 0
            self.hp_pixel_var.set("hp픽셀: 0")
            self.update_health_display()
            self.update_job = self.root.after(100, self.update_ratio)
            return

        pixels = list(image.getdata())
        match_count = 0
        for pixel in pixels:
            if normalize_pixel(pixel) == self.selected_color:
                match_count += 1

        self.hp_pixels = match_count
        self.hp_pixel_var.set(f"hp픽셀: {match_count}")
        self.update_health_display()
        self.update_job = self.root.after(100, self.update_ratio)


if __name__ == "__main__":
    root = tk.Tk()
    app = RegionRatioApp(root)
    root.mainloop()
