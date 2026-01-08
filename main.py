import tkinter as tk
from tkinter import ttk

def is_red(pixel):
    r, g, b = pixel
    return r >= 160 and r > g + 40 and r > b + 40


class RegionRatioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("색상 비율 측정기")
        self.region = None
        self.update_job = None

        self.status_var = tk.StringVar(value="영역을 선택하세요.")
        self.red_count_var = tk.StringVar(value="적색 픽셀 수: 0")

        main_frame = ttk.Frame(root, padding=16)
        main_frame.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        select_button = ttk.Button(main_frame, text="영역 선택", command=self.open_selector)
        select_button.grid(row=0, column=0, sticky="w")

        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, sticky="w", pady=(12, 0))

        red_label = ttk.Label(main_frame, textvariable=self.red_count_var, font=("Segoe UI", 14, "bold"))
        red_label.grid(row=2, column=0, sticky="w", pady=(8, 0))

    def open_selector(self):
        selector = tk.Toplevel(self.root)
        selector.attributes("-fullscreen", True)
        selector.attributes("-alpha", 0.3)
        selector.configure(background="black")
        selector.attributes("-topmost", True)
        selector.grab_set()

        canvas = tk.Canvas(selector, cursor="cross", bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

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
                self.status_var.set("선택된 영역에서 적색 픽셀 수를 측정 중입니다.")
                self.start_updates()
            selector.grab_release()
            selector.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)

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
        pixels = list(image.getdata())
        red_count = 0
        for pixel in pixels:
            if is_red(pixel):
                red_count += 1

        self.red_count_var.set(f"적색 픽셀 수: {red_count}")
        self.update_job = self.root.after(250, self.update_ratio)


if __name__ == "__main__":
    root = tk.Tk()
    app = RegionRatioApp(root)
    root.mainloop()
