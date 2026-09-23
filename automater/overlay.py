import tkinter as tk

import cv2
from PIL import Image, ImageTk

from . import capture


def select_region(root, prompt: str = "Drag to select a region  (Esc to cancel)"):
    """Blocking region picker. Returns (x, y, w, h) in screen coords, or None.

    Freezes a screenshot and shows *that* as the overlay's background instead
    of relying on window alpha transparency, which only renders correctly
    under a compositing window manager. This works with any WM.
    """
    result = {"bbox": None}

    screen_bgr = capture.grab()
    screen_rgb = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(screen_rgb)
    width, height = pil_img.width, pil_img.height

    top = tk.Toplevel(root)
    top.overrideredirect(True)
    top.geometry(f"{width}x{height}+0+0")
    top.attributes("-topmost", True)
    top.focus_force()

    canvas = tk.Canvas(top, cursor="cross", highlightthickness=0, width=width, height=height)
    canvas.pack(fill="both", expand=True)

    photo = ImageTk.PhotoImage(pil_img)
    canvas.create_image(0, 0, anchor="nw", image=photo)
    canvas.image = photo  # keep a reference so Tk doesn't garbage-collect it

    # Dim the frozen screenshot via stipple fill (pure software, no compositor
    # needed) so it's visually clear this is "selection mode".
    canvas.create_rectangle(0, 0, width, height, outline="", fill="black", stipple="gray50")
    canvas.create_text(
        20, 20, anchor="nw", fill="yellow", font=("Sans", 14, "bold"), text=prompt
    )

    state = {"x0": 0, "y0": 0, "rect": None}

    def on_press(event):
        state["x0"], state["y0"] = event.x, event.y
        state["rect"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red", width=2
        )

    def on_drag(event):
        if state["rect"] is not None:
            canvas.coords(state["rect"], state["x0"], state["y0"], event.x, event.y)

    def on_release(event):
        x1, y1 = state["x0"], state["y0"]
        x2, y2 = event.x, event.y
        x, y = min(x1, x2), min(y1, y2)
        w, h = abs(x2 - x1), abs(y2 - y1)
        if w > 3 and h > 3:
            result["bbox"] = (x, y, w, h)
        top.destroy()

    def on_escape(_event):
        result["bbox"] = None
        top.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    top.bind("<Escape>", on_escape)

    top.grab_set()
    root.wait_window(top)
    return result["bbox"]


def countdown(root, seconds: int, message: str):
    """Blocking on-screen countdown, e.g. to give the user time to open a
    dropdown/calendar manually before the next capture."""
    top = tk.Toplevel(root)
    top.overrideredirect(True)
    top.attributes("-topmost", True)
    top.configure(bg="black")
    label = tk.Label(
        top, fg="yellow", bg="black", font=("Sans", 18, "bold"), padx=20, pady=12
    )
    label.pack()
    top.update_idletasks()
    sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
    w, h = top.winfo_width(), top.winfo_height()
    top.geometry(f"+{(sw - w) // 2}+{40}")

    remaining = {"n": seconds}

    def tick():
        label.config(text=f"{message} {remaining['n']}...")
        if remaining["n"] <= 0:
            top.destroy()
            return
        remaining["n"] -= 1
        top.after(1000, tick)

    tick()
    root.wait_window(top)
