import tkinter as tk
from tkinter import ttk


def normalize_pixel(pixel):
    return tuple(pixel[:3])


class RegionRatioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("색상 비율 측정기")
        self.region = None
        self.update_job = None
        self.selected_color = None

        self.status_var = tk.StringVar(value="영역과 픽셀을 선택하세요.")
        self.color_var = tk.StringVar(value="선택된 색상: 없음")
        self.color_count_var = tk.StringVar(value="선택한 색상 픽셀 수: 0")

        main_frame = ttk.Frame(root, padding=16)
        main_frame.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        select_button = ttk.Button(main_frame, text="영역 선택", command=self.open_selector)
        select_button.grid(row=0, column=0, sticky="w")

        pixel_button = ttk.Button(main_frame, text="픽셀 선택", command=self.open_pixel_selector)
        pixel_button.grid(row=0, column=1, sticky="w", padx=(8, 0))

        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, sticky="w", pady=(12, 0))

        color_label = ttk.Label(main_frame, textvariable=self.color_var)
        color_label.grid(row=2, column=0, sticky="w", pady=(8, 0))

        count_label = ttk.Label(main_frame, textvariable=self.color_count_var, font=("Segoe UI", 14, "bold"))
        count_label.grid(row=3, column=0, sticky="w", pady=(8, 0))

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
            pixel = ImageGrab.grab(bbox=(screen_x, screen_y, screen_x + 1, screen_y + 1)).getpixel((0, 0))
            self.selected_color = normalize_pixel(pixel)
            color_hex = "#%02X%02X%02X" % self.selected_color
            self.color_var.set(f"선택된 색상: {color_hex}")
            self.status_var.set("선택된 색상 픽셀 수를 측정 중입니다.")
            self.start_updates()
            selector.grab_release()
            selector.destroy()

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

    def start_updates(self):
        if self.update_job is not None:
            self.root.after_cancel(self.update_job)
        self.update_job = self.root.after(250, self.update_ratio)

    def update_ratio(self):
        if self.region is None:
            self.update_job = self.root.after(250, self.update_ratio)
            return

        from PIL import ImageGrab

        image = ImageGrab.grab(bbox=self.region)
        if self.selected_color is None:
            self.color_count_var.set("선택한 색상 픽셀 수: 0")
            self.update_job = self.root.after(250, self.update_ratio)
            return

        pixels = list(image.getdata())
        match_count = 0
        for pixel in pixels:
            if normalize_pixel(pixel) == self.selected_color:
                match_count += 1

        self.color_count_var.set(f"선택한 색상 픽셀 수: {match_count}")
        self.update_job = self.root.after(250, self.update_ratio)


if __name__ == "__main__":
    root = tk.Tk()
    app = RegionRatioApp(root)
    root.mainloop()
