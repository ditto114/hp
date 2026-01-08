import tkinter as tk
from tkinter import ttk
import random
import time

import pyautogui

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

        self.status_var = tk.StringVar(value="영역과 픽셀을 선택하세요.")
        self.color_var = tk.StringVar(value="선택된 색상: 없음")
        self.hp_pixel_var = tk.StringVar(value="hp픽셀: 0")
        self.health_percent_var = tk.StringVar(value="체력 %: 0")
        self.current_health_var = tk.StringVar(value="현재 체력: 0")
        self.max_health_var = tk.StringVar(value="100")
        self.color_input_var = tk.StringVar(value="#")
        self.warning_threshold_var = tk.StringVar(value="30")
        self.warning_state_var = tk.StringVar(value="경고 상태: 정상")
        self.warning_duration_var = tk.StringVar(value="경고 지속시간: 0.00초")
        self.warning_trigger_duration_var = tk.StringVar(value="2.0")
        self.warning_shortcut_var = tk.StringVar(value="")
        self.warning_action_triggered = False
        self.warning_key_job = None

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

        max_health_label = ttk.Label(main_frame, text="최대 체력:")
        max_health_label.grid(row=5, column=0, sticky="w", pady=(8, 0))

        max_health_entry = ttk.Entry(main_frame, textvariable=self.max_health_var, width=10)
        max_health_entry.grid(row=5, column=1, sticky="w", padx=(8, 0))

        warning_threshold_label = ttk.Label(main_frame, text="체력 경고 %:")
        warning_threshold_label.grid(row=6, column=0, sticky="w", pady=(8, 0))

        warning_threshold_entry = ttk.Entry(main_frame, textvariable=self.warning_threshold_var, width=10)
        warning_threshold_entry.grid(row=6, column=1, sticky="w", padx=(8, 0))

        warning_trigger_duration_label = ttk.Label(main_frame, text="경고 지속 후 동작(초):")
        warning_trigger_duration_label.grid(row=7, column=0, sticky="w", pady=(8, 0))

        warning_trigger_duration_entry = ttk.Entry(
            main_frame,
            textvariable=self.warning_trigger_duration_var,
            width=10
        )
        warning_trigger_duration_entry.grid(row=7, column=1, sticky="w", padx=(8, 0))

        warning_shortcut_label = ttk.Label(main_frame, text="경고 단축키(+로 구분):")
        warning_shortcut_label.grid(row=8, column=0, sticky="w", pady=(8, 0))

        warning_shortcut_entry = ttk.Entry(main_frame, textvariable=self.warning_shortcut_var, width=18)
        warning_shortcut_entry.grid(row=8, column=1, sticky="w", padx=(8, 0))

        current_health_label = ttk.Label(main_frame, textvariable=self.current_health_var)
        current_health_label.grid(row=9, column=0, sticky="w", pady=(4, 0))

        self.health_percent_label = ttk.Label(
            main_frame,
            textvariable=self.health_percent_var,
            font=("Segoe UI", 12, "bold")
        )
        self.health_percent_label.grid(row=10, column=0, sticky="w", pady=(12, 0))

        self.warning_state_label = ttk.Label(main_frame, textvariable=self.warning_state_var)
        self.warning_state_label.grid(row=11, column=0, sticky="w", pady=(4, 0))

        warning_duration_label = ttk.Label(main_frame, textvariable=self.warning_duration_var)
        warning_duration_label.grid(row=12, column=0, sticky="w", pady=(4, 0))

        self.max_health_var.trace_add("write", self.on_max_health_change)
        self.warning_threshold_var.trace_add("write", self.on_warning_threshold_change)

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

    def on_max_health_change(self, *args):
        self.update_health_display()

    def on_warning_threshold_change(self, *args):
        self.update_health_display()

    def parse_warning_threshold(self):
        value = self.warning_threshold_var.get().strip()
        try:
            threshold = int(value)
        except ValueError:
            return 0
        return max(0, min(99, threshold))

    def parse_warning_trigger_duration(self):
        value = self.warning_trigger_duration_var.get().strip()
        try:
            duration = float(value)
        except ValueError:
            return 0.0
        return max(0.0, duration)

    def parse_warning_shortcut(self):
        raw_value = self.warning_shortcut_var.get().strip()
        if not raw_value:
            return []
        keys = [key.strip().lower() for key in raw_value.split("+") if key.strip()]
        return keys

    def schedule_warning_shortcut(self, keys):
        if not keys or self.warning_action_triggered:
            return
        self.warning_action_triggered = True
        delay_ms = random.randint(0, 200)
        self.warning_key_job = self.root.after(
            delay_ms,
            lambda: self.send_warning_shortcut(keys)
        )

    def send_warning_shortcut(self, keys):
        self.warning_key_job = None
        if not keys:
            return
        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)

    def update_warning_state(self, health_percent):
        threshold = self.parse_warning_threshold()
        if health_percent < threshold:
            if self.warning_start_time is None:
                self.warning_start_time = time.monotonic()
                self.warning_action_triggered = False
            elapsed = time.monotonic() - self.warning_start_time
            elapsed = round(elapsed / 0.25) * 0.25
            self.warning_state_var.set("경고 상태: 경고")
            self.warning_duration_var.set(f"경고 지속시간: {elapsed:.2f}초")
            self.health_percent_label.configure(style="Warning.TLabel")
            self.warning_state_label.configure(style="Warning.TLabel")
            trigger_duration = self.parse_warning_trigger_duration()
            if not self.warning_action_triggered and elapsed >= trigger_duration:
                keys = self.parse_warning_shortcut()
                self.schedule_warning_shortcut(keys)
        else:
            self.warning_start_time = None
            if self.warning_key_job is not None:
                self.root.after_cancel(self.warning_key_job)
                self.warning_key_job = None
            self.warning_action_triggered = False
            self.warning_state_var.set("경고 상태: 정상")
            self.warning_duration_var.set("경고 지속시간: 0.00초")
            self.health_percent_label.configure(style="TLabel")
            self.warning_state_label.configure(style="TLabel")

    def start_updates(self):
        if self.update_job is not None:
            self.root.after_cancel(self.update_job)
        self.update_job = self.root.after(250, self.update_ratio)

    def update_health_display(self):
        health_percent = (100 / 82) * ((self.hp_pixels / 2) + 3)
        rounded_percent = int(health_percent + 0.5)
        self.health_percent_var.set(f"체력 %: {rounded_percent}")
        try:
            max_health = float(self.max_health_var.get())
        except ValueError:
            max_health = 0
        current_health = round(max_health * (health_percent / 100))
        self.current_health_var.set(f"현재 체력: {current_health}")
        self.update_warning_state(rounded_percent)

    def update_ratio(self):
        if self.region is None:
            self.update_job = self.root.after(250, self.update_ratio)
            return

        from PIL import ImageGrab

        image = ImageGrab.grab(bbox=self.region)
        if self.selected_color is None:
            self.hp_pixels = 0
            self.hp_pixel_var.set("hp픽셀: 0")
            self.update_health_display()
            self.update_job = self.root.after(250, self.update_ratio)
            return

        pixels = list(image.getdata())
        match_count = 0
        for pixel in pixels:
            if normalize_pixel(pixel) == self.selected_color:
                match_count += 1

        self.hp_pixels = match_count
        self.hp_pixel_var.set(f"hp픽셀: {match_count}")
        self.update_health_display()
        self.update_job = self.root.after(250, self.update_ratio)


if __name__ == "__main__":
    root = tk.Tk()
    app = RegionRatioApp(root)
    root.mainloop()
